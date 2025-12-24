"""Session related database queries."""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import json
import logging

from ..connection import db_pool

logger = logging.getLogger(__name__)


async def create_session(
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    timeout_minutes: int = 60,
) -> str:
    """
    Create a new session.

    Args:
        user_id: Optional user identifier
        metadata: Optional session metadata
        timeout_minutes: Session timeout in minutes

    Returns:
        Session ID
    """
    async with db_pool.acquire() as conn:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=timeout_minutes)

        result = await conn.fetchrow(
            """
            INSERT INTO sessions (user_id, metadata, expires_at)
            VALUES ($1, $2, $3)
            RETURNING id::text
            """,
            user_id,
            json.dumps(metadata or {}),
            expires_at,
        )

        return result["id"]


async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get session by ID.

    Args:
        session_id: Session UUID

    Returns:
        Session data or None if not found/expired
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT
                id::text,
                user_id,
                metadata,
                created_at,
                updated_at,
                expires_at
            FROM sessions
            WHERE id = $1::uuid
            AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            """,
            session_id,
        )

        if result:
            return {
                "id": result["id"],
                "user_id": result["user_id"],
                "metadata": json.loads(result["metadata"]),
                "created_at": result["created_at"].isoformat(),
                "updated_at": result["updated_at"].isoformat(),
                "expires_at": (
                    result["expires_at"].isoformat() if result["expires_at"] else None
                ),
            }

        return None


async def delete_session(session_id: str) -> None:
    """
    Delete a session by ID.

    Args:
        session_id: Session UUID
    """
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM sessions
            WHERE id = $1::uuid
            """,
            session_id,
        )
        logger.info(f"Session {session_id} deleted.")


async def get_user_sessions(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all sessions for a specific user.

    Args:
        user_id: User identifier

    Returns:
        List of session data
    """
    async with db_pool.acquire() as conn:
        results = await conn.fetch(
            """
            SELECT
                s.id::text as session_id,
                s.user_id,
                s.metadata,
                s.created_at,
                s.updated_at,
                s.expires_at,
                COUNT(m.id) as message_count,
                (
                    SELECT m2.content
                    FROM messages m2
                    WHERE m2.session_id = s.id
                    AND m2.role = 'user'
                    ORDER BY m2.created_at DESC
                    LIMIT 1
                ) as last_message
            FROM sessions s
            LEFT JOIN messages m ON m.session_id = s.id
            WHERE s.user_id = $1
            AND (s.expires_at IS NULL OR s.expires_at > CURRENT_TIMESTAMP)
            GROUP BY s.id, s.user_id, s.metadata, s.created_at, s.updated_at, s.expires_at
            ORDER BY s.updated_at DESC
            """,
            user_id,
        )

        return [
            {
                "session_id": row["session_id"],
                "user_id": row["user_id"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat(),
                "expires_at": row["expires_at"].isoformat() if row["expires_at"] else None,
                "message_count": row["message_count"],
                "last_message": row["last_message"]
            }
            for row in results
        ]


async def check_user_exists(user_id: str) -> bool:
    """
    Check if a user has any sessions.

    Args:
        user_id: User identifier

    Returns:
        True if user has sessions, False otherwise
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM sessions
                WHERE user_id = $1
            )
            """,
            user_id,
        )
        return result
