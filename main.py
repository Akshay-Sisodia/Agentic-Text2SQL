"""Main entry point for the Agentic Text-to-SQL application."""

import argparse
import logging
import os
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.api.api import app
from app.core.settings import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")

    # No longer need to check DEBUG flag or build frontend here
    # as the app's own lifespan manager will handle initialization
    yield

    # Shutdown
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


# Update the app's lifespan
app.router.lifespan_context = lifespan


# Custom OpenAPI schema
def custom_openapi():
    """Generate custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema

    # Try to load OpenAPI schema from file
    openapi_path = os.path.join(os.path.dirname(__file__), "openapi.yaml")
    if os.path.exists(openapi_path):
        import yaml

        try:
            with open(openapi_path, "r") as f:
                app.openapi_schema = yaml.safe_load(f)
                return app.openapi_schema
        except Exception as e:
            logger.error(f"Failed to load OpenAPI schema from file: {str(e)}")

    # Generate schema using FastAPI
    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        routes=app.routes,
    )

    # Customize schema
    openapi_schema["info"]["x-logo"] = {"url": "/static/logo.png"}

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Set custom OpenAPI schema
app.openapi = custom_openapi


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Agentic Text-to-SQL Server")
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to bind the server to"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", 8000)),
        help="Port to bind the server to",
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--workers", type=int, default=1, help="Number of worker processes"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=settings.LOG_LEVEL.lower(),
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging level",
    )
    return parser.parse_args()


def main():
    """Run the application."""
    try:
        logger.info("Starting Agentic Text-to-SQL application...")

        # Parse command line arguments
        args = parse_arguments()

        # Start the server
        uvicorn.run(
            "app.api.api:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers,
            log_level=args.log_level,
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
