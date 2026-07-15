"""Tests for circuit breaker and retry patterns."""
import pytest
import time
from backend.resilience import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
    RetryStrategy,
    with_circuit_breaker,
    with_retry,
)


class TestCircuitBreaker:
    def test_initial_state(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_record_success(self):
        cb = CircuitBreaker()
        cb.record_success()
        assert cb.failure_count == 0

    def test_record_failure(self):
        cb = CircuitBreaker()
        cb.record_failure()
        assert cb.failure_count == 1

    def test_trips_on_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_rejects_when_open(self):
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        assert cb.can_execute() is False

    def test_transitions_to_half_open(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        time.sleep(0.15)
        assert cb.can_execute() is True
        assert cb.state == CircuitState.HALF_OPEN

    def test_recovers_from_half_open(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1, half_open_max_calls=2)
        cb.record_failure()
        time.sleep(0.15)
        cb.can_execute()
        cb.record_success()
        cb.can_execute()
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_trips_from_half_open(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        cb.record_failure()
        time.sleep(0.15)
        cb.can_execute()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_decreases_failures_on_success(self):
        cb = CircuitBreaker(failure_threshold=5)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.failure_count == 1

    def test_get_status(self):
        cb = CircuitBreaker()
        status = cb.get_status()
        assert "state" in status
        assert "failure_count" in status


class TestRetryStrategy:
    def test_delay_increases(self):
        strategy = RetryStrategy(base_delay=1.0, exponential_base=2.0, jitter=False)
        assert strategy.get_delay(0) == 1.0
        assert strategy.get_delay(1) == 2.0
        assert strategy.get_delay(2) == 4.0

    def test_delay_max_cap(self):
        strategy = RetryStrategy(max_delay=5.0, jitter=False)
        assert strategy.get_delay(10) == 5.0

    def test_execute_success(self):
        strategy = RetryStrategy(max_retries=2)
        result = strategy.execute_with_retry(lambda: "success")
        assert result == "success"

    def test_execute_retry_then_success(self):
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("temporary")
            return "success"

        strategy = RetryStrategy(max_retries=3, base_delay=0.01, jitter=False)
        result = strategy.execute_with_retry(flaky)
        assert result == "success"
        assert call_count == 3

    def test_execute_exhausted(self):
        def always_fails():
            raise ValueError("permanent")

        strategy = RetryStrategy(max_retries=2, base_delay=0.01, jitter=False)
        with pytest.raises(ValueError):
            strategy.execute_with_retry(always_fails)


class TestDecoratorPatterns:
    def test_with_circuit_breaker_decorator(self):
        @with_circuit_breaker(failure_threshold=1)
        def flaky_func():
            raise ValueError("test")

        with pytest.raises(ValueError):
            flaky_func()

        # Should be open now
        with pytest.raises(CircuitBreakerOpenError):
            flaky_func()

    def test_with_retry_decorator(self):
        call_count = 0

        @with_retry(max_retries=2, base_delay=0.01)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("temp")
            return "ok"

        result = flaky()
        assert result == "ok"
        assert call_count == 2
