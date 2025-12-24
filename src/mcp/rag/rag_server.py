from datetime import datetime
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from typing import List, Dict, Any, Optional
from fastmcp import FastMCP, Context
import asyncio

from src.config.settings import settings
from .models import (
    VectorSearchInput,
    HybridSearchInput,
    DocumentInput,
    DocumentListInput,
    ChunkResult,
    DocumentMetadata    
)
from src.database.rag.connection import (
    db_pool,
    initialize_database,
    close_database,
    test_db_connection
)
from src.database.rag.queries import (
    vector_search,
    hybrid_search,
    get_document,
    list_documents,
    delete_document,
    delete_all_documents,
    get_document_chunks,
    RAGContext
)

from src.llm import get_openai_embedding_client,get_openai_embedding_model

logger = logging.getLogger(__name__)

# Initialize embedding client with flexible provider
embedding_client = get_openai_embedding_client()
EMBEDDING_MODEL = get_openai_embedding_model()



@asynccontextmanager
async def rag_lifespan(server: FastMCP) -> AsyncIterator[RAGContext]:
    """Lifespan context manager with database initialization."""
    # Startup
    logger.info("Starting up RAG MCP system...")

    try:
        # Initialize database connections
        await initialize_database()
        logger.info("RAG Database initialized")

        # Test connections
        db_ok = await test_db_connection()
        if not db_ok:
            logger.error("RAG Database connection failed")
            raise RuntimeError("RAG Database connection failed")

        logger.info("RAG MCP system startup complete")
        
        # Yield context with database pool
        yield RAGContext(db_pool=db_pool.pool) # type: ignore


    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    # Shutdown
    logger.info("Shutting down RAG MCP system...")
    try:
        await close_database()
        logger.info("RAG Database connections closed")
    except Exception as e:
        logger.error(f"RAG DB Shutdown error: {e}")


mcp = FastMCP(
    name=settings.mcp.rag_mcp_name,
    version=settings.mcp.rag_mcp_version,
    lifespan=rag_lifespan,
    host=settings.mcp.rag_mcp_host,
    port=settings.mcp.rag_mcp_port,
    json_response=True
)


async def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for text using OpenAI.

    Args:
        text: Text to embed

    Returns:
        Embedding vector
    """
    try:
        response = await embedding_client.embeddings.create(
            model=EMBEDDING_MODEL, input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise




@mcp.tool()
async def vector_search_tool(ctx: Context, input_data: VectorSearchInput) -> List[ChunkResult]:
    """
    Perform vector similarity search.

    Args:
        ctx: FastMCP context containing database connection
        input_data: Search parameters

    Returns:
        List of matching chunks
    """
    try:
        # Access database pool from context
        pool = ctx.request_context.lifespan_context.db_pool
        
        # Generate embedding for the query
        embedding = await generate_embedding(input_data.query)

        # Perform vector search
        results = await vector_search(pool=pool, embedding=embedding, limit=input_data.limit)

        # Convert to ChunkResult models
        return [
            ChunkResult(
                chunk_id=str(r["chunk_id"]),
                document_id=str(r["document_id"]),
                content=r["content"],
                score=r["similarity"],
                metadata=r["metadata"],
                document_title=r["document_title"],
                document_source=r["document_source"],
            )
            for r in results
        ]

    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        return []

@mcp.tool()
async def hybrid_search_tool(ctx: Context, input_data: HybridSearchInput) -> List[ChunkResult]:
    """
    Perform hybrid search (vector + keyword).

    Args:
        ctx: FastMCP context containing database connection
        input_data: Search parameters

    Returns:
        List of matching chunks
    """
    try:
        # Access database pool from context
        pool = ctx.request_context.lifespan_context.db_pool
        
        # Generate embedding for the query
        embedding = await generate_embedding(input_data.query)

        # Perform hybrid search
        results = await hybrid_search(
            pool=pool,
            embedding=embedding,
            query_text=input_data.query,
            limit=input_data.limit,
            text_weight=input_data.text_weight,
        )

        # Convert to ChunkResult models
        return [
            ChunkResult(
                chunk_id=str(r["chunk_id"]),
                document_id=str(r["document_id"]),
                content=r["content"],
                score=r["combined_score"],
                metadata=r["metadata"],
                document_title=r["document_title"],
                document_source=r["document_source"],
            )
            for r in results
        ]

    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        return []

@mcp.tool()
async def get_document_tool(ctx: Context, input_data: DocumentInput) -> Optional[Dict[str, Any]]:
    """
    Retrieve a complete document.

    Args:
        ctx: FastMCP context containing database connection
        input_data: Document retrieval parameters

    Returns:
        Document data or None
    """
    try:
        # Access database pool from context
        pool = ctx.request_context.lifespan_context.db_pool
        
        document = await get_document(pool,input_data.document_id)

        if document:
            chunks = await get_document_chunks(pool=pool, document_id=input_data.document_id)
            document["chunks"] = chunks

        return document

    except Exception as e:
        logger.error(f"Document retrieval failed: {e}")
        return None

@mcp.tool()
async def list_documents_tool(ctx: Context, input_data: Optional[DocumentListInput]) -> List[DocumentMetadata]:
    """
    List available documents.

    Args:
        ctx: FastMCP context containing database connection
        input_data: Listing parameters

    Returns:
        List of document metadata
    """
    try:
        pool = ctx.request_context.lifespan_context.db_pool

        documents = await list_documents(
            pool=pool,
            limit=input_data.limit,
            offset=input_data.offset
        )
        logger.info(f"Documents fetched: {documents}")

        # Convert to DocumentMetadata models
        return [
            DocumentMetadata(
                id=d["id"],
                title=d["title"],
                source=d["source"],
                metadata=d["metadata"],
                created_at=datetime.fromisoformat(d["created_at"]),
                updated_at=datetime.fromisoformat(d["updated_at"]),
                chunk_count=d.get("chunk_count"),
            )
            for d in documents
        ]

    except Exception as e:
        logger.error(f"Document listing failed{e}")
        return []

@mcp.tool()
async def delete_document_tool(ctx: Context, input_data: DocumentInput) -> None:
    """
    Delete a document by ID.

    Args:
        ctx: FastMCP context containing database connection
        input_data: Document deletion parameters
    """
    try:
        pool = ctx.request_context.lifespan_context.db_pool
        await delete_document(pool, input_data.document_id)
    except Exception as e:
        logger.error(f"Document deletion failed: {e}")


@mcp.tool()
async def delete_all_documents_tool(ctx: Context) -> None:
    """
    Delete all documents from the database.

    Args:
        ctx: FastMCP context containing database connection
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        pool = ctx.request_context.lifespan_context.db_pool
        await delete_all_documents(pool)
    except Exception as e:
        logger.error(f"Failed to delete all documents: {e}")


async def main():
    """Main function to run MCP server."""
    transport = settings.mcp.rag_mcp_transport

    # Run with host and port for Docker compatibility
    await mcp.run_async(
        transport=transport,
        host=settings.mcp.rag_mcp_host,
        port=settings.mcp.rag_mcp_port
    )


if __name__ == "__main__":
    asyncio.run(main())