# -*- coding: utf-8 -*-
"""Agents for the Text-to-SQL system."""

import logging
import os
import sys
import importlib
from types import ModuleType

logger = logging.getLogger(__name__)

# Import and expose base agents
from app.agents.base_intent_agent import classify_intent
from app.agents.base_sql_agent import generate_sql
from app.agents.base_explanation_agent import generate_explanation

# Define flag for DSPy availability - permanently set to False
DSPY_AVAILABLE = False

# Import enhanced PydanticAI agents
try:
    # First check if PydanticAI is available
    import pydantic_ai
    
    # Import intent agent
    try:
        from app.agents.pydantic_intent_agent import classify_intent_enhanced, enhanced_intent_agent
    except Exception as e:
        logger.warning(f"Error importing pydantic_intent_agent: {str(e)}")
        classify_intent_enhanced = classify_intent
        enhanced_intent_agent = None
    
    # Import SQL agent
    try:
        from app.agents.pydantic_sql_agent import generate_sql_enhanced, enhanced_sql_agent
    except Exception as e:
        logger.warning(f"Error importing pydantic_sql_agent: {str(e)}")
        generate_sql_enhanced = generate_sql
        enhanced_sql_agent = None
    
    # Import explanation agent
    try:
        from app.agents.pydantic_explanation_agent import generate_explanation_enhanced, enhanced_explanation_agent
    except Exception as e:
        logger.warning(f"Error importing pydantic_explanation_agent: {str(e)}")
        generate_explanation_enhanced = generate_explanation
        enhanced_explanation_agent = None
    
    # Check if all enhanced agents were successfully imported
    ENHANCED_AGENT_AVAILABLE = (
        classify_intent_enhanced != classify_intent or
        generate_sql_enhanced != generate_sql or
        generate_explanation_enhanced != generate_explanation
    )
    
    if ENHANCED_AGENT_AVAILABLE:
        logger.info("Enhanced PydanticAI agents loaded successfully")
    else:
        logger.warning("Some enhanced agents failed to load, falling back to base agents")
except ImportError as e:
    # Fall back to standard agents if PydanticAI is not available
    logger.warning(f"PydanticAI not available: {str(e)}, falling back to base agents")
    ENHANCED_AGENT_AVAILABLE = False
    classify_intent_enhanced = classify_intent
    generate_sql_enhanced = generate_sql
    generate_explanation_enhanced = generate_explanation

# Define optimized agent functions - these are fallbacks since DSPy optimization is disabled
classify_intent_optimized = classify_intent_enhanced
generate_sql_optimized = generate_sql_enhanced
generate_explanation_optimized = generate_explanation_enhanced

# Log agent status
if ENHANCED_AGENT_AVAILABLE:
    logger.info("Enhanced agents (without DSPy optimization) are available")
else:
    logger.info("Only base agents are available") 