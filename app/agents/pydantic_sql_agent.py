# -*- coding: utf-8 -*-
"""Enhanced SQL Generation Agent using PydanticAI with optional DSPy optimization."""

import json
import re
import logging
import time
import traceback
from typing import Dict, List, Optional, Tuple, Union, Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelHTTPError

from app.core.config import settings
from app.schemas.sql import (DatabaseInfo, SQLGenerationInput,
                            SQLGenerationOutput)
from app.schemas.user_query import IntentOutput, UserQuery, EntityType

# Check if DSPy is available for optimization
DSPY_AVAILABLE = False
try:
    import dspy
    from dspy.teleprompt import BootstrapFewShot, BetterPrompt
    DSPY_AVAILABLE = True
except (ImportError, Exception):
    pass

# Import standard agent if needed for reference
# from app.agents.base_sql_agent import ...


# Set up logger
logger = logging.getLogger(__name__)


# Create the enhanced SQL generation agent
enhanced_sql_agent = Agent(
    f"{settings.LLM_PROVIDER}:{settings.LLM_MODEL}",
    deps_type=SQLGenerationInput,
    result_type=SQLGenerationOutput,
    system_prompt="""
    You are an expert SQL writer that generates correct and efficient SQL queries based on natural language requests.
    Your goal is to produce valid SQL that exactly matches the user's intent.
    
    When generating SQL, you should:
    1. Use the correct SQL dialect for the target database
    2. Include proper table and column names as they appear in the schema
    3. Write queries that are secure (avoid SQL injection vulnerabilities)
    4. Optimize queries for performance where possible
    5. Provide clear explanations of how the SQL works
    
    Follow these detailed guidelines:
    - For SELECT queries, include only necessary columns, use appropriate JOINs, and add WHERE conditions
    - For INSERT queries, specify all required columns and provide valid values
    - For UPDATE queries, clearly identify which table and columns to update and include WHERE conditions
    - For DELETE queries, always include WHERE conditions to avoid deleting all records
    
    Use these optimization techniques:
    - Use appropriate indexes (usually on primary keys and foreign keys)
    - Avoid using SELECT * unless all columns are needed
    - Use JOINs efficiently (prefer INNER JOIN over nested subqueries)
    - Use appropriate comparison operators (=, >, <, IN, etc.)
    - Add appropriate WHERE clauses to filter results
    
    Remember to handle edge cases like:
    - NULL values with IS NULL or IS NOT NULL
    - Empty results with appropriate error messages
    - Proper escaping of special characters
    - Data type conversions if needed
    
    Always validate your SQL before submitting:
    - Check table and column names
    - Verify JOIN conditions use the correct foreign keys
    - Ensure all required clauses (SELECT, FROM, etc.) are present
    - Check for balanced parentheses and quotes
    
    Do not include any placeholder values in your final SQL - all values should be properly quoted literals or parameters.
    """
)

# DSPy optimization components
if DSPY_AVAILABLE:
    # Sample training examples for the SQL generator
    SAMPLE_TRAINING_EXAMPLES = [
        dspy.Example(
            user_query="Show me all customers from New York",
            intent=IntentOutput(
                query_type="SELECT",
                entities=[
                    {"name": "customers", "type": "TABLE"},
                    {"name": "city", "type": "COLUMN"},
                    {"name": "New York", "type": "VALUE"}
                ],
                is_ambiguous=False
            ),
            database_schema=DatabaseInfo(
                tables=[
                    {
                        "name": "customers",
                        "columns": [
                            {"name": "id", "data_type": "INTEGER", "primary_key": True},
                            {"name": "name", "data_type": "VARCHAR"},
                            {"name": "city", "data_type": "VARCHAR"}
                        ]
                    }
                ]
            ),
            sql="SELECT * FROM customers WHERE city = 'New York'",
            explanation="This query retrieves all customers whose city is New York",
            confidence=0.95,
            referenced_tables=["customers"],
            referenced_columns=["customers.city"]
        ),
        dspy.Example(
            user_query="List all orders with their products",
            intent=IntentOutput(
                query_type="SELECT",
                entities=[
                    {"name": "orders", "type": "TABLE"},
                    {"name": "products", "type": "TABLE"}
                ],
                is_ambiguous=False
            ),
            database_schema=DatabaseInfo(
                tables=[
                    {
                        "name": "orders",
                        "columns": [
                            {"name": "id", "data_type": "INTEGER", "primary_key": True},
                            {"name": "customer_id", "data_type": "INTEGER", "foreign_key": "customers.id"}
                        ]
                    },
                    {
                        "name": "order_items",
                        "columns": [
                            {"name": "id", "data_type": "INTEGER", "primary_key": True},
                            {"name": "order_id", "data_type": "INTEGER", "foreign_key": "orders.id"},
                            {"name": "product_id", "data_type": "INTEGER", "foreign_key": "products.id"}
                        ]
                    },
                    {
                        "name": "products",
                        "columns": [
                            {"name": "id", "data_type": "INTEGER", "primary_key": True},
                            {"name": "name", "data_type": "VARCHAR"}
                        ]
                    }
                ]
            ),
            sql="SELECT o.id as order_id, p.name as product_name FROM orders o JOIN order_items oi ON o.id = oi.order_id JOIN products p ON oi.product_id = p.id",
            explanation="This query joins the orders, order_items, and products tables to list all orders with their associated products",
            confidence=0.9,
            referenced_tables=["orders", "order_items", "products"],
            referenced_columns=["orders.id", "order_items.order_id", "order_items.product_id", "products.id", "products.name"]
        )
    ]
    
    class SQLPredictor(dspy.Module):
        """DSPy module wrapper for the SQL generation agent."""
        
        def __init__(self, agent):
            """Initialize the SQLPredictor with the enhanced agent."""
            super().__init__()
            self.agent = agent
            self.signature = dspy.Signature(
                instructions="Generate SQL code based on user query and database schema",
                user_query=dspy.InputField(desc="User's natural language query"),
                intent=dspy.InputField(desc="Classified intent of the query"),
                database_schema=dspy.InputField(desc="Database schema information"),
                conversation_history=dspy.InputField(desc="Previous conversation turns"),
                sql=dspy.OutputField(desc="Generated SQL query"),
                explanation=dspy.OutputField(desc="Explanation of what the SQL does"),
                confidence=dspy.OutputField(desc="Confidence score from 0.0 to 1.0"),
                referenced_tables=dspy.OutputField(desc="Tables referenced in the query"),
                referenced_columns=dspy.OutputField(desc="Columns referenced in the query")
            )
        
        def forward(self, user_query, intent, database_schema, conversation_history=None):
            """Process a query with the SQL agent."""
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
                confidence=result.data.confidence,
                referenced_tables=result.data.referenced_tables,
                referenced_columns=result.data.referenced_columns
            )
    
    class EnhancedSQLPredictor(dspy.ChainOfThought):
        """Enhanced DSPy module with step-by-step reasoning for SQL generation."""
        
        def __init__(self, predictor):
            """Initialize the EnhancedSQLPredictor with reasoning capabilities."""
            super().__init__(predictor.signature)
            self.predictor = predictor
            self.agent = predictor.agent
        
        def forward(self, user_query, intent, database_schema, conversation_history=None):
            """Process a query with step-by-step reasoning."""
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
                confidence=result.data.confidence,
                referenced_tables=result.data.referenced_tables,
                referenced_columns=result.data.referenced_columns
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
        base_predictor = SQLPredictor(enhanced_sql_agent)
        
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
        dspy_enhanced_predictor = EnhancedSQLPredictor(final_predictor)
        
        # Get the optimized instructions
        optimized_instructions = final_predictor.signature.instructions
        
        # Update the original agent's system prompt with optimized instructions
        logger.info("Updating agent system prompt...")
        current_prompt = enhanced_sql_agent.system_prompt_template
        enhanced_prompt = current_prompt + f"\n\nDSPy Optimization Tips:\n{optimized_instructions}"
        enhanced_sql_agent.system_prompt_template = enhanced_prompt
        
        is_optimized = True
        logger.info("SQL agent successfully optimized with DSPy")
        return True
    except Exception as e:
        logger.error(f"Error optimizing with DSPy: {str(e)}\n{traceback.format_exc()}")
        return False


@enhanced_sql_agent.system_prompt
def add_database_context(ctx: RunContext[SQLGenerationInput]) -> str:
    """
    Add database schema information to the system prompt.
    
    Args:
        ctx: Run context with SQL generation input
        
    Returns:
        str: Database schema as formatted string
    """
    db_info = ctx.deps.database_info
    intent = ctx.deps.intent
    user_query = ctx.deps.user_query
    
    # Format table information
    tables_info = []
    for table in db_info.tables:
        table_desc = f"Table: {table.name}"
        if table.description:
            table_desc += f" - {table.description}"
        tables_info.append(table_desc)
        
        # Add primary key info
        if table.primary_keys:
            pk_str = ", ".join(table.primary_keys)
            tables_info.append(f"  Primary Key(s): {pk_str}")
        
        # Add column information
        for col in table.columns:
            constraints = []
            if col.primary_key:
                constraints.append("PRIMARY KEY")
            if col.foreign_key:
                constraints.append(f"FOREIGN KEY -> {col.foreign_key}")
            if not col.nullable:
                constraints.append("NOT NULL")
                
            constraint_str = ", ".join(constraints)
            col_desc = f"  - {col.name} ({col.data_type})"
            if constraint_str:
                col_desc += f" [{constraint_str}]"
            if col.description:
                col_desc += f" - {col.description}"
                
            tables_info.append(col_desc)
            
            # Add sample values if available
            if col.sample_values:
                sample_str = ", ".join([str(val) for val in col.sample_values[:5]])
                tables_info.append(f"    Sample Values: {sample_str}")
    
    schema_text = "\n".join(tables_info)
    
    # Get query type and entities information
    query_type = intent.query_type
    
    # Organize entities by type to make them more useful
    tables = []
    columns = []
    values = []
    conditions = []
    other_entities = []
    
    for entity in intent.entities:
        if entity.type == EntityType.TABLE:
            tables.append(entity.name)
        elif entity.type == EntityType.COLUMN:
            columns.append(entity.name)
        elif entity.type == EntityType.VALUE:
            values.append(entity.name)
        elif entity.type == EntityType.CONDITION:
            conditions.append(entity.name)
        else:
            other_entities.append(f"{entity.name} ({entity.type.value})")
    
    # Build entity info text
    entity_sections = []
    if tables:
        entity_sections.append(f"Tables: {', '.join(tables)}")
    if columns:
        entity_sections.append(f"Columns: {', '.join(columns)}")
    if values:
        entity_sections.append(f"Values: {', '.join(values)}")
    if conditions:
        entity_sections.append(f"Conditions: {', '.join(conditions)}")
    if other_entities:
        entity_sections.append(f"Other Entities: {', '.join(other_entities)}")
    
    entities_text = "\n".join([f"- {section}" for section in entity_sections]) if entity_sections else "No specific entities identified."
    
    # Add any clarification if the intent was ambiguous
    clarification_text = ""
    if intent.is_ambiguous and intent.clarification_question:
        clarification_text = f"\nNote: This query was flagged as potentially ambiguous. Clarification: {intent.clarification_question}"
    
    # Add conversation history context if available
    conversation_context = ""
    if ctx.deps.conversation_history:
        # Only consider the last few turns for brevity
        recent_history = ctx.deps.conversation_history[-3:]
        history_items = []
        for item in recent_history:
            if 'user_query' in item:
                history_items.append(f"User: {item['user_query']}")
            if 'generated_sql' in item:
                history_items.append(f"SQL: {item['generated_sql']}")
        
        if history_items:
            conversation_context = "\nRecent Conversation History:\n" + "\n".join(history_items)
    
    return f"""
    Database Schema:
    {schema_text}
    
    Intent Analysis:
    - Query Type: {query_type}
    - Entities:
    {entities_text}{clarification_text}{conversation_context}
    
    Original User Query: "{user_query.text}"
    
    Now, please generate a SQL query that addresses the user's intent. Ensure your response has proper:
    1. sql - The complete, executable SQL query
    2. explanation - A clear description of what the query does
    3. confidence - A score from 0.0 to 1.0 indicating your confidence
    4. referenced_tables - List of tables used in the query
    5. referenced_columns - List of columns used in the query
    
    IMPORTANT:
    - Do NOT use parameter placeholders (like '?', ':param', or '$1') unless you're sure the execution system provides values for them
    - For a query like "list all users", use "SELECT * FROM users" instead of "SELECT * FROM users WHERE email = ?"
    - For a query like "find user with email john@example.com", use "SELECT * FROM users WHERE email = 'john@example.com'" with the literal value
    - Only use parameter placeholders when generating a template for repeated use
    - When specific values are requested in the user query, include them as literals in the SQL
    """


@enhanced_sql_agent.tool
def validate_sql_syntax(ctx: RunContext[SQLGenerationInput], sql_query: str) -> str:
    """
    Perform comprehensive syntax validation of a SQL query.
    
    Args:
        ctx: Run context with SQL generation input
        sql_query: SQL query to validate
        
    Returns:
        str: Detailed validation result
    """
    if not sql_query or not sql_query.strip():
        return "SQL validation failed: Empty query"
        
    # Normalize the query for consistent validation
    sql_query = sql_query.strip()
    
    # Basic pattern matching for common SQL syntax errors
    errors = []
    warnings = []
    suggestions = []
    
    # Check for unbalanced parentheses
    open_parens = sql_query.count('(')
    close_parens = sql_query.count(')')
    if open_parens != close_parens:
        if open_parens > close_parens:
            errors.append(f"Unbalanced parentheses: missing {open_parens - close_parens} closing parenthesis/parentheses")
        else:
            errors.append(f"Unbalanced parentheses: {close_parens - open_parens} extra closing parenthesis/parentheses")
    
    # Check for missing semicolon at the end
    if not sql_query.endswith(';'):
        warnings.append("Missing semicolon at the end of the query")
        suggestions.append(f"Add a semicolon at the end: {sql_query};")
    
    # Check for unclosed quotes
    single_quotes_count = 0
    double_quotes_count = 0
    backtick_count = 0
    escape_mode = False
    
    for char in sql_query:
        if escape_mode:
            escape_mode = False
            continue
            
        if char == '\\':
            escape_mode = True
        elif char == "'":
            single_quotes_count += 1
        elif char == '"':
            double_quotes_count += 1
        elif char == '`':
            backtick_count += 1
    
    if single_quotes_count % 2 != 0:
        errors.append("Unclosed single quotes")
    if double_quotes_count % 2 != 0:
        errors.append("Unclosed double quotes")
    if backtick_count % 2 != 0:
        errors.append("Unclosed backticks")
        
    # Check for parameter placeholders without values
    if "?" in sql_query or ":param" in sql_query or "$1" in sql_query or "@param" in sql_query:
        warnings.append("Query contains parameter placeholders that may not be bound during execution")
        # Suggest replacing with literal values if there's a WHERE clause with a parameter
        if re.search(r'WHERE\s+\w+\s*=\s*[\?:$@]', sql_query, re.IGNORECASE):
            if "SELECT" in sql_query.upper():
                suggestions.append("For simple queries, use literal values instead of parameters. For example, replace 'WHERE email = ?' with 'WHERE email = 'specific@example.com'' if searching for a specific value.")
                suggestions.append("If this is a general query to list all records, remove the WHERE clause entirely or use a condition that's true for all records you want to return.")
    
    # Check for SELECT * which can be inefficient
    if "SELECT *" in sql_query.upper():
        warnings.append("Using 'SELECT *' can be inefficient on large tables")
        suggestions.append("Consider specifying only the columns you need")
    
    # Check for missing FROM clause in SELECT statements
    if sql_query.upper().startswith("SELECT") and "FROM" not in sql_query.upper():
        errors.append("SELECT statement missing FROM clause")
    
    # Check for potential SQL injection in dynamic parts
    if re.search(r'[\'"][^\'"\n]*\{.*\}[^\'"\n]*[\'"]', sql_query):
        errors.append("Potential SQL injection vulnerability detected - string contains curly braces for interpolation")
    
    # Check for mismatched column counts in INSERT
    if "INSERT" in sql_query.upper():
        # Try to find column list and values list
        columns_match = re.search(r'\(([^)]+)\)\s+VALUES\s+\(([^)]+)\)', sql_query, re.IGNORECASE)
        if columns_match:
            col_count = len(columns_match.group(1).split(','))
            val_count = len(columns_match.group(2).split(','))
            if col_count != val_count:
                errors.append(f"Column count ({col_count}) does not match value count ({val_count}) in INSERT statement")
    
    # Check for dangerous operations
    if "DROP" in sql_query.upper():
        warnings.append("Query contains DROP statement which can delete database objects")
    if "TRUNCATE" in sql_query.upper():
        warnings.append("Query contains TRUNCATE statement which will delete all data in the table")
    if "DELETE" in sql_query.upper() and "WHERE" not in sql_query.upper():
        warnings.append("DELETE query is missing WHERE clause - this will delete ALL rows")
        suggestions.append("Add a WHERE clause to restrict which rows are deleted")
    
    # Prepare the result
    validation_result = []
    if errors:
        validation_result.append("ERRORS:")
        for error in errors:
            validation_result.append(f"- {error}")
    
    if warnings:
        validation_result.append("WARNINGS:")
        for warning in warnings:
            validation_result.append(f"- {warning}")
    
    if suggestions:
        validation_result.append("SUGGESTIONS:")
        for suggestion in suggestions:
            validation_result.append(f"- {suggestion}")
    
    if not errors and not warnings:
        validation_result.append("SQL syntax appears valid.")
    
    return "\n".join(validation_result)


@enhanced_sql_agent.tool
def check_table_column_existence(
    ctx: RunContext[SQLGenerationInput], 
    tables: List[str], 
    columns: List[Tuple[str, str]]
) -> str:
    """
    Check if the specified tables and columns exist in the database schema.
    
    Args:
        ctx: Run context with SQL generation input
        tables: List of table names to check
        columns: List of (table, column) pairs to check
        
    Returns:
        str: Validation result with errors for any tables or columns that don't exist
    """
    db_info = ctx.deps.database_info
    
    # Create a lookup dictionary for tables and columns
    schema_tables = {table.name.lower(): table for table in db_info.tables}
    schema_columns = {}
    for table in db_info.tables:
        schema_columns[table.name.lower()] = {col.name.lower(): col for col in table.columns}
    
    # Check tables
    table_errors = []
    for table in tables:
        if table.lower() not in schema_tables:
            table_errors.append(f"Table '{table}' does not exist in the schema")
            
            # Suggest similar table names
            similar_tables = []
            for schema_table in schema_tables:
                if table.lower() in schema_table or schema_table in table.lower():
                    similar_tables.append(schema_tables[schema_table].name)
            
            if similar_tables:
                similar_tables_str = ", ".join(similar_tables)
                table_errors.append(f"  Similar tables: {similar_tables_str}")
    
    # Check columns
    column_errors = []
    for table, column in columns:
        if table.lower() in schema_columns:
            if column.lower() not in schema_columns[table.lower()]:
                column_errors.append(f"Column '{column}' does not exist in table '{table}'")
                
                # Suggest similar column names
                similar_columns = []
                for schema_column in schema_columns[table.lower()]:
                    if column.lower() in schema_column or schema_column in column.lower():
                        similar_columns.append(schema_columns[table.lower()][schema_column].name)
                
                if similar_columns:
                    similar_columns_str = ", ".join(similar_columns)
                    column_errors.append(f"  Similar columns in '{table}': {similar_columns_str}")
        else:
            column_errors.append(f"Cannot check column '{column}' - table '{table}' does not exist")
    
    # Format the result
    result = []
    if not table_errors and not column_errors:
        result.append("All tables and columns exist in the schema.")
    else:
        if table_errors:
            result.append("TABLE ERRORS:")
            result.extend(table_errors)
        
        if column_errors:
            result.append("COLUMN ERRORS:")
            result.extend(column_errors)
    
    return "\n".join(result)


@enhanced_sql_agent.tool
def extract_tables_and_columns_from_sql(ctx: RunContext[SQLGenerationInput], sql_query: str) -> str:
    """
    Extract table and column names from a SQL query.
    
    Args:
        ctx: Run context with SQL generation input
        sql_query: SQL query to analyze
        
    Returns:
        str: JSON string with extracted tables and columns
    """
    tables = set()
    columns = set()
    
    # Normalize SQL query for easier parsing
    sql = sql_query.strip()
    
    # Extract table names using regex patterns
    # Handle FROM, JOIN, INTO
    from_pattern = r"FROM\s+([a-zA-Z0-9_\.]+)"
    join_pattern = r"JOIN\s+([a-zA-Z0-9_\.]+)"
    into_pattern = r"INTO\s+([a-zA-Z0-9_\.]+)"
    update_pattern = r"UPDATE\s+([a-zA-Z0-9_\.]+)"
    
    for pattern in [from_pattern, join_pattern, into_pattern, update_pattern]:
        matches = re.finditer(pattern, sql, re.IGNORECASE)
        for match in matches:
            tables.add(match.group(1).split(".")[-1])  # Handle schema.table format
    
    # Extract column names - more complex due to various SQL constructs
    # This is a simplified approach - comprehensive parsing requires a SQL parser
    
    # Handle SELECT columns
    select_pattern = r"SELECT\s+(.*?)\s+FROM"
    select_matches = re.search(select_pattern, sql, re.IGNORECASE | re.DOTALL)
    if select_matches:
        select_clause = select_matches.group(1)
        # Handle SELECT *
        if "*" in select_clause:
            columns.add("*")
        else:
            # Split by commas, handle functions and aliases
            col_parts = select_clause.split(",")
            for part in col_parts:
                part = part.strip()
                # Handle column aliases (AS keyword)
                if " AS " in part.upper():
                    part = part.split(" AS ")[0].strip()
                # Handle simple function calls
                if "(" in part and ")" in part:
                    # Extract column inside function, e.g., COUNT(id) -> id
                    func_pattern = r"\(([^()]+)\)"
                    func_match = re.search(func_pattern, part)
                    if func_match:
                        col = func_match.group(1).strip()
                        if col != "*":
                            columns.add(col.split(".")[-1])
                else:
                    # Regular column
                    col = part.split(".")[-1]  # Handle table.column format
                    columns.add(col)
    
    # Handle UPDATE SET columns
    set_pattern = r"SET\s+(.*?)(?:WHERE|$)"
    set_matches = re.search(set_pattern, sql, re.IGNORECASE | re.DOTALL)
    if set_matches:
        set_clause = set_matches.group(1)
        col_parts = set_clause.split(",")
        for part in col_parts:
            if "=" in part:
                col = part.split("=")[0].strip()
                columns.add(col.split(".")[-1])
    
    # Handle INSERT columns
    insert_pattern = r"INSERT\s+INTO\s+[a-zA-Z0-9_\.]+\s*\((.*?)\)"
    insert_matches = re.search(insert_pattern, sql, re.IGNORECASE | re.DOTALL)
    if insert_matches:
        insert_cols = insert_matches.group(1)
        col_parts = insert_cols.split(",")
        for part in col_parts:
            columns.add(part.strip())
    
    # Handle WHERE columns
    where_pattern = r"WHERE\s+(.*?)(?:ORDER BY|GROUP BY|HAVING|LIMIT|$)"
    where_matches = re.search(where_pattern, sql, re.IGNORECASE | re.DOTALL)
    if where_matches:
        where_clause = where_matches.group(1)
        # This is simplified and won't catch all cases
        col_matches = re.finditer(r"([a-zA-Z0-9_\.]+)\s*(?:=|>|<|>=|<=|<>|!=|LIKE|IN|IS)", where_clause, re.IGNORECASE)
        for match in col_matches:
            col = match.group(1).strip()
            columns.add(col.split(".")[-1])
    
    # Convert sets to lists for JSON serialization
    tables_list = list(tables)
    columns_list = list(columns)
    
    # Create output dictionary
    result = {
        "tables": tables_list,
        "columns": columns_list
    }
    
    return json.dumps(result, indent=2)


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


async def generate_sql_enhanced(
    user_query: Union[str, UserQuery], 
    intent: IntentOutput, 
    database_info: DatabaseInfo,
    conversation_history: Optional[List[Dict]] = None,
    include_explanation: bool = True,
    use_dspy: bool = True
) -> SQLGenerationOutput:
    """
    Generate SQL from natural language using the enhanced PydanticAI agent with optional DSPy optimization.
    
    Args:
        user_query: Natural language query or UserQuery object
        intent: Classification of the query intent
        database_info: Database schema information
        conversation_history: Previous conversation turns
        include_explanation: Whether to include explanation in the output
        use_dspy: Whether to use DSPy optimization if available
        
    Returns:
        SQLGenerationOutput: Generated SQL and metadata
    """
    # Try to optimize with DSPy if requested and not already optimized
    if use_dspy and DSPY_AVAILABLE and not is_optimized:
        optimize_with_dspy()
    
    # If we have an optimized DSPy predictor and it's requested, use it
    if use_dspy and DSPY_AVAILABLE and is_optimized and dspy_enhanced_predictor:
        try:
            # Convert string query to UserQuery if needed
            if isinstance(user_query, str):
                user_query_obj = UserQuery(text=user_query)
            else:
                user_query_obj = user_query
            
            # Use the DSPy enhanced predictor with reasoning
            dspy_result = dspy_enhanced_predictor(
                user_query=user_query_obj.text,
                intent=intent,
                database_schema=database_info,
                conversation_history=conversation_history
            )
            
            # Convert DSPy result back to SQLGenerationOutput
            return SQLGenerationOutput(
                sql=dspy_result.sql,
                explanation=dspy_result.explanation if include_explanation else "",
                confidence=dspy_result.confidence,
                referenced_tables=dspy_result.referenced_tables,
                referenced_columns=dspy_result.referenced_columns,
                query_type=intent.query_type
            )
        except Exception as e:
            logger.error(f"Error using DSPy optimized agent, falling back to base enhanced agent: {str(e)}")
            # Fall back to the enhanced agent if there's an error
    
    # Otherwise, use the base enhanced agent
    # Convert string query to UserQuery if needed
    if isinstance(user_query, str):
        user_query = UserQuery(text=user_query)
    
    # Prepare the input
    if conversation_history is None:
        conversation_history = []
        
    input_data = SQLGenerationInput(
        user_query=user_query,
        intent=intent,
        database_info=database_info,
        conversation_history=conversation_history,
        include_explanation=include_explanation
    )
    
    # Debug logging
    logger.info(f"Generating SQL with enhanced agent for query: {user_query.text}")
    logger.info(f"Query type from intent: {intent.query_type}")
    logger.info(f"Found {len(intent.entities)} entities")
    
    # Define function to run with retry
    async def run_agent():
        return await enhanced_sql_agent.run("", deps=input_data)
    
    try:
        # Run the agent with retry capability
        result = await retry_with_backoff(run_agent)
        
        # Clean up the SQL before returning
        sql = result.data.sql.strip()
        
        # Remove semicolon at the end if present (for consistency)
        if sql.endswith(';'):
            sql = sql[:-1]
        
        # Create a copy with the cleaned SQL
        cleaned_result = SQLGenerationOutput(
            sql=sql,
            explanation=result.data.explanation if include_explanation else "",
            confidence=result.data.confidence,
            referenced_tables=result.data.referenced_tables,
            referenced_columns=result.data.referenced_columns,
            query_type=intent.query_type
        )
        
        return cleaned_result
    except Exception as e:
        logger.error(f"Error generating SQL: {str(e)}\n{traceback.format_exc()}")
        
        # Create a basic result if the agent fails
        return SQLGenerationOutput(
            sql="SELECT 1 -- Failed to generate proper SQL",
            explanation="Failed to generate SQL due to an error." if include_explanation else "",
            confidence=0.0,
            referenced_tables=[],
            referenced_columns=[],
            query_type=intent.query_type
        )

@enhanced_sql_agent.system_prompt
def add_few_shot_examples(ctx: RunContext[SQLGenerationInput]) -> str:
    """
    Add few-shot examples based on the query type to help the model.
    
    Args:
        ctx: Run context with SQL generation input
        
    Returns:
        str: Few-shot examples as formatted string
    """
    query_type = ctx.deps.intent.query_type.value if ctx.deps.intent.query_type else "SELECT"
    
    examples = {
        "SELECT": [
            {
                "query": "Show me all customers from New York",
                "sql": "SELECT * FROM customers WHERE city = 'New York';",
                "explanation": "This query selects all columns for customers where the city is 'New York'."
            },
            {
                "query": "Find the total order amount for each customer",
                "sql": "SELECT customer_id, SUM(amount) AS total_amount FROM orders GROUP BY customer_id;",
                "explanation": "This query calculates the sum of order amounts for each customer."
            }
        ],
        "INSERT": [
            {
                "query": "Add a new product named 'Widget' with price $19.99",
                "sql": "INSERT INTO products (name, price) VALUES ('Widget', 19.99);",
                "explanation": "This query inserts a new row into the products table with name 'Widget' and price 19.99."
            }
        ],
        "UPDATE": [
            {
                "query": "Update John's email to john@example.com",
                "sql": "UPDATE users SET email = 'john@example.com' WHERE name = 'John';",
                "explanation": "This query updates the email column for any user with the name 'John'."
            }
        ],
        "DELETE": [
            {
                "query": "Delete all orders from before 2020",
                "sql": "DELETE FROM orders WHERE order_date < '2020-01-01';",
                "explanation": "This query removes all order records with dates earlier than January 1, 2020."
            }
        ],
        "JOIN": [
            {
                "query": "Show all customers and their orders",
                "sql": "SELECT c.name, o.order_id, o.amount FROM customers c JOIN orders o ON c.customer_id = o.customer_id;",
                "explanation": "This query joins the customers and orders tables to show each customer's orders."
            }
        ]
    }
    
    # Get examples for the current query type, or default to SELECT
    current_examples = examples.get(query_type, examples["SELECT"])
    
    # Format examples
    formatted_examples = []
    for i, example in enumerate(current_examples[:2], 1):  # Limit to 2 examples
        formatted_examples.append(f"Example {i}:")
        formatted_examples.append(f"User Query: \"{example['query']}\"")
        formatted_examples.append(f"SQL: {example['sql']}")
        formatted_examples.append(f"Explanation: {example['explanation']}")
        formatted_examples.append("")
    
    return "\nHere are some examples of similar queries:\n\n" + "\n".join(formatted_examples)

@enhanced_sql_agent.tool
def analyze_query_complexity(ctx: RunContext[SQLGenerationInput], query: str) -> str:
    """
    Analyze the complexity of a SQL query and suggest optimizations.
    
    Args:
        ctx: Run context with SQL generation input
        query: The SQL query to analyze
        
    Returns:
        str: Analysis of query complexity and optimization suggestions
    """
    # Simple analysis looking for common anti-patterns
    analysis = []
    
    # Check for SELECT *
    if re.search(r'SELECT\s+\*', query, re.IGNORECASE):
        analysis.append("ISSUE: Using 'SELECT *' can retrieve unnecessary columns and harm performance.")
        analysis.append("SUGGESTION: Specify only the columns you need.")
    
    # Check for missing WHERE clause
    if (re.search(r'DELETE\s+FROM', query, re.IGNORECASE) or 
        re.search(r'UPDATE\s+', query, re.IGNORECASE)) and not re.search(r'WHERE', query, re.IGNORECASE):
        analysis.append("WARNING: Missing WHERE clause in UPDATE or DELETE statement.")
        analysis.append("SUGGESTION: Add a WHERE clause to avoid affecting all rows.")
    
    # Check for potential cartesian products
    from_count = len(re.findall(r'FROM\s+\w+', query, re.IGNORECASE))
    join_count = len(re.findall(r'JOIN', query, re.IGNORECASE))
    where_count = len(re.findall(r'ON\s+', query, re.IGNORECASE))
    
    if from_count > 1 and join_count < from_count - 1:
        analysis.append("WARNING: Potential cartesian product detected.")
        analysis.append("SUGGESTION: Ensure proper JOIN conditions between all tables.")
    
    # Check for LIKE with leading wildcard
    if re.search(r"LIKE\s+['\"]%", query, re.IGNORECASE):
        analysis.append("ISSUE: LIKE with a leading wildcard (%) can be slow on large tables.")
        analysis.append("SUGGESTION: Consider using a full-text search if available or restructuring the query.")
    
    # Check for unnecessary ORDER BY in subqueries
    if re.search(r'SELECT.*FROM.*SELECT.*ORDER\s+BY', query, re.IGNORECASE):
        analysis.append("POTENTIAL ISSUE: Using ORDER BY in a subquery is often unnecessary.")
        analysis.append("SUGGESTION: Move the ORDER BY to the outer query if the sort order is needed there.")
    
    # Check for IN with large number of values
    in_statements = re.findall(r'IN\s*\([^)]+\)', query, re.IGNORECASE)
    for in_stmt in in_statements:
        values_count = len(re.findall(r',', in_stmt)) + 1
        if values_count > 10:
            analysis.append(f"CONSIDERATION: Found IN statement with {values_count} values.")
            analysis.append("SUGGESTION: For large numbers of values, consider using a temporary table or JOIN instead.")
    
    if not analysis:
        analysis.append("No obvious issues detected. The query appears to be reasonably structured.")
    
    return "\n".join(analysis)

@enhanced_sql_agent.tool
def suggest_indexes(ctx: RunContext[SQLGenerationInput], sql_query: str) -> str:
    """
    Suggest indexes that might improve the performance of the given SQL query.
    
    Args:
        ctx: Run context with SQL generation input
        sql_query: The SQL query to analyze
        
    Returns:
        str: Suggestions for indexes that might help the query
    """
    # Get tables from the context
    db_info = ctx.deps.database_info
    
    # Initialize suggestions
    suggestions = []
    
    # Parse tables and columns from the query
    tables_in_query = []
    
    # Simple regex to find tables after FROM and JOIN
    from_tables = re.findall(r'FROM\s+([a-zA-Z0-9_]+)', sql_query, re.IGNORECASE)
    join_tables = re.findall(r'JOIN\s+([a-zA-Z0-9_]+)', sql_query, re.IGNORECASE)
    
    tables_in_query.extend(from_tables)
    tables_in_query.extend(join_tables)
    
    # Find columns in WHERE clause
    where_clause = re.search(r'WHERE\s+(.*?)(?:ORDER BY|GROUP BY|LIMIT|;|$)', sql_query, re.IGNORECASE)
    if where_clause:
        where_text = where_clause.group(1)
        # Find column names in WHERE conditions
        where_columns = re.findall(r'([a-zA-Z0-9_]+)\s*(?:=|>|<|>=|<=|LIKE|IN|BETWEEN)', where_text, re.IGNORECASE)
        
        # Remove table aliases from column names
        where_columns = [col.split('.')[-1] if '.' in col else col for col in where_columns]
        
        # For each column in the WHERE clause, suggest an index if appropriate
        for col in where_columns:
            for table in tables_in_query:
                table_info = next((t for t in db_info.tables if t.name == table), None)
                if table_info:
                    col_info = next((c for c in table_info.columns if c.name == col), None)
                    if col_info and not col_info.primary_key and not col_info.foreign_key:
                        # Only suggest for non-key columns that are used in filters
                        suggestions.append(f"Consider adding an index on {table}.{col} to improve filtering performance.")
    
    # Find columns in JOIN conditions
    join_conditions = re.findall(r'JOIN\s+[a-zA-Z0-9_]+\s+(?:AS\s+[a-zA-Z0-9_]+\s+)?ON\s+([^.]+)\.([^=]+)\s*=\s*([^.]+)\.([^\\s]+)', sql_query, re.IGNORECASE)
    for join_cond in join_conditions:
        if len(join_cond) >= 4:
            table1, col1, table2, col2 = join_cond
            # Check if the joined columns already have indexes (primary key, foreign key)
            suggestions.append(f"Ensure {table1.strip()}.{col1.strip()} and {table2.strip()}.{col2.strip()} have indexes for efficient joins.")
    
    # Check ORDER BY columns
    order_by = re.search(r'ORDER BY\s+(.*?)(?:LIMIT|;|$)', sql_query, re.IGNORECASE)
    if order_by:
        order_text = order_by.group(1)
        order_columns = re.findall(r'([a-zA-Z0-9_.]+)', order_text, re.IGNORECASE)
        for col in order_columns:
            if '.' in col:
                table, column = col.split('.')
                suggestions.append(f"Consider an index on {table}.{column} to improve sorting performance.")
            else:
                for table in tables_in_query:
                    suggestions.append(f"Consider an index on {table}.{col} to improve sorting performance if this column belongs to {table}.")
    
    if not suggestions:
        suggestions.append("No specific index suggestions for this query. The existing primary and foreign keys should provide adequate indexing.")
    
    return "\n".join(suggestions) 