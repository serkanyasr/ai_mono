"""Correlation ID middleware for request tracking.

This middleware adds a unique correlation ID to each request for tracking
purposes across distributed systems.
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import Request


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation ID to each request.

    This middleware:
    1. Generates a unique correlation ID for each request if not provided
    2. Stores it in request.state for access in endpoints
    3. Returns it in response headers for client-side tracking

    Usage:
        app.add_middleware(CorrelationIDMiddleware)

        # In endpoint
        correlation_id = request.state.correlation_id
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

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers[self._header_name] = correlation_id

        return response
