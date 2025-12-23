"""Document related database queries."""

from typing import Dict, Any, List, Optional
import json
import logging

from asyncpg.pool import Pool
from .connection import db_pool

logger = logging.getLogger(__name__)


async def get_document(pool: Pool, document_id: str) -> Optional[Dict[str, Any]]:
    """
    Get document by ID.

    Args:
        pool: Database connection pool
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
        pool: Database connection pool
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
        pool: Database connection pool
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
        pool: Database connection pool
    """
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM chunks")
        await conn.execute("DELETE FROM documents")
        logger.info("All documents and chunks deleted.")


async def get_document_chunks(pool: Pool, document_id: str) -> List[Dict[str, Any]]:
    """
    Get all chunks for a document.

    Args:
        pool: Database connection pool
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
