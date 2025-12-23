"""Base service class for all business logic services."""

import logging
from typing import Dict, Any


class BaseService:
    """Base service with common functionality for all services.

    This class provides:
    - Centralized logging
    - Centralized error handling
    - Common service utilities
    """

    def __init__(self, logger_name: str = None):
        """Initialize base service.

        Args:
            logger_name: Optional logger name. Defaults to class name.
        """
        self._logger = logging.getLogger(logger_name or self.__class__.__name__)

    async def _handle_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """Centralized error handling for services.

        Args:
            error: The exception that occurred
            context: Optional context information
        """
        error_context = context or {}
        error_context["service"] = self.__class__.__name__
        self._logger.error(f"Error in {self.__class__.__name__}: {error}", extra=error_context)
        raise
