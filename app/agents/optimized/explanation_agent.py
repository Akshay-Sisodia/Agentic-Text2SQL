"""Optimized Explanation Agent for Text-to-SQL."""

import logging
from typing import Dict, Optional, Union, Any

from app.schemas.response import ExplanationType, QueryResult, UserExplanation
from app.schemas.sql import SQLGenerationOutput
from app.schemas.user_query import UserQuery
from app.agents.base_explanation_agent import generate_explanation

# Set up logger
logger = logging.getLogger(__name__)

async def generate_explanation_optimized(
    user_query: Union[str, UserQuery],
    sql_generation: SQLGenerationOutput,
    query_result: Optional[Dict[str, Any]] = None,
    explanation_type: ExplanationType = ExplanationType.SIMPLIFIED,
    database_info: Optional[Dict[str, Any]] = None,  # Added to match the api.py signature
) -> UserExplanation:
    """
    Optimized explanation generation function with the same signature as in api.py.
    
    This is currently just a wrapper around the base function, but could be optimized in the future.
    
    Args:
        user_query: The user's query text or object
        sql_generation: The generated SQL
        query_result: Optional results from executing the SQL
        explanation_type: The type of explanation to generate
        database_info: Optional database schema information (not used, just for compatibility)
        
    Returns:
        UserExplanation: The generated explanation
    """
    logger.info("Using optimized explanation generator")
    
    # For now, just call the base function (ignoring database_info parameter)
    return await generate_explanation(
        user_query=user_query,
        sql_generation=sql_generation,
        query_result=query_result,
        explanation_type=explanation_type
    ) 