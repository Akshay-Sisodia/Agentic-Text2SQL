"""Database utility functions for query execution and schema management."""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_engine
from app.schemas.response import QueryResult, QueryStatus
from app.schemas.sql import (ColumnInfo, DatabaseInfo, TableInfo,
                            SQLGenerationOutput)

logger = logging.getLogger(__name__)


def execute_query(sql_query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
    """
    Execute a SQL query and return the results.
    
    Args:
        sql_query: SQL query string to execute
        params: Optional parameters for parameterized queries
        
    Returns:
        QueryResult: Results of the query execution
    """
    engine = get_engine()
    start_time = time.time()
    
    result = QueryResult(status=QueryStatus.PENDING)
    
    try:
        with engine.connect() as connection:
            # Execute the query
            if params:
                query_result = connection.execute(text(sql_query), params)
            else:
                query_result = connection.execute(text(sql_query))
            
            # Get column names
            if query_result.returns_rows:
                result.column_names = list(query_result.keys())
                
                # Get rows
                rows = []
                for row in query_result:
                    # Convert row to dictionary
                    row_dict = {}
                    for idx, col_name in enumerate(result.column_names):
                        # Handle different data types
                        value = row[idx]
                        if value is not None:
                            # Convert non-serializable objects to strings
                            if not isinstance(value, (str, int, float, bool, type(None))):
                                value = str(value)
                        row_dict[col_name] = value
                    rows.append(row_dict)
                
                result.rows = rows
                result.row_count = len(rows)
            else:
                # For non-SELECT queries
                result.row_count = query_result.rowcount
            
            # Set status to success
            result.status = QueryStatus.SUCCESS
            
    except SQLAlchemyError as e:
        logger.error(f"Database error executing query: {str(e)}")
        result.status = QueryStatus.ERROR
        result.error_message = str(e)
        
    except Exception as e:
        logger.error(f"Unexpected error executing query: {str(e)}")
        result.status = QueryStatus.ERROR
        result.error_message = f"Unexpected error: {str(e)}"
    
    # Set execution time
    result.execution_time = time.time() - start_time
    
    return result


def get_schema_info() -> DatabaseInfo:
    """
    Get information about the database schema.
    
    Returns:
        DatabaseInfo: Information about the database schema
    """
    engine = get_engine()
    db_name = engine.url.database or "unknown"
    
    # Initialize database info
    db_info = DatabaseInfo(
        tables=[],
        name=db_name,
        vendor=engine.name,
        version=engine.driver,
    )
    
    try:
        with engine.connect() as connection:
            # Get table list (dialect-specific)
            if engine.name == 'sqlite':
                tables_query = """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """
            elif engine.name == 'postgresql':
                tables_query = """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                """
            elif engine.name == 'mysql':
                tables_query = f"""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = '{db_name}'
                """
            elif engine.name == 'mssql':
                tables_query = """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'dbo'
                """
            elif engine.name == 'oracle':
                tables_query = """
                SELECT table_name FROM user_tables
                """
            else:
                # Generic fallback
                tables_query = """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema NOT IN ('information_schema', 'pg_catalog', 'sys')
                """
            
            tables_result = connection.execute(text(tables_query))
            table_names = [row[0] for row in tables_result]
            
            # Get information for each table
            for table_name in table_names:
                table_info = get_table_info(connection, table_name, engine.name, db_name)
                db_info.tables.append(table_info)
    
    except Exception as e:
        logger.error(f"Error getting schema info: {str(e)}")
        # Return partial info if available
    
    return db_info


def get_table_info(connection, table_name: str, dialect: str, db_name: str = None) -> TableInfo:
    """
    Get information about a specific table.
    
    Args:
        connection: SQLAlchemy connection
        table_name: Name of the table
        dialect: Database dialect
        db_name: Database name (used for some dialects)
        
    Returns:
        TableInfo: Information about the table
    """
    # Initialize table info
    table_info = TableInfo(
        name=table_name,
        columns=[],
    )
    
    try:
        # Get column information (dialect-specific)
        if dialect == 'sqlite':
            columns_query = f"PRAGMA table_info('{table_name}')"
            columns_result = connection.execute(text(columns_query))
            
            for row in columns_result:
                col_info = ColumnInfo(
                    name=row[1],
                    data_type=row[2],
                    nullable=not bool(row[3]),
                    primary_key=bool(row[5]),
                )
                table_info.columns.append(col_info)
                
                if col_info.primary_key:
                    table_info.primary_keys.append(col_info.name)
            
            # Get foreign keys
            fk_query = f"PRAGMA foreign_key_list('{table_name}')"
            fk_result = connection.execute(text(fk_query))
            
            for row in fk_result:
                # Find the column
                for col in table_info.columns:
                    if col.name == row[3]:  # 'from' column
                        col.foreign_key = f"{row[2]}.{row[4]}"  # table.column
                        table_info.foreign_keys[col.name] = col.foreign_key
        
        elif dialect == 'postgresql':
            # Get column info
            columns_query = f"""
            SELECT 
                column_name, 
                data_type, 
                is_nullable, 
                column_default,
                (SELECT true FROM pg_constraint c
                 JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
                 WHERE c.contype = 'p' AND c.conrelid = '{table_name}'::regclass AND a.attname = column_name)
                 as is_primary
            FROM information_schema.columns
            WHERE table_name = '{table_name}' AND table_schema = 'public'
            """
            columns_result = connection.execute(text(columns_query))
            
            for row in columns_result:
                col_info = ColumnInfo(
                    name=row[0],
                    data_type=row[1],
                    nullable=row[2].upper() == 'YES',
                    primary_key=bool(row[4]),
                )
                table_info.columns.append(col_info)
                
                if col_info.primary_key:
                    table_info.primary_keys.append(col_info.name)
            
            # Get foreign keys
            fk_query = f"""
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM
                information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = '{table_name}'
                AND tc.table_schema = 'public'
            """
            fk_result = connection.execute(text(fk_query))
            
            for row in fk_result:
                col_name, foreign_table, foreign_column = row[0], row[1], row[2]
                for col in table_info.columns:
                    if col.name == col_name:
                        col.foreign_key = f"{foreign_table}.{foreign_column}"
                        table_info.foreign_keys[col.name] = col.foreign_key
                        
        elif dialect == 'mysql':
            # Get column info
            columns_query = f"""
            SELECT 
                column_name, 
                data_type, 
                is_nullable, 
                column_default,
                column_key
            FROM information_schema.columns
            WHERE table_name = '{table_name}' AND table_schema = '{db_name}'
            """
            columns_result = connection.execute(text(columns_query))
            
            for row in columns_result:
                col_info = ColumnInfo(
                    name=row[0],
                    data_type=row[1],
                    nullable=row[2].upper() == 'YES',
                    primary_key=row[4] == 'PRI' if row[4] else False,
                )
                table_info.columns.append(col_info)
                
                if col_info.primary_key:
                    table_info.primary_keys.append(col_info.name)
            
            # Get foreign keys
            fk_query = f"""
            SELECT
                column_name,
                referenced_table_name,
                referenced_column_name
            FROM information_schema.key_column_usage
            WHERE table_name = '{table_name}'
                AND table_schema = '{db_name}'
                AND referenced_table_name IS NOT NULL
            """
            fk_result = connection.execute(text(fk_query))
            
            for row in fk_result:
                col_name, foreign_table, foreign_column = row[0], row[1], row[2]
                for col in table_info.columns:
                    if col.name == col_name:
                        col.foreign_key = f"{foreign_table}.{foreign_column}"
                        table_info.foreign_keys[col.name] = col.foreign_key
        
        elif dialect == 'mssql':
            # Get column info
            columns_query = f"""
            SELECT 
                c.name as column_name,
                t.name as data_type,
                c.is_nullable,
                CASE WHEN pk.column_id IS NOT NULL THEN 1 ELSE 0 END as is_primary_key
            FROM sys.columns c
            JOIN sys.types t ON c.user_type_id = t.user_type_id
            LEFT JOIN (
                SELECT ic.column_id, ic.object_id
                FROM sys.index_columns ic
                JOIN sys.indexes i ON ic.object_id = i.object_id AND ic.index_id = i.index_id
                JOIN sys.key_constraints kc ON i.object_id = kc.parent_object_id AND i.index_id = kc.unique_index_id
                WHERE kc.type = 'PK'
            ) pk ON c.column_id = pk.column_id AND c.object_id = pk.object_id
            WHERE c.object_id = OBJECT_ID('{table_name}')
            """
            columns_result = connection.execute(text(columns_query))
            
            for row in columns_result:
                col_info = ColumnInfo(
                    name=row[0],
                    data_type=row[1],
                    nullable=bool(row[2]),
                    primary_key=bool(row[3]),
                )
                table_info.columns.append(col_info)
                
                if col_info.primary_key:
                    table_info.primary_keys.append(col_info.name)
            
            # Get foreign keys
            fk_query = f"""
            SELECT 
                COL_NAME(fc.parent_object_id, fc.parent_column_id) AS column_name,
                OBJECT_NAME(f.referenced_object_id) AS foreign_table,
                COL_NAME(fc.referenced_object_id, fc.referenced_column_id) AS foreign_column
            FROM sys.foreign_keys AS f
            INNER JOIN sys.foreign_key_columns AS fc ON f.OBJECT_ID = fc.constraint_object_id
            WHERE OBJECT_NAME(f.parent_object_id) = '{table_name}'
            """
            fk_result = connection.execute(text(fk_query))
            
            for row in fk_result:
                col_name, foreign_table, foreign_column = row[0], row[1], row[2]
                for col in table_info.columns:
                    if col.name == col_name:
                        col.foreign_key = f"{foreign_table}.{foreign_column}"
                        table_info.foreign_keys[col.name] = col.foreign_key
                        
        elif dialect == 'oracle':
            # Get column info
            columns_query = f"""
            SELECT 
                column_name,
                data_type,
                nullable,
                CASE WHEN constraint_type = 'P' THEN 1 ELSE 0 END as is_primary
            FROM (
                SELECT
                    c.column_name,
                    c.data_type,
                    DECODE(c.nullable, 'Y', 1, 0) as nullable,
                    pk.constraint_type
                FROM user_tab_columns c
                LEFT JOIN (
                    SELECT cols.column_name, cons.constraint_type
                    FROM user_cons_columns cols
                    JOIN user_constraints cons ON cols.constraint_name = cons.constraint_name
                    WHERE cons.constraint_type = 'P' AND cons.table_name = '{table_name}'
                ) pk ON c.column_name = pk.column_name
                WHERE c.table_name = '{table_name}'
            )
            """
            columns_result = connection.execute(text(columns_query))
            
            for row in columns_result:
                col_info = ColumnInfo(
                    name=row[0],
                    data_type=row[1],
                    nullable=bool(row[2]),
                    primary_key=bool(row[3]),
                )
                table_info.columns.append(col_info)
                
                if col_info.primary_key:
                    table_info.primary_keys.append(col_info.name)
            
            # Get foreign keys
            fk_query = f"""
            SELECT 
                a.column_name,
                c_pk.table_name as foreign_table,
                b_pk.column_name as foreign_column
            FROM user_cons_columns a
            JOIN user_constraints c ON a.constraint_name = c.constraint_name
            JOIN user_constraints c_pk ON c.r_constraint_name = c_pk.constraint_name
            JOIN user_cons_columns b_pk ON c_pk.constraint_name = b_pk.constraint_name
            WHERE c.constraint_type = 'R'
              AND a.table_name = '{table_name}'
            """
            fk_result = connection.execute(text(fk_query))
            
            for row in fk_result:
                col_name, foreign_table, foreign_column = row[0], row[1], row[2]
                for col in table_info.columns:
                    if col.name == col_name:
                        col.foreign_key = f"{foreign_table}.{foreign_column}"
                        table_info.foreign_keys[col.name] = col.foreign_key
        
        else:
            # Generic approach for other databases (simplified)
            columns_query = f"""
            SELECT column_name, data_type, is_nullable, 
                   column_default, column_key, extra
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            """
            columns_result = connection.execute(text(columns_query))
            
            for row in columns_result:
                col_info = ColumnInfo(
                    name=row[0],
                    data_type=row[1],
                    nullable=row[2].upper() == 'YES',
                    primary_key=row[4] == 'PRI' if row[4] else False,
                )
                table_info.columns.append(col_info)
                
                if col_info.primary_key:
                    table_info.primary_keys.append(col_info.name)
        
        # Get row count (approximate)
        try:
            count_query = f"SELECT COUNT(*) FROM {table_name}"
            count_result = connection.execute(text(count_query))
            table_info.row_count = count_result.scalar()
        except Exception as e:
            logger.warning(f"Could not get row count for {table_name}: {str(e)}")
            table_info.row_count = 0
        
        # Get sample values for each column (limit to 5)
        for col in table_info.columns:
            try:
                if dialect == 'oracle':
                    sample_query = f"SELECT DISTINCT {col.name} FROM {table_name} WHERE ROWNUM <= 5"
                elif dialect == 'mssql':
                    sample_query = f"SELECT DISTINCT TOP 5 {col.name} FROM {table_name}"
                else:
                    sample_query = f"SELECT DISTINCT {col.name} FROM {table_name} LIMIT 5"
                    
                sample_result = connection.execute(text(sample_query))
                col.sample_values = [str(row[0]) for row in sample_result if row[0] is not None]
            except Exception:
                # Skip sample values if there's an error
                pass
    
    except Exception as e:
        logger.error(f"Error getting table info for {table_name}: {str(e)}")
    
    return table_info


def execute_generated_sql(sql_output: SQLGenerationOutput) -> QueryResult:
    """
    Execute a generated SQL query.
    
    Args:
        sql_output: Generated SQL query output
        
    Returns:
        QueryResult: Results of the query execution
    """
    sql_query = sql_output.sql
    
    # Basic security check
    dangerous_operations = ["DROP", "TRUNCATE", "DELETE FROM", "ALTER TABLE"]
    if any(op in sql_query.upper() for op in dangerous_operations):
        result = QueryResult(status=QueryStatus.ERROR)
        result.error_message = "Potentially harmful operation detected. Query execution aborted."
        result.warnings.append("This query contains potentially harmful operations that could delete or modify data structure.")
        return result
    
    # Execute the query
    return execute_query(sql_query) 