# -*- coding: utf-8 -*-
"""Agents for the Text-to-SQL system."""

import logging

# Setup logging
logger = logging.getLogger(__name__)

# Import and expose base agents
from app.agents.base_intent_agent import classify_intent
from app.agents.base_sql_agent import generate_sql
from app.agents.base_explanation_agent import generate_explanation

# Import Pydantic-enhanced agents
try:
    # Import enhanced agents
    from app.agents.pydantic_intent_agent import classify_intent_enhanced
    from app.agents.pydantic_sql_agent import generate_sql_enhanced
    from app.agents.pydantic_explanation_agent import generate_explanation_enhanced
    ENHANCED_AGENT_AVAILABLE = True
    logger.info("Enhanced Pydantic agents are available")
except ImportError:
    ENHANCED_AGENT_AVAILABLE = False
    # If we can't import, the enhanced agent is not available
    logger.warning("Enhanced Pydantic agents not available. Using base agents.")
    # Set fallbacks for enhanced agents
    from app.agents.base_intent_agent import classify_intent as classify_intent_enhanced
    from app.agents.base_sql_agent import generate_sql as generate_sql_enhanced
    from app.agents.base_explanation_agent import generate_explanation as generate_explanation_enhanced

# Use the enhanced agents as the optimized versions too
classify_intent_optimized = classify_intent_enhanced
generate_sql_optimized = generate_sql_enhanced
generate_explanation_optimized = generate_explanation_enhanced
OPTIMIZED_AGENT_AVAILABLE = ENHANCED_AGENT_AVAILABLE
