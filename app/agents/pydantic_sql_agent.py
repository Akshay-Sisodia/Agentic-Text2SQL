# -*- coding: utf-8 -*-
"""Enhanced SQL Generation Agent using PydanticAI."""

import logging
import time
import traceback
from typing import Dict, List, Optional, Union

from pydantic_ai import Agent, RunContext

from app.core.config import settings
from app.schemas.sql import DatabaseInfo, SQLGenerationInput, SQLGenerationOutput, TableInfo, ColumnInfo
from app.schemas.user_query import (
    UserQuery,
    IntentOutput,
)

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
    
    # Process each table
    for table in db_info.tables:
        table_desc = f"Table: {table.name}"
        if table.description:
            table_desc += f" - {table.description}"
        tables_info.append(table_desc)

        # Add primary key info if available
        if table.primary_keys:
            pk_str = ", ".join(table.primary_keys)
            tables_info.append(f"  Primary Key(s): {pk_str}")

        # Add column information
        for col in table.columns:
            # Collect constraints in compact format
            constraints = []
            if col.primary_key:
                constraints.append("PK")
            if hasattr(col, "foreign_key") and col.foreign_key:
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

    schema_text = "\n".join(tables_info)
    
    # Get information about the query
    query_type = intent.query_type
    entities_info = []
    
    for entity in intent.entities:
        entity_info = f"- {entity.name} (Type: {entity.type})"
        entities_info.append(entity_info)

    entities_text = (
        "\n".join(entities_info)
        if entities_info
        else "No specific entities identified."
    )

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

async def generate_sql_enhanced(
    user_query: Union[str, UserQuery],
    intent: IntentOutput,
    database_schema: Dict[str, Dict],
    conversation_history: Optional[List[Dict]] = None,
) -> SQLGenerationOutput:
    """
    Enhanced SQL generation using PydanticAI.

    Args:
        user_query: User's original query
        intent: Classification of query intent
        database_schema: Database schema information
        conversation_history: Optional conversation history

    Returns:
        SQLGenerationOutput: Generated SQL and metadata
    """
    try:
        # Convert string to UserQuery if needed
        if isinstance(user_query, str):
            user_query_obj = UserQuery(text=user_query)
        else:
            user_query_obj = user_query

        # Convert database_schema to TableInfo objects
        tables = []
        for table_name, table_info in database_schema.items():
            # Convert columns dictionary to ColumnInfo objects
            columns = []
            for col_name, col_info in table_info.get("columns", {}).items():
                columns.append(
                    ColumnInfo(
                        name=col_name,
                        data_type=col_info.get("type", "unknown"),
                        description=col_info.get("description"),
                        nullable=col_info.get("nullable", True),
                        primary_key=col_info.get("primary_key", False),
                        unique=col_info.get("unique", False),
                        foreign_key=col_info.get("foreign_key"),
                    )
                )
            
            # Create TableInfo object
            tables.append(
                TableInfo(
                    name=table_name,
                    description=table_info.get("description"),
                    columns=columns,
                )
            )

        # Create input for SQL generation
        input_data = SQLGenerationInput(
            user_query=user_query_obj,
            intent=intent,
            database_info=DatabaseInfo(
                name=settings.DB_NAME,
                vendor=settings.DB_TYPE,
                tables=tables,
            ),
            conversation_history=conversation_history or [],
        )

        # Log request
        logger.info(f"Generating SQL for query: {user_query_obj.text}")
        logger.info(f"Intent type: {intent.query_type}")
        logger.info(f"Entities identified: {len(intent.entities)}")

        # Track time for performance monitoring
        start_time = time.time()
        
        # Run the SQL generator
        response = await enhanced_sql_agent.run("", deps=input_data)
        
        # Log performance
        elapsed = time.time() - start_time
        logger.info(f"SQL generation completed in {elapsed:.2f}s")

        return response.data
    except Exception as e:
        # Log the error and traceback
        logger.error(f"Unexpected error in enhanced SQL generation: {str(e)}")
        logger.error(traceback.format_exc())

        # Fall back to base generator
        from app.agents.base_sql_agent import generate_sql

        logger.info("Falling back to base SQL generator")
        return await generate_sql(
            user_query=user_query,
            intent=intent,
            database_schema=database_schema,
            conversation_history=conversation_history,
        )
