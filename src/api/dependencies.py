"""Dependency injection container for FastAPI dependencies.

This module provides dependency injection functions for FastAPI endpoints,
enabling loose coupling and easier testing.
"""

from functools import lru_cache
from typing import AsyncGenerator

from fastapi import Depends

from src.repositories import SessionRepository, MessageRepository, DocumentRepository
from src.services.session_service import SessionService
from src.services.chat_service import ChatService


# =====================
# Singleton Instances
# =====================

@lru_cache()
def get_agent_orchestrator():
    """Get or create agent orchestrator singleton."""
    from src.agents.orchestrator import create_agent_orchestrator
    return create_agent_orchestrator()


@lru_cache()
def get_agent_service():
    """Get or create agent service singleton."""
    orchestrator = get_agent_orchestrator()
    return orchestrator.get_agent_service()


@lru_cache()
def get_agent_cache():
    """Get or create agent cache singleton."""
    from src.cache.agent_cache import get_agent_cache
    from src.config.settings import settings
    return get_agent_cache(
        max_size=settings.agent_cache_max_size,
        ttl_seconds=settings.agent_cache_ttl_seconds
    )


# =====================
# Repository Dependencies
# =====================

async def get_session_repository() -> AsyncGenerator[SessionRepository, None]:
    """Session repository dependency.

    Yields:
        SessionRepository instance
    """
    yield SessionRepository()


async def get_message_repository() -> AsyncGenerator[MessageRepository, None]:
    """Message repository dependency.

    Yields:
        MessageRepository instance
    """
    yield MessageRepository()


async def get_document_repository() -> AsyncGenerator[DocumentRepository, None]:
    """Document repository dependency.

    Yields:
        DocumentRepository instance
    """
    yield DocumentRepository()


# =====================
# Service Dependencies
# =====================

async def get_session_service(
    session_repo: SessionRepository = Depends(get_session_repository)
) -> AsyncGenerator[SessionService, None]:
    """Session service dependency.

    Args:
        session_repo: Session repository instance

    Yields:
        SessionService instance
    """
    yield SessionService(session_repository=session_repo)


async def get_chat_service(
    session_repo: SessionRepository = Depends(get_session_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
    agent_service = Depends(get_agent_service),
    agent_cache = Depends(get_agent_cache)
) -> AsyncGenerator[ChatService, None]:
    """Chat service dependency.

    Args:
        session_repo: Session repository instance
        message_repo: Message repository instance
        agent_service: Agent service instance
        agent_cache: Agent cache instance

    Yields:
        ChatService instance
    """
    yield ChatService(
        session_repository=session_repo,
        message_repository=message_repo,
        agent_service=agent_service,
        cache=agent_cache
    )


# =====================
# Application State Setup
# =====================

async def setup_app_state(app):
    """Setup application state and dependencies.

    Args:
        app: FastAPI application instance
    """
    from src.database.rag import initialize_database
    from src.database.memory.connection import test_db_connection as memory_db_conn_test
    from src.database.rag import test_db_connection as rag_db_conn_test

    # Store agent service in app state
    app.state.agent_service = get_agent_service()

    # Initialize agent cache
    cache = get_agent_cache()
    app.state.agent_cache = cache
    await cache.start_cleanup_task()

    # Initialize RAG database
    await initialize_database()

    # Test database connections
    rag_db_ok = await rag_db_conn_test()
    memory_db_ok = await memory_db_conn_test()

    if not rag_db_ok:
        app.state.logger.error("RAG Database connection failed")
    else:
        app.state.logger.info("RAG Database initialized")

    if not memory_db_ok:
        app.state.logger.error("MEMORY Database connection failed")
    else:
        app.state.logger.info("MEMORY Database initialized")

    # Initialize MCP servers
    orchestrator = get_agent_orchestrator()
    servers_ok = await orchestrator.load_servers()
    if servers_ok:
        app.state.logger.info("MCP Server loaded")
    else:
        app.state.logger.info("MCP server was not loaded")


async def teardown_app_state(app):
    """Cleanup application state.

    Args:
        app: FastAPI application instance
    """
    from src.database.rag import close_database

    # Stop cache cleanup task
    if hasattr(app.state, 'agent_cache'):
        await app.state.agent_cache.stop_cleanup_task()
        app.state.logger.info("Agent cache stopped")

    # Close database connections
    await close_database()
    app.state.logger.info("Connections closed")
