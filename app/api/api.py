"""FastAPI application for the Text-to-SQL API."""

import datetime
import os
import uuid
import logging
from typing import Dict, List, Optional, Any
from enum import Enum
import traceback
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

from app.agents.base_explanation_agent import generate_explanation
from app.agents.base_intent_agent import classify_intent
# Import the enhanced agents
try:
    from app.agents.pydantic_intent_agent import classify_intent_enhanced
    from app.agents.pydantic_sql_agent import generate_sql_enhanced
    from app.agents.pydantic_explanation_agent import generate_explanation_enhanced
    from app.agents import ENHANCED_AGENT_AVAILABLE
except ImportError:
    ENHANCED_AGENT_AVAILABLE = False
    classify_intent_enhanced = classify_intent
    # These will be defined below, but importing here for completeness
    # generate_sql_enhanced = generate_sql
    # generate_explanation_enhanced = generate_explanation

# Import optimized agents if available
try:
    from app.agents import (
        classify_intent_optimized,
        generate_sql_optimized,
        generate_explanation_optimized,
    )
except ImportError:
    # These will be set to fallbacks in app.agents.__init__.py
    pass

from app.agents.base_sql_agent import generate_sql
from app.core.config import settings
from app.core.database import get_database_url, get_engine, SAMPLE_DB_PATH
from app.schemas.response import (ExplanationType, QueryResult, QueryStatus,
                                 UserExplanation, UserResponse)
from app.schemas.sql import DatabaseInfo, SQLGenerationOutput
from app.schemas.user_query import IntentOutput, UserQuery
from app.utils.db_utils import execute_generated_sql, get_schema_info, execute_query

# Import sqlalchemy for database connection testing
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Set fallbacks for enhanced agents if not imported
if not ENHANCED_AGENT_AVAILABLE:
    from app.agents.base_sql_agent import generate_sql as generate_sql_enhanced
    from app.agents.base_explanation_agent import generate_explanation as generate_explanation_enhanced

# Set DSPY_AVAILABLE to False permanently
DSPY_AVAILABLE = False

# Setup logger
logger = logging.getLogger(__name__)

# Define lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    
    # Initialize default database connection
    initialize_default_database()
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.PROJECT_NAME}")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url="/docs",  # Make docs available at root /docs
    redoc_url="/redoc",  # Make redoc available at root /redoc
    lifespan=lifespan,
)

# Also register routes for docs at the API prefix path
app.get(f"{settings.API_PREFIX}/docs", include_in_schema=False)(app.routes[-2].endpoint)
app.get(f"{settings.API_PREFIX}/redoc", include_in_schema=False)(app.routes[-1].endpoint)

# Application state to store active database connection
app.state.active_engine = None
app.state.active_db_url = None

# Exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors and log them."""
    logger.error(f"Validation error: {exc.errors()}")
    body = await request.body()
    logger.error(f"Request body: {body.decode()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "http://localhost:5173",  # Vite dev ser,  # Your actual Vercel domain with hyphens during development (remove in production if security is a concern)
        "https://text2sql.akshaysisodia.studio"
    ],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create conversation storage (in-memory for simplicity)
# In a production app, this should be a database
conversations = {}

# Create a history store for all queries
query_history = []

# Define agent types
class AgentType(str, Enum):
    """Types of agent implementations available."""
    BASE = "base"
    ENHANCED = "enhanced"  # Enhanced agent with PydanticAI and DSPy optimization


class Text2SQLRequest(BaseModel):
    """Request for Text-to-SQL conversion."""
    
    query: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    explanation_type: ExplanationType = ExplanationType.SIMPLIFIED
    execute_query: bool = True
    use_enhanced_agent: bool = False  # Deprecated: auto-selection is now used
    database_url: Optional[str] = None  # Optional - will use active connection if not provided


class Text2SQLResponse(BaseModel):
    """Response from Text-to-SQL conversion."""
    
    user_response: UserResponse
    conversation_id: str
    timestamp: str
    enhanced_agent_used: bool = False
    optimized_agent_used: bool = False


class DatabaseConnectionRequest(BaseModel):
    """Request for database connection configuration."""
    
    db_type: Optional[str] = None
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    db_host: Optional[str] = None
    db_port: Optional[int] = None
    database_url: Optional[str] = None


class DatabaseConnectionResponse(BaseModel):
    """Response for database connection test."""
    
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class CustomSqlRequest(BaseModel):
    """Request for custom SQL execution."""
    
    sql: str
    database_url: Optional[str] = None
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None


def initialize_default_database():
    """Initialize default database connection using the sample database."""
    if os.path.exists(SAMPLE_DB_PATH):
        try:
            # Create a sample database URL
            database_url = f"sqlite:///{SAMPLE_DB_PATH}"
            
            # Create engine for the sample database
            engine = get_engine(database_url)
            
            # Test connection
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                if result.fetchone()[0] == 1:
                    # Store as the active engine
                    app.state.active_engine = engine
                    app.state.active_db_url = database_url
                    logger.info(f"Connected to sample database: {SAMPLE_DB_PATH}")
                    return True
        except Exception as e:
            logger.error(f"Failed to connect to sample database: {str(e)}")
    else:
        logger.warning(f"Sample database not found at: {SAMPLE_DB_PATH}")
    
    # If sample database connection failed, try to use default database URL
    try:
        database_url = get_database_url()
        engine = get_engine(database_url)
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            if result.fetchone()[0] == 1:
                # Store as the active engine
                app.state.active_engine = engine
                app.state.active_db_url = database_url
                logger.info(f"Connected to default database: {database_url}")
                return True
    except Exception as e:
        logger.error(f"Failed to connect to default database: {str(e)}")
    
    return False


# Helper functions
async def get_db_schema(database_url: str) -> DatabaseInfo:
    """
    Get database schema for the given database.
    
    Args:
        database_url: Database connection URL
        
    Returns:
        DatabaseInfo: Database schema information
    """
    # Create a temporary engine for this request
    engine = get_engine(database_url)
    return get_schema_info(engine=engine)


async def get_conversation_history(conversation_id: str) -> List[Dict]:
    """
    Get conversation history for the given ID.
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        List[Dict]: Conversation history
    """
    # Placeholder - in a real app, this would query a database
    if conversation_id not in conversations:
        conversations[conversation_id] = []
    return conversations[conversation_id]


async def save_conversation_history(conversation_id: str, history: List[Dict]):
    """
    Save conversation history for the given ID.
    
    Args:
        conversation_id: Conversation ID
        history: Conversation history
    """
    # Placeholder - in a real app, this would save to a database
    conversations[conversation_id] = history


@app.post(f"{settings.API_PREFIX}/process", response_model=Text2SQLResponse)
async def process_query(
    request: Text2SQLRequest,
    raw_request: Request
) -> Text2SQLResponse:
    """
    Process a natural language query and convert it to SQL.
    
    Args:
        request: Text2SQL request
        raw_request: Raw HTTP request
        
    Returns:
        Text2SQLResponse: Processed query response
    """
    start_time = time.time()
    
    try:
        # Log raw request body for debugging
        body = await raw_request.body()
        logger.info(f"Raw request body: {body.decode()}")
        logger.info(f"Request model data: {request}")
    except Exception as e:
        logger.error(f"Error reading request body: {e}")
        
    # Get or create conversation ID
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    # Get or create conversation history
    if conversation_id not in conversations:
        conversations[conversation_id] = []
    
    conversation_history = conversations[conversation_id]
    
    try:
        # Get database URL
        database_url = request.database_url
        
        # If no database URL is provided, use active connection
        if not database_url:
            if app.state.active_engine is None:
                # If no active connection, attempt to connect to sample database
                if os.path.exists(SAMPLE_DB_PATH):
                    initialize_default_database()
                    if app.state.active_engine is None:
                        raise HTTPException(
                            status_code=400,
                            detail="No active database connection and couldn't connect to sample database. Please connect using /api/v1/database/connect first."
                        )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="No active database connection. Please connect using /api/v1/database/connect first."
                    )
            
            # Use active engine for schema info
            engine = app.state.active_engine
            database_url = app.state.active_db_url
        else:
            # Create temporary engine for this request
            engine = get_engine(database_url)
        
        # Get schema information
        schema_info = get_schema_info(engine=engine)
        
        # Always try to use enhanced agent first
        use_optimized = True
        use_enhanced = True
        use_dspy = False
        
        agent_type = AgentType.ENHANCED
        
        logger.info(f"Selected agent type: {agent_type} (with automatic fallback)")
        
        # Define base and enhanced agent functions
        base_intent_classifier = classify_intent
        base_sql_generator = generate_sql
        base_explanation_generator = generate_explanation
        
        # Create user query object
        timestamp = datetime.datetime.now().isoformat()
        
        user_query = UserQuery(
            text=request.query,
            timestamp=timestamp,
            conversation_id=conversation_id,
            user_id=request.user_id,
        )
        
        # Create simplified schema for agent consumption
        tables_dict = {table.name: {
            "name": table.name,
            "description": table.description,
            "columns": {col.name: {
                "name": col.name,
                "type": col.data_type,
                "description": col.description
            } for col in table.columns}
        } for table in schema_info.tables}
        
        # Step 1: Classify query intent
        intent = None
        intent_agent_used = None
        try:
            if use_optimized:
                try:
                    logger.info("Attempting to use optimized intent agent")
                    intent = await classify_intent_optimized(
                        user_query=request.query, 
                        database_schema=tables_dict
                    )
                    intent_agent_used = "optimized"
                except Exception as e:
                    logger.warning(f"Error using optimized intent agent: {str(e)}")
                    logger.warning("Falling back to enhanced intent agent")
            
            # If optimized fails or is not used, try enhanced
            if intent is None and use_enhanced:
                try:
                    logger.info("Attempting to use enhanced intent agent")
                    intent = await classify_intent_enhanced(
                        user_query=request.query, 
                        database_schema=tables_dict,
                        use_dspy=use_dspy
                    )
                    intent_agent_used = AgentType.ENHANCED
                except Exception as e:
                    logger.warning(f"Error using enhanced intent agent: {str(e)}")
                    logger.warning("Falling back to base intent agent")
                    
            # If all fails, use base agent
            if intent is None:
                intent = await base_intent_classifier(
                    user_query=request.query, 
                    database_schema=tables_dict
                )
                intent_agent_used = AgentType.BASE
                
        except Exception as e:
            logger.error(f"Error in intent classification: {str(e)}")
            return Text2SQLResponse(
                user_response=UserResponse(
                    error=f"Failed to classify intent: {str(e)}",
                    query=request.query,  # Use the original query value
                    sql="",    # Add empty sql field to satisfy validation
                    user_query=UserQuery(text=request.query, timestamp=timestamp, conversation_id=conversation_id)
                ),
                conversation_id=conversation_id,
                timestamp=timestamp,
                enhanced_agent_used=False
            )
            
        # Verify we have a valid intent object before proceeding
        if intent is None or not hasattr(intent, 'query_type'):
            error_msg = "Invalid intent object received"
            logger.error(error_msg)
            return Text2SQLResponse(
                user_response=UserResponse(
                    error=error_msg,
                    query=request.query,
                    sql="",
                    user_query=UserQuery(text=request.query, timestamp=timestamp, conversation_id=conversation_id)
                ),
                conversation_id=conversation_id,
                timestamp=timestamp,
                enhanced_agent_used=False
            )
                
        logger.info(f"Classified intent: {intent.query_type}")
            
        # Step 2: Generate SQL
        sql_result = None
        sql_agent_used = None
        try:
            if use_optimized:
                try:
                    logger.info("Attempting to use optimized SQL agent")
                    sql_result = await generate_sql_optimized(
                        user_query=user_query,
                        intent=intent,
                        database_info=schema_info,
                        conversation_history=conversation_history
                    )
                    sql_agent_used = "optimized"
                except Exception as e:
                    logger.warning(f"Error using optimized SQL agent: {str(e)}")
                    logger.warning("Falling back to enhanced SQL agent")
            
            # If optimized fails or is not used, try enhanced
            if sql_result is None and use_enhanced:
                try:
                    logger.info("Attempting to use enhanced SQL agent")
                    sql_result = await generate_sql_enhanced(
                        user_query=user_query,
                        intent=intent,
                        database_info=schema_info,
                        conversation_history=conversation_history,
                        use_dspy=use_dspy
                    )
                    sql_agent_used = AgentType.ENHANCED
                except Exception as e:
                    logger.warning(f"Error using enhanced SQL agent: {str(e)}")
                    logger.warning("Falling back to base SQL agent")
                    
            # If all fails, use base agent
            if sql_result is None:
                sql_result = base_sql_generator(
                    user_query=user_query,
                    intent=intent,
                    database_info=schema_info,
                    conversation_history=conversation_history
                )
                sql_agent_used = AgentType.BASE
                
        except Exception as e:
            logger.error(f"Error in SQL generation: {str(e)}")
            return Text2SQLResponse(
                user_response=UserResponse(
                    error=f"Failed to generate SQL: {str(e)}",
                    query=request.query,  # Use the original query value
                    sql="",    # Add empty sql field to satisfy validation
                    user_query=UserQuery(text=request.query, timestamp=timestamp, conversation_id=conversation_id)
                ),
                conversation_id=conversation_id,
                timestamp=timestamp,
                enhanced_agent_used=(sql_agent_used == AgentType.ENHANCED),
                optimized_agent_used=(sql_agent_used == "optimized")
            )
            
        logger.info(f"Generated SQL: {sql_result.sql}")
            
        # Step 3: Execute SQL if requested
        query_result = None
        if request.execute_query and sql_result and sql_result.sql:
            try:
                query_result = execute_generated_sql(sql_result.sql, engine=engine)
                logger.info(f"Query executed: {query_result.status}")
            except Exception as e:
                logger.error(f"Error executing SQL: {str(e)}")
                query_result = QueryResult(
                    status=QueryStatus.ERROR,
                    error_message=f"Failed to execute query: {str(e)}"
                )
            
        # Step 4: Generate explanation
        explanation = None
        explanation_agent_used = None
        
        try:
            if use_optimized:
                try:
                    logger.info("Attempting to use optimized explanation agent")
                    explanation = await generate_explanation_optimized(
                        user_query=user_query,
                        sql_generation=sql_result,
                        query_result=query_result,
                        explanation_type=request.explanation_type,
                        database_info=schema_info
                    )
                    explanation_agent_used = "optimized"
                except Exception as e:
                    logger.warning(f"Error using optimized explanation agent: {str(e)}")
                    logger.warning("Falling back to enhanced explanation agent")
            
            # If optimized fails or is not used, try enhanced
            if explanation is None and use_enhanced:
                try:
                    logger.info("Attempting to use enhanced explanation agent")
                    explanation = await generate_explanation_enhanced(
                        user_query=user_query,
                        sql_generation=sql_result,
                        query_result=query_result,
                        explanation_type=request.explanation_type,
                        use_dspy=use_dspy
                    )
                    explanation_agent_used = AgentType.ENHANCED
                except Exception as e:
                    logger.warning(f"Error using enhanced explanation agent: {str(e)}")
                    logger.warning("Falling back to base explanation agent")
                    
            # If all fails, use base agent
            if explanation is None:
                explanation = await generate_explanation(
                    user_query=user_query,
                    sql_generation=sql_result,
                    query_result=query_result,
                    explanation_type=request.explanation_type
                )
                explanation_agent_used = AgentType.BASE
                
        except Exception as e:
            logger.error(f"Error in explanation generation: {str(e)}")
            explanation = UserExplanation(
                explanation_type=request.explanation_type,
                text=f"Failed to generate explanation due to an error: {str(e)}"
            )
            explanation_agent_used = None
            
        # Create user response
        user_response = UserResponse(
            user_query=user_query,
            intent=intent.dict() if intent else None,
            sql_generation=sql_result,
            query_result=query_result,
            explanation=explanation,
            conversation_id=conversation_id,
            timestamp=timestamp
        )
        
        # Add to conversation history
        conversation_history.append({
            "timestamp": timestamp,
            "user_query": request.query,
            "generated_sql": sql_result.sql if sql_result else "",
            "query_result": query_result.dict() if query_result else None,
            "explanation": explanation.dict(),
        })
        
        # Calculate processing time
        processing_time = time.time() - start_time
        logger.info(f"Total processing time: {processing_time:.2f} seconds")
        
        # Save updated conversation history
        conversations[conversation_id] = conversation_history
        
        # Add to global query history
        history_item = {
            "id": str(uuid.uuid4()),
            "query": request.query,
            "sql": sql_result.sql if sql_result else None,
            "timestamp": datetime.datetime.now().isoformat(),
            "conversation_id": conversation_id
        }
        query_history.append(history_item)
        
        return Text2SQLResponse(
            user_response=user_response,
            conversation_id=conversation_id,
            timestamp=timestamp,
            enhanced_agent_used=(sql_agent_used == AgentType.ENHANCED),
            optimized_agent_used=(sql_agent_used == "optimized")
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in query processing: {str(e)}", exc_info=True)
        return Text2SQLResponse(
            user_response=UserResponse(
                error=f"An unexpected error occurred: {str(e)}",
                query=request.query,  # Use the original query value
                sql="",    # Add empty sql field to satisfy validation
                user_query=UserQuery(text=request.query, timestamp=timestamp, conversation_id=conversation_id)
            ),
            conversation_id=conversation_id,
            timestamp=datetime.datetime.now().isoformat(),
            enhanced_agent_used=False
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
async def get_database_schema(database_url: Optional[str] = None) -> DatabaseInfo:
    """
    Get database schema information.
    
    Args:
        database_url: Optional database URL. If not provided, uses active connection.
        
    Returns:
        DatabaseInfo: Database schema
    """
    if database_url:
        # Use provided URL
        engine = get_engine(database_url)
    else:
        # Use active connection
        engine = get_active_engine()
        if engine is None:
            raise HTTPException(
                status_code=400,
                detail="No active database connection. Please connect using /api/v1/database/connect first."
            )
    
    return get_schema_info(engine=engine)


@app.get(f"{settings.API_PREFIX}/database/config")
async def get_database_config() -> Dict[str, Any]:
    """
    Get current database configuration.
    
    Returns:
        Dict: Database configuration
    """
    return {
        "message": "Direct database URL configuration is required for all API requests",
        "connection_example": "postgresql://username:password@host:port/database"
    }


@app.post(f"{settings.API_PREFIX}/database/connect", response_model=DatabaseConnectionResponse)
async def connect_database(request: DatabaseConnectionRequest) -> DatabaseConnectionResponse:
    """
    Connect to a database and store the connection in application state.
    
    Args:
        request: Database connection request
        
    Returns:
        DatabaseConnectionResponse: Connection result
    """
    try:
        # Check if we should use the sample database
        use_sample_db = (
            not request.database_url and 
            (not request.db_type or request.db_type.lower() == "sqlite") and
            (not request.db_name or request.db_name == "sample" or request.db_name == "sample_huge") and
            os.path.exists(SAMPLE_DB_PATH)
        )
        
        if use_sample_db:
            # Use the sample database
            database_url = f"sqlite:///{SAMPLE_DB_PATH}"
            logger.info("Using sample database")
        elif request.database_url:
            # Use the explicitly provided database URL
            database_url = request.database_url
        elif any([request.db_type, request.db_name, request.db_user, request.db_password, request.db_host, request.db_port]):
            # Construct URL from connection parameters
            database_url = get_database_url(
                db_type=request.db_type,
                db_name=request.db_name,
                db_user=request.db_user,
                db_password=request.db_password,
                db_host=request.db_host,
                db_port=request.db_port
            )
        else:
            # No connection details provided
            return DatabaseConnectionResponse(
                success=False,
                message="Database connection details are required. Please provide either a database_url or connection parameters.",
            )
            
        # Create engine
        engine = get_engine(database_url)
        
        # Test connection by executing a simple query
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            row = result.fetchone()
            if row[0] == 1:
                # Extract schema information
                schema_info = get_schema_info(engine=engine)
                
                # Store the connection in application state
                app.state.active_engine = engine
                app.state.active_db_url = database_url
                
                # Special message for sample database
                message = "Connection successful and stored for future requests"
                if use_sample_db:
                    message = "Connected to sample database successfully"
                
                # Return success response
                return DatabaseConnectionResponse(
                    success=True,
                    message=message,
                    details={
                        "table_count": len(schema_info.tables),
                        "tables": [table.name for table in schema_info.tables],
                        "dialect": engine.dialect.name,
                        "is_sample_db": use_sample_db
                    },
                )
            else:
                # Return failure response
                return DatabaseConnectionResponse(
                    success=False,
                    message="Connection test failed: unexpected result",
                )
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return DatabaseConnectionResponse(
            success=False,
            message=f"Database connection failed: {str(e)}",
        )


class AgentInfoResponse(BaseModel):
    """Response for agent information."""
    
    enhanced_available: bool
    current_agent_type: str
    message: str


@app.get(f"{settings.API_PREFIX}/agent/info", response_model=AgentInfoResponse)
async def get_agent_info() -> AgentInfoResponse:
    """
    Get information about the available agents.
    
    Returns:
        AgentInfoResponse: Information about agent availability
    """
    # Always use enhanced agent when available, with fallback to base
    current_type = "enhanced" if ENHANCED_AGENT_AVAILABLE else "base"
    
    if ENHANCED_AGENT_AVAILABLE:
        message = "Enhanced agent is used with automatic fallback to base agent if needed"
    else:
        message = "Only base agent is available"
    
    return AgentInfoResponse(
        enhanced_available=ENHANCED_AGENT_AVAILABLE,
        current_agent_type=current_type,
        message=message
    )


@app.get(f"{settings.API_PREFIX}/query", response_model=UserResponse)
async def process_query(
    request: Request,
    query: str,
    database_url: Optional[str] = None,
    explanation_type: ExplanationType = ExplanationType.SIMPLIFIED,
    conversation_id: Optional[str] = None
):
    """
    Process a natural language query and convert it to SQL (GET endpoint).
    
    Args:
        request: FastAPI request object
        query: Natural language query
        database_url: Optional database URL. If not provided, uses active connection.
        explanation_type: Type of explanation to generate
        conversation_id: Conversation ID for context
        
    Returns:
        UserResponse: Response with SQL and explanation
    """
    # Create conversation ID if not provided
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        
    # Convert to the Text2SQLRequest format
    text2sql_request = Text2SQLRequest(
        query=query,
        conversation_id=conversation_id,
        explanation_type=explanation_type,
        database_url=database_url
    )
    
    # Process using the main handler
    response = await process_query(text2sql_request, request)
    
    # Add to global query history if not already added by the main handler
    history_item = {
        "id": str(uuid.uuid4()),
        "query": query,
        "sql": response.user_response.sql_generation.sql if response.user_response.sql_generation else None,
        "timestamp": datetime.datetime.now().isoformat(),
        "conversation_id": conversation_id
    }
    query_history.append(history_item)
    
    # Return just the user response part
    return response.user_response


@app.post(f"{settings.API_PREFIX}/execute-custom-sql", response_model=QueryResult)
async def execute_custom_sql(request: CustomSqlRequest) -> QueryResult:
    """
    Execute a custom SQL query provided by the user.
    
    Args:
        request: Custom SQL request
        
    Returns:
        QueryResult: Results of the query execution
    """
    try:
        logger.info(f"Executing custom SQL query: {request.sql}")
        
        # Basic security check
        dangerous_operations = ["DROP", "TRUNCATE", "DELETE FROM", "ALTER TABLE"]
        if any(op in request.sql.upper() for op in dangerous_operations):
            return QueryResult(
                status=QueryStatus.ERROR,
                error_message="Potentially harmful operation detected. Query execution aborted.",
                warnings=["This query contains potentially harmful operations that could delete or modify data structure."]
            )
        
        # Create engine for this request
        if request.database_url:
            engine = get_engine(request.database_url)
        else:
            # Use active connection
            engine = get_active_engine()
            if engine is None:
                return QueryResult(
                    status=QueryStatus.ERROR,
                    error_message="No active database connection. Please connect using /api/v1/database/connect first or provide database_url.",
                    warnings=["Database connection is required to execute SQL."]
                )
        
        # Start time tracking
        start_time = time.time()
        
        # Execute the query
        result = execute_query(request.sql, engine=engine)
        
        # Add execution time
        result.execution_time = round(time.time() - start_time, 3)
        
        # If a conversation ID is provided, add the custom SQL execution to the history
        if request.conversation_id and request.conversation_id in conversations:
            conversations[request.conversation_id].append({
                "timestamp": datetime.datetime.now().isoformat(),
                "user_query": "User modified and executed custom SQL query",
                "generated_sql": request.sql,
                "query_result": result.dict() if result else None,
                "is_custom_sql": True,
            })
            
        # Add to global query history
        history_item = {
            "id": str(uuid.uuid4()),
            "query": "User modified and executed custom SQL query",
            "sql": request.sql,
            "timestamp": datetime.datetime.now().isoformat(),
            "conversation_id": request.conversation_id
        }
        query_history.append(history_item)
        
        return result
        
    except Exception as e:
        logger.error(f"Error executing custom SQL: {str(e)}", exc_info=True)
        return QueryResult(
            status=QueryStatus.ERROR,
            error_message=f"Error executing custom SQL: {str(e)}",
            warnings=["An error occurred during execution."]
        )


def get_active_engine():
    """
    Get the active database engine from application state.
    
    Returns:
        Engine: SQLAlchemy engine or None if not connected
    """
    return app.state.active_engine


@app.get(f"{settings.API_PREFIX}/database/status")
async def get_database_status() -> Dict[str, Any]:
    """
    Get current database connection status.
    
    Returns:
        Dict: Database connection status
    """
    if app.state.active_engine is None:
        return {
            "connected": False,
            "message": "No active database connection. Please connect using /api/v1/database/connect endpoint."
        }
    
    # Check if connection is still active
    try:
        with app.state.active_engine.connect() as connection:
            connection.execute(text("SELECT 1")).fetchone()
            
        # Check if this is the sample database
        is_sample_db = app.state.active_db_url and "sample_huge.db" in app.state.active_db_url
            
        return {
            "connected": True,
            "dialect": app.state.active_engine.dialect.name,
            "database_url_hash": hash(app.state.active_db_url),  # For security, don't return the actual URL
            "is_sample_db": is_sample_db,
            "message": "Database connection is active"
        }
    except Exception as e:
        app.state.active_engine = None
        app.state.active_db_url = None
        return {
            "connected": False,
            "message": f"Database connection was lost: {str(e)}"
        } 


@app.get(f"{settings.API_PREFIX}/history", response_model=List[Dict])
async def get_history() -> List[Dict]:
    """
    Get all query history.
    
    Returns:
        List[Dict]: All query history across conversations
    """
    return query_history


@app.delete(f"{settings.API_PREFIX}/history/{{history_id}}")
async def delete_history_item(history_id: str):
    """
    Delete a history item.
    
    Args:
        history_id: History item ID to delete
        
    Returns:
        Dict: Success message
    """
    global query_history
    
    # Find item with matching ID
    for idx, item in enumerate(query_history):
        if item.get("id") == history_id:
            # Remove the item
            deleted_item = query_history.pop(idx)
            return {"success": True, "message": "History item deleted", "id": history_id}
    
    # If we get here, item wasn't found
    raise HTTPException(
        status_code=404,
        detail=f"History item with ID {history_id} not found"
    ) 
