"""
Agentic Text-to-SQL Application
-------------------------------

A powerful interface for converting natural language to SQL queries.
"""

import logging

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

__version__ = "0.1.0"

# Initialize conversation database
try:
    from app.utils.conversation_db import initialize_conversation_db

    initialize_conversation_db()
except ImportError as e:
    logging.warning(f"Could not initialize conversation database: {str(e)}")
except Exception as e:
    logging.error(f"Error initializing conversation database: {str(e)}")
