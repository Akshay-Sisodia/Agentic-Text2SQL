"""Enhanced Intent Classification Agent using PydanticAI."""

import json
import logging
import time
from typing import Dict, List, Optional
import traceback

from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelHTTPError

from app.core.config import settings
from app.schemas.user_query import Entity, EntityType, IntentOutput, QueryType, UserQuery


# Set up logger
logger = logging.getLogger(__name__)


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


# Create the enhanced intent classification agent
enhanced_intent_agent = Agent(
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
    
    Follow these detailed guidelines:
    - For SELECT queries, identify tables to query from, columns to return, conditions, and any grouping or ordering.
    - For INSERT queries, identify the target table and the values to insert.
    - For UPDATE queries, identify the target table, columns to update, new values, and conditions.
    - For DELETE queries, identify the target table and conditions.
    
    When identifying entities:
    - Extract exact names of tables and columns when mentioned
    - Match entity names to the closest match in the database schema
    - For values, extract the specific values mentioned (numbers, strings, dates)
    - For conditions, identify comparisons (equals, greater than, less than, etc.)
    
    If the query is ambiguous:
    - Flag it as ambiguous
    - Provide a specific clarification question to resolve the ambiguity
    - Focus on resolving table or column ambiguities
    
    Always ensure your response is in the correct structured JSON format matching the expected result type.
    
    Respond with a structured analysis of the query intent, but do not generate SQL code yet.
    """
)


@enhanced_intent_agent.system_prompt
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
    
    Remember to output a valid structured response with query_type, entities array, is_ambiguous flag, and other required fields.
    """


@enhanced_intent_agent.tool
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


@enhanced_intent_agent.tool
def search_schema_entities(ctx: RunContext[DatabaseContext], search_term: str) -> str:
    """
    Search for entities in the database schema by name.
    
    Args:
        ctx: Run context with database information
        search_term: Term to search for in table and column names
        
    Returns:
        str: JSON string of matching entities
    """
    search_term = search_term.lower()
    matches = {
        "tables": [],
        "columns": {}
    }
    
    # Search tables
    for table_name, table_info in ctx.deps.database_schema.items():
        if search_term in table_name.lower():
            table_entry = {
                "name": table_name,
                "description": table_info.get("description", "")
            }
            matches["tables"].append(table_entry)
    
    # Search columns
    for table_name, table_info in ctx.deps.database_schema.items():
        table_columns = []
        for col_name, col_info in table_info.get("columns", {}).items():
            if search_term in col_name.lower():
                col_entry = {
                    "name": col_name,
                    "type": col_info.get("type", "unknown"),
                    "description": col_info.get("description", "")
                }
                table_columns.append(col_entry)
        
        if table_columns:
            matches["columns"][table_name] = table_columns
    
    return json.dumps(matches, indent=2)


async def retry_with_backoff(func, max_retries=3, initial_backoff=1):
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retries
        initial_backoff: Initial backoff time in seconds
        
    Returns:
        Result of the function
    """
    retries = 0
    backoff = initial_backoff
    
    while True:
        try:
            return await func()
        except ModelHTTPError as e:
            if "tool_use_failed" in str(e) and retries < max_retries:
                retries += 1
                wait_time = backoff * (2 ** (retries - 1))
                logger.warning(f"Tool use failed, retrying in {wait_time} seconds (retry {retries}/{max_retries})")
                time.sleep(wait_time)
                
                # We'll continue trying
                continue
            else:
                # If we've exhausted retries or it's another type of error, re-raise
                raise
        except Exception as e:
            logger.error(f"Unexpected error during agent execution: {str(e)}")
            raise


async def classify_intent_enhanced(user_query: str, database_schema: Dict) -> IntentOutput:
    """
    Classify the intent of a user's natural language query using the enhanced agent.
    
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
    
    # Add debug logging
    logger.info(f"Processing query with enhanced intent agent: {user_query}")
    
    # Run the intent agent asynchronously with retry
    try:
        async def run_agent():
            return await enhanced_intent_agent.run(user_query, deps=context)
        
        result = await retry_with_backoff(run_agent)
        
        # Additional logging for debugging
        logger.info(f"Enhanced agent result query type: {result.data.query_type}")
        logger.info(f"Enhanced agent found {len(result.data.entities)} entities")
        
        return result.data
    except Exception as e:
        # On failure, log the error and provide a fallback result
        logger.error(f"Error processing query with enhanced agent: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Create a fallback result
        return IntentOutput(
            query_type=QueryType.UNKNOWN,
            entities=[],
            is_ambiguous=True,
            clarification_question="I couldn't understand your query. Could you please rephrase it?",
            explanation="There was an error processing your query.",
            confidence=0.0,
        ) 