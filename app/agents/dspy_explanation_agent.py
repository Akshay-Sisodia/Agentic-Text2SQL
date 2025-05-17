"""Optimized Explanation Agent using DSPy for prompt optimization."""

import logging
import time
from typing import Dict, List, Optional, Any, Union

import dspy
from dspy.teleprompt import BootstrapFewShot

from app.core.config import settings
from app.schemas.response import ExplanationType, UserExplanation, QueryStatus
from app.schemas.sql import SQLGenerationOutput
from app.schemas.user_query import UserQuery
from app.agents.pydantic_explanation_agent import (
    enhanced_explanation_agent, 
    EnhancedUserExplanation,
    SQLConcept
)

# Set up logger
logger = logging.getLogger(__name__)


class ExplanationPredictor(dspy.Module):
    """DSPy module wrapper for the explanation agent."""
    
    def __init__(self, agent):
        """
        Initialize the ExplanationPredictor.
        
        Args:
            agent: The PydanticAI agent to wrap
        """
        super().__init__()
        self.agent = agent
        self.signature = dspy.Signature(
            instructions="Generate a human-friendly explanation of a SQL query and its results",
            user_query=dspy.InputField(desc="User's original natural language query"),
            sql_generation=dspy.InputField(desc="Generated SQL query and metadata"),
            query_result=dspy.InputField(desc="Results of executing the SQL query"),
            explanation_type=dspy.InputField(desc="Type of explanation to generate (TECHNICAL, SIMPLIFIED, EDUCATIONAL, BRIEF)"),
            text=dspy.OutputField(desc="Human-friendly explanation of the query"),
            referenced_concepts=dspy.OutputField(desc="SQL concepts referenced in the explanation"),
            query_summary=dspy.OutputField(desc="One-line summary of what the query does"),
            sql_breakdown=dspy.OutputField(desc="Clause-by-clause breakdown of the SQL")
        )
    
    def forward(self, user_query, sql_generation, query_result=None, explanation_type=ExplanationType.SIMPLIFIED):
        """
        Generate an explanation with the explanation agent.
        
        Args:
            user_query: The user's original query
            sql_generation: The generated SQL query and metadata
            query_result: The results of executing the SQL query
            explanation_type: The type of explanation to generate
            
        Returns:
            dspy.Prediction: The prediction result
        """
        # Convert string to UserQuery if needed
        if isinstance(user_query, str):
            user_query_obj = UserQuery(text=user_query)
        else:
            user_query_obj = user_query
            
        # Create context for the agent
        from app.agents.pydantic_explanation_agent import ExplanationContext
        context = ExplanationContext(
            user_query=user_query_obj,
            sql_generation=sql_generation,
            query_result=query_result,
            explanation_type=explanation_type
        )
        
        # Run the explanation agent synchronously
        result = self.agent.run_sync("", deps=context)
        
        # Extract data for DSPy output
        concepts = [concept.name for concept in result.data.concepts_used] if hasattr(result.data, "concepts_used") else []
        
        # Return prediction in DSPy format
        return dspy.Prediction(
            text=result.data.text,
            referenced_concepts=concepts,
            query_summary=result.data.query_summary if hasattr(result.data, "query_summary") else None,
            sql_breakdown=result.data.sql_breakdown if hasattr(result.data, "sql_breakdown") else None
        )


class EnhancedExplanationPredictor(dspy.ChainOfThought):
    """Enhanced DSPy module with step-by-step reasoning for explanation generation."""
    
    def __init__(self, predictor):
        """
        Initialize the EnhancedExplanationPredictor.
        
        Args:
            predictor: The base predictor to enhance with step-by-step reasoning
        """
        super().__init__(predictor.signature)
        self.predictor = predictor
        self.agent = predictor.agent
    
    def forward(self, user_query, sql_generation, query_result=None, explanation_type=ExplanationType.SIMPLIFIED):
        """
        Process a query with step-by-step reasoning before explanation generation.
        
        Args:
            user_query: The user's original query
            sql_generation: The generated SQL query and metadata
            query_result: The results of executing the SQL query
            explanation_type: The type of explanation to generate
            
        Returns:
            dspy.Prediction: The prediction result with reasoning
        """
        # First analyze the query to develop a plan for the explanation
        reasoning = self.solve(
            user_query=user_query,
            sql_generation=sql_generation,
            query_result=query_result,
            explanation_type=explanation_type
        )
        
        # Convert string to UserQuery if needed
        if isinstance(user_query, str):
            user_query_obj = UserQuery(text=user_query)
        else:
            user_query_obj = user_query
            
        # Create context for the agent
        from app.agents.pydantic_explanation_agent import ExplanationContext
        context = ExplanationContext(
            user_query=user_query_obj,
            sql_generation=sql_generation,
            query_result=query_result,
            explanation_type=explanation_type
        )
        
        # Run the explanation agent with the enhanced context
        result = self.agent.run_sync(
            "",
            deps=context,
            config={"additional_context": reasoning}  # Pass reasoning as additional context
        )
        
        # Extract data for DSPy output
        concepts = [concept.name for concept in result.data.concepts_used] if hasattr(result.data, "concepts_used") else []
        
        # Return prediction in DSPy format
        return dspy.Prediction(
            text=result.data.text,
            referenced_concepts=concepts,
            query_summary=result.data.query_summary if hasattr(result.data, "query_summary") else None,
            sql_breakdown=result.data.sql_breakdown if hasattr(result.data, "sql_breakdown") else None
        )


# Sample training examples for the explanation generator
SAMPLE_TRAINING_EXAMPLES = [
    dspy.Example(
        user_query="Show me all customers from New York",
        sql_generation=SQLGenerationOutput(
            sql="SELECT * FROM customers WHERE city = 'New York';",
            explanation="This query retrieves all columns for customers located in New York City.",
            confidence=0.95,
            referenced_tables=["customers"],
            referenced_columns=["customers.city"]
        ),
        query_result={
            "status": QueryStatus.SUCCESS,
            "rows": [
                {"id": 1, "name": "John Smith", "city": "New York", "email": "john@example.com"},
                {"id": 5, "name": "Sarah Miller", "city": "New York", "email": "sarah@example.com"}
            ],
            "column_names": ["id", "name", "city", "email"],
            "row_count": 2,
            "execution_time": 0.015
        },
        explanation_type=ExplanationType.SIMPLIFIED,
        text="The query found 2 customers from New York: John Smith and Sarah Miller. It searched the customers table and filtered based on the city field to only show people from New York.",
        referenced_concepts=["WHERE clause", "filtering"],
        query_summary="Shows all customer records from New York city",
        sql_breakdown="SELECT * - Retrieves all columns\nFROM customers - Gets data from the customers table\nWHERE city = 'New York' - Filters to only show New York customers"
    ),
    dspy.Example(
        user_query="List all orders with their products",
        sql_generation=SQLGenerationOutput(
            sql="""
            SELECT o.id as order_id, o.order_date, p.id as product_id, p.name as product_name, oi.quantity
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            ORDER BY o.id;
            """,
            explanation="This query joins the orders, order_items, and products tables to list all orders along with their associated products.",
            confidence=0.9,
            referenced_tables=["orders", "order_items", "products"],
            referenced_columns=["orders.id", "orders.order_date", "products.id", "products.name", "order_items.quantity"]
        ),
        query_result={
            "status": QueryStatus.SUCCESS,
            "rows": [
                {"order_id": 1, "order_date": "2023-01-15", "product_id": 101, "product_name": "Laptop", "quantity": 1},
                {"order_id": 1, "order_date": "2023-01-15", "product_id": 204, "product_name": "Mouse", "quantity": 1},
                {"order_id": 2, "order_date": "2023-01-20", "product_id": 155, "product_name": "Headphones", "quantity": 1}
            ],
            "column_names": ["order_id", "order_date", "product_id", "product_name", "quantity"],
            "row_count": 3,
            "execution_time": 0.025
        },
        explanation_type=ExplanationType.EDUCATIONAL,
        text="This query shows all orders along with the products that were purchased in each order. The query found 3 rows of data across 2 distinct orders. The first order (ID: 1) from January 15, 2023 contained two products: a Laptop and a Mouse. The second order (ID: 2) from January 20, 2023 contained Headphones. The query demonstrates how to join multiple tables to combine related information.",
        referenced_concepts=["JOIN", "table aliases", "ORDER BY"],
        query_summary="Lists all orders with their associated products, showing order details, product information, and quantities",
        sql_breakdown="SELECT o.id as order_id, o.order_date... - Selects specific columns with aliases\nFROM orders o - Gets data from the orders table with alias 'o'\nJOIN order_items oi ON o.id = oi.order_id - Connects orders to their items\nJOIN products p ON oi.product_id = p.id - Connects order items to product details\nORDER BY o.id - Sorts results by order ID"
    )
]


class OptimizedExplanationAgent:
    """Wrapper for the explanation agent with DSPy optimization."""
    
    def __init__(self):
        """Initialize the optimized explanation agent."""
        self.base_agent = enhanced_explanation_agent
        self.predictor = ExplanationPredictor(self.base_agent)
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
            self.enhanced_predictor = EnhancedExplanationPredictor(final_predictor)
            
            # Update the base agent's system prompt with the optimized instructions
            optimized_instructions = final_predictor.signature.instructions
            updated_prompt = f"""
            You are an expert SQL translator and educator who specializes in explaining SQL queries in human-friendly terms.
            
            {optimized_instructions}
            
            You adapt your explanation style based on the requested explanation type:
            - TECHNICAL: Include SQL-specific terminology, query optimization details, and technical insights
            - SIMPLIFIED: Use simple language with minimal technical jargon for non-technical users
            - EDUCATIONAL: Provide a learning-oriented explanation that teaches SQL concepts with examples
            - BRIEF: Give a very concise explanation focusing only on the essential results and their meaning
            """
            
            # Use the new prompt for the base agent as well
            self.base_agent._system_prompt = updated_prompt
            
            self.is_optimized = True
            logger.info("Explanation agent optimization complete.")
            
        except Exception as e:
            logger.error(f"Explanation agent optimization failed: {str(e)}")
            # Fall back to the unoptimized agent
    
    async def generate_explanation(
        self,
        user_query: UserQuery,
        sql_generation: SQLGenerationOutput,
        query_result: Optional[Dict[str, Any]] = None,
        explanation_type: ExplanationType = ExplanationType.SIMPLIFIED,
        schema_info: Optional[Dict[str, Any]] = None
    ) -> UserExplanation:
        """
        Generate an explanation using the optimized agent.
        
        Args:
            user_query: Original user query
            sql_generation: Generated SQL query
            query_result: Result of executing the SQL query
            explanation_type: Type of explanation to generate
            schema_info: Additional database schema information
            
        Returns:
            UserExplanation: Human-friendly explanation
        """
        # Debug logging
        logger.info(f"Generating explanation with DSPy-optimized agent for query: {user_query.text}")
        logger.info(f"Explanation type: {explanation_type}")
        
        try:
            # If we have an enhanced predictor, use it
            if self.enhanced_predictor and self.is_optimized:
                dspy_result = self.enhanced_predictor(
                    user_query=user_query.text,
                    sql_generation=sql_generation,
                    query_result=query_result,
                    explanation_type=explanation_type
                )
                
                # Create SQL concepts from referenced concepts, if any
                concepts_used = []
                if dspy_result.referenced_concepts:
                    for concept in dspy_result.referenced_concepts:
                        concepts_used.append(SQLConcept(
                            name=concept,
                            description=f"Used in the query",
                            level="basic"
                        ))
                
                # Convert DSPy result to EnhancedUserExplanation
                result = EnhancedUserExplanation(
                    text=dspy_result.text,
                    original_query=user_query.text,
                    sql=sql_generation.sql,
                    explanation_type=explanation_type,
                    referenced_concepts=[c.name for c in concepts_used],
                    concepts_used=concepts_used,
                    query_summary=dspy_result.query_summary,
                    sql_breakdown=dspy_result.sql_breakdown
                )
                
                return result
            else:
                # Fall back to the PydanticAI enhanced agent
                from app.agents.pydantic_explanation_agent import generate_explanation_enhanced
                return await generate_explanation_enhanced(
                    user_query=user_query,
                    sql_generation=sql_generation,
                    query_result=query_result,
                    explanation_type=explanation_type,
                    schema_info=schema_info
                )
                
        except Exception as e:
            logger.error(f"Error generating explanation with optimized agent: {str(e)}")
            # Fall back to the PydanticAI enhanced agent
            from app.agents.pydantic_explanation_agent import generate_explanation_enhanced
            return await generate_explanation_enhanced(
                user_query=user_query,
                sql_generation=sql_generation,
                query_result=query_result,
                explanation_type=explanation_type,
                schema_info=schema_info
            )


# Create a singleton instance of the optimized explanation agent
optimized_explanation_agent = OptimizedExplanationAgent()


async def generate_explanation_optimized(
    user_query: UserQuery,
    sql_generation: SQLGenerationOutput,
    query_result: Optional[Dict[str, Any]] = None,
    explanation_type: ExplanationType = ExplanationType.SIMPLIFIED,
    schema_info: Optional[Dict[str, Any]] = None
) -> UserExplanation:
    """
    Generate an explanation using the DSPy-optimized agent.
    
    Args:
        user_query: Original user query
        sql_generation: Generated SQL query
        query_result: Result of executing the SQL query
        explanation_type: Type of explanation to generate
        schema_info: Additional database schema information
        
    Returns:
        UserExplanation: Human-friendly explanation
    """
    # Ensure the agent is optimized
    if not optimized_explanation_agent.is_optimized:
        optimized_explanation_agent.optimize()
    
    # Generate explanation with the optimized agent
    return await optimized_explanation_agent.generate_explanation(
        user_query=user_query,
        sql_generation=sql_generation,
        query_result=query_result,
        explanation_type=explanation_type,
        schema_info=schema_info
    ) 