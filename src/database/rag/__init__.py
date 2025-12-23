from .connection import (
    db_pool,
    initialize_database,
    close_database,
    test_db_connection
)

from .queries import (
    add_message,
    get_session_messages,
    delete_message,
    delete_session_messages,
    get_document,
    list_documents,
    delete_document,
    delete_all_documents,
    vector_search,
    hybrid_search,
    get_document_chunks,
    create_session,
    get_session,
    delete_session,
    get_user_sessions,
    check_user_exists,
    
    
)

__all__ = [
    # connection
    "db_pool",
    "initialize_database",
    "close_database",
    "test_db_connection",
    
    #Message management
    "add_message",
    "get_session_messages",
    "delete_message",
    "delete_session_messages",
    
    # queries
    "get_document",
    "list_documents",
    "delete_document",
    "delete_all_documents",
    "vector_search",
    "hybrid_search",
    "get_document_chunks",
    
    #session
    "create_session",
    "get_session",
    "delete_session",
    "get_user_sessions",
    "check_user_exists"
    
]
