#!/usr/bin/env python
"""Test the DSPy-optimized agents."""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# First check if DSPy is available
try:
    import dspy
    DSPY_AVAILABLE = True
except Exception as e:
    logger.warning(f"DSPy not available or initialization error: {str(e)}")
    DSPY_AVAILABLE = False

# Import necessary components
from app.schemas.sql import DatabaseInfo
from app.schemas.user_query import UserQuery, IntentOutput, QueryType, EntityType, Entity
from app.schemas.response import ExplanationType
from app.utils.db_utils import get_sqlite_schema

# Check if we can import the optimized agents
try:
    # Import agents to test
    from app.agents import (
        OPTIMIZED_AGENT_AVAILABLE,
        classify_intent_optimized, 
        generate_sql_optimized, 
        generate_explanation_optimized
    )
    
    # Try to import the actual agent objects to check if they're available
    if OPTIMIZED_AGENT_AVAILABLE:
        from app.agents.dspy_intent_agent import optimized_intent_agent
        from app.agents.dspy_sql_agent import optimized_sql_agent
        from app.agents.dspy_explanation_agent import optimized_explanation_agent
except ImportError:
    logger.error("Could not import optimized agents")
    OPTIMIZED_AGENT_AVAILABLE = False

# Sample database path (update if needed)
DB_PATH = "sample_huge.db"

async def test_optimized_intent_agent():
    """Test the DSPy-optimized intent agent."""
    logger.info("Testing DSPy-optimized intent agent...")
    
    # Get database schema
    db_info = await get_sqlite_schema(DB_PATH)
    
    # Sample query
    query = "Show me all customers from California who placed orders in 2022"
    
    # Run the agent
    try:
        # Check if we have access to the actual optimized agent
        if 'optimized_intent_agent' in globals():
            # Optimize the agent first (if not already optimized)
            if not optimized_intent_agent.is_optimized:
                logger.info("Optimizing intent agent...")
                optimized_intent_agent.optimize()
        
        # Classify intent
        intent = await classify_intent_optimized(query, db_info)
        
        # Log results
        logger.info(f"Query: {query}")
        logger.info(f"Classified intent: {intent.query_type}")
        logger.info(f"Entities: {', '.join([f'{e.name} ({e.type})' for e in intent.entities])}")
        logger.info(f"Is ambiguous: {intent.is_ambiguous}")
        if intent.is_ambiguous:
            logger.info(f"Clarification: {intent.clarification_question}")
        
        return intent
    except Exception as e:
        logger.error(f"Error testing intent agent: {str(e)}")
        raise


async def test_optimized_sql_agent(intent):
    """Test the DSPy-optimized SQL agent."""
    logger.info("\nTesting DSPy-optimized SQL agent...")
    
    # Get database schema
    db_info = await get_sqlite_schema(DB_PATH)
    
    # Create user query
    user_query = UserQuery(text="Show me all customers from California who placed orders in 2022")
    
    # Run the agent
    try:
        # Check if we have access to the actual optimized agent
        if 'optimized_sql_agent' in globals():
            # Optimize the agent first (if not already optimized)
            if not optimized_sql_agent.is_optimized:
                logger.info("Optimizing SQL agent...")
                optimized_sql_agent.optimize()
        
        # Generate SQL
        sql_result = await generate_sql_optimized(
            user_query=user_query,
            intent=intent,
            database_info=db_info,
            conversation_history=[]
        )
        
        # Log results
        logger.info(f"Generated SQL: {sql_result.sql}")
        logger.info(f"Explanation: {sql_result.explanation}")
        logger.info(f"Referenced tables: {', '.join(sql_result.referenced_tables)}")
        logger.info(f"Referenced columns: {', '.join(sql_result.referenced_columns)}")
        logger.info(f"Confidence: {sql_result.confidence}")
        
        return sql_result
    except Exception as e:
        logger.error(f"Error testing SQL agent: {str(e)}")
        raise


async def test_optimized_explanation_agent(sql_result):
    """Test the DSPy-optimized explanation agent."""
    logger.info("\nTesting DSPy-optimized explanation agent...")
    
    # Create user query
    user_query = UserQuery(text="Show me all customers from California who placed orders in 2022")
    
    # Mock query result
    query_result = {
        "status": "SUCCESS",
        "rows": [
            {"customer_id": 1, "name": "John Smith", "state": "California", "order_id": 101, "order_date": "2022-05-15"},
            {"customer_id": 3, "name": "Alice Brown", "state": "California", "order_id": 103, "order_date": "2022-07-22"}
        ],
        "column_names": ["customer_id", "name", "state", "order_id", "order_date"],
        "row_count": 2,
        "execution_time": 0.012
    }
    
    # Run the agent
    try:
        # Check if we have access to the actual optimized agent
        if 'optimized_explanation_agent' in globals():
            # Optimize the agent first (if not already optimized)
            if not optimized_explanation_agent.is_optimized:
                logger.info("Optimizing explanation agent...")
                optimized_explanation_agent.optimize()
        
        # Generate explanation
        explanation = await generate_explanation_optimized(
            user_query=user_query,
            sql_generation=sql_result,
            query_result=query_result,
            explanation_type=ExplanationType.EDUCATIONAL
        )
        
        # Log results
        logger.info(f"Explanation: {explanation.text}")
        logger.info(f"Referenced concepts: {', '.join(explanation.referenced_concepts)}")
        
        return explanation
    except Exception as e:
        logger.error(f"Error testing explanation agent: {str(e)}")
        raise


async def main():
    """Main function to run all tests."""
    logger.info("Starting DSPy-optimized agents test...")
    
    # First, check if DSPy and optimized agents are available
    if not DSPY_AVAILABLE:
        logger.error("DSPy not available, cannot run tests.")
        return
    
    if not OPTIMIZED_AGENT_AVAILABLE:
        logger.warning("Optimized agents not available. Tests will run with fallback agents.")
    
    try:
        # Test intent agent
        intent = await test_optimized_intent_agent()
        
        # Test SQL agent
        sql_result = await test_optimized_sql_agent(intent)
        
        # Test explanation agent
        explanation = await test_optimized_explanation_agent(sql_result)
        
        logger.info("\nAll DSPy-optimized agent tests completed successfully!")
    except Exception as e:
        logger.error(f"Test suite failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 