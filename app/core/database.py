"""Database connection and session management."""

import os
from typing import Optional

from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

from app.core.config import settings

# Global metadata object
metadata = MetaData()

# Database engine
engine: Optional[Engine] = None

# Path to the sample database
# This sample database contains synthetic data for testing and demos
# It has a production-like schema populated by the generate_db.py script
SAMPLE_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sample_huge.db"
)


def get_database_url(
    db_type: str = None,
    db_name: str = None,
    db_user: str = None,
    db_password: str = None,
    db_host: str = None,
    db_port: int = None,
) -> str:
    """
    Construct the database URL based on settings or provided parameters.

    Args:
        db_type: Database type (postgresql, mysql, sqlite, etc.)
        db_name: Database name
        db_user: Database username
        db_password: Database password
        db_host: Database host
        db_port: Database port

    Returns:
        str: Database connection URL
    """
    # Check if sample database exists and should be used (when no explicit params provided)
    should_use_sample_db = (
        os.path.exists(SAMPLE_DB_PATH)
        and not any([
            (db_type and db_type != "sqlite"),
            (db_name and db_name not in ["text2sql", "sample_huge.db"]),
            db_user,
            db_password,
            db_host,
            db_port,
        ])
    )
    
    if should_use_sample_db:
        return f"sqlite:///{SAMPLE_DB_PATH}"

    # Use provided parameters or fall back to settings
    db_type = db_type or settings.DB_TYPE
    db_name = db_name or settings.DB_NAME
    db_user = db_user or settings.DB_USER
    db_password = db_password or settings.DB_PASSWORD
    db_host = db_host or settings.DB_HOST
    db_port = db_port or settings.DB_PORT

    # Prefer explicit DATABASE_URL when caller did not supply overrides
    if settings.DATABASE_URL and not any(
        [db_type, db_name, db_user, db_password, db_host, db_port]
    ):
        return settings.DATABASE_URL

    if db_type == "sqlite":
        # Use the provided db_name as the SQLite path
        # No need to check for sample DB again as we did that already at the top
        db_path = db_name if os.path.isabs(db_name) else os.path.join(os.getcwd(), db_name)
        return f"sqlite:///{db_path}"

    # Construct URL for other database types
    if db_type == "postgresql":
        driver = "postgresql+psycopg2"
    elif db_type == "mysql":
        driver = "mysql+pymysql"
    elif db_type == "mssql":
        driver = "mssql+pyodbc"
    elif db_type == "oracle":
        driver = "oracle+cx_oracle"
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

    # Build the URL with proper credentials
    if db_user and db_password:
        auth = f"{db_user}:{db_password}@"
    elif db_user:
        auth = f"{db_user}@"
    else:
        auth = ""

    # Add host and port if available
    if db_host:
        host = db_host
        port = f":{db_port}" if db_port else ""
    else:
        host = "localhost"
        port = f":{db_port}" if db_port else ""

    return f"{driver}://{auth}{host}{port}/{db_name}"


def get_engine(database_url: str = None) -> Engine:
    """
    Get or create the database engine.

    Args:
        database_url: Optional database URL to use. If None, uses the configured URL.

    Returns:
        Engine: SQLAlchemy engine instance
    """
    global engine

    # If a specific database URL is provided, create a new engine for it
    if database_url is not None:
        # Connection pooling configuration
        pool_options = {
            "poolclass": QueuePool,
            "pool_size": 20,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 3600,
        }

        # SQLite doesn't use connection pooling
        if database_url.startswith("sqlite"):
            pool_options = {}

        # Create and return a new engine for this specific connection
        return create_engine(
            database_url,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            future=True,
            **pool_options,
        )

    # Otherwise, return or create the global engine
    if engine is None:
        # Connection pooling configuration
        pool_options = {
            "poolclass": QueuePool,
            "pool_size": 20,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 3600,
        }

        # SQLite doesn't use connection pooling
        if settings.DB_TYPE == "sqlite":
            pool_options = {}

        # Create the engine
        engine = create_engine(get_database_url(), echo=settings.DEBUG, **pool_options)

    return engine


def get_metadata() -> MetaData:
    """
    Get the metadata object.

    Returns:
        MetaData: SQLAlchemy metadata
    """
    return metadata
