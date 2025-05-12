"""Schemas for API responses."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from app.schemas.sql import SQLGenerationOutput
from app.schemas.user_query import IntentOutput, UserQuery


class QueryStatus(str, Enum):
    """Status of a query execution."""
    
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"


class QueryResult(BaseModel):
    """Result of a SQL query execution."""
    
    status: QueryStatus = Field(..., description="Execution status")
    rows: Optional[List[Dict[str, Any]]] = Field(None, description="Query result rows")
    row_count: Optional[int] = Field(None, description="Number of rows returned")
    column_names: Optional[List[str]] = Field(None, description="Column names in result")
    columns: Optional[List[str]] = Field(None, description="Column names (frontend compatibility)")
    execution_time: Optional[float] = Field(None, description="Time taken to execute in seconds")
    error_message: Optional[str] = Field(None, description="Error message if execution failed")
    warnings: List[str] = Field(default_factory=list, description="Warnings during execution")


class ExplanationType(str, Enum):
    """Type of explanation to provide."""
    
    TECHNICAL = "TECHNICAL"  # Detailed technical explanation
    SIMPLIFIED = "SIMPLIFIED"  # Non-technical explanation
    EDUCATIONAL = "EDUCATIONAL"  # Educational with SQL concepts
    BRIEF = "BRIEF"  # Very short explanation


class UserExplanation(BaseModel):
    """Human-readable explanation of a query."""
    
    text: str = Field(..., description="Explanation text")
    type: ExplanationType = Field(default=ExplanationType.SIMPLIFIED, description="Type of explanation")
    referenced_concepts: List[str] = Field(default_factory=list, description="SQL concepts referenced")


class UserResponse(BaseModel):
    """Complete response to send back to the user."""
    
    user_query: UserQuery = Field(..., description="Original user query")
    intent: Optional[IntentOutput] = Field(None, description="Classified intent")
    sql_generation: Optional[SQLGenerationOutput] = Field(None, description="Generated SQL")
    query_result: Optional[QueryResult] = Field(None, description="Query execution result")
    explanation: Optional[UserExplanation] = Field(None, description="User-friendly explanation")
    suggested_followups: List[str] = Field(default_factory=list, description="Suggested follow-up queries")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for tracking")
    timestamp: Optional[str] = Field(None, description="Response timestamp")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata") 