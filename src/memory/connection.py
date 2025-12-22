from dataclasses import dataclass
from src.config.settings import settings
from src.utils.logging import get_logger

from mem0 import Memory
import asyncpg


logger = get_logger(__name__)


def get_mem0_client() -> Memory:

    try:

        config = {
            "llm": {
                "provider": settings.db.memory_llm_provider,
                "config": {
                    "model": settings.db.memory_llm_model,
                    "api_key": settings.llm.openai_api_key,
                },
            },
            "embedder": {
                "provider": settings.db.memory_embedding_provider,
                "config": {
                    "model": settings.db.memory_llm_model,
                    "embedding_dims": settings.db.memory_embedding_dims,
                    "api_key": settings.llm.openai_api_key,
                },
            },
            "vector_store": {
                "provider": settings.db.memory_vector_store_provider,
                "config": {
                    "user": settings.db.memory_db_user,
                    "password": settings.db.memory_db_password,
                    "host": settings.db.memory_db_host,
                    "port": settings.db.memory_db_port,
                    "dbname": settings.db.memory_db_name,
                },
            },
        }

        _memory = Memory.from_config(config)

        logger.info("Memory has been configured and started")
        return _memory
    except Exception as e:
        logger.error(f"Memory startup failed: {e}")
        raise


async def test_db_connection() -> bool:
    """
    Test the connection to the PostgreSQL database and check if the pgvector extension is enabled.
    """
    try:
        conn = await asyncpg.connect(
            host=settings.db.memory_db_host,
            port=settings.db.memory_db_port,
            user=settings.db.memory_db_user,
            password=settings.db.memory_db_password,
            database=settings.db.memory_db_name
        )

        version = await conn.fetchval("SELECT version();")
        logger.info(f"Connected to PostgreSQL database: {version}")

        vector_ext = await conn.fetchrow("SELECT * FROM pg_extension WHERE extname = 'vector';")
        if vector_ext:
            logger.info("pgvector extension is enabled.")
        else:
            logger.info("pgvector extension is NOT enabled! Initializing...")
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            logger.info("pgvector extension is initialized.")

        await conn.close()
        return True

    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return False

@dataclass
class Mem0Context:
    """Context for the Mem0 MCP server."""
    mem0_client: Memory