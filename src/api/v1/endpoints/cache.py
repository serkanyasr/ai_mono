"""Cache management endpoints."""

from fastapi import APIRouter, HTTPException
from src.utils import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/cache/stats")
async def get_cache_stats(request):
    """Get agent cache statistics."""
    try:
        if not hasattr(request.app.state, 'agent_cache'):
            return {"error": "Agent cache not initialized"}

        cache_stats = request.app.state.agent_cache.get_stats()
        return cache_stats
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/clear")
async def clear_cache(request):
    """Clear all cached agents."""
    try:
        if not hasattr(request.app.state, 'agent_cache'):
            return {"error": "Agent cache not initialized"}

        request.app.state.agent_cache.clear()
        return {"success": True, "message": "Cache cleared"}
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))
