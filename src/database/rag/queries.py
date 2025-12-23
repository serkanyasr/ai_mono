"""
DEPRECATED: This module has been restructured.

This file now serves as a backward compatibility wrapper.
Please import from the specialized submodules:
- src.database.rag.queries.session_queries
- src.database.rag.queries.message_queries
- src.database.rag.queries.document_queries
- src.database.rag.queries.search_queries

Or import from src.database.rag.queries (the __init__.py package)
"""

import warnings
from typing import List, Dict, Any, Optional
from asyncpg.pool import Pool
from dataclasses import dataclass

# Import all functions from the new modular structure
from .queries import (
    # Session queries
    create_session,
    get_session,
    delete_session,
    get_user_sessions,
    check_user_exists,
    # Message queries
    add_message,
    get_session_messages,
    delete_message,
    delete_session_messages,
    # Document queries
    get_document,
    list_documents,
    delete_document,
    delete_all_documents,
    get_document_chunks,
    # Search queries
    vector_search,
    hybrid_search,
    # Connection
    db_pool,
    RAGContext,
)

# Show deprecation warning when imported directly
warnings.warn(
    "Direct import from src.database.rag.queries.py is deprecated. "
    "Use 'from src.database.rag.queries import ...' instead.",
    DeprecationWarning,
    stacklevel=2
)

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
