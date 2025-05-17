# -*- coding: utf-8 -*-
"""Enhanced Intent Classification Agent using PydanticAI."""

import json
import logging
import time
import traceback
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelHTTPError

from app.core.config import settings
from app.schemas.user_query import (
    UserQuery, IntentOutput, EntityType, Entity, 
    QueryType
)

# Import standard agent if needed for reference
from app.agents.base_intent_agent import DatabaseContext

# Set DSPY_AVAILABLE to False permanently
DSPY_AVAILABLE = False

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

# Variables for optimized predictor
dspy_predictor = None
dspy_enhanced_predictor = None
is_optimized = False


# Rest of the agent implementation
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


def optimize_predictor(training_examples=None):
    """Optimize the intent predictor with training data."""
    global is_optimized
    
    # We always set is_optimized to True even though we're not using DSPy
    is_optimized = True
    
    # Log that we're skipping DSPy optimization
    logger.info("DSPy optimization is disabled, skipping optimization")
    
    return None  # Return None since we're not creating an optimized predictor


async def classify_intent_enhanced(
    user_query: str, 
    database_schema: Dict, 
    use_dspy: bool = False
) -> IntentOutput:
    """
    Enhanced intent classification using PydanticAI.
    
    Args:
        user_query: User's natural language query
        database_schema: Database schema information
        use_dspy: Set to False since DSPy is not available
        
    Returns:
        IntentOutput: Classification of the query intent
    """
    # Use PydanticAI for intent classification
    try:
        # Create context for the agent
        context = DatabaseContext(database_schema=database_schema, user_query=UserQuery(text=user_query))
        
        start_time = time.time()
        response = await enhanced_intent_agent.run(user_query, deps=context)
        elapsed = time.time() - start_time
        
        # Log performance metrics
        logger.info(f"Intent classification completed in {elapsed:.2f}s")
        
        return response.data
    except ModelHTTPError as e:
        # Log the error and traceback
        logger.error(f"Error in enhanced intent classification: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Fall back to base classifier
        from app.agents.base_intent_agent import classify_intent
        logger.info("Falling back to base intent classifier")
        return await classify_intent(user_query, database_schema)
    except Exception as e:
        # Log the error and traceback
        logger.error(f"Unexpected error in enhanced intent classification: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Fall back to base classifier
        from app.agents.base_intent_agent import classify_intent
        logger.info("Falling back to base intent classifier")
        return await classify_intent(user_query, database_schema) 