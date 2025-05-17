# -*- coding: utf-8 -*-
"""Enhanced Explanation Agent using PydanticAI with optional DSPy optimization."""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Union
import backoff
import traceback

from pydantic import BaseModel, Field, model_validator
from pydantic_ai import Agent, RunContext

from app.core.config import settings
from app.schemas.response import ExplanationType, UserExplanation, QueryStatus
from app.schemas.sql import SQLGenerationOutput
from app.schemas.user_query import UserQuery

# Check if DSPy is available for optimization
DSPY_AVAILABLE = False
try:
    import dspy
    from dspy.teleprompt import BootstrapFewShot, BetterPrompt
    DSPY_AVAILABLE = True
except (ImportError, Exception):
    pass

# Set up logging
logger = logging.getLogger(__name__)


class ExplanationError(Exception):
    """Exception raised for errors during explanation generation."""
    pass


class SQLConcept(BaseModel):
    """SQL concept identified in a query."""
    name: str = Field(..., description="Name of the SQL concept")
    description: str = Field(..., description="Brief description of the concept")
    example: Optional[str] = Field(None, description="Example of the concept from the query")
    level: str = Field("basic", description="Complexity level (basic, intermediate, advanced)")


class QueryResultSummary(BaseModel):
    """Summary of query execution results."""
    status: str = Field(..., description="Execution status (success, error, etc.)")
    row_count: Optional[int] = Field(None, description="Number of rows returned or affected")
    sample_data: Optional[str] = Field(None, description="Sample of the returned data")
    error_details: Optional[str] = Field(None, description="Details about any errors that occurred")
    execution_time: Optional[float] = Field(None, description="Time taken to execute the query (seconds)")


class EnhancedUserExplanation(UserExplanation):
    """Enhanced human-readable explanation of a query with additional context."""
    sql_breakdown: Optional[str] = Field(None, description="Clause-by-clause breakdown of the SQL")
    concepts_used: List[SQLConcept] = Field(default_factory=list, description="SQL concepts used in the query")
    query_summary: Optional[str] = Field(None, description="One-line summary of what the query does")
    result_summary: Optional[QueryResultSummary] = Field(None, description="Summary of query results")
    
    @model_validator(mode='after')
    def extract_referenced_concepts(self):
        """Extract referenced concepts from concepts_used."""
        self.referenced_concepts = [concept.name for concept in self.concepts_used]
        return self


class ExplanationContext:
    """Context for explanation generation."""
    
    def __init__(
        self,
        user_query: UserQuery,
        sql_generation: SQLGenerationOutput,
        query_result: Optional[Dict[str, Any]] = None,
        explanation_type: ExplanationType = ExplanationType.SIMPLIFIED,
        schema_info: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize explanation context.
        
        Args:
            user_query: Original user query
            sql_generation: Generated SQL query
            query_result: Result of executing the SQL query
            explanation_type: Type of explanation to generate
            schema_info: Additional database schema information
        """
        self.user_query = user_query
        self.sql_generation = sql_generation
        self.query_result = query_result
        self.explanation_type = explanation_type
        self.schema_info = schema_info or {}


# Create the enhanced explanation agent
enhanced_explanation_agent = Agent(
    f"{settings.LLM_PROVIDER}:{settings.LLM_MODEL}",
    deps_type=ExplanationContext,
    result_type=EnhancedUserExplanation,
    system_prompt="""
    You are an expert SQL translator and educator who specializes in explaining SQL queries in human-friendly terms.
    Your task is to generate clear, accurate, and insightful explanations of SQL queries based on the following context:
    
    1. The original user question
    2. The SQL query that was generated to answer that question
    3. The results of the query execution (if available)
    4. Database schema information (if provided)
    
    You adapt your explanation style based on the requested explanation type:
    - TECHNICAL: Include SQL-specific terminology, query optimization details, and technical insights
    - SIMPLIFIED: Use simple language with minimal technical jargon for non-technical users
    - EDUCATIONAL: Provide a learning-oriented explanation that teaches SQL concepts with examples
    - BRIEF: Give a very concise explanation focusing only on the essential results and their meaning
    
    Your explanation should:
    - Accurately describe what the query is doing and why
    - Break down complex queries into logical components
    - Connect the query directly to the user's original question
    - Highlight key parts of the query and why they matter
    - Use concrete examples from the actual data where relevant
    - Identify and explain SQL concepts at an appropriate level
    - Address any errors or performance issues that may have occurred
    
    Provide additional context based on the type of explanation requested, and always ensure
    that your explanation helps users understand both the SQL mechanics and the business insights
    gained from the query.
    """
)

# DSPy optimization components
if DSPY_AVAILABLE:
    # Sample training examples for the explanation generator
    SAMPLE_TRAINING_EXAMPLES = [
        dspy.Example(
            user_query="Show me all customers from New York",
            sql_generation=SQLGenerationOutput(
                sql="SELECT * FROM customers WHERE city = 'New York'",
                confidence=0.95,
                referenced_tables=["customers"],
                referenced_columns=["customers.city"],
                query_type="SELECT"
            ),
            query_result={
                "status": "SUCCESS",
                "rows": [{"id": 1, "name": "John Smith", "city": "New York"}, 
                         {"id": 2, "name": "Jane Doe", "city": "New York"}],
                "row_count": 2,
                "execution_time": 0.05
            },
            explanation_type=ExplanationType.SIMPLIFIED,
            text="This query lists all customers who are from New York City. It found 2 customers: John Smith and Jane Doe.",
            referenced_concepts=["WHERE clause", "Equality comparison"],
            query_summary="Retrieves customers filtered by city",
            sql_breakdown="SELECT * - Gets all customer data\nFROM customers - From the customers table\nWHERE city = 'New York' - Filters to only show New York customers"
        ),
        dspy.Example(
            user_query="What's the average order amount by product category?",
            sql_generation=SQLGenerationOutput(
                sql="SELECT p.category, AVG(oi.price * oi.quantity) as avg_order_amount FROM order_items oi JOIN products p ON oi.product_id = p.id GROUP BY p.category",
                confidence=0.9,
                referenced_tables=["order_items", "products"],
                referenced_columns=["products.category", "order_items.price", "order_items.quantity"],
                query_type="SELECT"
            ),
            query_result={
                "status": "SUCCESS",
                "rows": [{"category": "Electronics", "avg_order_amount": 120.50}, 
                         {"category": "Clothing", "avg_order_amount": 45.75}],
                "row_count": 2,
                "execution_time": 0.15
            },
            explanation_type=ExplanationType.EDUCATIONAL,
            text="This query calculates the average order amount for each product category. It joins the order_items table with the products table to access the category information, then uses the AVG function to calculate the average of price multiplied by quantity. The results show Electronics items have an average order amount of $120.50, while Clothing items average $45.75.",
            referenced_concepts=["JOIN", "GROUP BY", "Aggregation function", "Table alias"],
            query_summary="Calculates average order amounts grouped by product category",
            sql_breakdown="SELECT p.category - Gets the product category\nAVG(oi.price * oi.quantity) - Calculates average order amount\nFROM order_items oi JOIN products p - Joins the order items and products tables\nON oi.product_id = p.id - Links products to their orders\nGROUP BY p.category - Groups results by product category"
        )
    ]
    
    class ExplanationPredictor(dspy.Module):
        """DSPy module wrapper for the explanation generation agent."""
        
        def __init__(self, agent):
            """Initialize the ExplanationPredictor with the enhanced agent."""
            super().__init__()
            self.agent = agent
            self.signature = dspy.Signature(
                instructions="Generate an explanation of an SQL query in natural language",
                user_query=dspy.InputField(desc="User's original query"),
                sql_generation=dspy.InputField(desc="Generated SQL query and metadata"),
                query_result=dspy.InputField(desc="Results of executing the SQL query"),
                explanation_type=dspy.InputField(desc="Type of explanation to generate"),
                text=dspy.OutputField(desc="Natural language explanation of the query"),
                referenced_concepts=dspy.OutputField(desc="SQL concepts referenced in the explanation"),
                query_summary=dspy.OutputField(desc="One-line summary of the query"),
                sql_breakdown=dspy.OutputField(desc="Clause-by-clause breakdown of the SQL")
            )
        
        def forward(self, user_query, sql_generation, query_result=None, explanation_type=ExplanationType.SIMPLIFIED):
            """Process a query with the explanation agent."""
            # Convert string to UserQuery if needed
            if isinstance(user_query, str):
                user_query_obj = UserQuery(text=user_query)
            else:
                user_query_obj = user_query
                
            # Create context for the agent
            context = ExplanationContext(
                user_query=user_query_obj,
                sql_generation=sql_generation,
                query_result=query_result,
                explanation_type=explanation_type
            )
            
            # Run the explanation agent synchronously
            result = self.agent.run_sync("", deps=context)
            
            # Return prediction in DSPy format
            return dspy.Prediction(
                text=result.data.text,
                referenced_concepts=[concept.name for concept in result.data.concepts_used] if hasattr(result.data, "concepts_used") else [],
                query_summary=result.data.query_summary if hasattr(result.data, "query_summary") else None,
                sql_breakdown=result.data.sql_breakdown if hasattr(result.data, "sql_breakdown") else None
            )
    
    class EnhancedExplanationPredictor(dspy.ChainOfThought):
        """Enhanced DSPy module with step-by-step reasoning for explanation generation."""
        
        def __init__(self, predictor):
            """Initialize the EnhancedExplanationPredictor with reasoning capabilities."""
            super().__init__(predictor.signature)
            self.predictor = predictor
            self.agent = predictor.agent
        
        def forward(self, user_query, sql_generation, query_result=None, explanation_type=ExplanationType.SIMPLIFIED):
            """Process a query with step-by-step reasoning."""
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
        
        # Create DSPy predictor
        base_predictor = ExplanationPredictor(enhanced_explanation_agent)
        
        # Create DSPy optimizer
        bootstrap = BootstrapFewShot()
        better_prompt = BetterPrompt()
        
        # First use BootstrapFewShot for basic optimization
        logger.info("Optimizing with BootstrapFewShot...")
        optimized_predictor = bootstrap.compile(
            base_predictor,
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
        dspy_predictor = final_predictor
        dspy_enhanced_predictor = EnhancedExplanationPredictor(final_predictor)
        
        # Get the optimized instructions
        optimized_instructions = final_predictor.signature.instructions
        
        # Update the original agent's system prompt with optimized instructions
        logger.info("Updating agent system prompt...")
        current_prompt = enhanced_explanation_agent.system_prompt_template
        enhanced_prompt = current_prompt + f"\n\nDSPy Optimization Guidelines:\n{optimized_instructions}"
        enhanced_explanation_agent.system_prompt_template = enhanced_prompt
        
        is_optimized = True
        logger.info("Explanation agent successfully optimized with DSPy")
        return True
    except Exception as e:
        logger.error(f"Error optimizing with DSPy: {str(e)}\n{traceback.format_exc()}")
        return False


@enhanced_explanation_agent.system_prompt
def add_explanation_context(ctx: RunContext[ExplanationContext]) -> str:
    """
    Add detailed context information to the system prompt.
    
    Args:
        ctx: Run context with explanation context
        
    Returns:
        str: Formatted context information
    """
    user_query = ctx.deps.user_query
    sql_gen = ctx.deps.sql_generation
    query_result = ctx.deps.query_result
    explanation_type = ctx.deps.explanation_type
    schema_info = ctx.deps.schema_info
    
    sql_query = sql_gen.sql
    sql_explanation = sql_gen.explanation or "No explanation provided by SQL generation."
    
    # Format query result
    result_text = "No query results available."
    if query_result:
        if "status" in query_result and query_result["status"] == QueryStatus.SUCCESS:
            if "rows" in query_result and query_result["rows"]:
                rows = query_result["rows"]
                result_text = f"Query returned {len(rows)} rows of data.\n"
                
                # Show a sample of the results (up to 5 rows)
                sample_rows = rows[:5]
                sample_text = []
                for i, row in enumerate(sample_rows):
                    row_str = ", ".join([f"{k}: {v}" for k, v in row.items()])
                    sample_text.append(f"Row {i+1}: {row_str}")
                
                result_text += "Sample results:\n" + "\n".join(sample_text)
                
                if len(rows) > 5:
                    result_text += f"\n... and {len(rows) - 5} more rows."
                    
                if "column_names" in query_result and query_result["column_names"]:
                    result_text += f"\n\nColumns returned: {', '.join(query_result['column_names'])}"
                
                if "execution_time" in query_result and query_result["execution_time"]:
                    result_text += f"\nQuery execution time: {query_result['execution_time']:.4f} seconds"
            elif "row_count" in query_result:
                result_text = f"Query affected {query_result['row_count']} rows."
                
                if "execution_time" in query_result and query_result["execution_time"]:
                    result_text += f"\nQuery execution time: {query_result['execution_time']:.4f} seconds"
            else:
                # When query succeeded but returned no rows
                result_text = "Query executed successfully but returned no data."
                
                if "column_names" in query_result and query_result["column_names"]:
                    result_text += f"\n\nColumns in result schema: {', '.join(query_result['column_names'])}"
                
                if "execution_time" in query_result and query_result["execution_time"]:
                    result_text += f"\nQuery execution time: {query_result['execution_time']:.4f} seconds"
        elif "status" in query_result and query_result["status"] == QueryStatus.ERROR:
            error_msg = query_result.get("error_message", "Unknown error")
            result_text = f"Query execution failed with error: {error_msg}"
    
    # Format schema info if available
    schema_text = "No schema information available."
    if schema_info:
        schema_text = "Database schema information:\n"
        if "tables" in schema_info:
            tables = schema_info["tables"]
            schema_text += "\nTables referenced in the query:"
            for table in tables:
                table_name = table.get("name", "Unknown table")
                columns = table.get("columns", [])
                column_text = ", ".join([f"{col.get('name')} ({col.get('type', 'unknown')})" for col in columns])
                schema_text += f"\n- {table_name}: {column_text}"
    
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
    
    {schema_text}
    
    Explanation Type Requested: {explanation_type}
    
    Please generate a {explanation_type.lower()} explanation of this SQL query and its results,
    with appropriate level of detail and technical content based on the requested explanation type.
    """


@enhanced_explanation_agent.tool
def analyze_sql_structure(ctx: RunContext[ExplanationContext], sql_query: str) -> Dict[str, str]:
    """
    Analyze the SQL query structure to break it down into components.
    
    Args:
        ctx: Run context with explanation context
        sql_query: SQL query to analyze
        
    Returns:
        Dict[str, str]: Dictionary of query components and their descriptions
    """
    # Note: This is a simplified analysis - a real implementation would use a SQL parser
    components = {}
    
    # Handle basic query types
    if "SELECT" in sql_query.upper():
        components["query_type"] = "SELECT - retrieving data from the database"
        
        # Try to extract main parts
        select_parts = sql_query.upper().split("FROM")
        if len(select_parts) > 1:
            # Extract SELECT clause
            select_clause = select_parts[0].replace("SELECT", "").strip()
            components["select_clause"] = select_clause
            
            # Try to extract FROM and WHERE
            remaining = select_parts[1].strip()
            
            # Extract FROM
            if " WHERE " in remaining:
                from_clause, where_remaining = remaining.split(" WHERE ", 1)
                components["from_clause"] = from_clause.strip()
                
                # Extract WHERE and other clauses
                where_parts = where_remaining.split(" GROUP BY ")
                if len(where_parts) > 1:
                    components["where_clause"] = where_parts[0].strip()
                    group_parts = where_parts[1].split(" HAVING ")
                    if len(group_parts) > 1:
                        components["group_by_clause"] = group_parts[0].strip()
                        having_parts = group_parts[1].split(" ORDER BY ")
                        if len(having_parts) > 1:
                            components["having_clause"] = having_parts[0].strip()
                            order_parts = having_parts[1].split(" LIMIT ")
                            if len(order_parts) > 1:
                                components["order_by_clause"] = order_parts[0].strip()
                                components["limit_clause"] = order_parts[1].strip()
                            else:
                                components["order_by_clause"] = order_parts[0].strip()
                    else:
                        components["group_by_clause"] = group_parts[0].strip()
                else:
                    where_parts = where_remaining.split(" ORDER BY ")
                    if len(where_parts) > 1:
                        components["where_clause"] = where_parts[0].strip()
                        order_parts = where_parts[1].split(" LIMIT ")
                        if len(order_parts) > 1:
                            components["order_by_clause"] = order_parts[0].strip()
                            components["limit_clause"] = order_parts[1].strip()
                        else:
                            components["order_by_clause"] = order_parts[0].strip()
                    else:
                        where_parts = where_remaining.split(" LIMIT ")
                        if len(where_parts) > 1:
                            components["where_clause"] = where_parts[0].strip()
                            components["limit_clause"] = where_parts[1].strip()
                        else:
                            components["where_clause"] = where_remaining.strip()
            else:
                components["from_clause"] = remaining.strip()
    
    elif "INSERT" in sql_query.upper():
        components["query_type"] = "INSERT - adding new data to the database"
    elif "UPDATE" in sql_query.upper():
        components["query_type"] = "UPDATE - modifying existing data in the database"
    elif "DELETE" in sql_query.upper():
        components["query_type"] = "DELETE - removing data from the database"
    
    return components


@enhanced_explanation_agent.tool
def identify_sql_concepts(ctx: RunContext[ExplanationContext], sql_query: str) -> List[SQLConcept]:
    """
    Identify SQL concepts used in the query with detailed descriptions.
    
    Args:
        ctx: Run context with explanation context
        sql_query: SQL query to analyze
        
    Returns:
        List[SQLConcept]: List of SQL concepts used in the query
    """
    concepts = []
    
    # Normalize query for search
    sql_query = sql_query.upper()
    
    # Basic query types
    if "SELECT" in sql_query:
        concepts.append(SQLConcept(
            name="SELECT statement",
            description="Used to retrieve data from one or more database tables",
            example="SELECT * FROM users",
            level="basic"
        ))
    if "INSERT" in sql_query:
        concepts.append(SQLConcept(
            name="INSERT statement",
            description="Used to add new records to a database table",
            example="INSERT INTO users (name, email) VALUES ('John', 'john@example.com')",
            level="basic"
        ))
    if "UPDATE" in sql_query:
        concepts.append(SQLConcept(
            name="UPDATE statement",
            description="Used to modify existing records in a database table",
            example="UPDATE users SET status = 'active' WHERE id = 123",
            level="basic"
        ))
    if "DELETE" in sql_query:
        concepts.append(SQLConcept(
            name="DELETE statement",
            description="Used to remove records from a database table",
            example="DELETE FROM users WHERE inactive = TRUE",
            level="basic"
        ))
    
    # Common clauses and operations
    if " JOIN " in sql_query:
        join_level = "intermediate"
        if "LEFT JOIN" in sql_query or "RIGHT JOIN" in sql_query:
            join_level = "intermediate"
        if "FULL JOIN" in sql_query or "CROSS JOIN" in sql_query:
            join_level = "advanced"
            
        concepts.append(SQLConcept(
            name="JOIN operation",
            description="Combines rows from two or more tables based on a related column",
            example="SELECT * FROM orders JOIN customers ON orders.customer_id = customers.id",
            level=join_level
        ))
        
    if "WHERE" in sql_query:
        concepts.append(SQLConcept(
            name="WHERE clause",
            description="Filters records based on specified conditions",
            example="SELECT * FROM products WHERE price > 100",
            level="basic"
        ))
        
    if "GROUP BY" in sql_query:
        concepts.append(SQLConcept(
            name="GROUP BY clause",
            description="Groups rows with the same values into summary rows",
            example="SELECT category, COUNT(*) FROM products GROUP BY category",
            level="intermediate"
        ))
        
    if "HAVING" in sql_query:
        concepts.append(SQLConcept(
            name="HAVING clause",
            description="Filters groups based on aggregate functions",
            example="SELECT department, AVG(salary) FROM employees GROUP BY department HAVING AVG(salary) > 50000",
            level="intermediate"
        ))
        
    if "ORDER BY" in sql_query:
        concepts.append(SQLConcept(
            name="ORDER BY clause",
            description="Sorts the result set by one or more columns",
            example="SELECT * FROM products ORDER BY price DESC",
            level="basic"
        ))
        
    if "LIMIT" in sql_query:
        concepts.append(SQLConcept(
            name="LIMIT clause",
            description="Restricts the number of rows returned",
            example="SELECT * FROM products LIMIT 10",
            level="basic"
        ))
    
    # Aggregation functions
    if "COUNT" in sql_query:
        concepts.append(SQLConcept(
            name="COUNT function",
            description="Counts the number of rows or non-NULL values",
            example="SELECT COUNT(*) FROM orders",
            level="basic"
        ))
        
    if "SUM" in sql_query:
        concepts.append(SQLConcept(
            name="SUM function",
            description="Calculates the sum of numeric values",
            example="SELECT SUM(amount) FROM orders",
            level="basic"
        ))
        
    if "AVG" in sql_query:
        concepts.append(SQLConcept(
            name="AVG function",
            description="Calculates the average of numeric values",
            example="SELECT AVG(price) FROM products",
            level="basic"
        ))
        
    if "MIN" in sql_query:
        concepts.append(SQLConcept(
            name="MIN function",
            description="Finds the minimum value in a column",
            example="SELECT MIN(temperature) FROM weather_data",
            level="basic"
        ))
        
    if "MAX" in sql_query:
        concepts.append(SQLConcept(
            name="MAX function",
            description="Finds the maximum value in a column",
            example="SELECT MAX(score) FROM exam_results",
            level="basic"
        ))
    
    # Advanced concepts
    if "DISTINCT" in sql_query:
        concepts.append(SQLConcept(
            name="DISTINCT keyword",
            description="Eliminates duplicate rows from the result set",
            example="SELECT DISTINCT category FROM products",
            level="intermediate"
        ))
        
    if "UNION" in sql_query:
        concepts.append(SQLConcept(
            name="UNION operator",
            description="Combines result sets from multiple SELECT statements",
            example="SELECT * FROM table1 UNION SELECT * FROM table2",
            level="intermediate"
        ))
        
    if "CASE" in sql_query:
        concepts.append(SQLConcept(
            name="CASE statement",
            description="Provides conditional logic within a query",
            example="SELECT name, CASE WHEN age < 18 THEN 'Minor' ELSE 'Adult' END AS status FROM users",
            level="intermediate"
        ))
        
    if sql_query.count("SELECT") > 1:
        concepts.append(SQLConcept(
            name="Subquery",
            description="A query nested inside another query",
            example="SELECT * FROM users WHERE department_id IN (SELECT id FROM departments WHERE active = TRUE)",
            level="advanced"
        ))
        
    if "WITH" in sql_query:
        concepts.append(SQLConcept(
            name="Common Table Expression (CTE)",
            description="Named temporary result set used in a larger query",
            example="WITH active_users AS (SELECT * FROM users WHERE status = 'active') SELECT * FROM active_users",
            level="advanced"
        ))
    
    return concepts


@enhanced_explanation_agent.tool
def summarize_query_results(ctx: RunContext[ExplanationContext]) -> QueryResultSummary:
    """
    Create a structured summary of query execution results.
    
    Args:
        ctx: Run context with explanation context
        
    Returns:
        QueryResultSummary: Structured summary of query results
    """
    query_result = ctx.deps.query_result
    
    if not query_result:
        return QueryResultSummary(
            status="unknown",
            error_details="No query results available"
        )
    
    # Extract status
    status = query_result.get("status", "UNKNOWN")
    
    # Handle success
    if status == QueryStatus.SUCCESS:
        row_count = query_result.get("row_count", 0)
        if "rows" in query_result and query_result["rows"]:
            rows = query_result["rows"]
            row_count = len(rows)
            
            # Format sample data
            sample_data = ""
            sample_rows = rows[:3]
            for i, row in enumerate(sample_rows):
                row_str = ", ".join([f"{k}: {v}" for k, v in row.items()])
                sample_data += f"Row {i+1}: {row_str}\n"
                
            if len(rows) > 3:
                sample_data += f"... and {len(rows) - 3} more rows."
                
            return QueryResultSummary(
                status="success",
                row_count=row_count,
                sample_data=sample_data,
                execution_time=query_result.get("execution_time")
            )
        else:
            return QueryResultSummary(
                status="success",
                row_count=row_count,
                execution_time=query_result.get("execution_time")
            )
    
    # Handle errors
    elif status == QueryStatus.ERROR:
        return QueryResultSummary(
            status="error",
            error_details=query_result.get("error_message", "Unknown error"),
            execution_time=query_result.get("execution_time")
        )
    
    # Handle other cases
    else:
        return QueryResultSummary(
            status=status.lower(),
            error_details=f"Query status: {status}"
        )


@backoff.on_exception(
    backoff.expo,
    (Exception,),
    max_tries=3,
    max_time=30,
    giveup=lambda e: isinstance(e, ValueError)
)
async def generate_explanation_enhanced(
    user_query: UserQuery,
    sql_generation: SQLGenerationOutput,
    query_result: Optional[Dict[str, Any]] = None,
    explanation_type: ExplanationType = ExplanationType.SIMPLIFIED,
    schema_info: Optional[Dict[str, Any]] = None,
    use_dspy: bool = True
) -> UserExplanation:
    """
    Generate an explanation for an SQL query using the enhanced PydanticAI agent with optional DSPy optimization.
    
    Args:
        user_query: User's original query
        sql_generation: Generated SQL query
        query_result: Results of executing the SQL query
        explanation_type: Type of explanation to generate
        schema_info: Additional database schema information
        use_dspy: Whether to use DSPy optimization if available
        
    Returns:
        UserExplanation: Human-readable explanation of the query
    """
    # Try to optimize with DSPy if requested and not already optimized
    if use_dspy and DSPY_AVAILABLE and not is_optimized:
        optimize_with_dspy()
    
    # If we have an optimized DSPy predictor and it's requested, use it
    if use_dspy and DSPY_AVAILABLE and is_optimized and dspy_enhanced_predictor:
        try:
            # Use the DSPy enhanced predictor with reasoning
            dspy_result = dspy_enhanced_predictor(
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
        except Exception as e:
            logger.error(f"Error using DSPy optimized agent, falling back to base enhanced agent: {str(e)}")
            # Fall back to the enhanced agent if there's an error
    
    # Otherwise, use the base enhanced agent
    try:
        # Run the agent with the generated SQL and query context
        context = ExplanationContext(
            user_query=user_query,
            sql_generation=sql_generation,
            query_result=query_result,
            explanation_type=explanation_type,
            schema_info=schema_info
        )
        
        start_time = time.time()
        logger.info(f"Generating explanation for query: {user_query.text[:100]}...")
        
        # Call the agent
        result = await enhanced_explanation_agent.run("", deps=context)
        
        elapsed = time.time() - start_time
        logger.info(f"Explanation generated in {elapsed:.2f} seconds")
        
        # Get the explanation data
        explanation = result.data
        
        return explanation
    except Exception as e:
        logger.error(f"Error generating explanation: {str(e)}\n{traceback.format_exc()}")
        
        # Create a basic explanation if the agent fails
        return UserExplanation(
            text=f"I couldn't generate a detailed explanation due to an error. The SQL query is: {sql_generation.sql}",
            original_query=user_query.text,
            sql=sql_generation.sql,
            explanation_type=explanation_type
        ) 