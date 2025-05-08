"""Schemas for SQL generation and database information."""

from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field

from app.schemas.user_query import IntentOutput, UserQuery


class ColumnInfo(BaseModel):
    """Information about a database column."""
    
    name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="SQL data type")
    nullable: bool = Field(default=True, description="Whether the column can be NULL")
    primary_key: bool = Field(default=False, description="Whether this is a primary key column")
    foreign_key: Optional[str] = Field(None, description="Foreign key reference if applicable")
    description: Optional[str] = Field(None, description="Column description")
    sample_values: List[str] = Field(default_factory=list, description="Sample values from the column")


class TableInfo(BaseModel):
    """Information about a database table."""
    
    name: str = Field(..., description="Table name")
    schema: Optional[str] = Field(None, description="Schema name if applicable")
    columns: List[ColumnInfo] = Field(..., description="List of columns in the table")
    description: Optional[str] = Field(None, description="Table description or purpose")
    row_count: Optional[int] = Field(None, description="Approximate number of rows")
    primary_keys: List[str] = Field(default_factory=list, description="Names of primary key columns")
    foreign_keys: Dict[str, str] = Field(default_factory=dict, description="Column to referenced table mapping")


class DatabaseInfo(BaseModel):
    """Information about a database schema."""
    
    tables: List[TableInfo] = Field(..., description="List of tables in the database")
    name: Optional[str] = Field(None, description="Database name")
    description: Optional[str] = Field(None, description="Database description")
    vendor: Optional[str] = Field(None, description="Database vendor (PostgreSQL, MySQL, etc.)")
    version: Optional[str] = Field(None, description="Database version")


class SQLGenerationInput(BaseModel):
    """Input for SQL generation."""
    
    user_query: UserQuery = Field(..., description="The original user query")
    intent: IntentOutput = Field(..., description="The classified intent")
    database_info: DatabaseInfo = Field(..., description="Database schema information")
    conversation_history: List[Dict] = Field(default_factory=list, description="Previous conversation turns")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    include_explanation: bool = Field(default=True, description="Whether to include explanation")


class SQLGenerationOutput(BaseModel):
    """Output of SQL generation."""
    
    sql: str = Field(..., description="The generated SQL query")
    explanation: Optional[str] = Field(None, description="Explanation of the SQL query")
    confidence: float = Field(default=1.0, description="Confidence score (0.0-1.0)")
    alternatives: List[str] = Field(default_factory=list, description="Alternative SQL queries")
    warnings: List[str] = Field(default_factory=list, description="Warnings or notes about the query")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata about the generation")
    referenced_tables: List[str] = Field(default_factory=list, description="Tables referenced in the query")
    referenced_columns: List[str] = Field(default_factory=list, description="Columns referenced in the query") 