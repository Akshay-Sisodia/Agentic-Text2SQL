"""FastAPI application for the Text-to-SQL API."""

import datetime
import uuid
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel

from app.agents.explanation_agent import generate_explanation
from app.agents.intent_agent import classify_intent
from app.agents.sql_agent import generate_sql
from app.core.config import settings
from app.schemas.response import (ExplanationType, QueryResult, QueryStatus,
                                 UserExplanation, UserResponse)
from app.schemas.sql import DatabaseInfo, SQLGenerationOutput
from app.schemas.user_query import IntentOutput, UserQuery
from app.utils.db_utils import execute_generated_sql, get_schema_info


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
)


# In-memory store for conversations
conversations: Dict[str, List[Dict]] = {}


class Text2SQLRequest(BaseModel):
    """Request for Text-to-SQL conversion."""
    
    query: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    explanation_type: ExplanationType = ExplanationType.SIMPLIFIED
    execute_query: bool = True


class Text2SQLResponse(BaseModel):
    """Response from Text-to-SQL conversion."""
    
    user_response: UserResponse
    conversation_id: str
    timestamp: str


# Dependency to get database schema
async def get_db_schema() -> DatabaseInfo:
    """Get database schema information."""
    return get_schema_info()


@app.post(f"{settings.API_PREFIX}/process", response_model=Text2SQLResponse)
async def process_query(
    request: Text2SQLRequest,
    db_schema: DatabaseInfo = Depends(get_db_schema),
) -> Text2SQLResponse:
    """
    Process a natural language query and convert it to SQL.
    
    Args:
        request: Text-to-SQL request
        db_schema: Database schema information
        
    Returns:
        Text2SQLResponse: Response with SQL and explanation
    """
    # Create conversation ID if not provided
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    # Get or create conversation history
    if conversation_id not in conversations:
        conversations[conversation_id] = []
    
    conversation_history = conversations[conversation_id]
    
    try:
        # Create user query object
        timestamp = datetime.datetime.now().isoformat()
        user_query = UserQuery(
            text=request.query,
            conversation_id=conversation_id,
            user_id=request.user_id,
            timestamp=timestamp,
        )
        
        # Step 1: Classify query intent
        intent = classify_intent(request.query, {table.name: {
            "description": table.description,
            "columns": {col.name: {
                "type": col.data_type,
                "primary_key": col.primary_key,
                "nullable": col.nullable,
                "foreign_key": {"table": col.foreign_key.split(".")[0], "column": col.foreign_key.split(".")[1]} if col.foreign_key else None,
                "description": col.description
            } for col in table.columns}
        } for table in db_schema.tables})
        
        # Step 2: Generate SQL based on intent
        sql_result = generate_sql(
            user_query=user_query,
            intent=intent,
            database_info=db_schema,
            conversation_history=conversation_history,
        )
        
        # Step 3: Execute SQL if requested
        query_result = None
        if request.execute_query:
            query_result = execute_generated_sql(sql_result)
        
        # Step 4: Generate explanation
        explanation = generate_explanation(
            user_query=user_query,
            sql_generation=sql_result,
            query_result=query_result.dict() if query_result else None,
            explanation_type=request.explanation_type,
        )
        
        # Create user response
        user_response = UserResponse(
            user_query=user_query,
            intent=intent,
            sql_generation=sql_result,
            query_result=query_result,
            explanation=explanation,
            conversation_id=conversation_id,
            timestamp=timestamp,
        )
        
        # Update conversation history
        conversation_history.append({
            "role": "user",
            "content": request.query,
            "timestamp": timestamp,
        })
        
        conversation_history.append({
            "role": "assistant",
            "content": explanation.text,
            "sql": sql_result.sql,
            "timestamp": datetime.datetime.now().isoformat(),
        })
        
        # Limit conversation history size
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        
        # Create response
        response = Text2SQLResponse(
            user_response=user_response,
            conversation_id=conversation_id,
            timestamp=datetime.datetime.now().isoformat(),
        )
        
        return response
    
    except Exception as e:
        # Create error response
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}",
        )


@app.get(f"{settings.API_PREFIX}/conversations/{'{conversation_id}'}", response_model=List[Dict])
async def get_conversation(conversation_id: str) -> List[Dict]:
    """
    Get conversation history.
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        List[Dict]: Conversation history
    """
    if conversation_id not in conversations:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {conversation_id} not found",
        )
    
    return conversations[conversation_id]


@app.get(f"{settings.API_PREFIX}/schema", response_model=DatabaseInfo)
async def get_database_schema() -> DatabaseInfo:
    """
    Get database schema information.
    
    Returns:
        DatabaseInfo: Database schema
    """
    return get_schema_info() 