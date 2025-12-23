"""Centralized error handling middleware and handlers.

This module provides consistent error handling across the application
with proper logging, correlation IDs, and structured error responses.
"""

import traceback
import uuid
from typing import Union
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from src.exception import BaseAppException
from src.utils import get_logger

logger = get_logger(__name__)


async def app_exception_handler(request: Request, exc: BaseAppException):
    """Handler for application-specific exceptions.

    Args:
        request: Incoming request
        exc: Application exception

    Returns:
        JSON response with error details
    """
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

    logger.error(
        f"Application error: {exc.detail}",
        extra={
            "correlation_id": correlation_id,
            "error_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "error_type": exc.error_type,
            "correlation_id": correlation_id,
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler for HTTP exceptions.

    Args:
        request: Incoming request
        exc: HTTP exception

    Returns:
        JSON response with error details
    """
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

    logger.warning(
        f"HTTP error: {exc.detail}",
        extra={
            "correlation_id": correlation_id,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "error_type": "HTTPException",
            "correlation_id": correlation_id,
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handler for unexpected exceptions.

    Args:
        request: Incoming request
        exc: Unexpected exception

    Returns:
        JSON response with error details
    """
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "correlation_id": correlation_id,
            "error_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc(),
        }
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_type": type(exc).__name__,
            "correlation_id": correlation_id,
        }
    )


class ErrorHandlingMiddleware:
    """Middleware class for error handling.

    This middleware wraps the entire application to catch and handle
    exceptions consistently, adding correlation IDs and proper logging.
    """

    def __init__(self, app, debug: bool = False):
        """Initialize error handling middleware.

        Args:
            app: ASGI application
            debug: Whether to include debug information
        """
        self.app = app
        self.debug = debug

    async def __call__(self, scope, receive, send):
        """Middleware call method.

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            # Handle uncaught exceptions
            from fastapi import Request
            from fastapi.responses import JSONResponse

            # Create a mock request for error handling
            request = Request(scope, receive)

            correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

            logger.error(
                f"Uncaught exception in middleware: {str(exc)}",
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(exc).__name__,
                    "traceback": traceback.format_exc(),
                }
            )

            response = JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "error_type": type(exc).__name__,
                    "correlation_id": correlation_id,
                    **({"debug": str(exc)} if self.debug else {})
                }
            )

            await response(scope, receive, send)
