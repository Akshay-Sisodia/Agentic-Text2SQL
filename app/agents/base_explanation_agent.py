"""Base Explanation Agent for Text-to-SQL using standard LLM approach."""

from typing import Dict, Optional, Any
import re

from pydantic_ai import Agent, RunContext

from app.core.config import settings
from app.schemas.response import ExplanationType, UserExplanation
from app.schemas.sql import SQLGenerationOutput
from app.schemas.user_query import UserQuery

# Try to import sqlparse for better SQL parsing
try:
    import sqlparse
    HAS_SQLPARSE = True
except ImportError:
    HAS_SQLPARSE = False


class ExplanationContext:
    """Context for explanation generation."""

    def __init__(
        self,
        user_query: UserQuery,
        sql_generation: SQLGenerationOutput,
        query_result: Optional[Dict[str, Any]] = None,
        explanation_type: ExplanationType = ExplanationType.SIMPLIFIED,
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
    You are an expert at explaining SQL queries in natural, conversational language.
    Your task is to translate complex SQL into clear explanations that non-technical users can understand.
    
    When creating your explanation, you should:
    1. Explain the SQL query in simple terms, focusing on what it accomplishes
    2. Avoid technical jargon unless necessary, and when used, explain it
    3. Match the explanation style to the user's technical level
    4. Break down complex operations into understandable steps
    
    Adapt your explanations based on the requested explanation type:
    - For TECHNICAL explanations: Include details about query structure, joins, indexing, and optimization
    - For SIMPLIFIED explanations: Focus on what the query does in business/functional terms
    - For EDUCATIONAL explanations: Teach SQL concepts while explaining, with helpful analogies
    
    Important considerations:
    - Use natural, conversational language that sounds human
    - Connect the explanation directly to the user's original question
    - Explain any potential limitations or assumptions in the query
    - For complex queries, break down the explanation into logical sections
    - Address potential edge cases (empty results, NULL handling) where relevant
    - Use concrete examples from the data when helpful for understanding
    
    Make your explanation helpful and engaging, focusing on the information the user cares about most.
    """,
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
    sql_explanation = (
        sql_gen.explanation or "No explanation provided by SQL generation."
    )

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
                sample_text.append(f"Row {i + 1}: {row_str}")

            result_text += "Sample results:\n" + "\n".join(sample_text)

            if len(rows) > 3:
                result_text += f"\n... and {len(rows) - 3} more rows."
        elif "error_message" in query_result and query_result["error_message"]:
            result_text = (
                f"Query execution failed with error: {query_result['error_message']}"
            )
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
    
Explanation Type Requested: {explanation_type.value}
    
    Please generate a {explanation_type.value.lower()} explanation of this SQL query and its results.
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

    sql_query_upper = sql_query.upper()

    # Basic query types
    if "SELECT" in sql_query_upper:
        concepts.append("SELECT query - retrieving data from the database")
    if "INSERT" in sql_query_upper:
        concepts.append("INSERT statement - adding new records to the database")
    if "UPDATE" in sql_query_upper:
        concepts.append("UPDATE statement - modifying existing records")
    if "DELETE" in sql_query_upper:
        concepts.append("DELETE statement - removing records from the database")

    # Common clauses and operations
    if "JOIN" in sql_query_upper:
        concepts.append("JOIN - combining rows from multiple tables")
    if "WHERE" in sql_query_upper:
        concepts.append("WHERE clause - filtering records")
    if "GROUP BY" in sql_query_upper:
        concepts.append("GROUP BY - grouping records for aggregation")
    if "HAVING" in sql_query_upper:
        concepts.append("HAVING - filtering grouped results")
    if "ORDER BY" in sql_query_upper:
        concepts.append("ORDER BY - sorting results")
    if "LIMIT" in sql_query_upper:
        concepts.append("LIMIT - restricting the number of results")

    # Aggregation functions
    if "COUNT" in sql_query_upper:
        concepts.append("COUNT() - counting records")
    if "SUM" in sql_query_upper:
        concepts.append("SUM() - calculating the sum of values")
    if "AVG" in sql_query_upper:
        concepts.append("AVG() - calculating the average of values")
    if "MIN" in sql_query_upper:
        concepts.append("MIN() - finding the minimum value")
    if "MAX" in sql_query_upper:
        concepts.append("MAX() - finding the maximum value")

    # Advanced concepts
    if "DISTINCT" in sql_query_upper:
        concepts.append("DISTINCT - removing duplicate results")
    if "UNION" in sql_query_upper:
        concepts.append("UNION - combining results from multiple queries")
    if "CASE" in sql_query_upper:
        concepts.append("CASE statement - conditional logic in SQL")
    
    # More accurate subquery detection
    has_subquery = False
    
    if HAS_SQLPARSE:
        # Parse the SQL query using sqlparse
        try:
            parsed = sqlparse.parse(sql_query)
            if parsed:
                # Get the first statement
                statement = parsed[0]
                # Look for subqueries by checking for nested SELECT tokens
                # This method works by finding tokens of type Token.Keyword.DML with value 'SELECT'
                # that are not the first one in the statement
                tokens = list(statement.flatten())
                select_count = 0
                for token in tokens:
                    if token.ttype is not None and 'Keyword.DML' in str(token.ttype) and token.value.upper() == 'SELECT':
                        select_count += 1
                
                has_subquery = select_count > 1
        except Exception:
            # Fall back to a more conservative regex approach if parsing fails
            # Look for pattern of SELECT inside parentheses
            has_subquery = bool(re.search(r'\(\s*SELECT', sql_query_upper))
    else:
        # Fallback method without sqlparse - look for SELECT inside parentheses
        # This is more reliable than just counting SELECT occurrences
        has_subquery = bool(re.search(r'\(\s*SELECT', sql_query_upper))
    
    if has_subquery:
        concepts.append("Subquery - nested queries")

    return "\n".join([f"- {concept}" for concept in concepts])


async def generate_explanation(
    user_query: UserQuery,
    sql_generation: SQLGenerationOutput,
    query_result: Optional[Dict[str, Any]] = None,
    explanation_type: ExplanationType = ExplanationType.SIMPLIFIED,
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
        explanation_type=explanation_type,
    )

    # Run the explanation agent asynchronously
    result = await explanation_agent.run(
        f"Explain the SQL query for '{user_query.text}' in a {explanation_type.value.lower()} style.",
        deps=context,
    )

    return result.data
