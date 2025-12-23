from contextlib import asynccontextmanager
from src.config.settings import settings
from typing import Optional
import asyncpg
from asyncpg.pool import Pool
import logging

logger = logging.getLogger(__name__)


class DatabasePool:
    """Manages PostgreSQL connection pool."""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database pool.

        Args:
            database_url: PostgreSQL connection URL
        """
        # Construct asyncpg-compatible DSN (not SQLAlchemy format)
        self.database_url = (
            f"postgresql://{settings.db.rag_db_user}:{settings.db.rag_db_password}"
            f"@{settings.db.rag_db_host}:{settings.db.rag_db_port}/{settings.db.rag_db_name}"
        )

        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")

        self.pool: Optional[Pool] = None

    async def initialize(self):
        """Create connection pool."""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=settings.db.rag_db_min_connection,
                max_size=settings.db.rag_db_max_connection,
                max_inactive_connection_lifetime=settings.db.rag_db_max_inactive_lifetime,
                command_timeout=settings.db.rag_db_connection_timeout,
                statement_cache_size=0,
            )
            logger.info("Database connection pool initialized")

    async def close(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")

    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool."""
        if not self.pool:
            await self.initialize()

        async with self.pool.acquire() as connection:
            yield connection


# Global database pool instance
db_pool = DatabasePool()


async def initialize_database():
    """Initialize database connection pool."""
    await db_pool.initialize()


async def close_database():
    """Close database connection pool."""
    await db_pool.close()



async def test_db_connection() -> bool:
    """
    Test database connection.

    Returns:
        True if connection successful
    """
    try:
        USER = settings.db.rag_db_user
        HOST = settings.db.rag_db_host
        PORT = settings.db.rag_db_port
        DBNAME = settings.db.rag_db_name

        logger.info(
            f"RAG DB connection attempt: host={HOST}, port={PORT}, user={USER}, database={DBNAME}")

        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False
