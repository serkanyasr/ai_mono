"""
Custom exceptions for the AI Multi-Agent Enterprise System
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status

class BaseCustomException(Exception):
    """Base class for custom exceptions"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.detail = message  # Alias for compatibility
        self.status_code = status_code
        self.details = details or {}
        self.error_type = self.__class__.__name__
        super().__init__(self.message)


# Alias for compatibility with error_handlers
BaseAppException = BaseCustomException


class ValidationError(BaseCustomException):
    """Validation error exception"""

    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        details = {"field": field} if field else {}
        details.update(kwargs)
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class AuthenticationError(BaseCustomException):
    """Authentication error exception"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(BaseCustomException):
    """Authorization error exception"""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundError(BaseCustomException):
    """Resource not found error exception"""

    def __init__(self, message: str, resource_type: Optional[str] = None, **kwargs):
        details = {"resource_type": resource_type} if resource_type else {}
        details.update(kwargs)
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class ConflictError(BaseCustomException):
    """Conflict error exception (resource already exists)"""

    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        details = {"field": field} if field else {}
        details.update(kwargs)
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class RateLimitError(BaseCustomException):
    """Rate limit exceeded error exception"""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )


class DatabaseError(BaseCustomException):
    """Database error exception"""

    def __init__(self, message: str, operation: Optional[str] = None):
        details = {"operation": operation} if operation else {}
        super().__init__(
            message=f"Database error: {message}",
            details=details
        )


class ExternalServiceError(BaseCustomException):
    """External service error exception"""

    def __init__(self, message: str, service: Optional[str] = None, status_code: int = 502):
        details = {"service": service} if service else {}
        super().__init__(
            message=f"External service error: {message}",
            status_code=status_code,
            details=details
        )


class LLMError(ExternalServiceError):
    """LLM service error exception"""

    def __init__(self, message: str, model: Optional[str] = None, provider: Optional[str] = None):
        details = {}
        if model:
            details["model"] = model
        if provider:
            details["provider"] = provider
        super().__init__(
            message=message,
            service="LLM",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
        self.details.update(details)


class VectorStoreError(ExternalServiceError):
    """Vector store error exception"""

    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message=f"Vector store error: {message}",
            service="VectorStore",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
        if operation:
            self.details["operation"] = operation


class CacheError(ExternalServiceError):
    """Cache service error exception"""

    def __init__(self, message: str):
        super().__init__(
            message=f"Cache error: {message}",
            service="Cache",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class FileProcessingError(BaseCustomException):
    """File processing error exception"""

    def __init__(self, message: str, file_name: Optional[str] = None, file_type: Optional[str] = None):
        details = {}
        if file_name:
            details["file_name"] = file_name
        if file_type:
            details["file_type"] = file_type
        super().__init__(
            message=f"File processing error: {message}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class ConfigurationError(BaseCustomException):
    """Configuration error exception"""

    def __init__(self, message: str, config_key: Optional[str] = None):
        details = {"config_key": config_key} if config_key else {}
        super().__init__(
            message=f"Configuration error: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


# Exception handler setup for FastAPI
def setup_exception_handlers(app):
    """Setup custom exception handlers for FastAPI application"""

    @app.exception_handler(BaseCustomException)
    async def custom_exception_handler(request, exc: BaseCustomException):
        """Handle custom exceptions"""
        from fastapi.responses import JSONResponse
        import json

        response_data = {
            "error": exc.__class__.__name__,
            "message": exc.message,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }

        if exc.details:
            response_data["details"] = exc.details

        return JSONResponse(
            status_code=exc.status_code,
            content=response_data
        )

    @app.exception_handler(DatabaseError)
    async def database_exception_handler(request, exc: DatabaseError):
        """Handle database exceptions"""
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "DATABASE_ERROR",
                "message": "A database error occurred",
                "details": exc.details,
                "path": str(request.url.path)
            }
        )

    @app.exception_handler(LLMError)
    async def llm_exception_handler(request, exc: LLMError):
        """Handle LLM service exceptions"""
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "LLM_ERROR",
                "message": "AI service temporarily unavailable",
                "details": exc.details,
                "path": str(request.url.path)
            }
        )


# Utility functions for common error scenarios
def raise_not_found(resource: str, identifier: Any = None):
    """Raise a NotFoundError for a resource"""
    message = f"{resource} not found"
    if identifier:
        message += f" with identifier: {identifier}"
    raise NotFoundError(message, resource_type=resource)


def raise_already_exists(resource: str, field: str, value: Any):
    """Raise a ConflictError for existing resource"""
    raise ConflictError(
        f"{resource} with {field} '{value}' already exists",
        field=field,
        value=value
    )


def raise_permission_denied(action: str, resource: Optional[str] = None):
    """Raise an AuthorizationError for insufficient permissions"""
    message = f"Permission denied for action: {action}"
    if resource:
        message += f" on resource: {resource}"
    raise AuthorizationError(message)


def raise_validation_error(message: str, field: Optional[str] = None, **kwargs):
    """Raise a ValidationError"""
    raise ValidationError(message, field=field, **kwargs)


def raise_authentication_error(message: str = "Authentication required"):
    """Raise an AuthenticationError"""
    raise AuthenticationError(message)


def raise_rate_limit_error(retry_after: Optional[int] = None):
    """Raise a RateLimitError"""
    raise RateLimitError(retry_after=retry_after)
