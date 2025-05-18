# -*- coding: utf-8 -*-
"""Enhanced Explanation Agent using PydanticAI."""

import logging
import time
import traceback
from typing import Union, Optional, Dict

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

from app.core.config import settings
from app.schemas.response import ExplanationType, QueryResult, UserExplanation
from app.schemas.sql import SQLGenerationOutput
from app.schemas.user_query import UserQuery

# Set up logger
logger = logging.getLogger(__name__)


class ExplanationInput(BaseModel):
    """Input model for the explanation agent."""

    user_query: UserQuery
    sql_generation: SQLGenerationOutput
    query_result: QueryResult
    explanation_type: ExplanationType = ExplanationType.SIMPLIFIED


# Create the enhanced explanation agent
enhanced_explanation_agent = Agent(
    f"{settings.LLM_PROVIDER}:{settings.LLM_MODEL}",
    deps_type=ExplanationInput,
    result_type=UserExplanation,
    system_prompt="""
    You are an expert SQL educator that explains SQL queries to users of varying technical backgrounds.
    Your task is to generate clear, accurate, and helpful explanations of SQL queries based on the user's preferences.
    
    For each explanation request, you will:
    1. Analyze the SQL query structure and intent
    2. Review the query results 
    3. Generate an explanation tailored to the requested explanation type
    
    Your explanations should be:
    - Accurate and technically sound
    - Clear and understandable for the target audience
    - Focused on the most important aspects of the query
    - Free of technical jargon unless appropriate for the explanation type
    
    Adjust your explanation style based on the explanation type:
    - TECHNICAL: Include SQL concepts, optimization considerations, and detailed breakdown
    - SIMPLIFIED: Focus on what the query does in simple terms without technical details
    - EDUCATIONAL: Explain SQL concepts and syntax with examples from the query
    - BRIEF: Provide a very concise 1-2 sentence summary of the query
    
    Always ensure your response has:
    - A natural language explanation
    - A list of SQL concepts referenced
    - A one-line query summary
    - A clause-by-clause breakdown for TECHNICAL and EDUCATIONAL types
    """,
)


@enhanced_explanation_agent.system_prompt
def add_explanation_context(ctx: RunContext[ExplanationInput]) -> str:
    """
    Add context for SQL query explanation.

    Args:
        ctx: Run context with explanation input

    Returns:
        str: Context information as formatted string
    """
    user_query = ctx.deps.user_query.text
    sql = ctx.deps.sql_generation.sql
    explanation_type = ctx.deps.explanation_type

    # Format the query result information without including actual data
    result_metadata = ""
    if ctx.deps.query_result:
        if (
            hasattr(ctx.deps.query_result, "row_count")
            and ctx.deps.query_result.row_count is not None
        ):
            result_metadata += (
                f"Query returned {ctx.deps.query_result.row_count} rows. "
            )

        if (
            hasattr(ctx.deps.query_result, "column_names")
            and ctx.deps.query_result.column_names
        ):
            column_names = ctx.deps.query_result.column_names
            result_metadata += f"Columns returned: {', '.join(column_names)}. "

        if (
            hasattr(ctx.deps.query_result, "execution_time")
            and ctx.deps.query_result.execution_time
        ):
            result_metadata += (
                f"Execution took {ctx.deps.query_result.execution_time} seconds. "
            )

        if (
            hasattr(ctx.deps.query_result, "error_message")
            and ctx.deps.query_result.error_message
        ):
            result_metadata += f"Query error: {ctx.deps.query_result.error_message}"
    else:
        result_metadata = "No query execution information available."

    # Format explanation type guidance
    explanation_guidance = ""
    if explanation_type == ExplanationType.TECHNICAL:
        explanation_guidance = """
        Provide a TECHNICAL explanation with:
        - Detailed explanation of how the query works
        - Specific SQL concepts and techniques used
        - Efficiency considerations and potential optimizations
        - Clause-by-clause breakdown of the query
        """
    elif explanation_type == ExplanationType.EDUCATIONAL:
        explanation_guidance = """
        Provide an EDUCATIONAL explanation with:
        - Clear explanation of what the query does
        - Explanation of SQL concepts for someone learning SQL
        - Examples of how the syntax works
        - Step-by-step breakdown of the query execution
        """
    elif explanation_type == ExplanationType.SIMPLIFIED:
        explanation_guidance = """
        Provide a SIMPLIFIED explanation with:
        - Plain language description of what the query does
        - Minimal technical jargon
        - Focus on the real-world meaning of the query
        - No detailed SQL syntax explanations
        """
    elif explanation_type == ExplanationType.BRIEF:
        explanation_guidance = """
        Provide a BRIEF explanation with:
        - One or two sentences summarizing what the query does
        - Focus only on the core purpose of the query
        - Skip details about implementation or optimization
        """
    elif explanation_type == ExplanationType.CONVERSATIONAL:
        explanation_guidance = """
        Provide a CONVERSATIONAL explanation with:
        - Natural, friendly language
        - Focus on answering what the user really wants to know
        - Avoid technical details unless directly relevant
        """

    return f"""
    You need to explain the following SQL query:
    
    ```sql
    {sql}
    ```
    
    The query was generated for this user question:
    "{user_query}"
    
    Query execution information:
    {result_metadata}
    
    Explanation Type: {explanation_type.value}
    {explanation_guidance}
    
    Additional context:
    - Tables referenced: {", ".join(ctx.deps.sql_generation.referenced_tables)}
    - Columns referenced: {", ".join(ctx.deps.sql_generation.referenced_columns)}
    - Query type: {ctx.deps.sql_generation.metadata.get("query_type", "Unknown")}
    
    IMPORTANT: DO NOT refer to specific data values from the query results in your explanation,
    as you don't have access to the actual data. Focus only on explaining the query structure
    and its purpose based on the SQL and user question.
    
    Provide your explanation with these components:
    1. text: A natural language explanation
    2. referenced_concepts: List of SQL concepts used in the query
    3. query_summary: One-line summary of what the query does
    4. sql_breakdown: Clause-by-clause breakdown (for TECHNICAL and EDUCATIONAL only)
    """


async def generate_explanation_enhanced(
    user_query: Union[str, UserQuery],
    sql_generation: SQLGenerationOutput,
    query_result: QueryResult,
    explanation_type: ExplanationType = ExplanationType.SIMPLIFIED,
    use_dspy: bool = False,
    database_info: Optional[Dict] = None,
) -> UserExplanation:
    """
    Enhanced explanation generation using PydanticAI.

    Args:
        user_query: User's original query
        sql_generation: Generated SQL and metadata
        query_result: Results from executing the SQL
        explanation_type: Type of explanation to generate
        use_dspy: Whether to use DSPy optimization (not used, kept for compatibility)
        database_info: Optional database schema information (not used, kept for compatibility)

    Returns:
        UserExplanation: Generated explanation
    """
    try:
        # Check if this is a conversational query from metadata
        if getattr(sql_generation, "metadata", None) and sql_generation.metadata.get(
            "is_conversational"
        ):
            # For conversational queries, just return the explanation from SQL generation
            # without any additional framing text
            return UserExplanation(
                type=explanation_type,
                text=getattr(sql_generation, "explanation", "")  # safe access
            )

        # Convert string to UserQuery if needed
        if isinstance(user_query, str):
            user_query_obj = UserQuery(text=user_query)
        else:
            user_query_obj = user_query

        # Create input for explanation generation
        input_data = ExplanationInput(
            user_query=user_query_obj,
            sql_generation=sql_generation,
            query_result=query_result,
            explanation_type=explanation_type,
        )

        start_time = time.time()
        response = await enhanced_explanation_agent.run("", deps=input_data)
        elapsed = time.time() - start_time

        # Log performance metrics
        logger.info(f"Explanation generation completed in {elapsed:.2f}s")

        return response.data
    except Exception as e:
        # Log the error and traceback
        logger.error(f"Unexpected error in enhanced explanation generation: {str(e)}")
        logger.error(traceback.format_exc())

        # Fall back to base generator
        from app.agents.base_explanation_agent import generate_explanation

        logger.info("Falling back to base explanation generator")
        return await generate_explanation(
            user_query, sql_generation, query_result, explanation_type
        )
