"""
Structured logging utilities using structlog.

This module provides structured logging with JSON output, correlation ID support,
and contextual information for better log analysis and debugging.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Optional

import structlog
from structlog.types import EventDict, Processor


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application-level context to all log entries.

    Args:
        logger: Logger instance
        method_name: Method being called
        event_dict: Event dictionary with log data

    Returns:
        Updated event dictionary with app context
    """
    # Add app name if not present
    if "app" not in event_dict:
        event_dict["app"] = "ai_mono"

    return event_dict


def add_correlation_id(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add correlation ID from context if available.

    Args:
        logger: Logger instance
        method_name: Method being called
        event_dict: Event dictionary with log data

    Returns:
        Updated event dictionary with correlation_id
    """
    # Check if correlation_id is in structlog context
    context = structlog.get_context()
    if "correlation_id" in context:
        event_dict["correlation_id"] = context["correlation_id"]

    return event_dict


def rename_message(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Rename 'event' to 'message' for consistency.

    Args:
        logger: Logger instance
        method_name: Method being called
        event_dict: Event dictionary with log data

    Returns:
        Updated event dictionary
    """
    if "event" in event_dict:
        event_dict["message"] = event_dict.pop("event")
    return event_dict


def setup_structured_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = True,
    include_timestamp: bool = True,
    include_caller_info: bool = True,
) -> None:
    """Configure structured logging with structlog.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to
        json_format: Whether to use JSON format (True) or console format (False)
        include_timestamp: Include timestamp in logs
        include_caller_info: Include module/function/line number
    """
    # Configure standard logging to work with structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

    # Build shared processors list
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_correlation_id,
        add_app_context,
    ]

    if include_timestamp:
        shared_processors.append(structlog.processors.TimeStamper(fmt="iso"))

    if include_caller_info:
        shared_processors.append(structlog.stdlib.add_caller_info())

    if json_format:
        # JSON format for production/file logging
        shared_processors.extend([
            rename_message,
            structlog.processors.JSONRenderer()
        ])
    else:
        # Console format for development
        shared_processors.extend([
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback
            )
        ])

    # Configure structlog
    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Create file handler with JSON formatter
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(getattr(logging, level.upper()))

        # Add JSON processor for file output
        file_processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            add_correlation_id,
            add_app_context,
            structlog.processors.TimeStamper(fmt="iso"),
            rename_message,
            structlog.processors.JSONRenderer(),
        ]

        # Configure separate logger for file output
        structlog.configure(
            processors=file_processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.WriteLoggerFactory(file_handler),
            cache_logger_on_first_use=True,
        )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Structured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("User logged in", user_id="123", ip="192.168.1.1")
    """
    return structlog.get_logger(name)


def bind_correlation_id(correlation_id: str) -> None:
    """Bind correlation ID to the current logging context.

    Args:
        correlation_id: Unique correlation ID for request tracking

    Example:
        >>> bind_correlation_id("abc-123")
        >>> logger.info("Processing request")  # Will include correlation_id
    """
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def clear_context() -> None:
    """Clear all context variables from the current logging context.

    Example:
        >>> clear_context()
    """
    structlog.contextvars.clear_contextvars()


def unbind_correlation_id() -> None:
    """Remove correlation ID from the current logging context.

    Example:
        >>> unbind_correlation_id()
    """
    structlog.contextvars.unbind_contextvars("correlation_id")


class RequestContext:
    """Context manager for request-specific logging context.

    Automatically binds correlation ID and other context for the duration
    of a request, then cleans up.

    Example:
        >>> with RequestContext(correlation_id="abc-123", user_id="456"):
        ...     logger.info("Processing request")
        ... # Context automatically cleared here
    """

    def __init__(self, **kwargs):
        """Initialize request context.

        Args:
            **kwargs: Context variables to bind (e.g., correlation_id, user_id)
        """
        self.context = kwargs

    def __enter__(self):
        """Bind context variables."""
        structlog.contextvars.bind_contextvars(**self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clear context variables."""
        structlog.contextvars.clear_contextvars()
        return False
