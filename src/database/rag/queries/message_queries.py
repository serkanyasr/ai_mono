"""Message related database queries."""

from typing import Dict, Any, List, Optional
import json
import logging

from .connection import db_pool

logger = logging.getLogger(__name__)


async def add_message(
    session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Add a message to a session.

    Args:
        session_id: Session UUID
        role: Message role (user/assistant/system)
        content: Message content
        metadata: Optional message metadata

    Returns:
        Message ID
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            INSERT INTO messages (session_id, role, content, metadata)
            VALUES ($1::uuid, $2, $3, $4)
            RETURNING id::text
            """,
            session_id,
            role,
            content,
            json.dumps(metadata or {}),
        )

        return result["id"]


async def get_session_messages(
    session_id: str, limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get messages for a session.

    Args:
        session_id: Session UUID
        limit: Maximum number of messages to return

    Returns:
        List of messages ordered by creation time
    """
    async with db_pool.acquire() as conn:
        query = """
            SELECT
                id::text,
                role,
                content,
                metadata,
                created_at
            FROM messages
            WHERE session_id = $1::uuid
            ORDER BY created_at
        """

        if limit:
            query += f" LIMIT {limit}"

        results = await conn.fetch(query, session_id)

        return [
            {
                "id": row["id"],
                "role": row["role"],
                "content": row["content"],
                "metadata": json.loads(row["metadata"]),
                "created_at": row["created_at"].isoformat(),
            }
            for row in results
        ]


async def delete_message(message_id: str) -> None:
    """
    Delete a message by ID.

    Args:
        message_id: Message UUID
    """
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM messages
            WHERE id = $1::uuid
            """,
            message_id,
        )
        logger.info(f"Message {message_id} deleted.")


async def delete_session_messages(session_id: str) -> None:
    """
    Delete all messages for a session.

    Args:
        session_id: Session UUID
    """
    async with db_pool.acquire() as conn:
        result = await conn.execute(
            """
            DELETE FROM messages
            WHERE session_id = $1::uuid
            """,
            session_id,
        )
        logger.info(f"Deleted all messages for session {session_id}")
