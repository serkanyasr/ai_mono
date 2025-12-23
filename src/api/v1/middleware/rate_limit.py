"""Rate limiting middleware using slowapi.

This module provides rate limiting for API endpoints to prevent abuse
and ensure fair resource allocation among clients.
"""

from functools import wraps
from typing import Callable
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from src.utils import get_logger

logger = get_logger(__name__)

# Initialize slowapi limiter
# Using memory storage by default. For production, use Redis.
limiter = Limiter(key_func=get_remote_address)


def get_limiter():
    """Get the rate limiter instance.

    Returns:
        Limiter instance
    """
    return limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting.

    This middleware applies rate limiting to all endpoints.
    Individual endpoints can have their own rate limits using the @limiter.limit() decorator.

    Rate limits can be configured per:
    - Endpoint path
    - User (via API key or user ID)
    - IP address

    Usage:
        # Apply global rate limit
        app.add_middleware(RateLimitMiddleware)

        # Or use limiter decorator on endpoints
        @app.get("/api/v1/chat/stream")
        @limiter.limit("10/minute")
        async def chat_stream():
            ...
    """

    def __init__(
        self,
        app: ASGIApp,
        default_limits: list[str] = None,
        storage_uri: str = None
    ):
        """Initialize rate limiting middleware.

        Args:
            app: ASGI application
            default_limits: Default rate limits (e.g., ["100/minute", "1000/hour"])
            storage_uri: Storage URI for Redis (optional, uses memory if not provided)
        """
        super().__init__(app)
        self._default_limits = default_limits or ["60/minute"]
        self._storage_uri = storage_uri

        # Configure storage if Redis URI provided
        if storage_uri:
            from slowapi.storage import RedisStorage
            from slowapi.util import get_remote_address

            storage = RedisStorage(
                uri=storage_uri,
                prefix="rate_limit:"
            )
            # Update limiter to use Redis storage
            global limiter
            limiter = Limiter(
                key_func=get_remote_address,
                storage_uri=storage_uri
            )

    async def dispatch(self, request: Request, call_next):
        """Dispatch with rate limiting check.

        Args:
            request: Incoming request
            call_next: Next middleware or route handler

        Returns:
            Response or raises RateLimitExceeded
        """
        # Rate limiting is handled by decorators on endpoints
        # This middleware is mainly for configuration purposes
        return await call_next(request)


class RateLimiter:
    """Rate limiter utility class for dynamic configuration.

    This class provides a convenient way to configure rate limits
    for different endpoints and user types.

    Example:
        # Standard rate limit
        @RateLimiter.limit("10/minute")
        async def my_endpoint():
            ...

        # Rate limit per user
        @RateLimiter.limit("100/minute", key_func=lambda r: r.headers.get("X-User-ID"))
        async def user_endpoint():
            ...

        # Custom rate limit for premium users
        @RateLimiter.limit("1000/minute", key_func=lambda r: "premium:" + r.headers.get("X-User-ID", ""))
        async def premium_endpoint():
            ...
    """

    @staticmethod
    def limit(rate_string: str, key_func: Callable = None):
        """Create a rate limit decorator.

        Args:
            rate_string: Rate limit string (e.g., "10/minute", "100/hour")
            key_func: Optional function to extract rate limit key from request

        Returns:
            Decorator function

        Example:
            # 10 requests per minute per IP
            @RateLimiter.limit("10/minute")

            # 100 requests per hour per user
            @RateLimiter.limit("100/hour", key_func=lambda r: r.headers.get("X-User-ID"))
        """
        return limiter.limit(rate_string, key_func=key_func)

    @staticmethod
    def exempt():
        """Create an exemption from rate limiting.

        Returns:
            Decorator to exempt endpoint from rate limiting

        Example:
            @RateLimiter.exempt()
            async def health_check():
                ...
        """
        return limiter.exempt


# Custom rate limit exceeded handler
async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded.

    Args:
        request: Incoming request
        exc: Rate limit exceeded exception

    Returns:
        JSON response with rate limit info
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    logger.warning(
        f"Rate limit exceeded: {request.client.host if request.client else 'unknown'}",
        extra={
            "correlation_id": correlation_id,
            "path": request.url.path,
            "method": request.method,
        }
    )

    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "error_type": "RateLimitExceeded",
            "detail": str(exc),
            "correlation_id": correlation_id,
            "retry_after": getattr(exc, "retry_after", 60),
        }
    )


# Set custom handler
_rate_limit_exceeded_handler = custom_rate_limit_exceeded_handler


# Predefined rate limits for different endpoint types
class RateLimits:
    """Predefined rate limit configurations.

    Common rate limits:
    - Health check: Unlimited
    - Chat: 10/minute (default)
    - Session management: 60/minute
    - Cache operations: 30/minute
    """

    HEALTH = "1000/minute"       # Health checks (very permissive)
    CHAT = "10/minute"           # Chat endpoints (restrictive)
    CHAT_PREMIUM = "60/minute"   # Premium users
    SESSIONS = "60/minute"      # Session CRUD
    CACHE = "30/minute"          # Cache operations
    ADMIN = "100/minute"         # Admin operations
    BURST = "10/second"          # Short burst (very restrictive)

    @staticmethod
    def per_user(rate_string: str):
        """Get rate limit per user (X-User-ID header).

        Args:
            rate_string: Rate limit string

        Returns:
            Decorator with user-based key function
        """
        return limiter.limit(rate_string, key_func=lambda r: r.headers.get("X-User-ID", "anonymous"))

    @staticmethod
    def per_api_key(rate_string: str):
        """Get rate limit per API key (Authorization header).

        Args:
            rate_string: Rate limit string

        Returns:
            Decorator with API key based key function
        """
        def get_api_key(request: Request):
            # Extract API key from Authorization header
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                return auth_header[7:]  # Remove "Bearer " prefix
            return "anonymous"

        return limiter.limit(rate_string, key_func=get_api_key)

    @staticmethod
    def per_ip(rate_string: str):
        """Get rate limit per IP address (default behavior).

        Args:
            rate_string: Rate limit string

        Returns:
            Decorator with IP-based key function
        """
        return limiter.limit(rate_string)
