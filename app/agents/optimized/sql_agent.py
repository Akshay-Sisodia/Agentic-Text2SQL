"""Optimized SQL Generation Agent for Text-to-SQL."""

import logging
from typing import Dict, List, Optional, Union

from app.schemas.sql import SQLGenerationOutput
from app.schemas.user_query import IntentOutput, UserQuery
from app.agents.base_sql_agent import generate_sql

# Set up logger
logger = logging.getLogger(__name__)

async def generate_sql_optimized(
    user_query: Union[str, UserQuery],
    intent: IntentOutput,
    database_schema: Dict[str, Dict],
    conversation_history: Optional[List[Dict]] = None,
) -> SQLGenerationOutput:
    """
    Optimized SQL generation function with the same signature as the base function.
    
    This is currently just a wrapper around the base function, but could be optimized in the future.
    
    Args:
        user_query: The user's query text or object
        intent: The classified intent
        database_schema: Database schema information
        conversation_history: Optional conversation history
        
    Returns:
        SQLGenerationOutput: The generated SQL
    """
    logger.info("Using optimized SQL generator")
    
    # For now, just call the base function
    return await generate_sql(
        user_query=user_query,
        intent=intent,
        database_schema=database_schema,
        conversation_history=conversation_history
    ) 