"""
Database queries module.

This module provides backward compatibility by re-exporting all query functions
from the specialized submodules.
"""

# Session queries
from .session_queries import (
    create_session,
    get_session,
    delete_session,
    get_user_sessions,
    check_user_exists,
)

# Message queries
from .message_queries import (
    add_message,
    get_session_messages,
    delete_message,
    delete_session_messages,
)

# Document queries
from .document_queries import (
    get_document,
    list_documents,
    delete_document,
    delete_all_documents,
    get_document_chunks,
)

# Search queries
from .search_queries import (
    vector_search,
    hybrid_search,
)

# Connection pool
from ..connection import db_pool

# Dataclass for RAG context
from dataclasses import dataclass
from asyncpg.pool import Pool


@dataclass
class RAGContext:
    """Context for the RAG MCP server with database connection."""

    db_pool: Pool


__all__ = [
    # Session queries
    "create_session",
    "get_session",
    "delete_session",
    "get_user_sessions",
    "check_user_exists",
    # Message queries
    "add_message",
    "get_session_messages",
    "delete_message",
    "delete_session_messages",
    # Document queries
    "get_document",
    "list_documents",
    "delete_document",
    "delete_all_documents",
    "get_document_chunks",
    # Search queries
    "vector_search",
    "hybrid_search",
    # Connection
    "db_pool",
    "RAGContext",
]
