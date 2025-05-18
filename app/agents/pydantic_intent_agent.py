# -*- coding: utf-8 -*-
"""Enhanced Intent Classification Agent using PydanticAI."""

import logging
from typing import Dict, List, Optional

# json/BaseModel/Field removed – not referenced
from pydantic_ai import Agent, RunContext

from app.core.config import settings
from app.schemas.user_query import (
    UserQuery,
    IntentOutput,
)

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
    
    CRITICALLY IMPORTANT FOR QUERY REFINEMENTS:
    - When dealing with follow-up queries or refinements (e.g., "and show me products with weight > 30"), 
      treat these as ADDITIONS to the previous query, not as standalone queries
    - Look for markers like "and", "also", "with", "plus", etc. at the start of a query
    - For query refinements, include entities and conditions from previous queries in your analysis
    - Set "is_query_refinement" to true in the metadata field when a query builds on previous ones
    - Add all entities from both the current query and relevant previous queries
    
    For multi-turn conversations:
    - Consider the context from previous exchanges
    - Recognize references to previous queries or results
    - Understand implicit references (it, that, these, etc.)
    - Preserve filters from previous queries when new queries are refinements
    - When a query starts with conjunctions or phrases that suggest continuation, 
      maintain the context established in previous queries
    
    For purely conversational messages with no database query intent:
    - Set the metadata field "is_database_query" to false
    - Set the query_type to "UNKNOWN" 
    - In the explanation field, respond NATURALLY as a helpful assistant would
    - DO NOT explain that it's not a database query - just respond conversationally
    - Keep your conversational responses brief, friendly and natural
    - Respond directly to greetings, questions about capabilities, or other conversational messages
    
    Always ensure your response is in the correct structured JSON format matching the expected result type.
    
    Respond with a structured analysis of the query intent, but do not generate SQL code yet.
    """,
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
                constraints.append(
                    f"FOREIGN KEY -> {fk_info['table']}.{fk_info['column']}"
                )
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

    # Add conversation history context if available
    conversation_context = ""
    previous_query_info = ""
    previous_sql = ""
    # previous_entities = []  # Commented out unused variable

    # Check for conversation history to determine if this is a follow-up question
    has_conversation_history = False  # This will be overridden in the actual implementation
    
    # Get last conversation message
    if has_conversation_history:
        # Get most recent message with a query
        # This is a placeholder that will be replaced in the actual implementation
        pass

    # Check if the current query appears to be a refinement
    user_query_text = ctx.deps.user_query.text.lower().strip()
    refinement_markers = [
        "and",
        "also",
        "with",
        "plus",
        "but",
        "or",
        "except",
        "excluding",
        "including",
    ]
    is_likely_refinement = any(
        user_query_text.startswith(marker) for marker in refinement_markers
    )

    refinement_context = ""
    if is_likely_refinement and previous_sql:
        refinement_context = f"""
        IMPORTANT: The current query appears to be refining a previous query.
        Previous query: {previous_query_info}
        Previous SQL: {previous_sql}
        
        You should treat this as a continuation of the previous query and preserve relevant context.
        """

    return f"""
    DATABASE SCHEMA:
    {schema_text}
    
    USER QUERY:
    {ctx.deps.user_query.text}
    
    {refinement_context}
    
    Please analyze this query carefully to determine the SQL operation type and extract all entities.
    """


async def classify_intent_enhanced(
    user_query: str,
    database_schema: Dict,
    conversation_history: Optional[List[Dict]] = None,
) -> IntentOutput:
    """
    Enhanced intent classification using PydanticAI.

    Args:
        user_query: User's natural language query
        database_schema: Database schema information
        conversation_history: Optional conversation history

    Returns:
        IntentOutput: Classified intent
    """
    try:
        # Convert string to UserQuery
        user_query_obj = UserQuery(text=user_query)
        
        # Create database context
        context = DatabaseContext(
            database_schema=database_schema,
            user_query=user_query_obj,
        )
        
        # Run the intent agent asynchronously with additional context
        result = await enhanced_intent_agent.run(
            user_query + ("\n\n---\n\n" + str(conversation_history) if conversation_history else ""), 
            deps=context
        )

        return result.data
    except Exception as e:
        # Log the error
        logger.error(f"Error in enhanced intent classification: {str(e)}")
        
        # Fall back to base agent
        from app.agents.base_intent_agent import classify_intent
        
        logger.info("Falling back to base intent classifier")
        return await classify_intent(
            user_query=user_query,
            database_schema=database_schema,
            conversation_history=conversation_history
        )
