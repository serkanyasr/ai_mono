"""Main FastAPI application.

This file has been refactored to use modular endpoint structure.
All endpoint logic has been moved to src/api/v1/endpoints/
"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn

# Orchestrator and agent service
from src.agents.orchestrator import create_agent_orchestrator
from src.config.settings import settings

# Database
from src.database.rag import (
    initialize_database,
    close_database,
    test_db_connection as rag_db_conn_test,
)
from src.database.memory.connection import test_db_connection as memory_db_conn_test
# Redis
from src.cache.redis_provider import RedisConnectionManager

# Schemas
from .schemas import ErrorResponse

# Logging
from src.utils import get_logger, setup_logging

# API v1 router
from .v1.router import router as v1_router

# Middleware
from .v1.middleware.correlation import CorrelationIDMiddleware
from .v1.middleware.logging_middleware import LoggingMiddleware
from .v1.middleware.rate_limit import limiter, RateLimiter, RateLimits, custom_rate_limit_exceeded_handler
from .v1.middleware.error_handlers import (
    app_exception_handler,
    http_exception_handler,
    general_exception_handler,
)
from src.exception import BaseAppException

# Configure slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# =====================
# Initialize Services
# =====================

orchestrator = create_agent_orchestrator()
agent_service = orchestrator.get_agent_service()

# =====================
# API Configuration
# =====================

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

# =====================
# Lifespan Context Manager
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting up system...")

    try:
        # Store agent service in app state
        app.state.agent_service = agent_service

        # Initialize agent cache
        from src.cache.agent_cache import get_agent_cache
        app.state.agent_cache = get_agent_cache(
            max_size=settings.agent_cache_max_size,
            ttl_seconds=settings.agent_cache_ttl_seconds
        )
        await app.state.agent_cache.start_cleanup_task()
        logger.info("Agent cache initialized")

        # Initialize RAG database connections
        await initialize_database()

        # Initialize Redis connection
        try:
            await RedisConnectionManager.initialize()
            logger.info("Redis initialized", redis_url=settings.redis_url)

            # Update rate limiter to use Redis storage
            from src.api.v1.middleware.rate_limit import limiter

            # Create new limiter with Redis storage
            redis_limiter = Limiter(
                key_func=get_remote_address,
                storage_uri=settings.redis_url
            )
            # Update app state limiter
            app.state.limiter = redis_limiter
            logger.info("Rate limiting configured with Redis storage")
        except Exception as redis_err:
            logger.warning(f"Redis initialization failed: {redis_err}")
            logger.info("Rate limiting using in-memory storage")

        # Initialize MCP Servers
        servers_ok = await orchestrator.load_servers()
        if servers_ok:
            logger.info("MCP Server loaded")
            logger.info(orchestrator.servers)
        else:
            logger.info("MCP server was not loaded")

        # Test database connections
        rag_db_ok = await rag_db_conn_test()
        memory_db_ok = await memory_db_conn_test()

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
            await app.state.agent_cache.stop_cleanup_task()
            logger.info("Agent cache stopped")

        await close_database()
        logger.info("Database connections closed")
        
        # Close Redis connection
        await RedisConnectionManager.close()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

# =====================
# Create FastAPI App
# =====================

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
)

# =====================
# Middleware
# =====================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Correlation ID middleware (must be before logging)
app.add_middleware(CorrelationIDMiddleware)

# Request logging middleware (skip health checks)
app.add_middleware(
    LoggingMiddleware,
    log_query_params=True,
    skip_paths=["/health", "/api/v1/health"]
)

# =====================
# Rate Limiting
# =====================

# Set up rate limiting with slowapi
app.state.limiter = limiter

# Custom rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)

# =====================
# Include Routers
# =====================

# Include v1 API router
app.include_router(v1_router, prefix="/api/v1")

# =====================
# Exception Handlers
# =====================

# Application-specific exceptions
app.add_exception_handler(BaseAppException, app_exception_handler)

# HTTP exceptions
app.add_exception_handler(HTTPException, http_exception_handler)

# General/unhandled exceptions
app.add_exception_handler(Exception, general_exception_handler)

# =====================
# Run the App
# =====================

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=API_ENV == "development",
        log_level=API_LOG_LEVEL.lower(),
    )
