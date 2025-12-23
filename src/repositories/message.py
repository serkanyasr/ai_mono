from typing import Optional, Dict, Any, List


from  src.database.rag import (

    add_message as db_add_message,
    get_session_messages as db_get_session_messages,
    delete_message as db_delete_message,
)











class MessageRepository:
    async def add(self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add message to session."""
        return await db_add_message(session_id=session_id, role=role, content=content, metadata=metadata or {})

    async def list(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List messages in a session."""
        return await db_get_session_messages(session_id, limit=limit)

    async def delete(self, session_id: str) -> None:
        """Delete all messages in a session."""
        await db_delete_message(session_id)
        