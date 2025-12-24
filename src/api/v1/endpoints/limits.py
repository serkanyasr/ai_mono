"""Rate limit information endpoints.

This module provides endpoints to display current rate limit configurations.
"""

from fastapi import APIRouter, Request
from typing import Dict, Any

from src.api.v1.middleware.rate_limit import RateLimits
from src.utils import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/limits")
async def get_rate_limits(request: Request) -> Dict[str, Any]:
    """Get current rate limit configurations.

    Returns information about predefined rate limits for different endpoint types.

    Response includes:
    - Predefined rate limit categories (chat, sessions, cache, etc.)
    - Rate limit per category (e.g., "10/minute", "100/hour")
    - Client identification info (IP address)
    """
    return {
        "rate_limits": {
            "health": RateLimits.HEALTH,
            "chat": RateLimits.CHAT,
            "chat_premium": RateLimits.CHAT_PREMIUM,
            "sessions": RateLimits.SESSIONS,
            "cache": RateLimits.CACHE,
            "admin": RateLimits.ADMIN,
            "burst": RateLimits.BURST,
        },
        "descriptions": {
            "health": "Health check endpoints (very permissive)",
            "chat": "Chat endpoints (restrictive)",
            "chat_premium": "Premium user chat endpoints",
            "sessions": "Session CRUD operations",
            "cache": "Cache operations",
            "admin": "Admin operations",
            "burst": "Short burst requests (very restrictive)",
        },
        "client_info": {
            "ip": request.client.host if request.client else "unknown",
        },
        "documentation": {
            "rate_limit_format": "Requests per time period (e.g., '10/minute' = 10 requests per minute)",
            "header": "Rate limit information is returned in X-RateLimit-* headers when limits are enforced",
            "exceeded": "When rate limit is exceeded, HTTP 429 is returned with retry_after value",
        }
    }


@router.get("/limits/status")
async def get_rate_limit_status(request: Request) -> Dict[str, Any]:
    """Get rate limit status for current client.

    Returns the current rate limit status including:
    - Correlation ID for request tracking
    - Whether the client is currently rate limited
    - Information about the rate limiter configuration

    Note: This endpoint itself is exempt from rate limiting to allow
    clients to check their status even when rate limited.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    # Get storage type from limiter
    storage_type = "memory"
    storage_backend = "memory"
    if hasattr(request.app.state, 'limiter'):
        limiter_storage = request.app.state.limiter._storage
        storage_type = type(limiter_storage).__name__
        if "Redis" in storage_type:
            storage_backend = "redis"

    return {
        "correlation_id": correlation_id,
        "client": request.client.host if request.client else "unknown",
        "path": request.url.path,
        "limiter_type": storage_type,
        "storage_backend": storage_backend,
        "status": "active",
        "recommendations": {
            "production": "Rate limiting is configured with Redis storage" if storage_backend == "redis" else "Use Redis storage for distributed rate limiting",
            "configuration": "See src/api/v1/middleware/rate_limit.py for configuration",
        }
    }
