from .logging import (
    get_logger,
    setup_logging,
    bind_correlation_id,
    unbind_correlation_id,
    clear_context,
)

# Import structured logging functions with different names
from .structured_logging import (
    setup_structured_logging,
    RequestContext,
)

from .resilience import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitState,
    retry_on_exception,
    retry_with_jitter,
    resilient,
    LLM_CIRCUIT_BREAKER,
    MCP_CIRCUIT_BREAKER,
    DATABASE_CIRCUIT_BREAKER,
)

__all__ = [
    # Logging (backward compatible, now uses structlog)
    "get_logger",
    "setup_logging",
    "bind_correlation_id",
    "unbind_correlation_id",
    "clear_context",
    # Structured logging
    "setup_structured_logging",
    "RequestContext",
    # Resilience
    "CircuitBreaker",
    "CircuitBreakerError",
    "CircuitState",
    "retry_on_exception",
    "retry_with_jitter",
    "resilient",
    "LLM_CIRCUIT_BREAKER",
    "MCP_CIRCUIT_BREAKER",
    "DATABASE_CIRCUIT_BREAKER",
]
