"""Base Intent Classification Agent for Text-to-SQL using standard LLM approach."""

import json
from typing import Dict, List, Optional

from pydantic_ai import Agent, RunContext

from app.core.config import settings
from app.schemas.user_query import IntentOutput, UserQuery


class DatabaseContext:
    """Database context for agents."""

    def __init__(self, database_schema: Dict, user_query: UserQuery):
        """
        Initialize database context.

        Args:
            database_schema: Database schema information
            user_query: User's natural language query
        """
        self.database_schema = database_schema
        self.user_query = user_query


# Create the intent classification agent
intent_agent = Agent(
    f"{settings.LLM_PROVIDER}:{settings.LLM_MODEL}",
    deps_type=DatabaseContext,
    result_type=IntentOutput,
    system_prompt="""
    You are an expert SQL translator that helps users translate natural language queries into SQL.
    Your task is to analyze the user's query and determine the correct SQL operation to perform.
    
    For each query, you will:
    1. Determine the type of SQL operation (SELECT, INSERT, UPDATE, DELETE, etc.)
    2. Identify key entities mentioned in the query (tables, columns, values, etc.)
    3. Assess if the query is ambiguous and requires clarification
    
    Consider various phrasings and nuances in natural language:
    - Questions that implicitly require data (e.g., "How many customers...?")
    - Requests that don't explicitly mention SQL but need database info (e.g., "Show me sales figures")
    - Ambiguous terms that might refer to different database objects
    - Conversational follow-ups that reference previous queries
    
    If the user's query is purely conversational or doesn't require database access, indicate this in your response.
    
    When dealing with ambiguous queries:
    - Identify what's unclear (table names, column references, etc.)
    - Suggest what clarification is needed
    - Provide options when multiple interpretations are possible
    
    Respond with a structured analysis of the query intent, but do not generate SQL code yet.
    """,
)


@intent_agent.system_prompt
def add_database_context(ctx: RunContext[DatabaseContext]) -> str:
    """
    Add database schema information to the system prompt.

    Args:
        ctx: Run context with database information

    Returns:
        str: Database schema as formatted string
    """
    schema_info = []

    for table_name, table_info in ctx.deps.database_schema.items():
        table_desc = f"Table: {table_name}"
        if table_info.get("description"):
            table_desc += f" - {table_info['description']}"
        schema_info.append(table_desc)

        # Add column information
        for col_name, col_info in table_info.get("columns", {}).items():
            col_type = col_info.get("type", "unknown")
            constraints = []
            if col_info.get("primary_key"):
                constraints.append("PRIMARY KEY")
            if col_info.get("foreign_key"):
                fk_info = col_info["foreign_key"]
                constraints.append(
                    f"FOREIGN KEY -> {fk_info['table']}.{fk_info['column']}"
                )
            if col_info.get("unique"):
                constraints.append("UNIQUE")
            if not col_info.get("nullable", True):
                constraints.append("NOT NULL")

            constraint_str = ", ".join(constraints)
            col_desc = f"  - {col_name} ({col_type})"
            if constraint_str:
                col_desc += f" [{constraint_str}]"
            if col_info.get("description"):
                col_desc += f" - {col_info['description']}"

            schema_info.append(col_desc)

    schema_text = "\n".join(schema_info)
    return f"""
    Here is the database schema information to help you understand the query:
    
    {schema_text}
    
    User's query: "{ctx.deps.user_query.text}"
    
    In addition to analyzing the query intent, please identify if this is a database-related query or 
    just a conversational message. If it's conversational and doesn't require database access, set 
    "is_database_query" to false in the metadata field and provide a helpful response in the explanation field.
    """


@intent_agent.tool
def get_entity_examples(ctx: RunContext[DatabaseContext], entity_type: str) -> str:
    """
    Get examples of entities in the database schema.

    Args:
        ctx: Run context with database information
        entity_type: Type of entity to get examples for (table, column, etc.)

    Returns:
        str: JSON string of entity examples
    """
    examples = {}

    if entity_type.upper() == "TABLE":
        examples["tables"] = list(ctx.deps.database_schema.keys())
    elif entity_type.upper() == "COLUMN":
        column_examples = {}
        for table, table_info in ctx.deps.database_schema.items():
            column_examples[table] = list(table_info.get("columns", {}).keys())
        examples["columns"] = column_examples
    elif entity_type.upper() == "PRIMARY_KEY":
        pk_examples = {}
        for table, table_info in ctx.deps.database_schema.items():
            pks = [
                col
                for col, info in table_info.get("columns", {}).items()
                if info.get("primary_key")
            ]
            if pks:
                pk_examples[table] = pks
        examples["primary_keys"] = pk_examples
    elif entity_type.upper() == "FOREIGN_KEY":
        fk_examples = {}
        for table, table_info in ctx.deps.database_schema.items():
            fks = {}
            for col, info in table_info.get("columns", {}).items():
                if info.get("foreign_key"):
                    fk_info = info["foreign_key"]
                    fks[col] = f"{fk_info['table']}.{fk_info['column']}"
            if fks:
                fk_examples[table] = fks
        examples["foreign_keys"] = fk_examples

    return json.dumps(examples, indent=2)


@intent_agent.tool
def find_similar_entities(
    ctx: RunContext[DatabaseContext], entity_name: str, entity_type: str = "all"
) -> str:
    """
    Find entities with similar names to help disambiguate user queries.

    Args:
        ctx: Run context with database information
        entity_name: The entity name to search for similar matches
        entity_type: Type of entity to search (table, column, all)

    Returns:
        str: JSON string of similar entities
    """
    from difflib import SequenceMatcher

    def similarity_score(a, b):
        """Calculate a similarity score between strings using SequenceMatcher."""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def _find_matches(ctx, entity_name, entity_type, threshold):
        """Internal function to find matches with a given threshold."""
        similar_entities = {}
        
        # Search for similar table names
        if entity_type.lower() in ["table", "all"]:
            similar_tables = []
            for table_name in ctx.deps.database_schema.keys():
                score = similarity_score(entity_name, table_name)
                if score >= threshold:
                    similar_tables.append(
                        {"name": table_name, "similarity": round(score, 2)}
                    )

            # Sort by similarity score, highest first
            similar_tables.sort(key=lambda x: x["similarity"], reverse=True)

            if similar_tables:
                similar_entities["tables"] = similar_tables

        # Search for similar column names
        if entity_type.lower() in ["column", "all"]:
            similar_columns = []
            for table_name, table_info in ctx.deps.database_schema.items():
                for column_name in table_info.get("columns", {}).keys():
                    score = similarity_score(entity_name, column_name)
                    if score >= threshold:
                        similar_columns.append(
                            {
                                "name": column_name,
                                "table": table_name,
                                "similarity": round(score, 2),
                            }
                        )

            # Sort by similarity score, highest first
            similar_columns.sort(key=lambda x: x["similarity"], reverse=True)

            if similar_columns:
                similar_entities["columns"] = similar_columns
                
        return similar_entities

    similar_entities = _find_matches(ctx, entity_name, entity_type, 0.6)
    
    # If no similar entities found, try a lower threshold
    if not similar_entities and 0.6 > 0.4:
        # retry once with a lower threshold
        return json.dumps(
            _find_matches(ctx, entity_name, entity_type, 0.4), indent=2
        )

    return json.dumps(similar_entities, indent=2)


async def classify_intent(
    user_query: str,
    database_schema: Dict,
    conversation_history: Optional[List[Dict]] = None,
) -> IntentOutput:
    """
    Classify the intent of a user's natural language query.

    Args:
        user_query: User's natural language query
        database_schema: Database schema information
        conversation_history: Optional conversation history for context

    Returns:
        IntentOutput: Classification of the query intent
    """
    # Create user query object
    query = UserQuery(text=user_query)

    # Create context
    context = DatabaseContext(database_schema=database_schema, user_query=query)

    # Add conversation history to the system prompt
    additional_context = ""
    if conversation_history and len(conversation_history) > 0:
        # Extract the last few conversational turns (up to 3)
        recent_history = (
            conversation_history[-3:]
            if len(conversation_history) > 3
            else conversation_history
        )
        history_context = []

        for i, msg in enumerate(recent_history):
            if "query" in msg:
                history_context.append(f"User: {msg['query']}")
            if "result" in msg and "message" in msg["result"]:
                history_context.append(f"System: {msg['result']['message']}")

        if history_context:
            additional_context = "\n\nRecent conversation history:\n" + "\n".join(
                history_context
            )

    # Run the intent agent asynchronously with additional context
    result = await intent_agent.run(
        user_query + ("\n\n---\n\n" + additional_context if additional_context else ""), deps=context
    )

    return result.data
