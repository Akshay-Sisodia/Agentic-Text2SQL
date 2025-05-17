#!/usr/bin/env python
"""
Agentic Text-to-SQL Command Line Interface

This module provides a command-line interface for the Agentic Text-to-SQL application
using the Click library. It allows users to run queries, execute SQL, and get explanations
directly from the command line.
"""

import os
import sys
import click
import logging
from typing import Optional

from app.utils.db_utils import get_schema_info, execute_generated_sql
from app.agents.intent_agent import classify_intent
from app.agents.sql_agent import generate_sql
from app.agents.explanation_agent import generate_explanation
from app.schemas.user_query import UserQuery
from app.schemas.response import ExplanationType
from app.core.config import settings


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(settings.VERSION, prog_name=settings.PROJECT_NAME)
def cli():
    """Agentic Text-to-SQL CLI - Convert natural language to SQL queries."""
    # Check for API key
    if not os.environ.get("GROQ_API_KEY") and not settings.LLM_API_KEY:
        click.secho("WARNING: No LLM API key found. Set GROQ_API_KEY in your environment or LLM_API_KEY in .env file.", fg="yellow")
        click.echo("You can still use the tools that don't require LLM access, such as 'schema' and 'run-sql'.")
    pass


@cli.command()
@click.argument("query", required=False)
@click.option("--execute/--no-execute", "-e/-n", default=False, 
              help="Execute the generated SQL query")
@click.option("--explanation-type", "-t", 
              type=click.Choice(["technical", "simplified", "educational", "brief"]), 
              default="simplified", help="Type of explanation to provide")
@click.option("--interactive/--non-interactive", "-i/-ni", default=False, 
              help="Run in interactive mode")
@click.option("--api-key", help="LLM API key to use for this session")
def query(query: Optional[str], execute: bool, explanation_type: str, interactive: bool, api_key: Optional[str]):
    """Convert natural language to SQL and optionally execute it."""
    # Set API key if provided
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key
        
    # Check for API key
    if not os.environ.get("GROQ_API_KEY") and not settings.LLM_API_KEY:
        click.secho("ERROR: No LLM API key found. Set GROQ_API_KEY in your environment or use --api-key option.", fg="red")
        click.echo("You can get an API key from https://console.groq.com/")
        return
        
    # Get database schema
    try:
        schema = get_schema_info()
        click.echo(f"Connected to database: {schema.name}")
    except Exception as e:
        click.secho(f"Error connecting to database: {str(e)}", fg="red")
        click.echo("\nPlease ensure your database is properly configured in the .env file:")
        click.echo(f"  - Current DB type: {settings.DB_TYPE}")
        if settings.DB_TYPE == "sqlite":
            click.echo(f"  - DB name: {settings.DB_NAME}")
        else:
            click.echo(f"  - DB host: {settings.DB_HOST}")
            click.echo(f"  - DB port: {settings.DB_PORT}")
            click.echo(f"  - DB name: {settings.DB_NAME}")
            click.echo(f"  - DB user: {settings.DB_USER}")
            click.echo(f"  - DB password: {'*****' if settings.DB_PASSWORD else 'not set'}")
        return
    
    if interactive:
        run_interactive_mode(schema)
        return
    
    if not query:
        click.echo("Error: Query is required unless in interactive mode.")
        click.echo("Use --interactive/-i for interactive mode or provide a query.")
        return
    
    # Process the query
    process_single_query(query, schema, execute, explanation_type)


def process_single_query(query_text: str, schema, execute: bool, explanation_type_str: str):
    """Process a single query and display the results."""
    user_query = UserQuery(text=query_text)
    
    # Map string to ExplanationType enum
    explanation_type_map = {
        "technical": ExplanationType.TECHNICAL,
        "simplified": ExplanationType.SIMPLIFIED,
        "educational": ExplanationType.EDUCATIONAL,
        "brief": ExplanationType.BRIEF
    }
    explanation_type = explanation_type_map.get(explanation_type_str.lower(), ExplanationType.SIMPLIFIED)
    
    # Classify intent
    click.echo("\nClassifying intent...")
    intent = classify_intent(
        query_text,
        {
            t.name: {
                "columns": {
                    c.name: {
                        "type": c.data_type,
                        "primary_key": c.primary_key,
                        "foreign_key": (
                            {"table": c.foreign_key.split(".")[0], "column": c.foreign_key.split(".")[1]}
                            if c.foreign_key and "." in c.foreign_key else None
                        ),
                        "unique": False,
                        "nullable": c.nullable
                    }
                    for c in t.columns
                }
            }
            for t in schema.tables
        }
    )
    click.echo(f"Intent: {intent.query_type}, Entities: {[e.name for e in intent.entities]}, Ambiguous: {intent.is_ambiguous}")
    
    if intent.is_ambiguous and intent.clarification_question:
        click.echo(f"Clarification needed: {intent.clarification_question}")
        return
    
    # Generate SQL
    click.echo("\nGenerating SQL...")
    sql_output = generate_sql(user_query, intent, schema)
    click.secho(f"Generated SQL:", fg="green")
    click.secho(f"{sql_output.sql}\n", fg="cyan")
    
    if sql_output.explanation:
        click.echo(f"SQL Agent Explanation: {sql_output.explanation}\n")
    if sql_output.warnings:
        click.secho("Warnings:", fg="yellow")
        for warning in sql_output.warnings:
            click.secho(f"- {warning}", fg="yellow")
        click.echo()
    
    # Execute SQL if requested
    query_result = None
    if execute:
        click.echo("Executing SQL...")
        query_result = execute_generated_sql(sql_output)
        if query_result.status == 'SUCCESS':
            click.secho(f"Query executed successfully. Rows: {query_result.row_count}", fg="green")
            if query_result.rows:
                # Calculate column widths for formatting
                if query_result.rows:
                    widths = {}
                    for column in query_result.column_names:
                        widths[column] = len(column)
                    
                    for row in query_result.rows:
                        for column in query_result.column_names:
                            if column in row and row[column] is not None:
                                widths[column] = max(widths[column], len(str(row[column])))
                    
                    # Print header
                    header = "| " + " | ".join(column.ljust(widths[column]) for column in query_result.column_names) + " |"
                    separator = "+-" + "-+-".join("-" * widths[column] for column in query_result.column_names) + "-+"
                    
                    click.echo(separator)
                    click.echo(header)
                    click.echo(separator)
                    
                    # Print rows
                    for row in query_result.rows[:10]:  # Limit to 10 rows
                        row_str = "| " + " | ".join(str(row.get(column, "")).ljust(widths[column]) for column in query_result.column_names) + " |"
                        click.echo(row_str)
                    
                    click.echo(separator)
                    
                    if query_result.row_count > 10:
                        click.echo(f"... and {query_result.row_count - 10} more rows.")
        else:
            click.secho(f"Query execution failed: {query_result.error_message}", fg="red")
    
    # Generate explanation
    click.echo(f"\nGenerating {explanation_type.value.lower()} explanation...")
    explanation = generate_explanation(user_query, sql_output, query_result.dict() if query_result else None, explanation_type)
    click.secho("Explanation:", fg="green")
    click.echo(f"{explanation.text}\n")


def run_interactive_mode(schema):
    """Run the CLI in interactive mode."""
    click.secho("\nAgentic Text-to-SQL Interactive Mode", fg="green", bold=True)
    click.echo("-" * 40)
    click.echo(f"Connected to database: {schema.name}\n")
    
    while True:
        try:
            query_text = click.prompt("Enter your query (or 'exit' to quit)", type=str)
            if query_text.lower() in {"exit", "quit", ":q"}:
                click.echo("Exiting.")
                break
            if not query_text:
                continue
            
            # Process the user query
            process_single_query(
                query_text, 
                schema, 
                click.confirm("Execute the generated SQL?", default=False),
                click.prompt(
                    "Explanation type",
                    type=click.Choice(["technical", "simplified", "educational", "brief"]),
                    default="simplified"
                )
            )
            click.echo("-" * 40)
        except Exception as e:
            click.secho(f"Error processing query: {str(e)}", fg="red")
            click.echo("Please try again or type 'exit' to quit.")
            click.echo("-" * 40)


@cli.command()
def schema():
    """Display the current database schema."""
    try:
        schema = get_schema_info()
        click.secho(f"Database: {schema.name} ({schema.vendor})", fg="green", bold=True)
        
        for table in schema.tables:
            click.secho(f"\nTable: {table.name}", fg="cyan", bold=True)
            if table.description:
                click.echo(f"Description: {table.description}")
                
            # Print columns
            click.echo("\nColumns:")
            click.echo("+-" + "-" * 25 + "-+-" + "-" * 15 + "-+-" + "-" * 8 + "-+-" + "-" * 8 + "-+-" + "-" * 25 + "-+")
            click.echo("| " + "Name".ljust(25) + " | " + "Type".ljust(15) + " | " + "Nullable".ljust(8) + " | " + "PK".ljust(8) + " | " + "Foreign Key".ljust(25) + " |")
            click.echo("+-" + "-" * 25 + "-+-" + "-" * 15 + "-+-" + "-" * 8 + "-+-" + "-" * 8 + "-+-" + "-" * 25 + "-+")
            
            for col in table.columns:
                name = col.name[:25].ljust(25)
                data_type = col.data_type[:15].ljust(15)
                nullable = "Yes" if col.nullable else "No"
                pk = "Yes" if col.primary_key else "No"
                fk = col.foreign_key if col.foreign_key else ""
                fk = fk[:25].ljust(25)
                
                click.echo(f"| {name} | {data_type} | {nullable.ljust(8)} | {pk.ljust(8)} | {fk} |")
            
            click.echo("+-" + "-" * 25 + "-+-" + "-" * 15 + "-+-" + "-" * 8 + "-+-" + "-" * 8 + "-+-" + "-" * 25 + "-+")
    except Exception as e:
        click.secho(f"Error retrieving schema: {str(e)}", fg="red")


@cli.command()
@click.argument("sql", required=True)
def run_sql(sql: str):
    """Execute raw SQL query."""
    from app.schemas.sql import SQLGenerationOutput
    
    # Create a SQLGenerationOutput object
    sql_output = SQLGenerationOutput(sql=sql)
    
    click.echo(f"Executing SQL: {sql}")
    result = execute_generated_sql(sql_output)
    
    if result.status == 'SUCCESS':
        click.secho(f"Query executed successfully. Rows: {result.row_count}", fg="green")
        if result.rows:
            if result.column_names:
                # Calculate column widths for formatting
                widths = {}
                for column in result.column_names:
                    widths[column] = len(column)
                
                for row in result.rows:
                    for column in result.column_names:
                        if column in row and row[column] is not None:
                            widths[column] = max(widths[column], len(str(row[column])))
                
                # Print header
                header = "| " + " | ".join(column.ljust(widths[column]) for column in result.column_names) + " |"
                separator = "+-" + "-+-".join("-" * widths[column] for column in result.column_names) + "-+"
                
                click.echo(separator)
                click.echo(header)
                click.echo(separator)
                
                # Print rows
                for row in result.rows[:10]:  # Limit to 10 rows
                    row_str = "| " + " | ".join(str(row.get(column, "")).ljust(widths[column]) for column in result.column_names) + " |"
                    click.echo(row_str)
                
                click.echo(separator)
                
                if result.row_count > 10:
                    click.echo(f"... and {result.row_count - 10} more rows.")
    else:
        click.secho(f"Query execution failed: {result.error_message}", fg="red")


@cli.command()
def server():
    """Start the Text-to-SQL API server."""
    import uvicorn
    from app.core.config import settings
    
    click.echo(f"Starting {settings.PROJECT_NAME} API server...")
    
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
    cli() 