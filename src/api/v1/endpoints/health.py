"""Health check endpoints."""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from src.utils import get_logger

from src.api.schemas import HealthStatus
from src.database.rag import initialize_database, close_database, test_db_connection as rag_db_conn_test
from src.database.memory.connection import test_db_connection as memory_db_conn_test
from src.config.settings import settings

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connections
        rag_db_test = await rag_db_conn_test()
        memory_db_test = await memory_db_conn_test()

        # Determine overall status
        rag_db_status = "healthy" if rag_db_test else "unhealthy"
        memory_db_status = "healthy" if memory_db_test else "unhealthy"

        return HealthStatus(
            rag_db_status=rag_db_status,
            memory_db_status=memory_db_status,
            llm_connection=True,
            version=settings.app_version,
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")
