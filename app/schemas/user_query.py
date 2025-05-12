"""Schemas for user queries and intent classification."""

from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class QueryType(str, Enum):
    """Types of SQL queries."""
    
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    ALTER = "ALTER"
    DROP = "DROP"
    UNKNOWN = "UNKNOWN"


class EntityType(str, Enum):
    """Types of database entities."""
    
    TABLE = "TABLE"
    COLUMN = "COLUMN"
    VALUE = "VALUE"
    FUNCTION = "FUNCTION"
    OPERATOR = "OPERATOR"
    CONDITION = "CONDITION"
    DATABASE = "DATABASE"
    UNKNOWN = "UNKNOWN"


class Entity(BaseModel):
    """An entity extracted from the user query."""
    
    name: str = Field(..., description="The name of the entity")
    type: EntityType = Field(..., description="The type of the entity")
    confidence: float = Field(default=1.0, description="Confidence score (0.0-1.0)")
    aliases: List[str] = Field(default_factory=list, description="Alternative names for the entity")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata about the entity")


class UserQuery(BaseModel):
    """A user's natural language query."""
    
    text: str = Field(..., description="The original query text")
    conversation_id: Optional[str] = Field(None, description="ID for multi-turn conversations")
    user_id: Optional[str] = Field(None, description="User identifier")
    timestamp: Optional[str] = Field(None, description="Query timestamp")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata about the query")
    
    @validator('text')
    def text_must_not_be_empty(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Query text cannot be empty')
        return v


class IntentOutput(BaseModel):
    """The classified intent of a user query."""
    
    query_type: QueryType = Field(..., description="The type of SQL query to generate")
    entities: List[Entity] = Field(default_factory=list, description="Entities extracted from the query")
    confidence: float = Field(default=1.0, description="Overall confidence score (0.0-1.0)")
    is_ambiguous: bool = Field(default=False, description="Whether the query is ambiguous")
    clarification_question: Optional[str] = Field(None, description="Question to ask for clarification if ambiguous")
    explanation: Optional[str] = Field(None, description="Explanation of the intent classification")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata about the intent") 