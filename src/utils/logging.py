"""
Logging utilities for system.

This module provides backward-compatible logging functions that now use
structured logging (structlog) internally. For new code, consider using
the structured logging API directly from src.utils.structured_logging.

Example:
    # Old API (still works)
    from src.utils import get_logger, setup_logging
    setup_logging(level="INFO")
    logger = get_logger(__name__)
    logger.info("Message")

    # New structured API (recommended)
    from src.utils.structured_logging import get_logger, bind_correlation_id
    logger = get_logger(__name__)
    bind_correlation_id("abc-123")
    logger.info("Message", user_id="123")
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Import structlog for structured logging
import structlog


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    log_file: Optional[str] = None,
    use_structured: bool = True,
) -> logging.Logger:
    """
    Set up logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string (only for non-structured logging)
        log_file: Optional file path to write logs to
        use_structured: Use structured logging with structlog (recommended)

    Returns:
        Configured logger instance
    """
    if use_structured:
        # Use structured logging
        from .structured_logging import setup_structured_logging

        # Determine JSON format based on environment
        import os
        is_dev = os.getenv("API_ENV", "development") == "development"

        setup_structured_logging(
            level=level,
            log_file=log_file,
            json_format=not is_dev,  # Console format in dev, JSON in prod
        )
        return logging.getLogger()
    else:
        # Legacy logging setup
        if format_string is None:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        # Create root logger
        logger = logging.getLogger()
        logger.setLevel(getattr(logging, level.upper()))

        # Clear existing handlers
        logger.handlers.clear()

        # Create formatter
        formatter = logging.Formatter(format_string)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler (if specified)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a logger instance with the specified name.

    Now returns a structured logger that supports context binding and
    structured output.

    Args:
        name: Logger name

    Returns:
        Structured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Message")  # Legacy style
        >>> logger.info("Message", user_id="123")  # Structured style
    """
    # Import structlog logger
    from .structured_logging import get_logger as _get_structured_logger

    return _get_structured_logger(name)


# Convenience functions for structured logging context management
def bind_correlation_id(correlation_id: str) -> None:
    """Bind correlation ID to the current logging context.

    Args:
        correlation_id: Unique correlation ID for request tracking
    """
    from .structured_logging import bind_correlation_id as _bind
    _bind(correlation_id)


def unbind_correlation_id() -> None:
    """Remove correlation ID from the current logging context."""
    from .structured_logging import unbind_correlation_id as _unbind
    _unbind()


def clear_context() -> None:
    """Clear all context variables from the current logging context."""
    from .structured_logging import clear_context as _clear
    _clear()
