from dataclasses import dataclass
import json
from typing import List, Dict, Any, Optional
import logging
from src.config.settings import settings
from src.rag.connection import db_pool
from asyncpg.pool import Pool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


# Message Management Functions

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

# Document Management Functions


async def get_document(pool: Pool, document_id: str) -> Optional[Dict[str, Any]]:
    """
    Get document by ID.

    Args:
        document_id: Document UUID

    Returns:
        Document data or None if not found
    """
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT 
                id::text,
                title,
                source,
                content,
                metadata,
                created_at,
                updated_at
            FROM documents
            WHERE id = $1::uuid
            """,
            document_id,
        )

        if result:
            return {
                "id": result["id"],
                "title": result["title"],
                "source": result["source"],
                "content": result["content"],
                "metadata": json.loads(result["metadata"]),
                "created_at": result["created_at"].isoformat(),
                "updated_at": result["updated_at"].isoformat(),
            }

        return None


async def list_documents(
    pool: Pool,
    limit: int = 100,
    offset: int = 0,
    metadata_filter: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    List documents with optional filtering.

    Args:
        limit: Maximum number of documents to return
        offset: Number of documents to skip
        metadata_filter: Optional metadata filter

    Returns:
        List of documents
    """
    async with pool.acquire() as conn:
        query = """
            SELECT 
                d.id::text,
                d.title,
                d.source,
                d.metadata,
                d.created_at,
                d.updated_at,
                COUNT(c.id) AS chunk_count
            FROM documents d
            LEFT JOIN chunks c ON d.id = c.document_id
        """

        params = []
        conditions = []

        if metadata_filter:
            conditions.append(f"d.metadata @> ${len(params) + 1}::jsonb")
            params.append(json.dumps(metadata_filter))

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += """
            GROUP BY d.id, d.title, d.source, d.metadata, d.created_at, d.updated_at
            ORDER BY d.created_at DESC
            LIMIT $%d OFFSET $%d
        """ % (
            len(params) + 1,
            len(params) + 2,
        )

        params.extend([limit, offset])

        results = await conn.fetch(query, *params)

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "source": row["source"],
                "metadata": json.loads(row["metadata"]),
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat(),
                "chunk_count": row["chunk_count"],
            }
            for row in results
        ]


async def delete_document(pool: Pool, document_id: str) -> None:
    """
    Delete a document by ID.

    Args:
        document_id: Document UUID
    """

    async with pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM documents
            WHERE id = $1::uuid
            """,
            document_id,
        )
        logger.info(f"Document {document_id} deleted.")


async def delete_all_documents(pool: Pool) -> None:
    """
    Delete all documents and associated chunks.

    Args:
        None
    """
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM chunks")
        await conn.execute("DELETE FROM documents")
        logger.info("All documents and chunks deleted.")

# Vector Search Functions


async def vector_search(
    pool: Pool,
    embedding: List[float], limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Perform vector similarity search.

    Args:
        embedding: Query embedding vector
        limit: Maximum number of results

    Returns:
        List of matching chunks ordered by similarity (best first)
    """
    async with pool.acquire() as conn:
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        results = await conn.fetch(
            "SELECT * FROM match_chunks($1::vector, $2)", embedding_str, limit
        )

        return [
            {
                "chunk_id": row["chunk_id"],
                "document_id": row["document_id"],
                "content": row["content"],
                "similarity": row["similarity"],
                "metadata": json.loads(row["metadata"]),
                "document_title": row["document_title"],
                "document_source": row["document_source"],
            }
            for row in results
        ]


async def hybrid_search(
    pool: Pool,
    embedding: List[float], query_text: str, limit: int = 10, text_weight: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search (vector + keyword).

    Args:
        embedding: Query embedding vector
        query_text: Query text for keyword search
        limit: Maximum number of results
        text_weight: Weight for text similarity (0-1)

    Returns:
        List of matching chunks ordered by combined score (best first)
    """
    async with pool.acquire() as conn:
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"

        results = await conn.fetch(
            "SELECT * FROM hybrid_search($1::vector, $2, $3, $4)",
            embedding_str,
            query_text,
            limit,
            text_weight,
        )

        return [
            {
                "chunk_id": row["chunk_id"],
                "document_id": row["document_id"],
                "content": row["content"],
                "combined_score": row["combined_score"],
                "vector_similarity": row["vector_similarity"],
                "text_similarity": row["text_similarity"],
                "metadata": json.loads(row["metadata"]),
                "document_title": row["document_title"],
                "document_source": row["document_source"],
            }
            for row in results
        ]

# Chunk Management Functions


async def get_document_chunks(pool: Pool, document_id: str) -> List[Dict[str, Any]]:
    """
    Get all chunks for a document.

    Args:
        document_id: Document UUID

    Returns:
        List of chunks ordered by chunk index
    """
    async with pool.acquire() as conn:
        results = await conn.fetch(
            "SELECT * FROM get_document_chunks($1::uuid)", document_id
        )

        return [
            {
                "chunk_id": row["chunk_id"],
                "content": row["content"],
                "chunk_index": row["chunk_index"],
                "metadata": json.loads(row["metadata"]),
            }
            for row in results
        ]


@dataclass
class RAGContext:
    """Context for the RAG MCP server with database connection."""
    db_pool: Pool
