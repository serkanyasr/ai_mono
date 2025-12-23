import json
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException, Header, Request,UploadFile,File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn



# from src.ingestion.extractor import PDFExtractionConfig
# from src.ingestion.pipeline import IngestionConfig
from src.repositories import SessionRepository,MessageRepository,DocumentRepository
from src.retrieval.service import RetrievalService
from src.chat.stream import StreamChat, StreamChatDeps
from src.agents.orchestrator import create_agent_orchestrator
from src.config.settings import settings


from src.database.rag import (
    initialize_database,
    close_database,
    test_db_connection as rag_db_conn_test,
)
from src.database.memory.connection import test_db_connection as memory_db_conn_test



from .schemas import (
    ChatRequest,
    ErrorResponse,
    HealthStatus,
    MessageHistoryResponse,
    MessageInfo,
    SessionInfo,
    SessionListResponse
    )


from src.chat.stream import StreamChat, StreamChatDeps

from src.utils import get_logger,setup_logging

# from src.ingestion.use_case import UploadDocumentsUseCase, UploadDeps
# from src.ingestion.service import IngestionService




orchestrator = create_agent_orchestrator()


# Initialize global services
agent_service = orchestrator.get_agent_service()



# API configuration
API_ENV = settings.api.api_env
API_HOST = settings.api.api_host
API_PORT = settings.api.api_port
API_LOG_LEVEL = settings.api.api_log_level


setup_logging(
    level=API_LOG_LEVEL,
    log_file="logs/api.log" if API_ENV != "development" else None
)

logger = get_logger(__name__)

logger.info("Logging initialized")


#* =====================
#* API Config
#* =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager with cache management"""
    # Startup
    logger.info("Starting up system...")

    try:
        # Initialize  cache Agent 
        from src.cache.agent_cache import get_agent_cache
        app.state.agent_cache = get_agent_cache(
            max_size=settings.agent_cache_max_size,
            ttl_seconds=settings.agent_cache_ttl_seconds
        )
        await app.state.agent_cache.start_cleanup_task()
        logger.info("Agent cache initialized")

        # Initialize RAG database connections
        await initialize_database()
        # Init MCP Servers
        servers_ok = await orchestrator.load_servers()

        if servers_ok:
            logger.info("MCP Server loaded")
            logger.info(orchestrator.servers)
        else:
            logger.info("MCP server was not loaded")

        # Test connections
        rag_db_ok = await rag_db_conn_test()
        memory_db_ok = memory_db_conn_test()

        if not rag_db_ok:
            logger.error("RAG Database connection failed")
        else:
            logger.info("RAG Database initialized")
            
        if not memory_db_ok:
            logger.error("MEMORY Database connection failed")
        else:
            logger.info("MEMORY Database initialized")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down system...")

    try:
        # Stop cache cleanup task
        if hasattr(app.state, 'agent_cache'):
            await app.state.agent_cache.stop_cleanup_task() # type: ignore
            logger.info("Agent cache stopped")
        
        await close_database()
        logger.info("Connections closed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


#* =====================
#* Create FastAPI app
#* =====================

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
)


#* =====================
#* Middleware with flexible CORS
#* =====================

app.add_middleware(
    CORSMiddleware,
    allow_origins= "*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)



#* =====================
#* API HEALTH
#* =====================

@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connections
        rag_db_test = await rag_db_conn_test()
        memory_db_test = memory_db_conn_test()
        # Determine overall status
        if rag_db_test:
            rag_db_status = "healthy"
        else:
            rag_db_status = "unhealthy"

        if memory_db_test:
            memory_db_status = "healthy"
        else:
            memory_db_status = "unhealthy"

        return HealthStatus(
            rag_db_status=rag_db_status,
            memory_db_status=memory_db_status,
            llm_connection=True,
            version=settings.app_version,
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")



#* =====================
#* API Endpoints
#* =====================

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint using Server-Sent Events."""
    try:
        request_id = str(uuid.uuid4())
        logger.info(f"/chat/stream request_id={request_id} user_id={request.user_id}")
        sessions_repo = SessionRepository()
        messages_repo = MessageRepository()

        chat = StreamChat(
            deps=StreamChatDeps(
                sessions=sessions_repo,
                messages=messages_repo,
                agent_service=agent_service,
            ),
            cache=app.state.agent_cache if hasattr(app.state, 'agent_cache') else None
        )

        async def generate_stream():
            try:
                yield f"data: {json.dumps({'type': 'request', 'request_id': request_id})}\n\n"
                async for item in chat.stream(
                    message=request.message,
                    session_id=request.session_id,
                    user_id=request.user_id,
                    metadata=request.metadata or {},
                ):
                    yield f"data: {json.dumps(item)}\n\n"
            except Exception as e:
                logger.error(f"Stream error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            },
        )

    except Exception as e:
        logger.error(f"Streaming chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/users/{user_id}/sessions", response_model=SessionListResponse)
async def get_user_sessions(user_id: str):
    """Get all sessions for a user."""
    try:
        sessions_repo = SessionRepository()
        
        # Get all sessions for user using your existing function
        sessions = await sessions_repo.get_user_sessions(user_id)
        
        session_list = [
            SessionInfo(
                session_id=s["session_id"],
                user_id=s["user_id"],
                created_at=s["created_at"],
                updated_at=s["updated_at"],
                message_count=s.get("message_count", 0),
                last_message=s.get("last_message", "")[:100] if s.get("last_message") else None
            )
            for s in sessions
        ]
        
        return SessionListResponse(
            sessions=session_list,
            total=len(session_list)
        )
    
    except Exception as e:
        logger.error(f"Failed to get user sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/users/{user_id}/sessions")
async def create_new_session(user_id: str):
    """Create a new session for user."""
    try:
        sessions_repo = SessionRepository()
        
        # Create session using your existing function
        session_id = await sessions_repo.create(
            user_id=user_id,
            metadata={}
        )
        
        return {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and all its messages."""
    try:
        sessions_repo = SessionRepository()
        messages_repo = MessageRepository()
        
        # First delete all messages in the session
        await messages_repo.delete(session_id)
        
        # Delete session 
        await sessions_repo.delete(session_id)
        
        return {"success": True, "message": "Session deleted"}
    
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/exists")
async def check_user_exists(user_id: str):
    """Check if user has any sessions."""
    try:
        sessions_repo = SessionRepository()
        
        # Check if user exists using your new function
        exists = await sessions_repo.check_user_exists(user_id)
        
        # Get session count
        if exists:
            sessions = await sessions_repo.get_user_sessions(user_id)
            session_count = len(sessions)
        else:
            session_count = 0
        
        return {
            "exists": exists,
            "user_id": user_id,
            "session_count": session_count
        }
    
    except Exception as e:
        logger.error(f"Failed to check user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/messages", response_model=MessageHistoryResponse)
async def get_session_messages(session_id: str, limit: Optional[int] = None):
    """Get all messages for a session."""
    try:
        messages_repo = MessageRepository()
        
        # Get messages using your existing function
        messages = await messages_repo.list(session_id, limit=limit)
        
        message_list = [
            MessageInfo(
                message_id=m["id"],
                session_id=m["session_id"],
                role=m["role"],
                content=m["content"],
                created_at=m["created_at"],
                metadata=m.get("metadata", {})
            ) # type: ignore
            for m in messages
        ]
        
        return MessageHistoryResponse(
            messages=message_list,
            session_id=session_id,
            total=len(message_list)
        )
    
    except Exception as e:
        logger.error(f"Failed to get session messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cache/stats")
async def get_cache_stats():
    """Get agent cache statistics"""
    try:
        if not hasattr(app.state, 'agent_cache'):
            return {"error": "Agent cache not initialized"}
        
        cache_stats = app.state.agent_cache.get_stats()
        return cache_stats
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cache/clear")
async def clear_cache():
    """Clear all cached agents"""
    try:
        if not hasattr(app.state, 'agent_cache'):
            return {"error": "Agent cache not initialized"}
        
        app.state.agent_cache.clear()
        return {"success": True, "message": "Cache cleared"}
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))





#* =====================
#* Exception handlers
#* =====================

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")

    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=str(exc),
            error_type=type(exc).__name__,
            request_id=str(uuid.uuid4()),
        ).model_dump(),
    )
    
    
#* =====================
#* Run the app with Uvicorn
#* =====================

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=API_ENV == "development",
        log_level=API_LOG_LEVEL.lower(),
    )

