"""Repository interfaces for data access layer.

This module defines the interfaces that all repositories must implement,
providing abstraction for testing and enabling dependency injection.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class ISessionRepository(ABC):
    """Session repository interface."""

    @abstractmethod
    async def create(self, user_id: Optional[str], metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create new session.

        Args:
            user_id: Optional user identifier
            metadata: Optional session metadata

        Returns:
            Session ID
        """
        pass

    @abstractmethod
    async def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID.

        Args:
            session_id: Session UUID

        Returns:
            Session data or None if not found
        """
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Delete session.

        Args:
            session_id: Session UUID
        """
        pass

    @abstractmethod
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user.

        Args:
            user_id: User identifier

        Returns:
            List of session data
        """
        pass

    @abstractmethod
    async def check_user_exists(self, user_id: str) -> bool:
        """Check if user has any sessions.

        Args:
            user_id: User identifier

        Returns:
            True if user has sessions, False otherwise
        """
        pass


class IMessageRepository(ABC):
    """Message repository interface."""

    @abstractmethod
    async def add(self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add message to session.

        Args:
            session_id: Session UUID
            role: Message role (user/assistant/system)
            content: Message content
            metadata: Optional message metadata

        Returns:
            Message ID
        """
        pass

    @abstractmethod
    async def list(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List messages in a session.

        Args:
            session_id: Session UUID
            limit: Maximum number of messages to return

        Returns:
            List of messages ordered by creation time
        """
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Delete all messages in a session.

        Args:
            session_id: Session UUID
        """
        pass


class IDocumentRepository(ABC):
    """Document repository interface."""

    @abstractmethod
    async def get(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID.

        Args:
            document_id: Document UUID

        Returns:
            Document data or None if not found
        """
        pass

    @abstractmethod
    async def list(self, limit: int = 100, offset: int = 0, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List documents with optional filtering.

        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            metadata_filter: Optional metadata filter

        Returns:
            List of documents
        """
        pass
