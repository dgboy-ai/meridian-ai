"""Circuit breaker and retry patterns for enterprise resilience."""
import time
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger("meridian-ai.resilience")


class CircuitState(str, Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance.

    States:
    - CLOSED: Normal operation, calls pass through
    - OPEN: Failing, calls are rejected immediately
    - HALF_OPEN: Testing recovery, limited calls allowed
    """
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3

    # Internal state
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0
    half_open_calls: int = 0

    def record_success(self) -> None:
        """Record a successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_max_calls:
                self._reset()
                logger.info("Circuit breaker: HALF_OPEN → CLOSED (recovered)")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self) -> None:
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self._trip()
            logger.warning("Circuit breaker: HALF_OPEN → OPEN (still failing)")
        elif self.failure_count >= self.failure_threshold:
            self._trip()
            logger.warning(f"Circuit breaker: CLOSED → OPEN (failures: {self.failure_count})")

    def _trip(self) -> None:
        """Trip the circuit breaker to OPEN state."""
        self.state = CircuitState.OPEN
        self.half_open_calls = 0

    def _reset(self) -> None:
        """Reset to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0

    def can_execute(self) -> bool:
        """Check if a call can be executed."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                logger.info("Circuit breaker: OPEN → HALF_OPEN (testing recovery)")
                return True
            return False
        else:  # HALF_OPEN
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False

    def get_status(self) -> dict:
        """Get circuit breaker status."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
        }


class RetryStrategy:
    """Configurable retry strategy with exponential backoff."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            import random
            delay = delay * (0.5 + random.random())

        return delay

    def execute_with_retry(
        self,
        func: Callable,
        *args,
        circuit_breaker: Optional[CircuitBreaker] = None,
        **kwargs,
    ) -> Any:
        """Execute function with retry logic."""
        last_error = None

        for attempt in range(self.max_retries + 1):
            # Check circuit breaker
            if circuit_breaker and not circuit_breaker.can_execute():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. State: {circuit_breaker.get_status()}"
                )

            try:
                result = func(*args, **kwargs)
                if circuit_breaker:
                    circuit_breaker.record_success()
                return result
            except Exception as e:
                last_error = e
                if circuit_breaker:
                    circuit_breaker.record_failure()

                if attempt < self.max_retries:
                    delay = self.get_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed: {e}")

        raise last_error


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


def with_circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
):
    """Decorator to add circuit breaker to a function."""
    breaker = CircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
    )

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not breaker.can_execute():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN for {func.__name__}"
                )
            try:
                result = func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception:
                breaker.record_failure()
                raise
        wrapper.circuit_breaker = breaker  # type: ignore[attr-defined]
        return wrapper
    return decorator


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    exponential_base: float = 2.0,
):
    """Decorator to add retry logic to a function."""
    strategy = RetryStrategy(
        max_retries=max_retries,
        base_delay=base_delay,
        exponential_base=exponential_base,
    )

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return strategy.execute_with_retry(func, *args, **kwargs)
        return wrapper
    return decorator
