"""
Resilience patterns for external service calls.

This module provides retry and circuit breaker patterns for handling
transient failures in external service calls (LLM, MCP, database, etc.).
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, ParamSpec

import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)

logger = structlog.get_logger(__name__)

# Type variables for generic decorator
P = ParamSpec('P')
T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """Circuit breaker pattern implementation.

    The circuit breaker prevents cascading failures by blocking requests
    to a service that has been failing consistently.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service failing, requests blocked
    - HALF_OPEN: Testing if service has recovered

    Transitions:
    - CLOSED -> OPEN: When failure threshold is reached
    - OPEN -> HALF_OPEN: After timeout period
    - HALF_OPEN -> CLOSED: On successful request
    - HALF_OPEN -> OPEN: On failed request

    Example:
        >>> breaker = CircuitBreaker(
        ...     failure_threshold=5,
        ...     recovery_timeout=60,
        ...     expected_exception=Exception
        ... )
        >>>
        >>> @breaker
        ... async def call_external_service():
        ...     # Service call that might fail
        ...     pass
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type[Exception] = Exception,
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type that counts as failure
        """
        self._failure_threshold = failure_threshold
        self._recovery_timeout = timedelta(seconds=recovery_timeout)
        self._expected_exception = expected_exception

        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._state = CircuitState.CLOSED

        self._logger = logger

    def _should_allow_request(self) -> bool:
        """Check if request should be allowed based on circuit state."""
        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if (
                self._last_failure_time
                and datetime.now() - self._last_failure_time >= self._recovery_timeout
            ):
                self._state = CircuitState.HALF_OPEN
                self._logger.info(
                    "Circuit breaker entering HALF_OPEN state",
                    state=self._state.value,
                )
                return True

            self._logger.warning(
                "Circuit breaker is OPEN, blocking request",
                failure_count=self._failure_count,
            )
            return False

        if self._state == CircuitState.HALF_OPEN:
            return True

        return False

    def _on_success(self):
        """Handle successful request."""
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._logger.info(
                "Circuit breaker recovered, entering CLOSED state",
                state=self._state.value,
            )
        else:
            # Reset failure count on success in CLOSED state
            self._failure_count = 0

    def _on_failure(self, exc: Exception):
        """Handle failed request."""
        self._failure_count += 1
        self._last_failure_time = datetime.now()

        if self._failure_count >= self._failure_threshold:
            self._state = CircuitState.OPEN
            self._logger.error(
                "Circuit breaker opened due to failures",
                failure_count=self._failure_count,
                threshold=self._failure_threshold,
                exception=str(exc),
            )

    def __call__(self, func: Callable[P, T]) -> Callable[P, T]:
        """Decorator to apply circuit breaker to a function."""

        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if not self._should_allow_request():
                raise CircuitBreakerError(
                    f"Circuit breaker is {self._state.value}, request blocked"
                )

            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except self._expected_exception as e:
                self._on_failure(e)
                raise

        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if not self._should_allow_request():
                raise CircuitBreakerError(
                    f"Circuit breaker is {self._state.value}, request blocked"
                )

            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except self._expected_exception as e:
                self._on_failure(e)
                raise

        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    def reset(self):
        """Manually reset the circuit breaker to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._logger.info("Circuit breaker manually reset", state=self._state.value)

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count


# Predefined circuit breakers for common services
LLM_CIRCUIT_BREAKER = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception,
)

MCP_CIRCUIT_BREAKER = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30,
    expected_exception=Exception,
)

DATABASE_CIRCUIT_BREAKER = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30,
    expected_exception=Exception,
)


# Retry decorators using tenacity

def retry_on_exception(
    max_attempts: int = 3,
    wait_min: float = 1.0,
    wait_max: float = 10.0,
    exception_types: tuple[type[Exception], ...] = (Exception,),
):
    """Retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        wait_min: Minimum wait time between retries (seconds)
        wait_max: Maximum wait time between retries (seconds)
        exception_types: Exception types to retry on

    Returns:
        Decorator function

    Example:
        >>> @retry_on_exception(max_attempts=3, exception_types=(TimeoutError,))
        ... async def external_call():
        ...     # Service call that might timeout
        ...     pass
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        log_logger = logging.getLogger(__name__)

        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            retryer = retry(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(multiplier=1, min=wait_min, max=wait_max),
                retry=retry_if_exception_type(exception_types),
                before_sleep=before_sleep_log(log_logger, logging.WARNING),
                after=after_log(log_logger, logging.INFO),
            )
            retryed_func = retryer(func)
            return await retryed_func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            retryer = retry(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(multiplier=1, min=wait_min, max=wait_max),
                retry=retry_if_exception_type(exception_types),
                before_sleep=before_sleep_log(log_logger, logging.WARNING),
                after=after_log(log_logger, logging.INFO),
            )
            retryed_func = retryer(func)
            return retryed_func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


def retry_with_jitter(
    max_attempts: int = 3,
    base_wait: float = 1.0,
    max_wait: float = 10.0,
    jitter: bool = True,
    exception_types: tuple[type[Exception], ...] = (Exception,),
):
    """Retry decorator with jitter to avoid thundering herd.

    Args:
        max_attempts: Maximum number of retry attempts
        base_wait: Base wait time (seconds)
        max_wait: Maximum wait time (seconds)
        jitter: Add random jitter to wait time
        exception_types: Exception types to retry on

    Returns:
        Decorator function
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        log_logger = logging.getLogger(__name__)

        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            from tenacity import wait_random_exponential

            retryer = retry(
                stop=stop_after_attempt(max_attempts),
                wait=wait_random_exponential(multiplier=base_wait, max=max_wait) if jitter else wait_exponential(multiplier=1, min=base_wait, max=max_wait),
                retry=retry_if_exception_type(exception_types),
                before_sleep=before_sleep_log(log_logger, logging.WARNING),
            )
            retryed_func = retryer(func)
            return await retryed_func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            from tenacity import wait_random_exponential

            retryer = retry(
                stop=stop_after_attempt(max_attempts),
                wait=wait_random_exponential(multiplier=base_wait, max=max_wait) if jitter else wait_exponential(multiplier=1, min=base_wait, max=max_wait),
                retry=retry_if_exception_type(exception_types),
                before_sleep=before_sleep_log(log_logger, logging.WARNING),
            )
            retryed_func = retryer(func)
            return retryed_func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


# Combined retry and circuit breaker decorator

def resilient(
    max_attempts: int = 3,
    wait_min: float = 1.0,
    wait_max: float = 10.0,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    exception_types: tuple[type[Exception], ...] = (Exception,),
):
    """Combined retry and circuit breaker decorator.

    Applies both retry logic and circuit breaker pattern for maximum resilience.

    Args:
        max_attempts: Maximum number of retry attempts
        wait_min: Minimum wait time between retries (seconds)
        wait_max: Maximum wait time between retries (seconds)
        failure_threshold: Circuit breaker failure threshold
        recovery_timeout: Circuit breaker recovery timeout (seconds)
        exception_types: Exception types to handle

    Returns:
        Decorator function

    Example:
        >>> @resilient(
        ...     max_attempts=3,
        ...     failure_threshold=5,
        ...     recovery_timeout=60,
        ...     exception_types=(TimeoutError, ConnectionError)
        ... )
        ... async def call_external_api():
        ...     # API call with full resilience
        ...     pass
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        # Create circuit breaker
        breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=exception_types[0] if len(exception_types) == 1 else Exception,
        )

        # Apply retry decorator first, then circuit breaker
        retry_decorator = retry_on_exception(
            max_attempts=max_attempts,
            wait_min=wait_min,
            wait_max=wait_max,
            exception_types=exception_types,
        )

        # Apply both decorators
        return breaker(retry_decorator(func))

    return decorator
