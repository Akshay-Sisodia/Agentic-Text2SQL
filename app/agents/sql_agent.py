"""SQL Generation Agent using PydanticAI."""

import json
import re
from typing import Dict, List, Optional, Tuple

from pydantic_ai import Agent, RunContext

from app.core.config import settings
from app.schemas.sql import (DatabaseInfo, SQLGenerationInput,
                            SQLGenerationOutput)
from app.schemas.user_query import IntentOutput, UserQuery


# Create the SQL generation agent
sql_agent = Agent(
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
    
    Remember to handle edge cases like:
    - NULL values
    - Empty results
    - Proper escaping of special characters
    - Data type conversions if needed
    
    Do not include any placeholder values in your final SQL - all values should be properly quoted literals or parameters.
    """
)


@sql_agent.system_prompt
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
    entities_info = []
    for entity in intent.entities:
        entity_info = f"- {entity.name} (Type: {entity.type})"
        if entity.aliases:
            aliases_str = ", ".join(entity.aliases)
            entity_info += f" | Aliases: {aliases_str}"
        entities_info.append(entity_info)
    
    entities_text = "\n".join(entities_info) if entities_info else "No specific entities identified."
    
    return f"""
    Database Schema:
    {schema_text}
    
    Intent Analysis:
    - Query Type: {query_type}
    - Entities:
    {entities_text}
    
    Original User Query: "{user_query.text}"
    
    Now, please generate a SQL query that addresses the user's intent.
    """


@sql_agent.tool
def validate_sql_syntax(ctx: RunContext[SQLGenerationInput], sql_query: str) -> str:
    """
    Perform basic syntax validation of a SQL query.
    
    Args:
        ctx: Run context with SQL generation input
        sql_query: SQL query to validate
        
    Returns:
        str: Validation result
    """
    # Basic pattern matching for common SQL syntax errors
    errors = []
    
    # Check for unbalanced parentheses
    if sql_query.count('(') != sql_query.count(')'):
        errors.append("Unbalanced parentheses")
    
    # Check for missing semicolon at the end
    if not sql_query.strip().endswith(';'):
        errors.append("Missing semicolon at the end of the query")
    
    # Check for unclosed quotes
    single_quotes = sql_query.count("'") % 2
    double_quotes = sql_query.count('"') % 2
    if single_quotes != 0:
        errors.append("Unclosed single quotes")
    if double_quotes != 0:
        errors.append("Unclosed double quotes")
    
    # Check for proper SELECT syntax
    if sql_query.strip().upper().startswith("SELECT"):
        if "FROM" not in sql_query.upper():
            errors.append("SELECT query missing FROM clause")
    
    # Check for proper INSERT syntax
    if sql_query.strip().upper().startswith("INSERT"):
        if "VALUES" not in sql_query.upper() and "SELECT" not in sql_query.upper():
            errors.append("INSERT query missing VALUES or SELECT clause")
    
    # Check for proper UPDATE syntax
    if sql_query.strip().upper().startswith("UPDATE"):
        if "SET" not in sql_query.upper():
            errors.append("UPDATE query missing SET clause")
    
    # Check for proper DELETE syntax
    if sql_query.strip().upper().startswith("DELETE"):
        if "FROM" not in sql_query.upper():
            errors.append("DELETE query missing FROM clause")
    
    if errors:
        return f"SQL validation failed with the following errors:\n- " + "\n- ".join(errors)
    
    return "SQL validation passed. No basic syntax errors detected."


@sql_agent.tool
def check_table_column_existence(
    ctx: RunContext[SQLGenerationInput], 
    tables: List[str], 
    columns: List[Tuple[str, str]]
) -> str:
    """
    Check if tables and columns exist in the database schema.
    
    Args:
        ctx: Run context with SQL generation input
        tables: List of table names to check
        columns: List of (table_name, column_name) tuples to check
        
    Returns:
        str: Validation result
    """
    db_info = ctx.deps.database_info
    
    # Create lookup dictionaries
    table_dict = {table.name.lower(): table for table in db_info.tables}
    
    errors = []
    
    # Check tables
    for table in tables:
        if table.lower() not in table_dict:
            errors.append(f"Table '{table}' does not exist in the database schema")
    
    # Check columns
    for table_name, column_name in columns:
        if table_name.lower() not in table_dict:
            errors.append(f"Table '{table_name}' does not exist in the database schema")
        else:
            table = table_dict[table_name.lower()]
            column_dict = {col.name.lower(): col for col in table.columns}
            
            if column_name.lower() not in column_dict:
                errors.append(f"Column '{column_name}' does not exist in table '{table_name}'")
    
    if errors:
        return f"Schema validation failed with the following errors:\n- " + "\n- ".join(errors)
    
    return "All tables and columns exist in the database schema."


def extract_tables_and_columns(sql_query: str) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    Extract table and column names from a SQL query.
    This is a simplified extraction for validation purposes.
    
    Args:
        sql_query: SQL query to analyze
        
    Returns:
        Tuple of (tables, columns) where columns are (table_name, column_name) tuples
    """
    # Extract table names (simplified)
    from_pattern = r'FROM\s+([a-zA-Z0-9_]+)'
    join_pattern = r'JOIN\s+([a-zA-Z0-9_]+)'
    update_pattern = r'UPDATE\s+([a-zA-Z0-9_]+)'
    insert_pattern = r'INSERT\s+INTO\s+([a-zA-Z0-9_]+)'
    delete_pattern = r'DELETE\s+FROM\s+([a-zA-Z0-9_]+)'
    
    tables = []
    tables.extend(re.findall(from_pattern, sql_query, re.IGNORECASE))
    tables.extend(re.findall(join_pattern, sql_query, re.IGNORECASE))
    tables.extend(re.findall(update_pattern, sql_query, re.IGNORECASE))
    tables.extend(re.findall(insert_pattern, sql_query, re.IGNORECASE))
    tables.extend(re.findall(delete_pattern, sql_query, re.IGNORECASE))
    
    # Extract column references with table aliases (simplified)
    # This is very basic and won't catch all column references
    column_pattern = r'([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)'
    columns = re.findall(column_pattern, sql_query)
    
    return tables, columns


def generate_sql(
    user_query: str, 
    intent: IntentOutput, 
    database_info: DatabaseInfo,
    conversation_history: Optional[List[Dict]] = None,
    include_explanation: bool = True
) -> SQLGenerationOutput:
    """
    Generate SQL for a given user query and intent.
    
    Args:
        user_query: User's natural language query
        intent: Classified intent
        database_info: Database schema information
        conversation_history: Previous conversation turns
        include_explanation: Whether to include explanation
        
    Returns:
        SQLGenerationOutput: Generated SQL and related information
    """
    # Create user query object if string is provided
    if isinstance(user_query, str):
        user_query = UserQuery(text=user_query)
    
    # Create input for SQL generation
    input_data = SQLGenerationInput(
        user_query=user_query,
        intent=intent,
        database_info=database_info,
        conversation_history=conversation_history or [],
        include_explanation=include_explanation
    )
    
    # Run the SQL agent
    result = sql_agent.run_sync(user_query.text, deps=input_data)
    
    return result.data 