"""Session service for session management business logic."""

from datetime import datetime
from typing import Dict, Any, List, Optional

from .base_service import BaseService
from src.core.interfaces.repositories import ISessionRepository


class SessionService(BaseService):
    """Service for session management operations.

    This service provides business logic for session management,
    including CRUD operations and validation.
    """

    def __init__(self, session_repository: ISessionRepository):
        """Initialize session service.

        Args:
            session_repository: Session repository instance
        """
        super().__init__()
        self._session_repo = session_repository

    async def create_session(
        self,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new session.

        Args:
            user_id: User identifier
            metadata: Optional session metadata

        Returns:
            Dictionary with session_id, user_id, and created_at

        Raises:
            Exception: If session creation fails
        """
        try:
            session_id = await self._session_repo.create(
                user_id=user_id,
                metadata=metadata or {}
            )

            return {
                "session_id": session_id,
                "user_id": user_id,
                "created_at": datetime.now().isoformat()
            }
        except Exception as e:
            await self._handle_error(e, {"operation": "create_session", "user_id": user_id})

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID.

        Args:
            session_id: Session UUID

        Returns:
            Session data or None if not found
        """
        try:
            return await self._session_repo.get(session_id)
        except Exception as e:
            await self._handle_error(e, {"operation": "get_session", "session_id": session_id})

    async def delete_session(self, session_id: str) -> None:
        """Delete a session.

        Args:
            session_id: Session UUID

        Raises:
            Exception: If deletion fails
        """
        try:
            await self._session_repo.delete(session_id)
            self._logger.info(f"Session {session_id} deleted")
        except Exception as e:
            await self._handle_error(e, {"operation": "delete_session", "session_id": session_id})

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user.

        Args:
            user_id: User identifier

        Returns:
            List of session data
        """
        try:
            return await self._session_repo.get_user_sessions(user_id)
        except Exception as e:
            await self._handle_error(e, {"operation": "get_user_sessions", "user_id": user_id})

    async def check_user_exists(self, user_id: str) -> Dict[str, Any]:
        """Check if user exists and get session count.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with exists, user_id, and session_count
        """
        try:
            exists = await self._session_repo.check_user_exists(user_id)

            if exists:
                sessions = await self._session_repo.get_user_sessions(user_id)
                session_count = len(sessions)
            else:
                session_count = 0

            return {
                "exists": exists,
                "user_id": user_id,
                "session_count": session_count
            }
        except Exception as e:
            await self._handle_error(e, {"operation": "check_user_exists", "user_id": user_id})
