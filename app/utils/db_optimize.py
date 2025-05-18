"""
Database optimization utilities for improving query performance.
"""

import logging
from typing import List, Dict, Optional, Any
from sqlalchemy import text

from app.utils.db_utils import get_engine

logger = logging.getLogger(__name__)


def analyze_database(database_url: Optional[str] = None) -> bool:
    """
    Execute the ANALYZE command to optimize query planning.
    For SQLite, this updates statistics used by the query planner.

    Args:
        database_url: Optional database URL. If not provided, uses active connection

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get engine
        engine = get_engine(database_url) if database_url else get_engine()

        with engine.connect() as conn:
            # SQLite-specific optimization
            if engine.dialect.name == "sqlite":
                # Run ANALYZE to collect statistics for the query planner
                conn.execute(text("ANALYZE"))
                logger.info("SQLite database analyzed for query optimization")

                # Run PRAGMA optimizations
                pragmas = [
                    "PRAGMA optimize",  # General optimization
                    "PRAGMA automatic_index = ON",  # Enable automatic indexing
                    "PRAGMA cache_size = 10000",  # Increase cache size (in pages)
                    "PRAGMA temp_store = MEMORY",  # Store temp tables in memory
                    "PRAGMA mmap_size = 268435456",  # Memory mapping (256MB)
                ]

                for pragma in pragmas:
                    try:
                        conn.execute(text(pragma))
                    except Exception as e:
                        logger.warning(f"Failed to execute pragma {pragma}: {str(e)}")

            # PostgreSQL optimization
            elif engine.dialect.name == "postgresql":
                # Run ANALYZE to update statistics
                conn.execute(text("ANALYZE"))
                logger.info("PostgreSQL database analyzed for query optimization")

            # MySQL/MariaDB optimization
            elif engine.dialect.name in ("mysql", "mariadb"):
                # Optimize all tables
                conn.execute(text("OPTIMIZE TABLE *"))
                logger.info("MySQL/MariaDB tables optimized")

                # Analyze tables for statistics
                conn.execute(text("ANALYZE TABLE *"))
                logger.info("MySQL/MariaDB tables analyzed for query optimization")

            # Microsoft SQL Server optimization
            elif engine.dialect.name == "mssql":
                # Update statistics on all tables
                conn.execute(text("EXEC sp_updatestats"))
                logger.info("SQL Server statistics updated for query optimization")

                # Rebuild indexes with better fill factor
                try:
                    # Get list of user tables
                    tables_result = conn.execute(
                        text("SELECT name FROM sys.tables WHERE is_ms_shipped = 0")
                    )
                    tables = [row[0] for row in tables_result]

                    # Rebuild indexes for each table
                    for table in tables:
                        conn.execute(
                            text(
                                f"ALTER INDEX ALL ON {table} REBUILD WITH (FILLFACTOR = 90)"
                            )
                        )

                    logger.info("SQL Server indexes rebuilt with optimized fill factor")
                except Exception as e:
                    logger.warning(f"Failed to rebuild SQL Server indexes: {str(e)}")

            # Oracle optimization
            elif engine.dialect.name == "oracle":
                # Gather schema statistics
                conn.execute(text("BEGIN DBMS_STATS.GATHER_SCHEMA_STATS(NULL); END;"))
                logger.info("Oracle schema statistics gathered for query optimization")

                # Check for tables with stale statistics
                try:
                    stale_tables_result = conn.execute(
                        text(
                            "SELECT table_name FROM dba_tab_statistics WHERE stale_stats = 'YES'"
                        )
                    )
                    stale_tables = [row[0] for row in stale_tables_result]

                    # Gather statistics for stale tables specifically
                    for table in stale_tables:
                        conn.execute(
                            text(
                                f"BEGIN DBMS_STATS.GATHER_TABLE_STATS(NULL, '{table}'); END;"
                            )
                        )

                    logger.info(
                        f"Oracle statistics refreshed for {len(stale_tables)} stale tables"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to gather Oracle table statistics: {str(e)}"
                    )

            # Other databases
            else:
                logger.info(
                    f"No specific optimization implemented for {engine.dialect.name}"
                )
                return False

            return True

    except Exception as e:
        logger.error(f"Error optimizing database: {str(e)}")
        return False


def suggest_indices(database_url: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Analyze query patterns and suggest potential indices for improved performance.

    Args:
        database_url: Optional database URL. If not provided, uses active connection

    Returns:
        List[Dict[str, Any]]: Suggested indices with table and column information
    """
    try:
        # Get engine
        engine = get_engine(database_url) if database_url else get_engine()

        # Initialize results
        suggestions = []

        with engine.connect() as conn:
            # Get table list and process based on database type
            if engine.dialect.name == "sqlite":
                tables_result = conn.execute(
                    text(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    )
                )
                tables = [row[0] for row in tables_result]

                # Get existing indices
                indices_result = conn.execute(
                    text("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
                )
                indices_rows = list(indices_result)
                
                existing_indices = {}
                for name, tbl in indices_rows:
                    existing_indices.setdefault(tbl, []).append(name)

                # Analyze each table
                for table in tables:
                    # Get columns used in queries
                    columns_result = conn.execute(text(f"PRAGMA table_info('{table}')"))
                    columns = [row[1] for row in columns_result]

                    # Skip small tables (less than 1000 rows)
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM '{table}'"))
                    row_count = count_result.scalar()
                    if row_count < 1000:
                        continue

                    # Identify columns that might benefit from indices
                    for column in columns:
                        # Skip if column is already indexed
                        if any(
                            idx.lower().find(column.lower()) != -1
                            for idx in existing_indices.get(table, [])
                        ):
                            continue

                        # Check if column is used in WHERE clauses
                        # Ideally this would be from analyzing query logs, but we'll use heuristics

                        # Check if column appears to be a foreign key
                        if column.lower().endswith("_id") or column.lower() == "id":
                            suggestions.append(
                                {
                                    "table": table,
                                    "column": column,
                                    "reason": "Potential foreign key or ID column",
                                    "sql": f"CREATE INDEX idx_{table}_{column} ON {table}({column})",
                                    "impact": "High",
                                }
                            )

                        # Check if column appears to be a date/time
                        elif any(
                            date_term in column.lower()
                            for date_term in ["date", "time", "created", "updated"]
                        ):
                            suggestions.append(
                                {
                                    "table": table,
                                    "column": column,
                                    "reason": "Temporal column likely used in filtering and sorting",
                                    "sql": f"CREATE INDEX idx_{table}_{column} ON {table}({column})",
                                    "impact": "Medium",
                                }
                            )

            # SQL Server specific suggestions
            elif engine.dialect.name == "mssql":
                # Get tables with missing indices using DMVs
                missing_indices_query = """
                SELECT 
                    OBJECT_NAME(mid.object_id) AS TableName,
                    COL_NAME(mid.object_id, mic.column_id) AS ColumnName,
                    migs.avg_user_impact AS Impact,
                    migs.unique_compiles AS QueryCount
                FROM sys.dm_db_missing_index_details mid
                CROSS APPLY sys.dm_db_missing_index_columns(mid.index_handle) mic
                INNER JOIN sys.dm_db_missing_index_groups mig ON mid.index_handle = mig.index_handle
                INNER JOIN sys.dm_db_missing_index_group_stats migs ON mig.index_group_handle = migs.group_handle
                WHERE migs.avg_user_impact > 50  -- Only suggest indices with impact > 50%
                ORDER BY migs.avg_user_impact DESC
                """
                try:
                    missing_indices_result = conn.execute(text(missing_indices_query))

                    # Process missing index suggestions
                    table_columns = {}  # Group by table
                    for row in missing_indices_result:
                        table = row[0]
                        column = row[1]
                        impact = row[2]
                        query_count = row[3]

                        if table not in table_columns:
                            table_columns[table] = []

                        if column not in [c["column"] for c in table_columns[table]]:
                            table_columns[table].append(
                                {
                                    "column": column,
                                    "impact": impact,
                                    "query_count": query_count,
                                }
                            )

                    # Create suggestions for each table
                    for table, columns in table_columns.items():
                        if len(columns) == 1:
                            # Single column index
                            col = columns[0]
                            suggestions.append(
                                {
                                    "table": table,
                                    "column": col["column"],
                                    "reason": f"Used in WHERE clauses ({col['query_count']} queries)",
                                    "sql": f"CREATE INDEX idx_{table}_{col['column']} ON {table}({col['column']})",
                                    "impact": f"High - {col['impact']}% performance improvement",
                                }
                            )
                        else:
                            # Multi-column index for tables with multiple suggestions
                            # Sort by impact
                            columns_sorted = sorted(
                                columns, key=lambda x: x["impact"], reverse=True
                            )
                            column_list = [
                                c["column"] for c in columns_sorted[:3]
                            ]  # Limit to 3 columns
                            column_list_str = ", ".join(column_list)

                            suggestions.append(
                                {
                                    "table": table,
                                    "column": column_list_str,
                                    "reason": "Compound index for multiple query patterns",
                                    "sql": f"CREATE INDEX idx_{table}_{'_'.join(column_list)} ON {table}({column_list_str})",
                                    "impact": f"High - {columns_sorted[0]['impact']}% potential improvement",
                                }
                            )
                except Exception as e:
                    logger.warning(
                        f"Failed to get SQL Server missing index suggestions: {str(e)}"
                    )

            # Oracle specific suggestions
            elif engine.dialect.name == "oracle":
                # Query for table and column information
                tables_query = "SELECT table_name FROM user_tables"
                tables_result = conn.execute(text(tables_query))
                tables = [row[0] for row in tables_result]

                # Get existing indices
                indices_query = """
                SELECT index_name, table_name, column_name 
                FROM user_ind_columns
                """
                indices_result = conn.execute(text(indices_query))

                existing_indices = {}
                for row in indices_result:
                    table = row[1]
                    column = row[2]

                    if table not in existing_indices:
                        existing_indices[table] = []

                    existing_indices[table].append(column)

                # Check for tables with many rows but no indices
                for table in tables:
                    # Count rows in table
                    count_query = f"SELECT COUNT(*) FROM {table}"
                    count_result = conn.execute(text(count_query))
                    row_count = count_result.scalar()

                    if row_count < 1000:
                        continue  # Skip small tables

                    # Get table columns
                    columns_query = f"SELECT column_name, data_type FROM user_tab_columns WHERE table_name = '{table}'"
                    columns_result = conn.execute(text(columns_query))

                    for row in columns_result:
                        column = row[0]
                        data_type = row[1]

                        # Skip if column is already indexed
                        if (
                            table in existing_indices
                            and column in existing_indices[table]
                        ):
                            continue

                        # Generate suggestions based on column name and type
                        if column.lower().endswith("_id") or column.lower() == "id":
                            suggestions.append(
                                {
                                    "table": table,
                                    "column": column,
                                    "reason": "Potential foreign key or ID column",
                                    "sql": f"CREATE INDEX idx_{table}_{column} ON {table}({column})",
                                    "impact": "High",
                                }
                            )
                        elif data_type in ("DATE", "TIMESTAMP"):
                            suggestions.append(
                                {
                                    "table": table,
                                    "column": column,
                                    "reason": "Date/time column likely used in filters",
                                    "sql": f"CREATE INDEX idx_{table}_{column} ON {table}({column})",
                                    "impact": "Medium",
                                }
                            )
                        elif any(
                            term in column.lower()
                            for term in ["name", "status", "type", "category"]
                        ):
                            suggestions.append(
                                {
                                    "table": table,
                                    "column": column,
                                    "reason": "Categorical column likely used in filters or joins",
                                    "sql": f"CREATE INDEX idx_{table}_{column} ON {table}({column})",
                                    "impact": "Medium",
                                }
                            )

        return suggestions

    except Exception as e:
        logger.error(f"Error suggesting indices: {str(e)}")
        return []


def initialize_db_optimization(database_url: Optional[str] = None) -> bool:
    """
    Initialize database optimization during application startup.

    Args:
        database_url: Optional database URL. If not provided, uses active connection

    Returns:
        bool: True if optimization was initialized successfully
    """
    try:
        # Run analyze to optimize query planning
        success = analyze_database(database_url)

        if success:
            logger.info("Database optimization initialized successfully")

        return success
    except Exception as e:
        logger.error(f"Failed to initialize database optimization: {str(e)}")
        return False
