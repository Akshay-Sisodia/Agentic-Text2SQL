"""
Utilities for storing and retrieving conversations from a database.
Replaces the in-memory conversations dictionary in api.py.
"""

import uuid
import logging
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy.engine import Engine

from app.core.settings import settings

# Set up logging
logger = logging.getLogger(__name__)

# Create SQLAlchemy base class
Base = declarative_base()

# Module-level locks for thread safety
_engine_lock = threading.Lock()
_session_factory_lock = threading.Lock()

# Module-level variables for engine and session factory
_engine: Optional[Engine] = None
_SessionLocal = None


# Define SQLAlchemy models
class Conversation(Base):
    """SQLAlchemy model for a conversation."""

    __tablename__ = "conversations"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    title = Column(String, nullable=True)

    # Relationship to messages
    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    """SQLAlchemy model for a message in a conversation."""

    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # 'user', 'assistant', or 'system'
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    message_metadata = Column(JSON, nullable=True)

    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")


def get_conversation_engine():
    """
    Get SQLAlchemy engine for the conversation database in a thread-safe manner.
    
    Returns:
        Engine: SQLAlchemy engine instance
    """
    global _engine
    
    # Fast path - engine already initialized
    if _engine is not None:
        return _engine
        
    # Slow path with lock for thread safety
    with _engine_lock:
        # Double-check pattern to avoid unnecessary initialization
        if _engine is not None:
            return _engine
            
        db_url = settings.CONVERSATION_DB_URL or "sqlite:///conversations.db"
        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
        _engine = create_engine(db_url, connect_args=connect_args)
        logger.debug("Conversation database engine initialized")
        
        return _engine


def get_session_factory():
    """
    Get the session factory in a thread-safe manner.
    
    Returns:
        sessionmaker: SQLAlchemy sessionmaker instance
    """
    global _SessionLocal
    
    # Fast path - session factory already initialized
    if _SessionLocal is not None:
        return _SessionLocal
        
    # Slow path with lock for thread safety
    with _session_factory_lock:
        # Double-check pattern to avoid unnecessary initialization
        if _SessionLocal is not None:
            return _SessionLocal
            
        engine = get_conversation_engine()
        _SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
        logger.debug("Conversation database session factory initialized")
        
        return _SessionLocal


# Create all tables
def initialize_conversation_db():
    """Initialize the conversation database."""
    engine = get_conversation_engine()
    Base.metadata.create_all(engine)
    # Initialize session factory as well
    get_session_factory()
    logger.info("Conversation database initialized")


# Conversation database functions
def get_conversation_session():
    """
    Get a session for the conversation database.
    
    Returns:
        Session: SQLAlchemy session instance
    """
    SessionFactory = get_session_factory()
    return SessionFactory()


def create_conversation(
    user_id: Optional[str] = None, title: Optional[str] = None
) -> str:
    """
    Create a new conversation in the database.

    Args:
        user_id: Optional user ID
        title: Optional conversation title

    Returns:
        str: Conversation ID
    """
    conversation_id = str(uuid.uuid4())

    session = get_conversation_session()
    try:
        conversation = Conversation(id=conversation_id, user_id=user_id, title=title)
        session.add(conversation)
        session.commit()
        return conversation_id
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating conversation: {str(e)}")
        raise
    finally:
        session.close()


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a conversation by ID.

    Args:
        conversation_id: Conversation ID

    Returns:
        Optional[Dict[str, Any]]: Conversation data or None if not found
    """
    session = get_conversation_session()
    try:
        conversation = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        if not conversation:
            return None

        return {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "title": conversation.title,
        }
    except Exception as e:
        logger.error(f"Error getting conversation {conversation_id}: {str(e)}")
        return None
    finally:
        session.close()


def get_conversation_messages(conversation_id: str) -> List[Dict[str, Any]]:
    """
    Get all messages for a conversation.

    Args:
        conversation_id: Conversation ID

    Returns:
        List[Dict[str, Any]]: List of messages
    """
    session = get_conversation_session()
    try:
        messages = (
            session.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp)
            .all()
        )

        return [
            {
                "role": message.role,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
                "metadata": message.message_metadata,
            }
            for message in messages
        ]
    except Exception as e:
        logger.error(
            f"Error getting messages for conversation {conversation_id}: {str(e)}"
        )
        return []
    finally:
        session.close()


def add_message_to_conversation(
    conversation_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Add a message to a conversation.

    Args:
        conversation_id: Conversation ID
        role: Message role ('user', 'assistant', or 'system')
        content: Message content
        metadata: Optional message metadata

    Returns:
        bool: True if successful, False otherwise
    """
    session = get_conversation_session()
    try:
        # Check if conversation exists
        conversation = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        if not conversation:
            # Create conversation if it doesn't exist
            conversation = Conversation(id=conversation_id, updated_at=datetime.now())
            session.add(conversation)
        else:
            # Update conversation timestamp
            conversation.updated_at = datetime.now()

        # Create message
        message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_metadata=metadata,
        )
        session.add(message)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(
            f"Error adding message to conversation {conversation_id}: {str(e)}"
        )
        return False
    finally:
        session.close()


def save_conversation_history(conversation_id: str, history: List[Dict]) -> bool:
    """
    Save a complete conversation history.

    Args:
        conversation_id: Conversation ID
        history: Conversation history as a list of message dictionaries

    Returns:
        bool: True if successful, False otherwise
    """
    session = get_conversation_session()
    try:
        # Delete existing messages for this conversation
        session.query(Message).filter(
            Message.conversation_id == conversation_id
        ).delete()

        # Check if conversation exists
        conversation = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        if not conversation:
            # Create conversation if it doesn't exist
            conversation = Conversation(id=conversation_id, updated_at=datetime.now())
            session.add(conversation)
        else:
            # Update conversation timestamp
            conversation.updated_at = datetime.now()

        # Add context to history messages if not present
        processed_history = []
        for i, message in enumerate(history):
            if i > 0 and "context" not in message:
                # Add reference to previous message for context
                prev_message = history[i - 1]
                if "query" in prev_message:
                    message["context"] = {
                        "previous_query": prev_message.get("query", ""),
                        "turn_number": i,
                        "is_followup": any(
                            marker in message.get("query", "").lower()
                            for marker in [
                                "it",
                                "that",
                                "those",
                                "these",
                                "this",
                                "the result",
                                "previous",
                            ]
                        ),
                    }
            processed_history.append(message)

        # Add messages
        for msg in processed_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if "query" in msg:
                content = msg["query"]
                role = "user"
            elif "response" in msg:
                content = msg["response"]
                role = "assistant"

            # Extract metadata
            metadata = {
                k: v
                for k, v in msg.items()
                if k not in ["role", "content", "query", "response"]
            }

            # Create message
            message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role=role,
                content=content,
                message_metadata=metadata,
            )
            session.add(message)

        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(
            f"Error saving conversation history for {conversation_id}: {str(e)}"
        )
        return False
    finally:
        session.close()


def get_user_conversations(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all conversations for a user.

    Args:
        user_id: User ID

    Returns:
        List[Dict[str, Any]]: List of conversations
    """
    session = get_conversation_session()
    try:
        conversations = (
            session.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .all()
        )

        return [
            {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
            }
            for conversation in conversations
        ]
    except Exception as e:
        logger.error(f"Error getting conversations for user {user_id}: {str(e)}")
        return []
    finally:
        session.close()


def delete_conversation(conversation_id: str) -> bool:
    """
    Delete a conversation and all its messages.

    Args:
        conversation_id: Conversation ID

    Returns:
        bool: True if successful, False otherwise
    """
    session = get_conversation_session()
    try:
        # Get conversation
        conversation = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        if not conversation:
            return False

        # Delete conversation (messages will be deleted via cascade)
        session.delete(conversation)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
        return False
    finally:
        session.close()


def update_conversation_title(conversation_id: str, title: str) -> bool:
    """
    Update a conversation's title.

    Args:
        conversation_id: Conversation ID
        title: New title

    Returns:
        bool: True if successful, False otherwise
    """
    session = get_conversation_session()
    try:
        # Get conversation
        conversation = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        if not conversation:
            return False

        # Update title
        conversation.title = title
        conversation.updated_at = datetime.now()
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(
            f"Error updating conversation title for {conversation_id}: {str(e)}"
        )
        return False
    finally:
        session.close()
