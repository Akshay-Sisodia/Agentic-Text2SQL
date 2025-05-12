# -*- coding: utf-8 -*-
"""Agents for the Text-to-SQL system."""

import logging
import os
import sys
import importlib
import codecs
from types import ModuleType

logger = logging.getLogger(__name__)

# Import and expose base agents
from app.agents.base_intent_agent import classify_intent
from app.agents.base_sql_agent import generate_sql
from app.agents.base_explanation_agent import generate_explanation

# Define flag for DSPy availability and create mock module if needed
DSPY_AVAILABLE = False

# Create a MockDSPy class to use only as fallback if all import attempts fail
class MockDSPy(ModuleType):
    """Mock DSPy module that won't raise errors when attributes are accessed."""
    
    def __getattr__(self, name):
        """Return either a MockDSPy instance or a no-op function."""
        if name.startswith('__'):
            raise AttributeError(f"MockDSPy has no attribute {name}")
        
        # For class-like attributes, return another mock
        return MockDSPy(name)
    
    def __call__(self, *args, **kwargs):
        """Make instances callable and return self."""
        return self

# Define a custom error handler for decoding issues
def custom_decode_error_handler(error):
    """Custom error handler for encoding/decoding errors."""
    # Replace problematic characters with a question mark
    return ('?', error.end)

# Register our custom error handler
codecs.register_error('dspy_replace', custom_decode_error_handler)

# Try to import DSPy with explicit encoding handling
try:
    # First try normal import
    import dspy
    DSPY_AVAILABLE = True
    logger.info("DSPy package loaded successfully via standard import")
except (ImportError, UnicodeDecodeError) as e:
    logger.warning(f"Standard DSPy import failed: {str(e)}")
    logger.info("Trying alternative import methods...")
    
    try:
        # Try to locate the DSPy package
        import site
        dspy_locations = [os.path.join(path, 'dspy') for path in site.getsitepackages()]
        dspy_init_file = None
        
        for loc in dspy_locations:
            if os.path.exists(os.path.join(loc, '__init__.py')):
                dspy_init_file = os.path.join(loc, '__init__.py')
                break
        
        if dspy_init_file:
            logger.info(f"Found DSPy at: {dspy_init_file}")
            
            # Add encoding declaration to the DSPy __init__.py file
            with open(dspy_init_file, 'r', encoding='utf-8', errors='dspy_replace') as f:
                content = f.read()
                
            if "# -*- coding: utf-8 -*-" not in content:
                logger.info("Adding UTF-8 encoding declaration to DSPy __init__.py")
                modified_content = "# -*- coding: utf-8 -*-\n" + content
                with open(dspy_init_file, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
            
            # Try import again after adding encoding declaration
            import importlib
            if 'dspy' in sys.modules:
                del sys.modules['dspy']  # Remove any failed import
            import dspy
            DSPY_AVAILABLE = True
            logger.info("DSPy successfully imported after adding encoding declaration")
        else:
            logger.warning("Could not find DSPy package location")
            sys.modules['dspy'] = MockDSPy('dspy')
            logger.info("Created mock DSPy module as fallback")
    except Exception as alt_e:
        logger.warning(f"All DSPy import attempts failed: {str(alt_e)}")
        # Create mock module as last resort
        sys.modules['dspy'] = MockDSPy('dspy')
        logger.info("Created mock DSPy module as fallback")
except Exception as e:
    logger.warning(f"DSPy not available due to unexpected error: {str(e)}")
    # Create mock module
    sys.modules['dspy'] = MockDSPy('dspy')
    logger.info("Created mock DSPy module due to unexpected error")

# Import enhanced PydanticAI agents
try:
    # First check if PydanticAI is available
    import pydantic_ai
    
    # The agent implementations will check DSPY_AVAILABLE flag internally
    from app.agents.pydantic_intent_agent import classify_intent_enhanced, enhanced_intent_agent
    from app.agents.pydantic_sql_agent import generate_sql_enhanced, enhanced_sql_agent
    from app.agents.pydantic_explanation_agent import generate_explanation_enhanced, enhanced_explanation_agent
    ENHANCED_AGENT_AVAILABLE = True
    logger.info("Enhanced PydanticAI agents loaded successfully")
except ImportError as e:
    # Fall back to standard agents if PydanticAI is not available
    logger.warning(f"PydanticAI not available: {str(e)}, falling back to base agents")
    ENHANCED_AGENT_AVAILABLE = False
    classify_intent_enhanced = classify_intent
    generate_sql_enhanced = generate_sql
    generate_explanation_enhanced = generate_explanation

# Log agent status
if ENHANCED_AGENT_AVAILABLE:
    if DSPY_AVAILABLE:
        logger.info("Enhanced agents with DSPy optimization are available")
    else:
        logger.info("Enhanced agents (without DSPy optimization) are available")
else:
    logger.info("Only base agents are available") 