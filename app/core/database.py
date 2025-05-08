"""Database connection and session management."""

import os
from typing import Dict, Optional

from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

from app.core.config import settings

# Global metadata object
metadata = MetaData()

# Database engine
engine: Optional[Engine] = None


def get_database_url() -> str:
    """
    Construct the database URL based on settings.
    
    Returns:
        str: Database connection URL
    """
    if settings.DATABASE_URL:
        return settings.DATABASE_URL
    
    if settings.DB_TYPE == "sqlite":
        db_path = os.path.join(os.getcwd(), f"{settings.DB_NAME}")
        return f"sqlite:///{db_path}"
    
    # Construct URL for other database types
    if settings.DB_TYPE == "postgresql":
        driver = "postgresql+psycopg2"
    elif settings.DB_TYPE == "mysql":
        driver = "mysql+pymysql"
    elif settings.DB_TYPE == "mssql":
        driver = "mssql+pyodbc"
    elif settings.DB_TYPE == "oracle":
        driver = "oracle+cx_oracle"
    else:
        raise ValueError(f"Unsupported database type: {settings.DB_TYPE}")
    
    # Build the URL with proper credentials
    if settings.DB_USER and settings.DB_PASSWORD:
        auth = f"{settings.DB_USER}:{settings.DB_PASSWORD}@"
    elif settings.DB_USER:
        auth = f"{settings.DB_USER}@"
    else:
        auth = ""
    
    # Add host and port if available
    if settings.DB_HOST:
        host = settings.DB_HOST
        port = f":{settings.DB_PORT}" if settings.DB_PORT else ""
    else:
        host = "localhost"
        port = f":{settings.DB_PORT}" if settings.DB_PORT else ""
    
    return f"{driver}://{auth}{host}{port}/{settings.DB_NAME}"


def get_engine() -> Engine:
    """
    Get or create the database engine.
    
    Returns:
        Engine: SQLAlchemy engine instance
    """
    global engine
    
    if engine is None:
        # Connection pooling configuration
        pool_options: Dict = {
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
        engine = create_engine(
            get_database_url(),
            echo=settings.DEBUG,
            **pool_options
        )
    
    return engine


def get_metadata() -> MetaData:
    """
    Get the metadata object.
    
    Returns:
        MetaData: SQLAlchemy metadata
    """
    return metadata 