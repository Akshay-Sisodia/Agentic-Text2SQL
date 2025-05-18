"""Optimized Intent Classification Agent for Text-to-SQL."""

import logging
from typing import Dict, List, Optional

from app.schemas.user_query import IntentOutput, UserQuery
from app.agents.base_intent_agent import classify_intent

# Set up logger
logger = logging.getLogger(__name__)

async def classify_intent_optimized(
    user_query: str,
    database_schema: Dict[str, Dict],
    conversation_history: Optional[List[Dict]] = None,
) -> IntentOutput:
    """
    Optimized intent classification function with the same signature as the base function.
    
    This is currently just a wrapper around the base function, but could be optimized in the future.
    
    Args:
        user_query: The user's query text
        database_schema: Database schema information
        conversation_history: Optional conversation history
        
    Returns:
        IntentOutput: The classified intent
    """
    logger.info("Using optimized intent classifier")
    
    # For now, just call the base function
    return await classify_intent(
        user_query=user_query,
        database_schema=database_schema,
        conversation_history=conversation_history
    ) 