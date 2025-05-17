# -*- coding: utf-8 -*-
"""Enhanced SQL Generation Agent using PydanticAI."""

import json
import logging
import time
import traceback
from typing import Dict, List, Optional, Any, Union

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelHTTPError

from app.core.config import settings
from app.schemas.sql import (
    DatabaseInfo, SQLGenerationInput, SQLGenerationOutput
)
from app.schemas.user_query import (
    UserQuery, IntentOutput, EntityType, Entity, QueryType
)

# Set DSPY_AVAILABLE to False permanently
DSPY_AVAILABLE = False

# Set up logger
logger = logging.getLogger(__name__)

# Variables for optimized predictor
dspy_predictor = None
dspy_enhanced_predictor = None
is_optimized = False

# Create the enhanced SQL generation agent
enhanced_sql_agent = Agent(
    f"{settings.LLM_PROVIDER}:{settings.LLM_MODEL}",
    deps_type=SQLGenerationInput,
    result_type=SQLGenerationOutput,
    system_prompt="""
    You are an expert SQL code generator that helps users translate natural language queries into SQL.
    Your task is to generate syntactically correct SQL based on the user's query and the database schema.
    
    For each query, you should:
    1. Identify the relevant tables and columns from the schema
    2. Construct appropriate SQL that handles the user's intent
    3. Provide a clear explanation of what the SQL does
    
    Follow these detailed guidelines:
    - For SELECT queries, construct proper joins between tables
    - For INSERT queries, ensure all required fields are included
    - For UPDATE queries, include appropriate WHERE conditions
    - For DELETE queries, always include WHERE conditions for safety
    
    Make sure your SQL:
    - Has correct syntax for the detected database type
    - Uses proper quoting for identifiers when needed
    - Handles NULL values appropriately
    - Includes all necessary table qualifiers for column names in joins
    
    Your response should include:
    - The generated SQL query
    - An explanation of what the query does
    - A confidence score from 0.0 to 1.0
    - The list of tables and columns referenced in the query
    
    Always use the schema information provided to generate accurate SQL.
    """
)

def optimize_predictor(training_examples=None):
    """Optimize the SQL predictor with training data."""
    global is_optimized
    
    # We always set is_optimized to True even though we're not using DSPy
    is_optimized = True
    
    # Log that we're skipping DSPy optimization
    logger.info("DSPy optimization is disabled, skipping optimization")
    
    return None  # Return None since we're not creating an optimized predictor

@enhanced_sql_agent.system_prompt
def add_database_context(ctx: RunContext[SQLGenerationInput]) -> str:
    """
    Add database schema and intent information to the system prompt.
    
    Args:
        ctx: Run context with database schema and intent information
        
    Returns:
        str: Database schema and intent as formatted string
    """
    # Format database schema information
    schema_info = []
    for table in ctx.deps.database_info.tables:
        table_desc = f"Table: {table.name}"
        if table.description:
            table_desc += f" - {table.description}"
        schema_info.append(table_desc)
        
        # Add column information
        for column in table.columns:
            constraints = []
            if column.primary_key:
                constraints.append("PRIMARY KEY")
            if column.foreign_key:
                # Handle foreign key as a string in format "table.column"
                fk_str = column.foreign_key
                constraints.append(f"FOREIGN KEY -> {fk_str}")
            if column.unique:
                constraints.append("UNIQUE")
            if not column.nullable:
                constraints.append("NOT NULL")
                
            constraint_str = ", ".join(constraints)
            col_desc = f"  - {column.name} ({column.data_type})"
            if constraint_str:
                col_desc += f" [{constraint_str}]"
            if column.description:
                col_desc += f" - {column.description}"
                
            schema_info.append(col_desc)
            
    # Format conversation history
    conversation_summary = ""
    if ctx.deps.conversation_history and len(ctx.deps.conversation_history) > 0:
        conversation_summary = "\nPrevious conversation:\n"
        for i, conv in enumerate(ctx.deps.conversation_history[-3:]):  # Show last 3 exchanges
            conversation_summary += f"User: {conv.get('user_query', '')}\n"
            if conv.get('generated_sql', ''):
                conversation_summary += f"SQL: {conv.get('generated_sql', '')}\n"
                
    # Format intent information
    intent_info = "No intent information provided."
    if ctx.deps.intent:
        entity_info = []
        for entity in ctx.deps.intent.entities:
            entity_info.append(f"- {entity.name} ({entity.type.value})")
            
        intent_info = f"""
        Query Intent: {ctx.deps.intent.query_type.value}
        Entities:
        {chr(10).join(entity_info)}
        Ambiguous: {"Yes - " + ctx.deps.intent.clarification_question if ctx.deps.intent.is_ambiguous else "No"}
        """
            
    schema_text = "\n".join(schema_info)
    return f"""
    Here is the database schema information to help you generate SQL:
    
    {schema_text}
    
    {intent_info}
    
    User's query: "{ctx.deps.user_query.text}"
    {conversation_summary}
    
    Generate SQL that accurately addresses the user's question.
    Be sure to include all required fields in your response:
    - SQL query
    - Explanation
    - Confidence score
    - Referenced tables and columns
    """

async def generate_sql_enhanced(
    user_query: Union[str, UserQuery], 
    intent: IntentOutput, 
    database_info: DatabaseInfo,
    conversation_history: Optional[List[Dict]] = None,
    include_explanation: bool = True,
    use_dspy: bool = False  # DSPy is not available so this defaults to False
) -> SQLGenerationOutput:
    """
    Enhanced SQL generation using PydanticAI.
    
    Args:
        user_query: User's natural language query
        intent: Classified intent from intent classification
        database_info: Database schema information
        conversation_history: Previous conversation turns
        include_explanation: Whether to include explanation in result
        use_dspy: Set to False since DSPy is not available
        
    Returns:
        SQLGenerationOutput: Generated SQL and metadata
    """
    
    try:
        # Convert string to UserQuery if needed
        if isinstance(user_query, str):
            user_query_obj = UserQuery(text=user_query)
        else:
            user_query_obj = user_query
        
        # Create input for SQL generation
        input_data = SQLGenerationInput(
            user_query=user_query_obj,
            intent=intent,
            database_info=database_info,
            conversation_history=conversation_history or []
        )
        
        start_time = time.time()
        response = await enhanced_sql_agent.run("", deps=input_data)
        elapsed = time.time() - start_time
        
        # Log performance metrics
        logger.info(f"SQL generation completed in {elapsed:.2f}s")
        
        # Return the result, optionally excluding explanation
        result = response.data
        if not include_explanation:
            result.explanation = ""
            
        return result
    except ModelHTTPError as e:
        # Log the error and traceback
        logger.error(f"Error in enhanced SQL generation: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Fall back to base generator
        from app.agents.base_sql_agent import generate_sql
        logger.info("Falling back to base SQL generator")
        return await generate_sql(user_query, intent, database_info, conversation_history, include_explanation)
    except Exception as e:
        # Log the error and traceback
        logger.error(f"Unexpected error in enhanced SQL generation: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Fall back to base generator
        from app.agents.base_sql_agent import generate_sql
        logger.info("Falling back to base SQL generator")
        return await generate_sql(user_query, intent, database_info, conversation_history, include_explanation) 

