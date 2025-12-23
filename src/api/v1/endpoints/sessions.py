"""Session management endpoints."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from src.utils import get_logger

from src.api.schemas import SessionListResponse, SessionInfo, MessageHistoryResponse, MessageInfo
from src.repositories import SessionRepository, MessageRepository

router = APIRouter()
logger = get_logger(__name__)


@router.get("/users/{user_id}/sessions", response_model=SessionListResponse)
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


@router.post("/users/{user_id}/sessions")
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


@router.delete("/sessions/{session_id}")
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


@router.get("/users/{user_id}/exists")
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


@router.get("/sessions/{session_id}/messages", response_model=MessageHistoryResponse)
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
            )  # type: ignore
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
