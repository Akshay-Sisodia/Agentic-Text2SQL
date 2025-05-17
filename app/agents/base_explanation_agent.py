"""Base Explanation Agent for Text-to-SQL using standard LLM approach."""

from typing import Dict, List, Optional, Any

from pydantic_ai import Agent, RunContext

from app.core.config import settings
from app.schemas.response import ExplanationType, UserExplanation
from app.schemas.sql import SQLGenerationOutput
from app.schemas.user_query import UserQuery


class ExplanationContext:
    """Context for explanation generation."""
    
    def __init__(
        self,
        user_query: UserQuery,
        sql_generation: SQLGenerationOutput,
        query_result: Optional[Dict[str, Any]] = None,
        explanation_type: ExplanationType = ExplanationType.SIMPLIFIED
    ):
        """
        Initialize explanation context.
        
        Args:
            user_query: Original user query
            sql_generation: Generated SQL query
            query_result: Result of executing the SQL query
            explanation_type: Type of explanation to generate
        """
        self.user_query = user_query
        self.sql_generation = sql_generation
        self.query_result = query_result
        self.explanation_type = explanation_type


# Create the explanation agent
explanation_agent = Agent(
    f"{settings.LLM_PROVIDER}:{settings.LLM_MODEL}",
    deps_type=ExplanationContext,
    result_type=UserExplanation,
    system_prompt="""
    You are an AI assistant specializing in explaining SQL queries in human-friendly terms.
    Your task is to generate clear, accurate explanations of SQL queries based on the following:
    
    1. The original user question
    2. The SQL query that was generated
    3. The results of the query (if available)
    
    Different users need different types of explanations:
    - TECHNICAL: Include SQL-specific terminology and details for technical users
    - SIMPLIFIED: Use simple language that non-technical users can understand
    - EDUCATIONAL: Provide a learning-oriented explanation that teaches SQL concepts
    - BRIEF: Give a very concise explanation focusing only on the essential results
    
    Adapt your explanation style based on the requested explanation type.
    
    Your explanation should:
    - Accurately describe what the query is doing
    - Highlight key parts of the query and why they matter
    - Be easy to understand for the target audience
    - Use concrete examples from the data where relevant
    - Avoid unnecessary technical jargon unless it's a TECHNICAL explanation
    """
)


@explanation_agent.system_prompt
def add_explanation_context(ctx: RunContext[ExplanationContext]) -> str:
    """
    Add context information to the system prompt.
    
    Args:
        ctx: Run context with explanation context
        
    Returns:
        str: Formatted context information
    """
    user_query = ctx.deps.user_query
    sql_gen = ctx.deps.sql_generation
    query_result = ctx.deps.query_result
    explanation_type = ctx.deps.explanation_type
    
    sql_query = sql_gen.sql
    sql_explanation = sql_gen.explanation or "No explanation provided by SQL generation."
    
    # Format query result if available
    result_text = "No query results available."
    if query_result:
        if "rows" in query_result and query_result["rows"]:
            rows = query_result["rows"]
            result_text = f"Query returned {len(rows)} rows of data.\n"
            
            # Show a sample of the results (up to 3 rows)
            sample_rows = rows[:3]
            sample_text = []
            for i, row in enumerate(sample_rows):
                row_str = ", ".join([f"{k}: {v}" for k, v in row.items()])
                sample_text.append(f"Row {i+1}: {row_str}")
            
            result_text += "Sample results:\n" + "\n".join(sample_text)
            
            if len(rows) > 3:
                result_text += f"\n... and {len(rows) - 3} more rows."
        elif "error_message" in query_result and query_result["error_message"]:
            result_text = f"Query execution failed with error: {query_result['error_message']}"
        elif "row_count" in query_result:
            result_text = f"Query affected {query_result['row_count']} rows."
    
    return f"""
    User's Original Question: "{user_query.text}"
    
    Generated SQL Query:
    ```sql
    {sql_query}
    ```
    
    SQL Generation Explanation:
    {sql_explanation}
    
    Query Execution Results:
    {result_text}
    
    Explanation Type Requested: {explanation_type}
    
    Please generate a {explanation_type.lower()} explanation of this SQL query and its results.
    """


@explanation_agent.tool
def identify_sql_concepts(ctx: RunContext[ExplanationContext], sql_query: str) -> str:
    """
    Identify SQL concepts used in the query for educational explanations.
    
    Args:
        ctx: Run context with explanation context
        sql_query: SQL query to analyze
        
    Returns:
        str: List of SQL concepts used in the query
    """
    # Simple concept identification based on keywords
    concepts = []
    
    sql_query = sql_query.upper()
    
    # Basic query types
    if "SELECT" in sql_query:
        concepts.append("SELECT query - retrieving data from the database")
    if "INSERT" in sql_query:
        concepts.append("INSERT statement - adding new records to the database")
    if "UPDATE" in sql_query:
        concepts.append("UPDATE statement - modifying existing records")
    if "DELETE" in sql_query:
        concepts.append("DELETE statement - removing records from the database")
    
    # Common clauses and operations
    if "JOIN" in sql_query:
        concepts.append("JOIN - combining rows from multiple tables")
    if "WHERE" in sql_query:
        concepts.append("WHERE clause - filtering records")
    if "GROUP BY" in sql_query:
        concepts.append("GROUP BY - grouping records for aggregation")
    if "HAVING" in sql_query:
        concepts.append("HAVING - filtering grouped results")
    if "ORDER BY" in sql_query:
        concepts.append("ORDER BY - sorting results")
    if "LIMIT" in sql_query:
        concepts.append("LIMIT - restricting the number of results")
    
    # Aggregation functions
    if "COUNT" in sql_query:
        concepts.append("COUNT() - counting records")
    if "SUM" in sql_query:
        concepts.append("SUM() - calculating the sum of values")
    if "AVG" in sql_query:
        concepts.append("AVG() - calculating the average of values")
    if "MIN" in sql_query:
        concepts.append("MIN() - finding the minimum value")
    if "MAX" in sql_query:
        concepts.append("MAX() - finding the maximum value")
    
    # Advanced concepts
    if "DISTINCT" in sql_query:
        concepts.append("DISTINCT - removing duplicate results")
    if "UNION" in sql_query:
        concepts.append("UNION - combining results from multiple queries")
    if "CASE" in sql_query:
        concepts.append("CASE statement - conditional logic in SQL")
    if "SUBQUERY" in sql_query or sql_query.count("SELECT") > 1:
        concepts.append("Subquery - nested queries")
    
    return "\n".join([f"- {concept}" for concept in concepts])


async def generate_explanation(
    user_query: UserQuery,
    sql_generation: SQLGenerationOutput,
    query_result: Optional[Dict[str, Any]] = None,
    explanation_type: ExplanationType = ExplanationType.SIMPLIFIED
) -> UserExplanation:
    """
    Generate a human-friendly explanation of a SQL query.
    
    Args:
        user_query: Original user query
        sql_generation: Generated SQL query
        query_result: Result of executing the SQL query
        explanation_type: Type of explanation to generate
        
    Returns:
        UserExplanation: Human-friendly explanation
    """
    # Create context
    context = ExplanationContext(
        user_query=user_query,
        sql_generation=sql_generation,
        query_result=query_result,
        explanation_type=explanation_type
    )
    
    # Run the explanation agent asynchronously
    result = await explanation_agent.run(
        f"Explain the SQL query for '{user_query.text}' in a {explanation_type.value.lower()} style.",
        deps=context
    )
    
    return result.data 