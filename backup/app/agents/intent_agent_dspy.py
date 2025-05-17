"""Intent Classification Agent using PydanticAI with DSPy optimization."""

import json
from typing import Dict, List, Optional

import dspy
from dspy.teleprompt import InferRules, BetterTogether
from pydantic_ai import Agent, RunContext

from app.core.config import settings
from app.schemas.user_query import Entity, EntityType, IntentOutput, QueryType, UserQuery
from app.agents.intent_agent import DatabaseContext, intent_agent, classify_intent

# Add ChainOfThought for better reasoning
class EnhancedIntentPredictor(dspy.ChainOfThought):
    """Enhanced DSPy module with step-by-step reasoning for intent classification."""
    
    def __init__(self, predictor):
        """
        Initialize the EnhancedIntentPredictor.
        
        Args:
            predictor: The base predictor to enhance with step-by-step reasoning
        """
        super().__init__(predictor.signature)
        self.predictor = predictor
        self.agent = predictor.agent
    
    def forward(self, query, database_schema):
        """
        Process a query with step-by-step reasoning before classification.
        
        Args:
            query: The user's natural language query
            database_schema: The database schema information
            
        Returns:
            dspy.Prediction: The prediction result with reasoning
        """
        # First analyze the query to identify key components
        reasoning = self.solve(
            query=query,
            database_schema=database_schema
        )
        
        # Create context for the agent with the reasoning
        context = DatabaseContext(database_schema=database_schema, user_query=UserQuery(text=query))
        
        # Run the intent agent with the enhanced context
        result = self.predictor.agent.run_sync(
            query,
            deps=context,
            config={"additional_context": reasoning}  # Pass reasoning as additional context
        )
        
        # Extract entities list for DSPy
        entities_list = []
        for entity in result.data.entities:
            entities_list.append({
                "name": entity.name,
                "type": entity.type.value
            })
        
        # Return prediction in DSPy format
        return dspy.Prediction(
            intent=result.data.query_type.value,
            entities=entities_list,
            is_ambiguous=result.data.is_ambiguous,
            clarification=result.data.clarification_question
        )


class IntentPredictor(dspy.Module):
    """DSPy module wrapper for the intent classification agent."""
    
    def __init__(self, agent):
        """
        Initialize the IntentPredictor.
        
        Args:
            agent: The PydanticAI agent to wrap
        """
        super().__init__()
        self.agent = agent
        self.signature = dspy.Signature(
            instructions="Analyze the user query to extract SQL intent and entities",
            query=dspy.InputField(desc="User's natural language query"),
            database_schema=dspy.InputField(desc="Database schema information"),
            intent=dspy.OutputField(desc="SQL intent (SELECT, INSERT, etc.)"),
            entities=dspy.OutputField(desc="Entities mentioned in the query"),
            is_ambiguous=dspy.OutputField(desc="Whether the query is ambiguous"),
            clarification=dspy.OutputField(desc="Clarification question if ambiguous")
        )
    
    def forward(self, query, database_schema):
        """
        Process a query with the intent agent.
        
        Args:
            query: The user's natural language query
            database_schema: The database schema information
            
        Returns:
            dspy.Prediction: The prediction result
        """
        # Create context for the agent
        context = DatabaseContext(database_schema=database_schema, user_query=UserQuery(text=query))
        
        # Run the intent agent synchronously
        result = self.agent.run_sync(query, deps=context)
        
        # Extract entities list for DSPy
        entities_list = []
        for entity in result.data.entities:
            entities_list.append({
                "name": entity.name,
                "type": entity.type.value
            })
        
        # Return prediction in DSPy format
        return dspy.Prediction(
            intent=result.data.query_type.value,
            entities=entities_list,
            is_ambiguous=result.data.is_ambiguous,
            clarification=result.data.clarification_question
        )


# Sample training examples for the intent classifier
SAMPLE_TRAINING_EXAMPLES = [
    dspy.Example(
        query="Show me all customers from New York",
        database_schema={
            "customers": {
                "columns": {
                    "id": {"type": "INTEGER", "primary_key": True},
                    "name": {"type": "VARCHAR"},
                    "city": {"type": "VARCHAR"}
                }
            }
        },
        intent="SELECT",
        entities=[
            {"name": "customers", "type": "TABLE"},
            {"name": "city", "type": "COLUMN"},
            {"name": "New York", "type": "VALUE"}
        ],
        is_ambiguous=False,
        clarification=None
    ),
    dspy.Example(
        query="List all orders with their products",
        database_schema={
            "orders": {
                "columns": {
                    "id": {"type": "INTEGER", "primary_key": True},
                    "customer_id": {"type": "INTEGER", "foreign_key": {"table": "customers", "column": "id"}}
                }
            },
            "order_items": {
                "columns": {
                    "id": {"type": "INTEGER", "primary_key": True},
                    "order_id": {"type": "INTEGER", "foreign_key": {"table": "orders", "column": "id"}},
                    "product_id": {"type": "INTEGER", "foreign_key": {"table": "products", "column": "id"}}
                }
            },
            "products": {
                "columns": {
                    "id": {"type": "INTEGER", "primary_key": True},
                    "name": {"type": "VARCHAR"}
                }
            }
        },
        intent="SELECT",
        entities=[
            {"name": "orders", "type": "TABLE"},
            {"name": "products", "type": "TABLE"}
        ],
        is_ambiguous=False,
        clarification=None
    ),
    dspy.Example(
        query="Update John's email address to john@example.com",
        database_schema={
            "users": {
                "columns": {
                    "id": {"type": "INTEGER", "primary_key": True},
                    "name": {"type": "VARCHAR"},
                    "email": {"type": "VARCHAR"}
                }
            }
        },
        intent="UPDATE",
        entities=[
            {"name": "users", "type": "TABLE"},
            {"name": "email", "type": "COLUMN"},
            {"name": "John", "type": "VALUE"},
            {"name": "john@example.com", "type": "VALUE"}
        ],
        is_ambiguous=False,
        clarification=None
    )
]


class OptimizedIntentAgent:
    """Wrapper for the intent agent with DSPy optimization."""
    
    def __init__(self):
        """Initialize the optimized intent agent."""
        self.base_agent = intent_agent
        self.predictor = IntentPredictor(self.base_agent)
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
        
        # Create DSPy optimizers
        infer_rules = InferRules()
        better_together = BetterTogether()
        
        try:
            # First use BetterTogether for overall optimization
            print("Optimizing with BetterTogether...")
            optimized_predictor = better_together.compile(
                self.predictor,
                examples,
                strategy="p -> w -> p"  # Prompt -> Weight -> Prompt optimization
            )
            
            # Then extract natural language rules
            print("Generating natural language rules...")
            nl_rules = infer_rules.induce_natural_language_rules(optimized_predictor, examples)
            
            # Update the program instructions with the rules
            print("Updating program instructions...")
            infer_rules.update_program_instructions(optimized_predictor, nl_rules)
            
            # Create an enhanced predictor with chain-of-thought reasoning
            print("Creating enhanced predictor with reasoning...")
            self.enhanced_predictor = EnhancedIntentPredictor(optimized_predictor)
            
            # Get the optimized instructions
            optimized_instructions = optimized_predictor.signature.instructions
            
            # Update the base agent's system prompt
            print("Updating agent system prompt...")
            updated_prompt = f"""
            You are an expert SQL translator that helps users translate natural language queries into SQL.
            Your task is to analyze the user's query and determine the correct SQL operation to perform.
            
            {optimized_instructions}
            
            For each query, you will:
            1. Determine the type of SQL operation (SELECT, INSERT, UPDATE, DELETE, etc.)
            2. Identify key entities mentioned in the query (tables, columns, values, etc.)
            3. Assess if the query is ambiguous and requires clarification
            
            Respond with a structured analysis of the query intent, but do not generate SQL code yet.
            """
            
            # Create a new agent with the optimized prompt
            self.base_agent = Agent(
                f"{settings.LLM_PROVIDER}:{settings.LLM_MODEL}",
                deps_type=DatabaseContext,
                result_type=IntentOutput,
                system_prompt=updated_prompt
            )
            
            # Add the existing system prompt function for database context
            self.base_agent._system_prompt_funcs = intent_agent._system_prompt_funcs
            
            # Add the existing tools
            self.base_agent._tools = intent_agent._tools
            
            self.is_optimized = True
            print("Optimization complete.")
            
        except Exception as e:
            print(f"Optimization failed: {str(e)}")
            # Fall back to the original agent
    
    async def classify_intent(self, user_query: str, database_schema: Dict) -> IntentOutput:
        """
        Classify the intent of a user's query using the optimized agent.
        
        Args:
            user_query: User's natural language query
            database_schema: Database schema information
            
        Returns:
            IntentOutput: Classification of the query intent
        """
        # Create user query object
        query = UserQuery(text=user_query)
        
        # Create context
        context = DatabaseContext(database_schema=database_schema, user_query=query)
        
        # If we've created an enhanced predictor with reasoning, use it
        if self.enhanced_predictor and self.is_optimized:
            # Run DSPy prediction with reasoning
            dspy_result = self.enhanced_predictor(user_query, database_schema)
            
            # Convert DSPy result back to IntentOutput
            entities = []
            for entity_dict in dspy_result.entities:
                entities.append(Entity(
                    name=entity_dict["name"],
                    type=EntityType(entity_dict["type"])
                ))
            
            return IntentOutput(
                query_type=QueryType(dspy_result.intent),
                entities=entities,
                is_ambiguous=dspy_result.is_ambiguous,
                clarification_question=dspy_result.clarification
            )
        else:
            # Fall back to the base agent if enhanced predictor isn't available
            result = await self.base_agent.run(user_query, deps=context)
            return result.data


# Create a singleton instance of the optimized intent agent
optimized_intent_agent = OptimizedIntentAgent()


async def classify_intent_optimized(user_query: str, database_schema: Dict) -> IntentOutput:
    """
    Classify the intent of a user's query with the optimized agent.
    
    Args:
        user_query: User's natural language query
        database_schema: Database schema information
        
    Returns:
        IntentOutput: Classification of the query intent
    """
    # Ensure the agent is optimized
    if not optimized_intent_agent.is_optimized:
        optimized_intent_agent.optimize()
    
    # Classify intent with the optimized agent
    return await optimized_intent_agent.classify_intent(user_query, database_schema) 