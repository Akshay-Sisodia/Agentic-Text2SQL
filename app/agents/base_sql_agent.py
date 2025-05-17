"""Base SQL Generation Agent for Text-to-SQL using standard LLM approach."""

import json
import re
from typing import Dict, List, Optional, Tuple, Union

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
    
    # Determine the query type
    query_type = None
    if sql_query.upper().startswith("SELECT"):
        query_type = "SELECT"
    elif sql_query.upper().startswith("INSERT"):
        query_type = "INSERT"
    elif sql_query.upper().startswith("UPDATE"):
        query_type = "UPDATE"
    elif sql_query.upper().startswith("DELETE"):
        query_type = "DELETE"
    elif sql_query.upper().startswith("CREATE"):
        query_type = "CREATE"
    elif sql_query.upper().startswith("ALTER"):
        query_type = "ALTER"
    elif sql_query.upper().startswith("DROP"):
        query_type = "DROP"
    
    # Check for statement-specific syntax
    if query_type == "SELECT":
        # Check for FROM clause
        if "FROM" not in sql_query.upper():
            errors.append("SELECT query missing FROM clause")
        
        # Check for proper WHERE syntax if present
        if "WHERE" in sql_query.upper():
            # Basic check for comparison operators in WHERE clause
            where_clause = sql_query.upper().split("WHERE")[1].split(";")[0].split("ORDER BY")[0].split("GROUP BY")[0].split("HAVING")[0].split("LIMIT")[0]
            if not any(op in where_clause for op in ["=", ">", "<", ">=", "<=", "<>", "!=", "LIKE", "IN", "BETWEEN", "IS NULL", "IS NOT NULL"]):
                warnings.append("WHERE clause may be missing comparison operators")
        
        # Check for GROUP BY with aggregate functions
        if "GROUP BY" in sql_query.upper():
            select_clause = sql_query.upper().split("SELECT")[1].split("FROM")[0]
            if not any(func in select_clause for func in ["COUNT(", "SUM(", "AVG(", "MIN(", "MAX("]):
                warnings.append("GROUP BY clause without obvious aggregate functions in SELECT")
        
        # Check for ORDER BY syntax
        if "ORDER BY" in sql_query.upper() and "," in sql_query.upper().split("ORDER BY")[1]:
            if "ASC" not in sql_query.upper() and "DESC" not in sql_query.upper():
                suggestions.append("Consider specifying ASC or DESC in ORDER BY clause")
    
    elif query_type == "INSERT":
        # Check for INTO keyword
        if "INTO" not in sql_query.upper():
            errors.append("INSERT statement missing INTO keyword")
        
        # Check for VALUES or SELECT
        if "VALUES" not in sql_query.upper() and "SELECT" not in sql_query.upper():
            errors.append("INSERT statement missing VALUES or SELECT clause")
        
        # Check for column list
        if "(" not in sql_query.split("INTO")[1].split("VALUES")[0].split("SELECT")[0]:
            warnings.append("INSERT statement doesn't specify column names")
    
    elif query_type == "UPDATE":
        # Check for SET clause
        if "SET" not in sql_query.upper():
            errors.append("UPDATE statement missing SET clause")
        
        # Check for WHERE clause
        if "WHERE" not in sql_query.upper():
            warnings.append("UPDATE statement without WHERE clause - this will update all rows")
    
    elif query_type == "DELETE":
        # Check for FROM clause
        if "FROM" not in sql_query.upper():
            errors.append("DELETE statement missing FROM clause")
        
        # Check for WHERE clause
        if "WHERE" not in sql_query.upper():
            warnings.append("DELETE statement without WHERE clause - this will delete all rows")
    
    # Examine aliases for consistency
    alias_pattern = r'\b(AS\s+)([a-zA-Z0-9_]+)\b'
    aliases = re.findall(alias_pattern, sql_query, re.IGNORECASE)
    alias_list = [alias[1] for alias in aliases]
    
    # Check for duplicate aliases
    duplicate_aliases = set([alias for alias in alias_list if alias_list.count(alias) > 1])
    if duplicate_aliases:
        errors.append(f"Duplicate aliases found: {', '.join(duplicate_aliases)}")
    
    # Check for reserved keywords used as identifiers without quotes
    common_reserved_keywords = ["SELECT", "FROM", "WHERE", "AS", "JOIN", "ON", "GROUP", "ORDER", 
                                "HAVING", "UNION", "ALL", "INSERT", "UPDATE", "DELETE", "CREATE", 
                                "TABLE", "INDEX", "VIEW", "DROP", "ALTER", "ADD", "COLUMN", "SET",
                                "INTO", "VALUES", "AND", "OR", "NOT", "NULL", "TRUE", "FALSE"]
    
    # Simple check for unquoted reserved words used as identifiers
    # This is a simplified approach and may have false positives
    for alias in alias_list:
        if alias.upper() in common_reserved_keywords:
            warnings.append(f"Using reserved keyword '{alias}' as an identifier without quotes")
    
    # Check for common SQL injection patterns
    if ("'--" in sql_query or "' --" in sql_query or "';--" in sql_query or 
        "' OR '1'='1" in sql_query or "\" OR \"1\"=\"1" in sql_query):
        warnings.append("Potential SQL injection pattern detected - ensure parameters are properly sanitized")
    
    # Construct the response
    response_parts = []
    
    if errors:
        response_parts.append("SQL validation failed with the following errors:")
        for error in errors:
            response_parts.append(f"- {error}")
        response_parts.append("")
    
    if warnings:
        response_parts.append("Warnings:")
        for warning in warnings:
            response_parts.append(f"- {warning}")
        response_parts.append("")
    
    if suggestions:
        response_parts.append("Suggestions:")
        for suggestion in suggestions:
            response_parts.append(f"- {suggestion}")
        response_parts.append("")
    
    if not errors and not warnings:
        response_parts.append("SQL validation passed. No syntax errors detected.")
        
        # Add query type information
        if query_type:
            response_parts.append(f"Query type: {query_type}")
    
    return "\n".join(response_parts)


@sql_agent.tool
def check_table_column_existence(
    ctx: RunContext[SQLGenerationInput], 
    tables: List[str], 
    columns: List[Tuple[str, str]]
) -> str:
    """
    Check if tables and columns exist in the database schema.
    Provides detailed validation including suggested alternatives.
    
    Args:
        ctx: Run context with SQL generation input
        tables: List of table names to check
        columns: List of (table_name, column_name) tuples to check
        
    Returns:
        str: Validation result with suggestions
    """
    db_info = ctx.deps.database_info
    
    # Create lookup dictionaries
    table_dict = {table.name.lower(): table for table in db_info.tables}
    all_table_names = [table.name for table in db_info.tables]
    
    errors = []
    warnings = []
    suggestions = []
    
    # Check tables
    for table in tables:
        if not table:  # Skip empty table names
            continue
            
        if table.lower() not in table_dict:
            error_msg = f"Table '{table}' does not exist in the database schema"
            errors.append(error_msg)
            
            # Suggest similar table names using string similarity
            similar_tables = []
            for existing_table in all_table_names:
                # Simple similarity check - tables with a similar name
                # Could be enhanced with Levenshtein distance for better suggestions
                if (existing_table.lower().startswith(table.lower()) or 
                    table.lower().startswith(existing_table.lower()) or
                    existing_table.lower().replace('_', '') == table.lower().replace('_', '')):
                    similar_tables.append(existing_table)
            
            if similar_tables:
                suggestions.append(f"Similar tables to '{table}': {', '.join(similar_tables)}")
    
    # Check columns
    for table_name, column_name in columns:
        if not table_name or not column_name:  # Skip incomplete pairs
            continue
            
        if table_name.lower() not in table_dict:
            # Table doesn't exist, error already reported above
            pass
        else:
            table = table_dict[table_name.lower()]
            column_dict = {col.name.lower(): col for col in table.columns}
            
            if column_name.lower() not in column_dict:
                error_msg = f"Column '{column_name}' does not exist in table '{table_name}'"
                errors.append(error_msg)
                
                # Suggest similar column names
                similar_columns = []
                for existing_col in [col.name for col in table.columns]:
                    # Simple similarity check
                    if (existing_col.lower().startswith(column_name.lower()) or 
                        column_name.lower().startswith(existing_col.lower()) or
                        existing_col.lower().replace('_', '') == column_name.lower().replace('_', '')):
                        similar_columns.append(existing_col)
                
                if similar_columns:
                    suggestions.append(f"Similar columns to '{column_name}' in table '{table_name}': {', '.join(similar_columns)}")
                else:
                    # If no similar columns, show all available columns
                    available_columns = [col.name for col in table.columns]
                    suggestions.append(f"Available columns in table '{table_name}': {', '.join(available_columns)}")
    
    # Check for tables used in column references that weren't in the tables list
    # This helps catch issues where column references use table aliases
    column_tables = set(table for table, _ in columns if table)
    for table in column_tables:
        if table not in tables and table.lower() not in table_dict:
            warnings.append(f"Table '{table}' is referenced in column expressions but not found in the FROM/JOIN clauses or database schema")
    
    # Build response
    response_parts = []
    
    if errors:
        response_parts.append("VALIDATION FAILED with the following errors:")
        for error in errors:
            response_parts.append(f"- {error}")
        response_parts.append("")
    
    if warnings:
        response_parts.append("Warnings:")
        for warning in warnings:
            response_parts.append(f"- {warning}")
        response_parts.append("")
    
    if suggestions:
        response_parts.append("Suggestions:")
        for suggestion in suggestions:
            response_parts.append(f"- {suggestion}")
        response_parts.append("")
    
    if not errors and not warnings:
        response_parts.append("Schema validation passed! All tables and columns exist in the database schema.")
    
    return "\n".join(response_parts)


def extract_tables_and_columns(sql_query: str) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    Extract table and column names from a SQL query.
    This is a more robust extraction for validation purposes.
    
    Args:
        sql_query: SQL query to analyze
        
    Returns:
        Tuple of (tables, columns) where columns are (table_name, column_name) tuples
    """
    # Normalize the query by removing extra whitespace and comments
    sql_query = re.sub(r'--.*?$', ' ', sql_query, flags=re.MULTILINE)  # Remove single-line comments
    sql_query = re.sub(r'/\*.*?\*/', ' ', sql_query, flags=re.DOTALL)  # Remove multi-line comments
    sql_query = ' '.join(sql_query.split())  # Normalize whitespace
    
    tables = []
    
    # Extract table names from common SQL patterns
    # FROM clause
    from_pattern = r'FROM\s+([a-zA-Z0-9_"`.]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?'
    from_matches = re.finditer(from_pattern, sql_query, re.IGNORECASE)
    for match in from_matches:
        table_name = match.group(1).strip('"`.')
        tables.append(table_name)
    
    # JOIN clauses (all types of joins: INNER, LEFT, RIGHT, FULL, CROSS)
    join_pattern = r'(?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\s+([a-zA-Z0-9_"`.]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?'
    join_matches = re.finditer(join_pattern, sql_query, re.IGNORECASE)
    for match in join_matches:
        table_name = match.group(1).strip('"`.')
        tables.append(table_name)
    
    # UPDATE statement
    update_pattern = r'UPDATE\s+([a-zA-Z0-9_"`.]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?'
    update_matches = re.finditer(update_pattern, sql_query, re.IGNORECASE)
    for match in update_matches:
        table_name = match.group(1).strip('"`.')
        tables.append(table_name)
    
    # INSERT statement
    insert_pattern = r'INSERT\s+INTO\s+([a-zA-Z0-9_"`.]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?'
    insert_matches = re.finditer(insert_pattern, sql_query, re.IGNORECASE)
    for match in insert_matches:
        table_name = match.group(1).strip('"`.')
        tables.append(table_name)
    
    # DELETE statement
    delete_pattern = r'DELETE\s+FROM\s+([a-zA-Z0-9_"`.]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?'
    delete_matches = re.finditer(delete_pattern, sql_query, re.IGNORECASE)
    for match in delete_matches:
        table_name = match.group(1).strip('"`.')
        tables.append(table_name)
    
    # Remove duplicates while preserving order
    unique_tables = []
    for table in tables:
        if table.lower() not in [t.lower() for t in unique_tables]:
            unique_tables.append(table)
    
    # Extract column references with table prefixes
    columns = []
    
    # Extract explicit table.column references
    column_pattern = r'([a-zA-Z0-9_"`.]+)\.([a-zA-Z0-9_"`.]+)'
    column_matches = re.finditer(column_pattern, sql_query)
    for match in column_matches:
        table_name = match.group(1).strip('"`.')
        column_name = match.group(2).strip('"`.')
        if (table_name, column_name) not in columns:
            columns.append((table_name, column_name))
    
    # Extract columns from SELECT clauses - this is more complex and may not catch all cases
    # but it helps identify column names mentioned without table references
    try:
        select_clauses = re.findall(r'SELECT\s+(.*?)(?:FROM|WHERE|ORDER\s+BY|GROUP\s+BY|HAVING|LIMIT|$)', 
                                     sql_query, re.IGNORECASE | re.DOTALL)
        
        for select_clause in select_clauses:
            # Split by commas, but handle function calls with commas inside parentheses
            # This is a simplified approach and may not handle all complex cases
            items = []
            current_item = ""
            paren_level = 0
            
            for char in select_clause:
                if char == '(':
                    paren_level += 1
                    current_item += char
                elif char == ')':
                    paren_level -= 1
                    current_item += char
                elif char == ',' and paren_level == 0:
                    items.append(current_item.strip())
                    current_item = ""
                else:
                    current_item += char
            
            if current_item:
                items.append(current_item.strip())
            
            for item in items:
                # Try to extract column names from the SELECT items
                # This is a basic extraction and won't catch all cases
                # Especially for complex expressions or calculated columns
                # Skip * selections 
                if item == '*':
                    continue
                    
                # Check for "AS" alias pattern
                as_match = re.search(r'(?:AS\s+)?([a-zA-Z0-9_"`.]+)$', item, re.IGNORECASE)
                if as_match:
                    alias = as_match.group(1).strip('"`.')
                    # We can't reliably map this to a table without deeper parsing
                
                # Check for direct column references without functions or operations
                direct_col_match = re.search(r'^([a-zA-Z0-9_"`.]+)$', item)
                if direct_col_match and '.' not in item:
                    column_name = direct_col_match.group(1).strip('"`.')
                    # We don't know which table this belongs to without deeper analysis
                    # Could be added as (None, column_name) if needed for validation
    except Exception:
        # Skip the SELECT clause parsing if it fails
        pass
    
    return unique_tables, columns


async def generate_sql(
    user_query: Union[str, UserQuery], 
    intent: IntentOutput, 
    database_info: DatabaseInfo,
    conversation_history: Optional[List[Dict]] = None,
    include_explanation: bool = True
) -> SQLGenerationOutput:
    """
    Generate SQL for a given user query and intent.
    
    Args:
        user_query: User's natural language query (string or UserQuery object)
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
    
    # Process conversation history to extract relevant context
    processed_history = []
    if conversation_history:
        # Limit history to last 5 interactions to avoid token limits
        recent_history = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
        
        for item in recent_history:
            # Extract only the relevant parts of the conversation
            if item.get("role") == "user":
                processed_history.append({
                    "role": "user",
                    "content": item.get("content", "")
                })
            elif item.get("role") == "assistant" and "sql" in item:
                processed_history.append({
                    "role": "assistant",
                    "content": item.get("content", ""),
                    "sql": item.get("sql", "")
                })
    
    # Create input for SQL generation
    input_data = SQLGenerationInput(
        user_query=user_query,
        intent=intent,
        database_info=database_info,
        conversation_history=processed_history or [],
        include_explanation=include_explanation
    )
    
    # Set up logging for debugging if needed
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Generating SQL for query: {user_query.text}")
    logger.info(f"Intent type: {intent.query_type.value}")
    logger.info(f"Entities identified: {len(intent.entities)}")
    
    try:
        # Run the SQL agent asynchronously
        result = await sql_agent.run(user_query.text, deps=input_data)
        return result.data
        
    except Exception as e:
        logger.error(f"Error generating SQL: {str(e)}")
        
        # Return a fallback SQL generation output with error information
        return SQLGenerationOutput(
            sql="",
            error_message=f"Failed to generate SQL: {str(e)}",
            explanation="An error occurred during SQL generation.",
            validation_issues=[f"Fatal error: {str(e)}"],
            confidence=0.0
        ) 