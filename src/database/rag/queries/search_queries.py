"""Vector and hybrid search database queries."""

from typing import Dict, Any, List
from asyncpg.pool import Pool
import json
import logging

from .connection import db_pool

logger = logging.getLogger(__name__)


async def vector_search(
    pool: Pool, embedding: List[float], limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Perform vector similarity search.

    Args:
        pool: Database connection pool
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
    embedding: List[float],
    query_text: str,
    limit: int = 10,
    text_weight: float = 0.3,
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search (vector + keyword).

    Args:
        pool: Database connection pool
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
