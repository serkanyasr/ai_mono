"""Request/response logging middleware.

This middleware provides detailed logging of all incoming requests and
outgoing responses with correlation IDs for debugging and monitoring.
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from src.utils import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses.

    This middleware logs:
    - Request method, path, and correlation ID
    - Request processing time
    - Response status code
    - Request body (optional, for debugging)

    Usage:
        app.add_middleware(LoggingMiddleware, log_body=True)
    """

    def __init__(
        self,
        app: ASGIApp,
        log_body: bool = False,
        log_query_params: bool = True,
        skip_paths: list[str] = None
    ):
        """Initialize logging middleware.

        Args:
            app: ASGI application
            log_body: Whether to log request/response body
            log_query_params: Whether to log query parameters
            skip_paths: Paths to skip logging (e.g., /health)
        """
        super().__init__(app)
        self._log_body = log_body
        self._log_query_params = log_query_params
        self._skip_paths = set(skip_paths or ["/health", "/metrics"])

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request and log details.

        Args:
            request: Incoming request
            call_next: Next middleware or route handler

        Returns:
            Response
        """
        # Skip logging for health checks
        if request.url.path in self._skip_paths:
            return await call_next(request)

        # Get correlation ID
        correlation_id = getattr(request.state, "correlation_id", "unknown")

        # Start timer
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params) if self._log_query_params else None,
                "client": request.client.host if request.client else None,
            }
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time_ms": round(process_time * 1000, 2),
                }
            )

            # Add custom header with processing time
            response.headers["X-Process-Time"] = f"{process_time:.3f}"

            return response

        except Exception as exc:
            # Calculate processing time for failed requests
            process_time = time.time() - start_time

            # Log error
            logger.error(
                f"Request failed",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "process_time_ms": round(process_time * 1000, 2),
                }
            )

            raise


class RequestBodyLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging request/response bodies.

    This middleware should be used with caution as it can:
    - Log sensitive data
    - Impact performance for large payloads
    - Consume significant log storage

    Only use in development environments!
    """

    def __init__(self, app: ASGIApp, max_body_size: int = 10_000):
        """Initialize body logging middleware.

        Args:
            app: ASGI application
            max_body_size: Maximum body size to log (bytes)
        """
        super().__init__(app)
        self._max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request and log body.

        Args:
            request: Incoming request
            call_next: Next middleware or route handler

        Returns:
            Response
        """
        correlation_id = getattr(request.state, "correlation_id", "unknown")

        # Log request body for POST/PUT
        if request.method in ("POST", "PUT", "PATCH"):
            body = await request.body()
            if body:
                body_str = body.decode("utf-8")[:self._max_body_size]
                logger.debug(
                    f"Request body",
                    extra={
                        "correlation_id": correlation_id,
                        "method": request.method,
                        "path": request.url.path,
                        "body": body_str,
                    }
                )

        # Process request
        response = await call_next(request)

        return response
