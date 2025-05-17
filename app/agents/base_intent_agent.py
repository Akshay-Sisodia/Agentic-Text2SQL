"""Base Intent Classification Agent for Text-to-SQL using standard LLM approach."""

import json
from typing import Dict, List, Optional

from pydantic_ai import Agent, RunContext

from app.core.config import settings
from app.schemas.user_query import Entity, EntityType, IntentOutput, QueryType, UserQuery


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
    
    Respond with a structured analysis of the query intent, but do not generate SQL code yet.
    """
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
                constraints.append(f"FOREIGN KEY -> {fk_info['table']}.{fk_info['column']}")
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
            pks = [col for col, info in table_info.get("columns", {}).items() 
                  if info.get("primary_key")]
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


async def classify_intent(user_query: str, database_schema: Dict) -> IntentOutput:
    """
    Classify the intent of a user's natural language query.
    
    Args:
        user_query: User's natural language query
        database_schema: Database schema information
        
    Returns:
        IntentOutput: Classification of the query intent
    """
    # Create user query object
    query = UserQuery(text=user_query)
    
    # Create context
    context = DatabaseContext(database_schema=database_schema, user_query=query)
    
    # Run the intent agent asynchronously
    result = await intent_agent.run(user_query, deps=context)
    
    return result.data 