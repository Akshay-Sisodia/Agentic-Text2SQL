"""Optimized SQL Generation Agent using DSPy for prompt optimization."""

import logging
import time
import json
from typing import Dict, List, Optional, Union, Any

import dspy
from dspy.teleprompt import BootstrapFewShot

from app.core.config import settings
from app.schemas.sql import (DatabaseInfo, SQLGenerationInput, 
                            SQLGenerationOutput)
from app.schemas.user_query import IntentOutput, UserQuery, EntityType
from app.agents.pydantic_sql_agent import enhanced_sql_agent

# Set up logger
logger = logging.getLogger(__name__)


class SQLPredictor(dspy.Module):
    """DSPy module wrapper for the SQL generation agent."""
    
    def __init__(self, agent):
        """
        Initialize the SQLPredictor.
        
        Args:
            agent: The PydanticAI agent to wrap
        """
        super().__init__()
        self.agent = agent
        self.signature = dspy.Signature(
            instructions="Generate a SQL query based on the user's intent and database schema",
            user_query=dspy.InputField(desc="User's natural language query"),
            intent=dspy.InputField(desc="Classified intent of the query"),
            database_schema=dspy.InputField(desc="Database schema information"),
            conversation_history=dspy.InputField(desc="Previous conversation turns"),
            sql=dspy.OutputField(desc="Generated SQL query"),
            explanation=dspy.OutputField(desc="Explanation of the SQL query"),
            confidence=dspy.OutputField(desc="Confidence score (0.0-1.0)"),
            referenced_tables=dspy.OutputField(desc="Tables referenced in the query"),
            referenced_columns=dspy.OutputField(desc="Columns referenced in the query")
        )
    
    def forward(self, user_query, intent, database_schema, conversation_history=None):
        """
        Process a query with the SQL agent.
        
        Args:
            user_query: The user's natural language query
            intent: The classified intent
            database_schema: The database schema
            conversation_history: Previous conversation turns
            
        Returns:
            dspy.Prediction: The prediction result
        """
        # Convert string to UserQuery if needed
        if isinstance(user_query, str):
            user_query_obj = UserQuery(text=user_query)
        else:
            user_query_obj = user_query
            
        # Create input for SQL generation
        input_data = SQLGenerationInput(
            user_query=user_query_obj,
            intent=intent,
            database_info=database_schema,
            conversation_history=conversation_history or [],
        )
        
        # Run the SQL agent synchronously
        result = self.agent.run_sync("", deps=input_data)
        
        # Return prediction in DSPy format
        return dspy.Prediction(
            sql=result.data.sql,
            explanation=result.data.explanation,
            confidence=float(result.data.confidence),
            referenced_tables=result.data.referenced_tables,
            referenced_columns=result.data.referenced_columns
        )


class EnhancedSQLPredictor(dspy.ChainOfThought):
    """Enhanced DSPy module with step-by-step reasoning for SQL generation."""
    
    def __init__(self, predictor):
        """
        Initialize the EnhancedSQLPredictor.
        
        Args:
            predictor: The base predictor to enhance with step-by-step reasoning
        """
        super().__init__(predictor.signature)
        self.predictor = predictor
        self.agent = predictor.agent
    
    def forward(self, user_query, intent, database_schema, conversation_history=None):
        """
        Process a query with step-by-step reasoning before SQL generation.
        
        Args:
            user_query: The user's natural language query
            intent: The classified intent
            database_schema: The database schema
            conversation_history: Previous conversation turns
            
        Returns:
            dspy.Prediction: The prediction result with reasoning
        """
        # First analyze the query to develop a plan
        reasoning = self.solve(
            user_query=user_query,
            intent=intent,
            database_schema=database_schema,
            conversation_history=conversation_history
        )
        
        # Convert string to UserQuery if needed
        if isinstance(user_query, str):
            user_query_obj = UserQuery(text=user_query)
        else:
            user_query_obj = user_query
            
        # Create input for SQL generation
        input_data = SQLGenerationInput(
            user_query=user_query_obj,
            intent=intent,
            database_info=database_schema,
            conversation_history=conversation_history or [],
        )
        
        # Run the SQL agent with the enhanced context
        result = self.agent.run_sync(
            "",
            deps=input_data,
            config={"additional_context": reasoning}  # Pass reasoning as additional context
        )
        
        # Return prediction in DSPy format
        return dspy.Prediction(
            sql=result.data.sql,
            explanation=result.data.explanation,
            confidence=float(result.data.confidence),
            referenced_tables=result.data.referenced_tables,
            referenced_columns=result.data.referenced_columns
        )


# Sample training examples for the SQL generator
SAMPLE_TRAINING_EXAMPLES = [
    dspy.Example(
        user_query="Show me all customers from New York",
        intent=IntentOutput(
            query_type=EntityType.SELECT,
            entities=[
                {"name": "customers", "type": "TABLE"},
                {"name": "city", "type": "COLUMN"},
                {"name": "New York", "type": "VALUE"}
            ],
            is_ambiguous=False,
        ),
        database_schema=DatabaseInfo(
            tables=[{
                "name": "customers",
                "columns": [
                    {"name": "id", "data_type": "INTEGER", "primary_key": True},
                    {"name": "name", "data_type": "VARCHAR", "nullable": False},
                    {"name": "city", "data_type": "VARCHAR"},
                    {"name": "state", "data_type": "VARCHAR"},
                    {"name": "country", "data_type": "VARCHAR"}
                ],
                "primary_keys": ["id"]
            }]
        ),
        conversation_history=[],
        sql="SELECT * FROM customers WHERE city = 'New York';",
        explanation="This query retrieves all columns for customers located in New York City.",
        confidence=0.95,
        referenced_tables=["customers"],
        referenced_columns=["customers.city"]
    ),
    dspy.Example(
        user_query="List all orders with their products",
        intent=IntentOutput(
            query_type=EntityType.SELECT,
            entities=[
                {"name": "orders", "type": "TABLE"},
                {"name": "products", "type": "TABLE"}
            ],
            is_ambiguous=False,
        ),
        database_schema=DatabaseInfo(
            tables=[
                {
                    "name": "orders",
                    "columns": [
                        {"name": "id", "data_type": "INTEGER", "primary_key": True},
                        {"name": "customer_id", "data_type": "INTEGER", "foreign_key": "customers.id"},
                        {"name": "order_date", "data_type": "DATE"}
                    ],
                    "primary_keys": ["id"]
                },
                {
                    "name": "order_items",
                    "columns": [
                        {"name": "id", "data_type": "INTEGER", "primary_key": True},
                        {"name": "order_id", "data_type": "INTEGER", "foreign_key": "orders.id"},
                        {"name": "product_id", "data_type": "INTEGER", "foreign_key": "products.id"},
                        {"name": "quantity", "data_type": "INTEGER"}
                    ],
                    "primary_keys": ["id"]
                },
                {
                    "name": "products",
                    "columns": [
                        {"name": "id", "data_type": "INTEGER", "primary_key": True},
                        {"name": "name", "data_type": "VARCHAR"},
                        {"name": "price", "data_type": "DECIMAL"}
                    ],
                    "primary_keys": ["id"]
                }
            ]
        ),
        conversation_history=[],
        sql="""
        SELECT o.id as order_id, o.order_date, p.id as product_id, p.name as product_name, oi.quantity
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        ORDER BY o.id;
        """,
        explanation="This query joins the orders, order_items, and products tables to list all orders along with their associated products. It includes order details, product information, and the quantity ordered.",
        confidence=0.9,
        referenced_tables=["orders", "order_items", "products"],
        referenced_columns=["orders.id", "orders.order_date", "products.id", "products.name", "order_items.quantity", "order_items.order_id", "order_items.product_id"]
    )
]


class OptimizedSQLAgent:
    """Wrapper for the SQL agent with DSPy optimization."""
    
    def __init__(self):
        """Initialize the optimized SQL agent."""
        self.base_agent = enhanced_sql_agent
        self.predictor = SQLPredictor(self.base_agent)
        self.enhanced_predictor = None
        self.is_optimized = False
    
    def optimize(self, training_examples=None):
        """
        Optimize the agent using DSPy.
        
        Args:
            training_examples: Optional list of training examples, uses default if None
        """
        if self.is_optimized:
            return
        
        # Use provided examples or defaults
        examples = training_examples or SAMPLE_TRAINING_EXAMPLES
        
        try:
            # Try to import DSPy optimizers
            try:
                from dspy.teleprompt import BootstrapFewShot, BetterPrompt
            except ImportError:
                logger.warning("Could not import all DSPy optimization modules. Falling back to standard operation.")
                return
            
            # Create DSPy optimizers
            bootstrap = BootstrapFewShot()
            better_prompt = BetterPrompt()
            
            # First use BootstrapFewShot for basic optimization
            logger.info("Optimizing with BootstrapFewShot...")
            optimized_predictor = bootstrap.compile(
                self.predictor,
                examples,
                max_bootstrapped_demos=3
            )
            
            # Then use BetterPrompt for further optimization
            logger.info("Further optimizing with BetterPrompt...")
            final_predictor = better_prompt.compile(
                optimized_predictor,
                examples
            )
            
            # Create an enhanced predictor with chain-of-thought reasoning
            logger.info("Creating enhanced predictor with reasoning...")
            self.enhanced_predictor = EnhancedSQLPredictor(final_predictor)
            
            # Update the base agent's system prompt with the optimized instructions
            optimized_instructions = final_predictor.signature.instructions
            updated_prompt = f"""
            You are an expert SQL writer that generates correct and efficient SQL queries based on natural language requests.
            
            {optimized_instructions}
            
            When generating SQL, you should:
            1. Use the correct SQL dialect for the target database
            2. Include proper table and column names as they appear in the schema
            3. Write queries that are secure and avoid SQL injection vulnerabilities
            4. Optimize queries for performance where possible
            
            Remember to handle edge cases like NULL values, empty results, and data type conversions.
            """
            
            # Use the new prompt for the base agent as well
            self.base_agent._system_prompt = updated_prompt
            
            self.is_optimized = True
            logger.info("SQL agent optimization complete.")
            
        except Exception as e:
            logger.error(f"SQL agent optimization failed: {str(e)}")
            # Fall back to the unoptimized agent
    
    async def generate_sql(
        self,
        user_query: Union[str, UserQuery], 
        intent: IntentOutput, 
        database_info: DatabaseInfo,
        conversation_history: Optional[List[Dict]] = None,
        include_explanation: bool = True
    ) -> SQLGenerationOutput:
        """
        Generate SQL using the optimized agent.
        
        Args:
            user_query: User's natural language query or UserQuery object
            intent: Classification of the query intent
            database_info: Database schema information
            conversation_history: Previous conversation turns
            include_explanation: Whether to include explanation in the output
            
        Returns:
            SQLGenerationOutput: Generated SQL and metadata
        """
        # Convert string query to UserQuery if needed
        if isinstance(user_query, str):
            user_query_obj = UserQuery(text=user_query)
        else:
            user_query_obj = user_query
        
        # Debug logging
        logger.info(f"Generating SQL with DSPy-optimized agent for query: {user_query_obj.text}")
        logger.info(f"Query type from intent: {intent.query_type}")
        logger.info(f"Found {len(intent.entities)} entities")
        
        try:
            # If we have an enhanced predictor, use it
            if self.enhanced_predictor and self.is_optimized:
                dspy_result = self.enhanced_predictor(
                    user_query=user_query_obj.text, 
                    intent=intent,
                    database_schema=database_info,
                    conversation_history=conversation_history
                )
                
                # Convert DSPy result to SQLGenerationOutput
                result = SQLGenerationOutput(
                    sql=dspy_result.sql,
                    explanation=dspy_result.explanation if include_explanation else None,
                    confidence=float(dspy_result.confidence),
                    referenced_tables=dspy_result.referenced_tables,
                    referenced_columns=dspy_result.referenced_columns
                )
                
                return result
            else:
                # Fall back to the PydanticAI enhanced agent
                from app.agents.pydantic_sql_agent import generate_sql_enhanced
                return await generate_sql_enhanced(
                    user_query=user_query_obj,
                    intent=intent,
                    database_info=database_info,
                    conversation_history=conversation_history,
                    include_explanation=include_explanation
                )
                
        except Exception as e:
            logger.error(f"Error generating SQL with optimized agent: {str(e)}")
            # Fall back to the PydanticAI enhanced agent
            from app.agents.pydantic_sql_agent import generate_sql_enhanced
            return await generate_sql_enhanced(
                user_query=user_query_obj,
                intent=intent,
                database_info=database_info,
                conversation_history=conversation_history,
                include_explanation=include_explanation
            )


# Create a singleton instance of the optimized SQL agent
optimized_sql_agent = OptimizedSQLAgent()


async def generate_sql_optimized(
    user_query: Union[str, UserQuery], 
    intent: IntentOutput, 
    database_info: DatabaseInfo,
    conversation_history: Optional[List[Dict]] = None,
    include_explanation: bool = True
) -> SQLGenerationOutput:
    """
    Generate SQL using the DSPy-optimized agent.
    
    Args:
        user_query: User's natural language query or UserQuery object
        intent: Classification of the query intent
        database_info: Database schema information
        conversation_history: Previous conversation turns
        include_explanation: Whether to include explanation in the output
        
    Returns:
        SQLGenerationOutput: Generated SQL and metadata
    """
    # Ensure the agent is optimized
    if not optimized_sql_agent.is_optimized:
        optimized_sql_agent.optimize()
    
    # Generate SQL with the optimized agent
    return await optimized_sql_agent.generate_sql(
        user_query=user_query,
        intent=intent,
        database_info=database_info,
        conversation_history=conversation_history,
        include_explanation=include_explanation
    ) 