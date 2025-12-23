
from typing import Optional, Dict, Any, List


from  src.database.rag import (
    create_session as db_create_session,
    get_session as db_get_session,
    delete_session as db_delete_session,
    get_user_sessions as db_get_user_sessions,
    check_user_exists as db_check_user_exists,
    db_pool,
)










class SessionRepository:
    """Session repository using existing memory_db functions."""
    
    async def create(self, user_id: Optional[str], metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create new session."""
        return await db_create_session(user_id=user_id, metadata=metadata)

    async def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        return await db_get_session(session_id)
    
    async def delete(self, session_id: str) -> None:
        """Delete session."""
        await db_delete_session(session_id)
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user."""
        return await db_get_user_sessions(user_id)
    
    async def check_user_exists(self, user_id: str) -> bool:
        """Check if user has any sessions."""
        return await db_check_user_exists(user_id)
