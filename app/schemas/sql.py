"""Schemas for SQL generation and database information."""

from typing import Dict, List, Optional, Any, Literal

from pydantic import BaseModel, Field, validator

from app.schemas.user_query import IntentOutput, UserQuery


class ColumnInfo(BaseModel):
    """Information about a database column."""

    name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="SQL data type")
    nullable: bool = Field(default=True, description="Whether the column can be NULL")
    primary_key: bool = Field(
        default=False, description="Whether this is a primary key column"
    )
    unique: bool = Field(
        default=False, description="Whether this column has a UNIQUE constraint"
    )
    foreign_key: Optional[str] = Field(
        None, description="Foreign key reference if applicable"
    )
    description: Optional[str] = Field(None, description="Column description")
    sample_values: List[str] = Field(
        default_factory=list, description="Sample values from the column"
    )


class TableInfo(BaseModel):
    """Information about a database table."""

    name: str = Field(..., description="Table name")
    db_schema: Optional[str] = Field(None, description="Schema name if applicable")
    columns: List[ColumnInfo] = Field(..., description="List of columns in the table")
    description: Optional[str] = Field(None, description="Table description or purpose")
    row_count: Optional[int] = Field(None, description="Approximate number of rows")
    primary_keys: List[str] = Field(
        default_factory=list, description="Names of primary key columns"
    )
    foreign_keys: Dict[str, str] = Field(
        default_factory=dict, description="Column to referenced table mapping"
    )


class Relationship(BaseModel):
    """Information about a relationship between database tables."""

    source_table: str = Field(..., description="Source table name")
    source_column: str = Field(..., description="Source column name")
    target_table: str = Field(..., description="Target table name")
    target_column: str = Field(..., description="Target column name")
    relationship_type: str = Field(
        ..., description="Type of relationship (ONE_TO_MANY, MANY_TO_ONE, etc.)"
    )


class DatabaseInfo(BaseModel):
    """Information about a database schema."""

    tables: List[TableInfo] = Field(..., description="List of tables in the database")
    relationships: List[Relationship] = Field(
        default_factory=list, description="List of relationships between tables"
    )
    name: Optional[str] = Field(None, description="Database name")
    description: Optional[str] = Field(None, description="Database description")
    vendor: Optional[str] = Field(
        None, description="Database vendor (PostgreSQL, MySQL, etc.)"
    )
    version: Optional[str] = Field(None, description="Database version")


class ConversationTurn(BaseModel):
    """A single turn in a conversation."""
    
    role: Literal["user", "assistant"] = Field(..., description="Role of the speaker")
    content: str = Field(..., description="Content of the message")
    sql: Optional[str] = Field(None, description="SQL query if the role is assistant")
    timestamp: Optional[str] = Field(None, description="Timestamp of the message")


class SQLGenerationInput(BaseModel):
    """Input for SQL generation."""

    user_query: UserQuery = Field(..., description="The original user query")
    intent: IntentOutput = Field(..., description="The classified intent")
    database_info: DatabaseInfo = Field(..., description="Database schema information")
    conversation_history: List[ConversationTurn] = Field(
        default_factory=list, description="Previous conversation turns"
    )
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    include_explanation: bool = Field(
        default=True, description="Whether to include explanation"
    )


class SQLGenerationOutput(BaseModel):
    """Output of SQL generation."""

    sql: str = Field(..., description="The generated SQL query")
    sql_query: Optional[str] = Field(
        None, 
        description="DEPRECATED: Use 'sql' instead. Maintained for backward compatibility."
    )
    explanation: Optional[str] = Field(None, description="Explanation of the SQL query")
    confidence: float = Field(default=1.0, description="Confidence score (0.0-1.0)")
    alternatives: List[str] = Field(
        default_factory=list, description="Alternative SQL queries"
    )
    warnings: List[str] = Field(
        default_factory=list, description="Warnings or notes about the query"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the generation"
    )
    referenced_tables: List[str] = Field(
        default_factory=list, description="Tables referenced in the query"
    )
    referenced_columns: List[str] = Field(
        default_factory=list, description="Columns referenced in the query"
    )
    validation_issues: List[str] = Field(
        default_factory=list, description="Issues found during validation"
    )
    error_message: Optional[str] = Field(
        None, description="Error message if SQL generation failed"
    )

    @validator("sql_query", always=True)
    def sync_sql_query(cls, v, values):
        """Ensure sql_query is always the same as sql. DEPRECATED: This field is maintained for backward compatibility."""
        if "sql" in values:
            return values["sql"]
        return v
