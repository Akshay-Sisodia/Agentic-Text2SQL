from datetime import datetime
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field

# Add conversation database models
class ConversationModel(BaseModel):
    """Database model for conversations."""

    id: str
    user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    title: Optional[str] = None

class Config:
     from_attributes = True

 from enum import Enum
 
 class MessageRole(str, Enum):
     USER = "user"
     ASSISTANT = "assistant"
     SYSTEM = "system"

class MessageModel(BaseModel):
    """Database model for conversation messages."""

    id: str
    conversation_id: str
   role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(
     default=None, 
     description="Additional message metadata like SQL query results, timing information, etc."
 )

    class Config:
        orm_mode = True
