"""Correlation ID middleware for request tracking.

This middleware adds a unique correlation ID to each request for tracking
purposes across distributed systems. Also integrates with structured logging
to automatically include correlation ID in all log entries.
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import Request

# Import for structured logging integration
from src.utils import bind_correlation_id, clear_context


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation ID to each request.

    This middleware:
    1. Generates a unique correlation ID for each request if not provided
    2. Stores it in request.state for access in endpoints
    3. Binds it to structured logging context for automatic inclusion in logs
    4. Returns it in response headers for client-side tracking
    5. Cleans up logging context after request processing

    Usage:
        app.add_middleware(CorrelationIDMiddleware)

        # In endpoint
        correlation_id = request.state.correlation_id

        # In logs (correlation_id is automatically included)
        logger.info("Processing request", user_id="123")
    """

    def __init__(self, app: ASGIApp, header_name: str = "X-Correlation-ID"):
        """Initialize correlation ID middleware.

        Args:
            app: ASGI application
            header_name: Header name for correlation ID
        """
        super().__init__(app)
        self._header_name = header_name

    async def dispatch(self, request: Request, call_next):
        """Process request and add correlation ID.

        Args:
            request: Incoming request
            call_next: Next middleware or route handler

        Returns:
            Response with correlation ID header
        """
        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get(self._header_name) or str(uuid.uuid4())

        # Store in request state for access in endpoints
        request.state.correlation_id = correlation_id

        # Bind to structured logging context
        bind_correlation_id(correlation_id)

        try:
            # Process request
            response = await call_next(request)

            # Add correlation ID to response headers
            response.headers[self._header_name] = correlation_id

            return response
        finally:
            # Clean up logging context
            clear_context()
