"""Base SQL Generation Agent for Text-to-SQL using standard LLM approach."""

import re
from typing import Dict, List, Optional, Tuple, Union
from functools import lru_cache

from pydantic_ai import Agent, RunContext

from app.core.config import settings
from app.schemas.sql import DatabaseInfo, SQLGenerationInput, SQLGenerationOutput
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
    - NULL values and proper NULL handling in WHERE clauses
    - Empty results and appropriate error handling
    - Proper escaping of special characters in strings
    - Data type conversions if needed
    - JOINs across multiple tables when relationships exist
    - Complex filtering with nested conditions
    - Aggregation functions (COUNT, SUM, AVG) with proper GROUP BY clauses
    - HAVING clauses for filtering on aggregated data
    
    Context awareness:
    - Consider previous questions in the conversation if referenced
    - If the query builds on previous results, incorporate that context
    - Use CTEs (WITH clauses) for complex multi-step queries
    
    Explanations should be:
    - Clear and concise, focusing on the query logic
    - Using natural, conversational language
    - Explaining the chosen approach and any performance considerations
    - Highlighting how the query maps to the specific user request
    
    Do not include any placeholder values in your final SQL - all values should be properly quoted literals or parameters.
    """,
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
    
    # Constants for truncation
    MAX_TABLES = 25  # Maximum number of tables to include in full detail
    MAX_COLUMNS_PER_TABLE = 15  # Maximum number of columns per table
    MAX_SAMPLE_VALUES = 3  # Maximum number of sample values to show
    SAMPLE_VALUE_MAX_LENGTH = 20  # Maximum length for any sample value (to prevent huge values)
    MAX_SAMPLE_VALUES_TOTAL_CHARS = 100  # Maximum total characters across all sample values

    # Format table information with truncation and summarization
    tables_info = []
    
    # Get tables in the schema
    all_tables = db_info.tables
    total_tables = len(all_tables)
    
    # Sort tables by name for deterministic output
    sorted_tables = sorted(all_tables, key=lambda t: t.name)
    
    # Determine if we need to truncate the list of tables
    tables_to_process = sorted_tables
    tables_truncated = False
    
    if total_tables > MAX_TABLES:
        tables_to_process = sorted_tables[:MAX_TABLES]
        tables_truncated = True
    
    # Process each table
    for table in tables_to_process:
        table_desc = f"Table: {table.name}"
        if table.description:
            table_desc += f" - {table.description}"
        tables_info.append(table_desc)

        # Add primary key info (compact format)
        if table.primary_keys:
            pk_str = ", ".join(table.primary_keys)
            tables_info.append(f"  Primary Key(s): {pk_str}")

        # Get columns for the table
        all_columns = table.columns
        total_columns = len(all_columns)
        
        # Sort columns to ensure deterministic output
        sorted_columns = sorted(all_columns, key=lambda c: c.name)
        
        # Determine if we need to truncate columns
        columns_to_process = sorted_columns
        columns_truncated = False
        
        if total_columns > MAX_COLUMNS_PER_TABLE:
            # Prioritize primary key and foreign key columns
            priority_columns = [c for c in sorted_columns if c.primary_key or c.foreign_key]
            regular_columns = [c for c in sorted_columns if not (c.primary_key or c.foreign_key)]
            
            # Keep all priority columns and fill remaining slots with regular columns
            remaining_slots = MAX_COLUMNS_PER_TABLE - len(priority_columns)
            if remaining_slots > 0:
                columns_to_process = priority_columns + regular_columns[:remaining_slots]
            else:
                columns_to_process = priority_columns[:MAX_COLUMNS_PER_TABLE]
                
            columns_truncated = True

        # Add column information with truncation
        for col in columns_to_process:
            # Collect constraints in compact JSON-like format
            constraints = []
            if col.primary_key:
                constraints.append("PK")
            if col.foreign_key:
                constraints.append(f"FK->{col.foreign_key}")
            if not col.nullable:
                constraints.append("NOT NULL")

            constraint_str = ", ".join(constraints)
            col_desc = f"  - {col.name} ({col.data_type})"
            if constraint_str:
                col_desc += f" [{constraint_str}]"
            if col.description:
                col_desc += f" - {col.description}"

            tables_info.append(col_desc)

            # Add sample values if available, with truncation
            if col.sample_values and len(col.sample_values) > 0:
                # Truncate and format sample values
                truncated_values = []
                total_chars = 0
                
                for val in col.sample_values[:MAX_SAMPLE_VALUES]:
                    # Convert value to string and truncate if too long
                    val_str = str(val)
                    if len(val_str) > SAMPLE_VALUE_MAX_LENGTH:
                        val_str = val_str[:SAMPLE_VALUE_MAX_LENGTH] + "..."
                    
                    # Check if adding this value exceeds our character budget
                    if total_chars + len(val_str) <= MAX_SAMPLE_VALUES_TOTAL_CHARS:
                        truncated_values.append(val_str)
                        total_chars += len(val_str)
                    else:
                        break
                
                if truncated_values:
                    sample_str = ", ".join(truncated_values)
                    if len(col.sample_values) > len(truncated_values):
                        sample_str += ", ..."
                    tables_info.append(f"    Sample Values: {sample_str}")
        
        # Add truncation notice for columns if needed
        if columns_truncated:
            tables_info.append(f"  ... {total_columns - len(columns_to_process)} more columns truncated ...")
    
    # Add truncation notice for tables if needed
    if tables_truncated:
        remaining_table_names = ", ".join([t.name for t in sorted_tables[MAX_TABLES:MAX_TABLES+5]])
        if len(sorted_tables) > MAX_TABLES + 5:
            remaining_table_names += ", ..."
        tables_info.append(f"... {total_tables - MAX_TABLES} more tables truncated: {remaining_table_names}")

    schema_text = "\n".join(tables_info)

    # Get query type and entities information (keep this concise)
    query_type = intent.query_type
    entities_info = []
    
    # Limit number of entities to prevent explosion
    MAX_ENTITIES = 10
    entities_to_process = intent.entities[:MAX_ENTITIES] if len(intent.entities) > MAX_ENTITIES else intent.entities
    entities_truncated = len(intent.entities) > MAX_ENTITIES
    
    for entity in entities_to_process:
        entity_info = f"- {entity.name} (Type: {entity.type})"
        if entity.aliases:
            # Limit number of aliases
            MAX_ALIASES = 3
            aliases = entity.aliases[:MAX_ALIASES] if len(entity.aliases) > MAX_ALIASES else entity.aliases
            aliases_str = ", ".join(aliases)
            if len(entity.aliases) > MAX_ALIASES:
                aliases_str += ", ..."
            entity_info += f" | Aliases: {aliases_str}"
        entities_info.append(entity_info)
    
    if entities_truncated:
        entities_info.append(f"... {len(intent.entities) - MAX_ENTITIES} more entities truncated ...")

    entities_text = (
        "\n".join(entities_info)
        if entities_info
        else "No specific entities identified."
    )

    # Truncate user query if extremely long
    MAX_QUERY_LENGTH = 500
    truncated_query = user_query.text
    if len(truncated_query) > MAX_QUERY_LENGTH:
        truncated_query = truncated_query[:MAX_QUERY_LENGTH] + "... (truncated)"

    return f"""
    Database Schema:
    {schema_text}
    
    Intent Analysis:
    - Query Type: {query_type}
    - Entities:
    {entities_text}
    
    Original User Query: "{truncated_query}"
    
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
    performance_tips = []

    # Improved check for unbalanced parentheses using sqlparse
    try:
        import sqlparse

        # Parse the SQL query to handle comments and string literals properly
        parsed = sqlparse.format(sql_query, strip_comments=True)
        
        # Function to count balanced parentheses while ignoring those in string literals
        def check_balanced_parentheses(sql_text):
            tokens = sqlparse.parse(sql_text)[0].flatten()
            
            # Only count parentheses outside of string literals
            parens_stack = []
            unbalanced_positions = []
            
            for token in tokens:
                # Skip string literals and comments
                if token.ttype in (sqlparse.tokens.String, sqlparse.tokens.Comment):
                    continue
                
                token_str = str(token)
                
                for i, char in enumerate(token_str):
                    if char == '(':
                        parens_stack.append((token, i))
                    elif char == ')':
                        if not parens_stack:  # Extra closing parenthesis
                            unbalanced_positions.append(("extra_closing", token, i))
                        else:
                            parens_stack.pop()
            
            # Any remaining items in the stack are unclosed parentheses
            return parens_stack, unbalanced_positions
        
        unclosed_parens, extra_closing = check_balanced_parentheses(sql_query)
        
        if unclosed_parens:
            errors.append(f"Unbalanced parentheses: missing {len(unclosed_parens)} closing parenthesis/parentheses")
        
        if extra_closing:
            errors.append(f"Unbalanced parentheses: {len(extra_closing)} extra closing parenthesis/parentheses")
            
    except ImportError:
        # Fallback method if sqlparse is not available
        # This is still imperfect but better than naive counting
        def count_parens_with_state(text):
            stack = []
            in_string = False
            string_char = None
            in_comment = False
            escaped = False
            
            for i, char in enumerate(text):
                # Handle string literals
                if not in_comment and (char == "'" or char == '"') and not escaped:
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                        string_char = None
                
                # Handle escape character
                if char == '\\' and not escaped:
                    escaped = True
                    continue
                escaped = False
                
                # Handle comments
                if not in_string and char == '-' and i+1 < len(text) and text[i+1] == '-':
                    in_comment = True
                elif in_comment and char == '\n':
                    in_comment = False
                
                # Count parentheses only when not in string or comment
                if not in_string and not in_comment:
                    if char == '(':
                        stack.append(i)
                    elif char == ')':
                        if not stack:  # Extra closing parenthesis
                            return False, "extra closing"
                        stack.pop()
            
            if stack:
                return False, "missing closing"
            return True, None
        
        is_balanced, issue = count_parens_with_state(sql_query)
        if not is_balanced:
            if issue == "missing closing":
                errors.append("Unbalanced parentheses: missing closing parenthesis/parentheses")
            else:
                errors.append("Unbalanced parentheses: extra closing parenthesis/parentheses")

    # Check for missing semicolon at the end
    if not sql_query.endswith(";"):
        warnings.append("Missing semicolon at the end of the query")
        suggestions.append(f"Add a semicolon at the end: {sql_query};")

    # Improved check for unclosed quotes that accounts for escaped quotes
    def check_quotes_balance(text):
        single_quote_open = False
        double_quote_open = False
        backtick_open = False
        escaped = False
        
        for char in text:
            if char == '\\' and not escaped:
                escaped = True
                continue
                
            if not escaped:
                if char == "'":
                    single_quote_open = not single_quote_open
                elif char == '"':
                    double_quote_open = not double_quote_open
                elif char == '`':
                    backtick_open = not backtick_open
            
            escaped = False
        
        return single_quote_open, double_quote_open, backtick_open
    
    single_quotes_unclosed, double_quotes_unclosed, backticks_unclosed = check_quotes_balance(sql_query)
    
    if single_quotes_unclosed:
        errors.append("Unclosed single quotes")
    if double_quotes_unclosed:
        errors.append("Unclosed double quotes")
    if backticks_unclosed:
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
            where_clause = (
                sql_query.upper()
                .split("WHERE")[1]
                .split(";")[0]
                .split("ORDER BY")[0]
                .split("GROUP BY")[0]
                .split("HAVING")[0]
                .split("LIMIT")[0]
            )
            if not any(
                op in where_clause
                for op in [
                    "=",
                    ">",
                    "<",
                    ">=",
                    "<=",
                    "<>",
                    "!=",
                    "LIKE",
                    "IN",
                    "BETWEEN",
                    "IS NULL",
                    "IS NOT NULL",
                ]
            ):
                warnings.append("WHERE clause may be missing comparison operators")

            # Extract tables and potential columns used in WHERE clause for index suggestion
            tables_in_query, columns_in_query = extract_tables_and_columns(sql_query)
            if tables_in_query:
                # Check WHERE clause against available indices
                where_columns = []

                # Simple pattern to extract column references in WHERE clause
                # This is a simplified approach and won't catch all cases
                column_refs = re.findall(
                    r"([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)\s*(?:=|>|<|>=|<=|<>|!=|LIKE|IN|BETWEEN)",
                    where_clause,
                )

                # Add columns without table prefix if they exist
                direct_cols = re.findall(
                    r"(?:WHERE|AND|OR)\s+([a-zA-Z0-9_]+)\s*(?:=|>|<|>=|<=|<>|!=|LIKE|IN|BETWEEN)",
                    where_clause,
                    re.IGNORECASE,
                )

                for col in direct_cols:
                    # These are column names without table prefix
                    if col.lower() not in [
                        "and",
                        "or",
                        "not",
                        "null",
                        "between",
                        "like",
                        "in",
                    ]:
                        where_columns.append(col)

                for table, col in column_refs:
                    where_columns.append(f"{table}.{col}")

                # Get index information from the schema
                db_info = ctx.deps.database_info

                missing_indices = []
                potential_compound_indices = {}

                for table_name in tables_in_query:
                    table_info = next(
                        (
                            t
                            for t in db_info.tables
                            if t.name.lower() == table_name.lower()
                        ),
                        None,
                    )
                    if table_info and hasattr(table_info, "indices"):
                        # Check if WHERE columns are indexed
                        table_columns = [col.name.lower() for col in table_info.columns]

                        # Get indexed columns
                        indexed_columns = []
                        for idx in table_info.indices:
                            indexed_columns.extend([col.lower() for col in idx.columns])

                        # Find columns used in WHERE that aren't indexed
                        table_where_columns = []

                        for col in where_columns:
                            if "." in col:
                                tbl, col_name = col.split(".")
                                if tbl.lower() == table_name.lower():
                                    col_name = col_name.lower()
                                    table_where_columns.append(col_name)
                                    if (
                                        col_name in table_columns
                                        and col_name not in indexed_columns
                                    ):
                                        missing_indices.append(
                                            f"{table_name}.{col_name}"
                                        )
                            else:
                                col_name = col.lower()
                                table_where_columns.append(col_name)
                                if (
                                    col_name in table_columns
                                    and col_name not in indexed_columns
                                ):
                                    missing_indices.append(f"{table_name}.{col_name}")

                        # Check for potential compound indices
                        if len(table_where_columns) > 1:
                            # If multiple columns from same table are used in WHERE, may benefit from compound index
                            potential_compound_indices[table_name] = table_where_columns

                # Suggest creating indices for columns used in WHERE that aren't indexed
                if missing_indices:
                    suggestions.append(
                        f"Consider creating indices on these columns used in WHERE clause: {', '.join(missing_indices)}"
                    )

                    # Add performance impact explanation
                    performance_tips.append(
                        "Missing indices on WHERE clause columns can result in full table scans, which are very inefficient for large tables."
                    )

                # Suggest compound indices if multiple columns from same table are used
                for table, cols in potential_compound_indices.items():
                    if len(cols) > 1:
                        suggestions.append(
                            f"Consider creating a compound index on table '{table}' for columns: {', '.join(cols)}"
                        )
                        performance_tips.append(
                            "Compound indices can significantly improve queries that filter on multiple columns simultaneously."
                        )

                # Check for table join optimization
                join_pattern = r'JOIN\s+([a-zA-Z0-9_"`.]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?\s+ON\s+([a-zA-Z0-9_"`.]+)\.([a-zA-Z0-9_"`.]+)\s*=\s*([a-zA-Z0-9_"`.]+)\.([a-zA-Z0-9_"`.]+)'
                join_matches = re.finditer(join_pattern, sql_query, re.IGNORECASE)

                for match in join_matches:
                    join_table = match.group(1).strip('"`.')
                    # join_condition = match.group(3).strip('"`.')  # Unused variable, commented out
                    join_column = match.group(4).strip('"`.')
                    other_table = match.group(5).strip('"`.')
                    other_column = match.group(6).strip('"`.')

                    # Check if join columns are indexed
                    join_table_info = next(
                        (
                            t
                            for t in db_info.tables
                            if t.name.lower() == join_table.lower()
                        ),
                        None,
                    )
                    other_table_info = next(
                        (
                            t
                            for t in db_info.tables
                            if t.name.lower() == other_table.lower()
                        ),
                        None,
                    )

                    if join_table_info and other_table_info:
                        join_columns_indexed = False
                        other_columns_indexed = False

                        # Check if join columns are indexed
                        if hasattr(join_table_info, "indices"):
                            for idx in join_table_info.indices:
                                if join_column.lower() in [
                                    col.lower() for col in idx.columns
                                ]:
                                    join_columns_indexed = True
                                    break

                        if hasattr(other_table_info, "indices"):
                            for idx in other_table_info.indices:
                                if other_column.lower() in [
                                    col.lower() for col in idx.columns
                                ]:
                                    other_columns_indexed = True
                                    break

                        # Suggest creating indices for join columns
                        if not join_columns_indexed:
                            suggestions.append(
                                f"Consider creating an index on join column {join_table}.{join_column}"
                            )
                            performance_tips.append(
                                f"Missing index on join column {join_table}.{join_column} will result in slow joins."
                            )

                        if not other_columns_indexed:
                            suggestions.append(
                                f"Consider creating an index on join column {other_table}.{other_column}"
                            )
                            performance_tips.append(
                                f"Missing index on join column {other_table}.{other_column} will result in slow joins."
                            )

        # Check for GROUP BY with aggregate functions
        if "GROUP BY" in sql_query.upper():
            select_clause = sql_query.upper().split("SELECT")[1].split("FROM")[0]
            if not any(
                func in select_clause
                for func in ["COUNT(", "SUM(", "AVG(", "MIN(", "MAX("]
            ):
                warnings.append(
                    "GROUP BY clause without obvious aggregate functions in SELECT"
                )

        # Check for ORDER BY syntax
        if (
            "ORDER BY" in sql_query.upper()
            and "," in sql_query.upper().split("ORDER BY")[1]
        ):
            if "ASC" not in sql_query.upper() and "DESC" not in sql_query.upper():
                suggestions.append("Consider specifying ASC or DESC in ORDER BY clause")

        # Check for expensive operations
        expensive_patterns = [
            (
                r"SELECT \*",
                "Selecting all columns with * can be inefficient - consider specifying only needed columns",
            ),
            (
                r"SELECT .+ FROM .+ ORDER BY",
                "ORDER BY without LIMIT can be expensive on large tables",
            ),
            (
                r"LIKE\\'%[\w]+'",
                "Leading wildcard in LIKE pattern prevents index usage and forces full table scan",
            ),
            (
                r"IN \(\s*SELECT",
                "Using IN with a subquery may be less efficient than a JOIN",
            ),
            (
                r"SELECT DISTINCT",
                "DISTINCT can be expensive - consider if it's truly needed",
            ),
        ]

        for pattern, message in expensive_patterns:
            if re.search(pattern, sql_query, re.IGNORECASE):
                warnings.append(message)
                # Add to performance tips with more detailed explanation
                if "Selecting all columns" in message:
                    performance_tips.append(
                        "SELECT * retrieves all columns which increases I/O, network traffic, and memory usage. Specify only needed columns to improve performance."
                    )
                elif "ORDER BY without LIMIT" in message:
                    performance_tips.append(
                        "Sorting large result sets is memory-intensive. Always use LIMIT with ORDER BY on large tables."
                    )
                elif "Leading wildcard" in message:
                    performance_tips.append(
                        "Queries with leading wildcards (LIKE '%text') cannot use indices and require full table scans."
                    )
                elif "IN with a subquery" in message:
                    performance_tips.append(
                        "IN with subqueries can cause performance issues. Consider using EXISTS or JOINs instead for better performance."
                    )
                elif "DISTINCT" in message:
                    performance_tips.append(
                        "DISTINCT requires sorting or hashing the entire result set, which is costly for large result sets."
                    )

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
            performance_tips.append(
                "Not specifying column names in INSERT can lead to data errors if table schema changes. Always specify columns explicitly."
            )

        # Check for bulk insert performance
        if "VALUES" in sql_query.upper() and sql_query.upper().count("VALUES") > 3:
            performance_tips.append(
                "For multiple inserts, consider using batch/bulk insert or a transaction to improve performance."
            )

    elif query_type == "UPDATE":
        # Check for SET clause
        if "SET" not in sql_query.upper():
            errors.append("UPDATE statement missing SET clause")

        # Check for WHERE clause
        if "WHERE" not in sql_query.upper():
            warnings.append(
                "UPDATE statement without WHERE clause - this will update all rows"
            )
            performance_tips.append(
                "UPDATE without WHERE affects all rows, which can be very expensive and possibly unintended."
            )
        else:
            # Check if WHERE columns are indexed
            where_clause = sql_query.upper().split("WHERE")[1].split(";")[0]
            tables_in_query, columns_in_query = extract_tables_and_columns(sql_query)

            # Extract columns from WHERE clause
            where_columns = []
            # Extract qualified column references (table.column)
            column_refs = re.findall(
                r"([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)\s*(?:=|>|<|>=|<=|<>|!=|LIKE|IN|BETWEEN)",
                where_clause,
            )
            for table, col in column_refs:
                where_columns.append(f"{table}.{col}")

            # Extract unqualified column references
            direct_cols = re.findall(
                r"(?:WHERE|AND|OR)\s+([a-zA-Z0-9_]+)\s*(?:=|>|<|>=|<=|<>|!=|LIKE|IN|BETWEEN)",
                where_clause,
                re.IGNORECASE,
            )
            for col in direct_cols:
                if col.lower() not in [
                    "and",
                    "or",
                    "not",
                    "null",
                    "between",
                    "like",
                    "in",
                ]:
                    where_columns.append(col)

            # Check for missing indices on WHERE columns
            db_info = ctx.deps.database_info
            missing_indices = []

            for table_name in tables_in_query:
                table_info = next(
                    (t for t in db_info.tables if t.name.lower() == table_name.lower()),
                    None,
                )
                if table_info and hasattr(table_info, "indices"):
                    # Check if WHERE columns are indexed
                    table_columns = [col.name.lower() for col in table_info.columns]
                    indexed_columns = []
                    for idx in table_info.indices:
                        indexed_columns.extend([col.lower() for col in idx.columns])

                    for col in where_columns:
                        if "." in col:
                            tbl, col_name = col.split(".")
                            if (
                                tbl.lower() == table_name.lower()
                                and col_name.lower() in table_columns
                                and col_name.lower() not in indexed_columns
                            ):
                                missing_indices.append(f"{table_name}.{col_name}")
                        else:
                            col_name = col.lower()
                            if (
                                col_name in table_columns
                                and col_name not in indexed_columns
                            ):
                                missing_indices.append(f"{table_name}.{col_name}")

            if missing_indices:
                suggestions.append(
                    f"Consider creating indices on WHERE columns for UPDATE: {', '.join(missing_indices)}"
                )
                performance_tips.append(
                    "Updates without indices on WHERE columns require full table scans, which are very inefficient."
                )

    elif query_type == "DELETE":
        # Check for FROM clause
        if "FROM" not in sql_query.upper():
            errors.append("DELETE statement missing FROM clause")

        # Check for WHERE clause
        if "WHERE" not in sql_query.upper():
            warnings.append(
                "DELETE statement without WHERE clause - this will delete all rows"
            )
            performance_tips.append(
                "DELETE without WHERE deletes all rows, which can be very expensive and possibly unintended."
            )
        else:
            # Similar index checking as for UPDATE
            where_clause = sql_query.upper().split("WHERE")[1].split(";")[0]
            tables_in_query, columns_in_query = extract_tables_and_columns(sql_query)

            # Extract columns from WHERE clause
            where_columns = []
            column_refs = re.findall(
                r"([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)\s*(?:=|>|<|>=|<=|<>|!=|LIKE|IN|BETWEEN)",
                where_clause,
            )
            direct_cols = re.findall(
                r"(?:WHERE|AND|OR)\s+([a-zA-Z0-9_]+)\s*(?:=|>|<|>=|<=|<>|!=|LIKE|IN|BETWEEN)",
                where_clause,
                re.IGNORECASE,
            )

            for table, col in column_refs:
                where_columns.append(f"{table}.{col}")

            for col in direct_cols:
                if col.lower() not in [
                    "and",
                    "or",
                    "not",
                    "null",
                    "between",
                    "like",
                    "in",
                ]:
                    where_columns.append(col)

            # Check for missing indices
            db_info = ctx.deps.database_info
            missing_indices = []

            for table_name in tables_in_query:
                table_info = next(
                    (t for t in db_info.tables if t.name.lower() == table_name.lower()),
                    None,
                )
                if table_info and hasattr(table_info, "indices"):
                    table_columns = [col.name.lower() for col in table_info.columns]
                    indexed_columns = []
                    for idx in table_info.indices:
                        indexed_columns.extend([col.lower() for col in idx.columns])

                    for col in where_columns:
                        if "." in col:
                            tbl, col_name = col.split(".")
                            if (
                                tbl.lower() == table_name.lower()
                                and col_name.lower() in table_columns
                                and col_name.lower() not in indexed_columns
                            ):
                                missing_indices.append(f"{table_name}.{col_name}")
                        else:
                            col_name = col.lower()
                            if (
                                col_name in table_columns
                                and col_name not in indexed_columns
                            ):
                                missing_indices.append(f"{table_name}.{col_name}")

            if missing_indices:
                suggestions.append(
                    f"Consider creating indices on WHERE columns for DELETE: {', '.join(missing_indices)}"
                )
                performance_tips.append(
                    "Deletes without indices on WHERE columns require full table scans, which are very inefficient."
                )

    # Examine aliases for consistency
    alias_pattern = r"\b(AS\s+)([a-zA-Z0-9_]+)\b"
    aliases = re.findall(alias_pattern, sql_query, re.IGNORECASE)
    alias_list = [alias[1] for alias in aliases]

    # Check for duplicate aliases
    duplicate_aliases = set(
        [alias for alias in alias_list if alias_list.count(alias) > 1]
    )
    if duplicate_aliases:
        errors.append(f"Duplicate aliases found: {', '.join(duplicate_aliases)}")

    # Check for reserved keywords used as identifiers without quotes
    common_reserved_keywords = [
        "SELECT",
        "FROM",
        "WHERE",
        "AS",
        "JOIN",
        "ON",
        "GROUP",
        "ORDER",
        "HAVING",
        "UNION",
        "ALL",
        "INSERT",
        "UPDATE",
        "DELETE",
        "CREATE",
        "TABLE",
        "INDEX",
        "VIEW",
        "DROP",
        "ALTER",
        "ADD",
        "COLUMN",
        "SET",
        "INTO",
        "VALUES",
        "AND",
        "OR",
        "NOT",
        "NULL",
        "TRUE",
        "FALSE",
    ]

    # Simple check for unquoted reserved words used as identifiers
    # This is a simplified approach and may have false positives
    for alias in alias_list:
        if alias.upper() in common_reserved_keywords:
            warnings.append(
                f"Using reserved keyword '{alias}' as an identifier without quotes"
            )

    # Check for common SQL injection patterns
    if (
        "'--" in sql_query
        or "' --" in sql_query
        or "';--" in sql_query
        or "' OR '1'='1" in sql_query
        or '" OR "1"="1' in sql_query
    ):
        warnings.append(
            "Potential SQL injection pattern detected - ensure parameters are properly sanitized"
        )

    # Performance optimization suggestions based on general best practices
    if query_type == "SELECT":
        optimization_suggestions = []

        # Check for JOIN without a condition
        if (
            re.search(
                r'JOIN\s+[a-zA-Z0-9_"`.]+\s+(?:ON|USING)', sql_query, re.IGNORECASE
            )
            is None
            and "JOIN" in sql_query.upper()
        ):
            optimization_suggestions.append(
                "JOIN without ON or USING clause will result in a Cartesian product, which is very inefficient"
            )
            performance_tips.append(
                "Cartesian product joins are extremely expensive, growing with O(n²) complexity."
            )

        # Check for SELECT * within a subquery
        if re.search(r"\(\s*SELECT\s+\*", sql_query, re.IGNORECASE):
            optimization_suggestions.append(
                "Using SELECT * in subqueries is inefficient - specify only needed columns"
            )
            performance_tips.append(
                "SELECT * in subqueries passes unnecessary data between query execution stages, causing memory and processing overhead."
            )

        # Check for multiple levels of nested subqueries
        subquery_pattern = r"\(\s*SELECT[^()]*?(?:\(\s*SELECT[^()]*?(?:\(\s*SELECT[^()]*?\))?[^()]*?\))?[^()]*?\)"
        matches = re.findall(subquery_pattern, sql_query, re.IGNORECASE | re.DOTALL)
        nested_count = sum(m.count("SELECT") for m in matches)
        if nested_count > 2:
            optimization_suggestions.append(
                f"Query has {nested_count} levels of nested subqueries. Consider refactoring with CTEs (WITH clause) for readability and potentially better performance"
            )
            performance_tips.append(
                "Deeply nested subqueries are difficult for query optimizers to handle efficiently. CTEs can provide better readability and often better performance."
            )

        # Check for UNION vs UNION ALL
        if "UNION" in sql_query.upper() and "UNION ALL" not in sql_query.upper():
            optimization_suggestions.append(
                "Using UNION without ALL causes duplicate elimination, which may be unnecessary overhead. Use UNION ALL if duplicates are acceptable."
            )
            performance_tips.append(
                "UNION performs distinct operations which are expensive. UNION ALL is much faster if duplicate rows are acceptable."
            )

        # Extend with optimization suggestions
        suggestions.extend(optimization_suggestions)

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

    if performance_tips:
        response_parts.append("Performance Impact Details:")
        for tip in performance_tips:
            response_parts.append(f"- {tip}")
        response_parts.append("")

    if not errors and not warnings and not suggestions and not performance_tips:
        response_parts.append(
            "Validation passed! The SQL query looks well-formed and optimized."
        )

    return "\n".join(response_parts)


# Add Levenshtein distance implementation with caching
@lru_cache(maxsize=1024)
def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate the Levenshtein distance between two strings.
    Uses lru_cache for improved performance when called multiple times with same inputs.

    Args:
        s1: First string
        s2: Second string

    Returns:
        int: The Levenshtein distance between the strings
    """
    # Handle edge cases
    if s1 == s2:
        return 0

    if len(s1) == 0:
        return len(s2)

    if len(s2) == 0:
        return len(s1)

    # Optimization: swap strings to ensure s1 is shorter for faster processing
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    # Initialize previous and current cost rows
    previous_row = list(range(len(s2) + 1))
    current_row = [0] * (len(s2) + 1)

    # Fill the matrix
    for i, c1 in enumerate(s1):
        current_row[0] = i + 1

        # Fill in the current row
        for j, c2 in enumerate(s2):
            # Calculate insertion, deletion, and substitution costs
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            
            # Take the minimum cost operation
            current_row[j + 1] = min(insertions, deletions, substitutions)

        # Swap rows for next iteration
        previous_row, current_row = current_row, previous_row

    return previous_row[-1]


# Function to find similar names using Levenshtein distance
def find_similar_names(
    name: str, candidates: List[str], threshold: float = 0.7
) -> List[str]:
    """
    Find similar names using Levenshtein distance with a similarity threshold.

    Args:
        name: The name to find similar candidates for
        candidates: List of candidate names to check
        threshold: Similarity threshold (0-1), higher means more similar

    Returns:
        List[str]: List of similar names
    """
    similar_names = []
    for candidate in candidates:
        # Calculate max possible distance
        max_len = max(len(name), len(candidate))
        if max_len == 0:
            continue

        # Calculate normalized similarity (1 - distance/max_len)
        distance = levenshtein_distance(name.lower(), candidate.lower())
        similarity = 1 - (distance / max_len)

        # Check if meets threshold
        if similarity >= threshold:
            similar_names.append(candidate)

    # Also include simple matching as fallback
    for candidate in candidates:
        if (
            candidate.lower().startswith(name.lower())
            or name.lower().startswith(candidate.lower())
            or candidate.lower().replace("_", "") == name.lower().replace("_", "")
        ):
            if candidate not in similar_names:
                similar_names.append(candidate)

    return similar_names


@sql_agent.tool
def check_table_column_existence(
    ctx: RunContext[SQLGenerationInput],
    tables: List[str],
    columns: List[Tuple[str, str]],
) -> str:
    """
    Check if specified tables and columns exist in the database schema.

    Args:
        ctx: Execution context
        tables: List of table names to check
        columns: List of (table_name, column_name) tuples to check

    Returns:
        str: Validation results with errors and suggestions
    """
    database_info = ctx.deps.database_info

    errors = []
    warnings = []
    suggestions = []

    # Create lookup dictionaries
    table_dict = {table.name.lower(): table for table in database_info.tables}
    all_table_names = [table.name for table in database_info.tables]

    # Check tables
    for table in tables:
        if not table:  # Skip empty table names
            continue

        if table.lower() not in table_dict:
            error_msg = f"Table '{table}' does not exist in the database schema"
            errors.append(error_msg)

            # Find similar table names using Levenshtein distance for better suggestions
            similar_tables = find_similar_names(table, all_table_names, threshold=0.6)

            if similar_tables:
                # Sort similar tables by similarity (higher similarity first)
                sorted_tables = sorted(
                    similar_tables,
                    key=lambda x: 1
                    - (
                        levenshtein_distance(table.lower(), x.lower())
                        / max(len(table), len(x))
                    ),
                )
                suggestions.append(
                    f"Did you mean: '{sorted_tables[0]}'? Similar tables: {', '.join(sorted_tables)}"
                )
            else:
                # If no similar tables found, suggest looking at all available tables
                suggestions.append(
                    f"Available tables: {', '.join(all_table_names[:10])}"
                    + ("..." if len(all_table_names) > 10 else "")
                )

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
                error_msg = (
                    f"Column '{column_name}' does not exist in table '{table_name}'"
                )
                errors.append(error_msg)

                # Suggest similar column names using Levenshtein distance
                available_columns = [col.name for col in table.columns]
                similar_columns = find_similar_names(
                    column_name, available_columns, threshold=0.65
                )

                if similar_columns:
                    # Sort similar columns by similarity (higher similarity first)
                    sorted_columns = sorted(
                        similar_columns,
                        key=lambda x: 1
                        - (
                            levenshtein_distance(column_name.lower(), x.lower())
                            / max(len(column_name), len(x))
                        ),
                    )
                    suggestions.append(
                        f"Did you mean: '{sorted_columns[0]}'? Similar columns in table '{table_name}': {', '.join(sorted_columns)}"
                    )
                else:
                    # Show all available columns if no similar columns found
                    suggestions.append(
                        f"Available columns in table '{table_name}': {', '.join(available_columns)}"
                    )

                # Check if the column exists in another table (common mistake)
                all_columns = []
                column_in_other_tables = []

                for other_table_name, other_table in table_dict.items():
                    if other_table_name != table_name.lower():
                        for col in other_table.columns:
                            all_columns.append((other_table.name, col.name))
                            if col.name.lower() == column_name.lower():
                                column_in_other_tables.append(
                                    (other_table.name, col.name)
                                )

                if column_in_other_tables:
                    other_tables_msg = ", ".join(
                        [f"'{table}'" for table, _ in column_in_other_tables]
                    )
                    suggestions.append(
                        f"Column '{column_name}' exists in other table(s): {other_tables_msg}"
                    )

                # Look for fuzzy matches across all tables (for when the column is completely wrong)
                if not similar_columns and not column_in_other_tables:
                    all_column_names = [col_name for _, col_name in all_columns]
                    similar_cols_in_db = find_similar_names(
                        column_name, all_column_names, threshold=0.7
                    )

                    if similar_cols_in_db:
                        similar_cols_with_tables = []
                        for col in similar_cols_in_db[:5]:  # Limit to top 5 matches
                            tables_with_this_col = [
                                t_name
                                for t_name, c_name in all_columns
                                if c_name == col
                            ]
                            similar_cols_with_tables.append(
                                f"'{col}' (in {', '.join(tables_with_this_col)})"
                            )

                        suggestions.append(
                            f"Similar columns in other tables: {', '.join(similar_cols_with_tables)}"
                        )

    # Check for tables used in column references that weren't in the tables list
    column_tables = set(table for table, _ in columns if table)
    for table in column_tables:
        if table not in tables and table.lower() not in table_dict:
            warnings.append(
                f"Table '{table}' is referenced in column expressions but not found in the FROM/JOIN clauses or database schema"
            )

            # Suggest similar table names
            similar_tables = find_similar_names(table, all_table_names, threshold=0.6)
            if similar_tables:
                suggestions.append(
                    f"Did you mean to reference table '{similar_tables[0]}'?"
                )

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
        response_parts.append(
            "Schema validation passed! All tables and columns exist in the database schema."
        )

    return "\n".join(response_parts)


def extract_tables_and_columns(
    sql_query: str,
) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    Extract table and column names from a SQL query.
    This is a more robust extraction for validation purposes.

    Args:
        sql_query: SQL query to analyze

    Returns:
        Tuple of (tables, columns) where columns are (table_name, column_name) tuples
    """
    # Normalize the query by removing extra whitespace and comments
    sql_query = re.sub(
        r"--.*?$", " ", sql_query, flags=re.MULTILINE
    )  # Remove single-line comments
    sql_query = re.sub(
        r"/\*.*?\*/", " ", sql_query, flags=re.DOTALL
    )  # Remove multi-line comments
    sql_query = " ".join(sql_query.split())  # Normalize whitespace

    tables = []

    # Extract table names from common SQL patterns
    # FROM clause
    from_pattern = r'FROM\s+([a-zA-Z0-9_"`.]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?'
    from_matches = re.finditer(from_pattern, sql_query, re.IGNORECASE)
    for match in from_matches:
        table_name = match.group(1).strip('"`.')
        tables.append(table_name)

    # JOIN clauses (all types of joins: INNER, LEFT, RIGHT, FULL, CROSS)
    JOIN_PATTERN = re.compile(
        r'JOIN\s+([a-zA-Z0-9_"`.]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?\s+ON\s+([a-zA-Z0-9_"`.]+)\.([a-zA-Z0-9_"`.]+)\s*=\s*([a-zA-Z0-9_"`.]+)\.([a-zA-Z0-9_"`.]+)',
        re.IGNORECASE,
    )
    join_matches = JOIN_PATTERN.finditer(sql_query)
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
    insert_pattern = (
        r'INSERT\s+INTO\s+([a-zA-Z0-9_"`.]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?'
    )
    insert_matches = re.finditer(insert_pattern, sql_query, re.IGNORECASE)
    for match in insert_matches:
        table_name = match.group(1).strip('"`.')
        tables.append(table_name)

    # DELETE statement
    delete_pattern = (
        r'DELETE\s+FROM\s+([a-zA-Z0-9_"`.]+)(?:\s+(?:AS\s+)?([a-zA-Z0-9_]+))?'
    )
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
        select_clauses = re.findall(
            r"SELECT\s+(.*?)(?:FROM|WHERE|ORDER\s+BY|GROUP\s+BY|HAVING|LIMIT|$)",
            sql_query,
            re.IGNORECASE | re.DOTALL,
        )

        for select_clause in select_clauses:
            # Split by commas, but handle function calls with commas inside parentheses
            # This is a simplified approach and may not handle all complex cases
            items = []
            current_item = ""
            paren_level = 0

            for char in select_clause:
                if char == "(":
                    paren_level += 1
                    current_item += char
                elif char == ")":
                    paren_level -= 1
                    current_item += char
                elif char == "," and paren_level == 0:
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
                if item == "*":
                    continue

                # Check for "AS" alias pattern
                as_match = re.search(
                    r'(?:AS\s+)?([a-zA-Z0-9_"`.]+)$', item, re.IGNORECASE
                )
                if as_match:
                    # alias = as_match.group(1).strip('"`.')  # Unused variable, commented out
                    # We can't reliably map this to a table without deeper parsing
                    column_info = {
                        "column": item,
                        "alias": None,  # We'll keep this for future improvements
                        "table": None,
                    }

                # Check for direct column references without functions or operations
                direct_col_match = re.search(r'^([a-zA-Z0-9_"`.]+)$', item)
                if direct_col_match and "." not in item:
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
    database_schema: Dict[str, Dict],
    conversation_history: Optional[List[Dict]] = None,
) -> SQLGenerationOutput:
    """
    Generate SQL for a given user query and intent.

    Args:
        user_query: User's natural language query (string or UserQuery object)
        intent: Classified intent
        database_schema: Database schema information
        conversation_history: Previous conversation turns

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
        recent_history = (
            conversation_history[-5:]
            if len(conversation_history) > 5
            else conversation_history
        )

        for item in recent_history:
            # Extract only the relevant parts of the conversation
            if item.get("role") == "user":
                processed_history.append(
                    {"role": "user", "content": item.get("content", "")}
                )
            elif item.get("role") == "assistant" and "sql" in item:
                processed_history.append(
                    {
                        "role": "assistant",
                        "content": item.get("content", ""),
                        "sql": item.get("sql", ""),
                    }
                )

    # Create input for SQL generation
    input_data = SQLGenerationInput(
        user_query=user_query,
        intent=intent,
        database_info=database_schema,
        conversation_history=processed_history or [],
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
            confidence=0.0,
        )
