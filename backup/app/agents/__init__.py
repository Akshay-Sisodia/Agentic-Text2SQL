"""Agents for the Text-to-SQL system."""

# Import and expose agents
from app.agents.intent_agent import classify_intent
from app.agents.sql_agent import generate_sql
from app.agents.explanation_agent import generate_explanation

# Import enhanced PydanticAI agents
try:
    from app.agents.intent_agent_pydantic import classify_intent_enhanced, enhanced_intent_agent
    from app.agents.sql_agent_pydantic import generate_sql_enhanced, enhanced_sql_agent
    from app.agents.explanation_agent_pydantic import generate_explanation_enhanced, enhanced_explanation_agent
    ENHANCED_AGENT_AVAILABLE = True
except ImportError:
    # Fall back to standard agents if PydanticAI is not available
    ENHANCED_AGENT_AVAILABLE = False
    classify_intent_enhanced = classify_intent
    generate_sql_enhanced = generate_sql
    generate_explanation_enhanced = generate_explanation 