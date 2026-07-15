"""Extended tests for Resilience patterns."""
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


class TestCircuitBreakerExtended:
    def test_initial_state_closed(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.can_execute() is True

    def test_trip_on_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.can_execute() is False

    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        time.sleep(0.15)
        assert cb.can_execute() is True
        assert cb.state == CircuitState.HALF_OPEN

    def test_recover_from_half_open(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1, half_open_max_calls=2)
        cb.record_failure()
        time.sleep(0.15)
        cb.can_execute()
        cb.record_success()
        cb.can_execute()
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_fail_from_half_open(self):
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
        assert "success_count" in status
        assert "last_failure_time" in status


class TestRetryStrategyExtended:
    def test_delay_increases_exponentially(self):
        strategy = RetryStrategy(base_delay=1.0, exponential_base=2.0, jitter=False)
        assert strategy.get_delay(0) == 1.0
        assert strategy.get_delay(1) == 2.0
        assert strategy.get_delay(2) == 4.0
        assert strategy.get_delay(3) == 8.0

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

    def test_with_circuit_breaker(self):
        cb = CircuitBreaker(failure_threshold=2)
        strategy = RetryStrategy(max_retries=1, base_delay=0.01)
        result = strategy.execute_with_retry(lambda: "ok", circuit_breaker=cb)
        assert result == "ok"
        assert cb.failure_count == 0

    def test_with_circuit_breaker_open(self):
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        strategy = RetryStrategy(max_retries=1, base_delay=0.01)
        with pytest.raises(CircuitBreakerOpenError):
            strategy.execute_with_retry(lambda: "ok", circuit_breaker=cb)


class TestDecoratorPatternsExtended:
    def test_with_circuit_breaker_decorator_success(self):
        @with_circuit_breaker(failure_threshold=2)
        def ok_func():
            return "ok"

        assert ok_func() == "ok"

    def test_with_circuit_breaker_decorator_failure(self):
        @with_circuit_breaker(failure_threshold=1)
        def fail_func():
            raise ValueError("test")

        with pytest.raises(ValueError):
            fail_func()

        with pytest.raises(CircuitBreakerOpenError):
            fail_func()

    def test_with_retry_decorator_success(self):
        call_count = 0

        @with_retry(max_retries=2, base_delay=0.01)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("temp")
            return "ok"

        assert flaky() == "ok"
        assert call_count == 2

    def test_with_retry_decorator_exhausted(self):
        @with_retry(max_retries=1, base_delay=0.01)
        def always_fails():
            raise ValueError("permanent")

        with pytest.raises(ValueError):
            always_fails()
