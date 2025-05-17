# -*- coding: utf-8 -*-
"""Enhanced Intent Classification Agent using PydanticAI with optional DSPy optimization."""

import json
import logging
import time
import traceback
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelHTTPError

from app.core.config import settings
from app.schemas.user_query import (
    UserQuery, IntentOutput, EntityType, Entity, 
    QueryType
)

# Import standard agent if needed for reference
from app.agents.base_intent_agent import DatabaseContext

# Check if DSPy is available for optimization
DSPY_AVAILABLE = False
try:
    import dspy
    from dspy.teleprompt import BootstrapFewShot, BetterPrompt, InferRules
    DSPY_AVAILABLE = True
except (ImportError, Exception):
    pass

# Set up logger
logger = logging.getLogger(__name__)


class DatabaseContext:
    """Database context for agents."""
    
    def __init__(self, database_schema: Dict, user_query: UserQuery):
        """
        Initialize database context.
        
        Args:
            database_schema: Database schema information
            user_query: User's natural language query
        """
        self.database_schema = database_schema
        self.user_query = user_query


# Create the enhanced intent classification agent
enhanced_intent_agent = Agent(
    f"{settings.LLM_PROVIDER}:{settings.LLM_MODEL}",
    deps_type=DatabaseContext,
    result_type=IntentOutput,
    system_prompt="""
    You are an expert SQL translator that helps users translate natural language queries into SQL.
    Your task is to analyze the user's query and determine the correct SQL operation to perform.
    
    For each query, you will:
    1. Determine the type of SQL operation (SELECT, INSERT, UPDATE, DELETE, etc.)
    2. Identify key entities mentioned in the query (tables, columns, values, etc.)
    3. Assess if the query is ambiguous and requires clarification
    
    Follow these detailed guidelines:
    - For SELECT queries, identify tables to query from, columns to return, conditions, and any grouping or ordering.
    - For INSERT queries, identify the target table and the values to insert.
    - For UPDATE queries, identify the target table, columns to update, new values, and conditions.
    - For DELETE queries, identify the target table and conditions.
    
    When identifying entities:
    - Extract exact names of tables and columns when mentioned
    - Match entity names to the closest match in the database schema
    - For values, extract the specific values mentioned (numbers, strings, dates)
    - For conditions, identify comparisons (equals, greater than, less than, etc.)
    
    If the query is ambiguous:
    - Flag it as ambiguous
    - Provide a specific clarification question to resolve the ambiguity
    - Focus on resolving table or column ambiguities
    
    Always ensure your response is in the correct structured JSON format matching the expected result type.
    
    Respond with a structured analysis of the query intent, but do not generate SQL code yet.
    """
)

# DSPy optimization components
if DSPY_AVAILABLE:
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
    
    class IntentPredictor(dspy.Module):
        """DSPy module wrapper for the intent classification agent."""
        
        def __init__(self, agent):
            """Initialize the IntentPredictor with the enhanced agent."""
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
            """Process a query with the intent agent."""
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
    
    class EnhancedIntentPredictor(dspy.ChainOfThought):
        """Enhanced DSPy module with step-by-step reasoning for intent classification."""
        
        def __init__(self, predictor):
            """Initialize the EnhancedIntentPredictor with reasoning capabilities."""
            super().__init__(predictor.signature)
            self.predictor = predictor
            self.agent = predictor.agent
        
        def forward(self, query, database_schema):
            """Process a query with step-by-step reasoning."""
            # First analyze the query to develop a plan
            reasoning = self.solve(
                query=query,
                database_schema=database_schema
            )
            
            # Create context for the agent
            context = DatabaseContext(database_schema=database_schema, user_query=UserQuery(text=query))
            
            # Run the intent agent with the enhanced context
            result = self.agent.run_sync(
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

# Rest of the agent implementation
@enhanced_intent_agent.system_prompt
def add_database_context(ctx: RunContext[DatabaseContext]) -> str:
    """
    Add database schema information to the system prompt.
    
    Args:
        ctx: Run context with database information
        
    Returns:
        str: Database schema as formatted string
    """
    schema_info = []
    
    for table_name, table_info in ctx.deps.database_schema.items():
        table_desc = f"Table: {table_name}"
        if table_info.get("description"):
            table_desc += f" - {table_info['description']}"
        schema_info.append(table_desc)
        
        # Add column information
        for col_name, col_info in table_info.get("columns", {}).items():
            col_type = col_info.get("type", "unknown")
            constraints = []
            if col_info.get("primary_key"):
                constraints.append("PRIMARY KEY")
            if col_info.get("foreign_key"):
                fk_info = col_info["foreign_key"]
                constraints.append(f"FOREIGN KEY -> {fk_info['table']}.{fk_info['column']}")
            if col_info.get("unique"):
                constraints.append("UNIQUE")
            if not col_info.get("nullable", True):
                constraints.append("NOT NULL")
                
            constraint_str = ", ".join(constraints)
            col_desc = f"  - {col_name} ({col_type})"
            if constraint_str:
                col_desc += f" [{constraint_str}]"
            if col_info.get("description"):
                col_desc += f" - {col_info['description']}"
                
            schema_info.append(col_desc)
    
    schema_text = "\n".join(schema_info)
    return f"""
    Here is the database schema information to help you understand the query:
    
    {schema_text}
    
    User's query: "{ctx.deps.user_query.text}"
    
    Remember to output a valid structured response with query_type, entities array, is_ambiguous flag, and other required fields.
    """

@enhanced_intent_agent.tool
def get_entity_examples(ctx: RunContext[DatabaseContext], entity_type: str) -> str:
    """
    Get examples of entities in the database schema.
    
    Args:
        ctx: Run context with database information
        entity_type: Type of entity to get examples for (table, column, etc.)
        
    Returns:
        str: JSON string of entity examples
    """
    examples = {}
    
    if entity_type.upper() == "TABLE":
        examples["tables"] = list(ctx.deps.database_schema.keys())
    elif entity_type.upper() == "COLUMN":
        column_examples = {}
        for table, table_info in ctx.deps.database_schema.items():
            column_examples[table] = list(table_info.get("columns", {}).keys())
        examples["columns"] = column_examples
    elif entity_type.upper() == "PRIMARY_KEY":
        pk_examples = {}
        for table, table_info in ctx.deps.database_schema.items():
            pks = [col for col, info in table_info.get("columns", {}).items() 
                  if info.get("primary_key")]
            if pks:
                pk_examples[table] = pks
        examples["primary_keys"] = pk_examples
    elif entity_type.upper() == "FOREIGN_KEY":
        fk_examples = {}
        for table, table_info in ctx.deps.database_schema.items():
            fks = {}
            for col, info in table_info.get("columns", {}).items():
                if info.get("foreign_key"):
                    fk_info = info["foreign_key"]
                    fks[col] = f"{fk_info['table']}.{fk_info['column']}"
            if fks:
                fk_examples[table] = fks
        examples["foreign_keys"] = fk_examples
    
    return json.dumps(examples, indent=2)

@enhanced_intent_agent.tool
def search_schema_entities(ctx: RunContext[DatabaseContext], search_term: str) -> str:
    """
    Search for entities in the database schema by name.
    
    Args:
        ctx: Run context with database information
        search_term: Term to search for in table and column names
        
    Returns:
        str: JSON string of matching entities
    """
    search_term = search_term.lower()
    matches = {
        "tables": [],
        "columns": {}
    }
    
    # Search tables
    for table_name, table_info in ctx.deps.database_schema.items():
        if search_term in table_name.lower():
            table_entry = {
                "name": table_name,
                "description": table_info.get("description", "")
            }
            matches["tables"].append(table_entry)
    
    # Search columns
    for table_name, table_info in ctx.deps.database_schema.items():
        table_columns = []
        for col_name, col_info in table_info.get("columns", {}).items():
            if search_term in col_name.lower():
                col_entry = {
                    "name": col_name,
                    "type": col_info.get("type", "unknown"),
                    "description": col_info.get("description", "")
                }
                table_columns.append(col_entry)
        
        if table_columns:
            matches["columns"][table_name] = table_columns
    
    return json.dumps(matches, indent=2)

async def retry_with_backoff(func, max_retries=3, initial_backoff=1):
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retries
        initial_backoff: Initial backoff time in seconds
        
    Returns:
        Result of the function
    """
    retries = 0
    backoff = initial_backoff
    
    while True:
        try:
            return await func()
        except ModelHTTPError as e:
            if "tool_use_failed" in str(e) and retries < max_retries:
                retries += 1
                wait_time = backoff * (2 ** (retries - 1))
                logger.warning(f"Tool use failed, retrying in {wait_time} seconds (retry {retries}/{max_retries})")
                time.sleep(wait_time)
                
                # We'll continue trying
                continue
            else:
                # If we've exhausted retries or it's another type of error, re-raise
                raise
        except Exception as e:
            logger.error(f"Unexpected error during agent execution: {str(e)}")
            raise

# Initialize DSPy components for optimization
dspy_predictor = None
dspy_enhanced_predictor = None
is_optimized = False

# Function to optimize the agent with DSPy
def optimize_with_dspy(training_examples=None):
    """
    Optimize the agent using DSPy if available.
    
    Args:
        training_examples: Optional list of training examples
        
    Returns:
        bool: Whether optimization was successful
    """
    global dspy_predictor, dspy_enhanced_predictor, is_optimized
    
    if not DSPY_AVAILABLE:
        logger.warning("DSPy not available for optimization")
        return False
    
    if is_optimized:
        return True
    
    try:
        # Use provided examples or defaults
        examples = training_examples or SAMPLE_TRAINING_EXAMPLES
        
        # Create DSPy predictors
        base_predictor = IntentPredictor(enhanced_intent_agent)
        
        # Create DSPy optimizers
        infer_rules = InferRules()
        better_together = BetterPrompt()
        
        # First use BetterPrompt for basic optimization
        logger.info("Optimizing with BetterPrompt...")
        optimized_predictor = better_together.compile(
            base_predictor,
            examples
        )
        
        # Then extract natural language rules if available
        logger.info("Generating natural language rules...")
        nl_rules = infer_rules.induce_natural_language_rules(optimized_predictor, examples)
        
        # Update the program instructions with the rules
        logger.info("Updating program instructions...")
        infer_rules.update_program_instructions(optimized_predictor, nl_rules)
        
        # Create an enhanced predictor with chain-of-thought reasoning
        logger.info("Creating enhanced predictor with reasoning...")
        dspy_predictor = optimized_predictor
        dspy_enhanced_predictor = EnhancedIntentPredictor(optimized_predictor)
        
        # Get the optimized instructions
        optimized_instructions = optimized_predictor.signature.instructions
        
        # Update the original agent's system prompt with optimized instructions
        logger.info("Updating agent system prompt...")
        current_prompt = enhanced_intent_agent.system_prompt_template
        enhanced_prompt = current_prompt + f"\n\nDSPy Optimization Rules:\n{optimized_instructions}\n{nl_rules}"
        enhanced_intent_agent.system_prompt_template = enhanced_prompt
        
        is_optimized = True
        logger.info("Intent agent successfully optimized with DSPy")
        return True
    except Exception as e:
        logger.error(f"Error optimizing with DSPy: {str(e)}\n{traceback.format_exc()}")
        return False

async def classify_intent_enhanced(user_query: str, database_schema: Dict, use_dspy: bool = True) -> IntentOutput:
    """
    Classify the intent of a user's query using the enhanced agent with optional DSPy optimization.
    
    Args:
        user_query: User's natural language query
        database_schema: Database schema information
        use_dspy: Whether to use DSPy optimization if available
        
    Returns:
        IntentOutput: Classification of the query intent
    """
    # Try to optimize with DSPy if requested and not already optimized
    if use_dspy and DSPY_AVAILABLE and not is_optimized:
        optimize_with_dspy()
    
    # If we have an optimized DSPy predictor and it's requested, use it
    if use_dspy and DSPY_AVAILABLE and is_optimized and dspy_enhanced_predictor:
        try:
            # Use the DSPy enhanced predictor with reasoning
            dspy_result = dspy_enhanced_predictor(user_query, database_schema)
            
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
        except Exception as e:
            logger.error(f"Error using DSPy optimized agent, falling back to base enhanced agent: {str(e)}")
            # Fall back to the enhanced agent if there's an error
    
    # Otherwise, use the base enhanced agent
    # Create user query object
    query_obj = UserQuery(text=user_query)
    
    # Create context
    context = DatabaseContext(database_schema=database_schema, user_query=query_obj)
    
    # Define function to run with retry
    async def run_agent():
        return await enhanced_intent_agent.run(user_query, deps=context)
    
    try:
        # Run the agent with retry capability
        result = await retry_with_backoff(run_agent)
        return result.data
    except Exception as e:
        logger.error(f"Error classifying intent: {str(e)}\n{traceback.format_exc()}")
        # Create a basic intent if the agent fails
        return IntentOutput(
            query_type=QueryType.SELECT,
            entities=[],
            is_ambiguous=True,
            clarification_question="I couldn't understand your query. Could you rephrase it?"
        ) 