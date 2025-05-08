"""Main entry point for the Agentic Text-to-SQL application."""

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.api.api import app as api_app
from app.core.config import settings
from app.utils.sample_db import create_sample_database
from app.utils.sample_postgres_db import create_sample_postgres_database
from app.utils.sample_mysql_db import create_sample_mysql_database
from app.utils.sample_mssql_db import create_sample_mssql_database
from app.utils.sample_oracle_db import create_sample_oracle_database

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events for the application.
    
    Args:
        app: FastAPI application
    """
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    
    # Initialize sample database based on database type
    if settings.DB_TYPE == "sqlite":
        create_sample_database()
    elif settings.DB_TYPE == "postgresql":
        create_sample_postgres_database()
    elif settings.DB_TYPE == "mysql":
        create_sample_mysql_database()
    elif settings.DB_TYPE == "mssql":
        create_sample_mssql_database()
    elif settings.DB_TYPE == "oracle":
        create_sample_oracle_database()
    else:
        logger.warning(f"Unsupported database type: {settings.DB_TYPE}")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


def main():
    """Run the application."""
    logger.info("Starting Agentic Text-to-SQL application...")
    
    # Add lifespan to the app
    api_app.router.lifespan_context = lifespan
    
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Start the server
    uvicorn.run(
        "app.api.api:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
