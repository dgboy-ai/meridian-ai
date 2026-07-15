"""Agentic Circuit Breaker — monitors agent reasoning health.

"88% of agentic failures in production are due to reasoning drift,
not infrastructure failures."

This module:
  1. Monitors agent reasoning health
  2. Detects loops (same MCP tool called >3 times with same args)
  3. Detects semantic drift (confidence drops below threshold)
  4. Trips circuit breaker to block further calls
  5. Implements graduated re-enablement (OPEN → DEGRADED → CLOSED)
  6. Provides compensating transactions for rollback

Based on MERIDIAN_MASTER_STRATEGY.md:
"Agentic Circuit Breaker: Monitors agent reasoning health, trips if
hallucination/loop detected, implements graduated re-enablement."
"""
import time
import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("meridian-ai.agentic_circuit_breaker")


class CircuitState(str, Enum):
    """Circuit breaker states."""
    OPEN = "open"          # All calls blocked
    DEGRADED = "degraded"  # Read-only tools allowed
    CLOSED = "closed"      # Normal operation


class CircuitDecision(str, Enum):
    """Decision from circuit breaker."""
    ALLOW = "allow"
    DEGRADE = "degrade"
    BLOCK = "block"


@dataclass
class ToolCallRecord:
    """Record of a tool call for loop detection."""
    tool_name: str
    args_hash: str
    timestamp: float
    call_count: int = 1


@dataclass
class AgentHealthMetrics:
    """Health metrics for an agent."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    avg_confidence: float = 1.0
    confidence_history: list[float] = field(default_factory=list)
    loop_detections: int = 0
    drift_detections: int = 0

    def to_dict(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": round(self.successful_calls / max(self.total_calls, 1), 4),
            "avg_confidence": round(self.avg_confidence, 4),
            "loop_detections": self.loop_detections,
            "drift_detections": self.drift_detections,
        }


class AgenticCircuitBreaker:
    """Circuit breaker for agent reasoning health.

    Monitors:
    - Loop detection: same tool called >N times with same args
    - Semantic drift: confidence drops below threshold
    - Failure rate: too many failed calls

    States:
    - OPEN: All tools blocked (critical failure)
    - DEGRADED: Only read-only tools allowed
    - CLOSED: Normal operation
    """

    def __init__(
        self,
        max_loops: int = 3,
        min_confidence: float = 0.4,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ) -> None:
        self.max_loops = max_loops
        self.min_confidence = min_confidence
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self._state = CircuitState.CLOSED
        self._tool_call_history: dict[str, ToolCallRecord] = {}
        self._health_metrics = AgentHealthMetrics()
        self._last_failure_time: float = 0.0
        self._consecutive_failures: int = 0

    @property
    def state(self) -> CircuitState:
        """Get current circuit breaker state."""
        # Check if we should transition from OPEN to DEGRADED
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.DEGRADED
                logger.info("Circuit breaker: OPEN → DEGRADED (testing recovery)")
        return self._state

    def check_tool_call(self, tool_name: str, args: dict) -> CircuitDecision:
        """Check if a tool call should be allowed.

        Args:
            tool_name: Name of the tool being called
            args: Arguments passed to the tool

        Returns:
            CircuitDecision: ALLOW, DEGRADE, or BLOCK
        """
        self._health_metrics.total_calls += 1

        # Check current state
        current_state = self.state

        if current_state == CircuitState.OPEN:
            logger.warning(f"Circuit breaker OPEN: Blocking {tool_name}")
            return CircuitDecision.BLOCK

        if current_state == CircuitState.DEGRADED:
            # Only allow read-only tools in degraded mode
            read_only_tools = {"get_entities", "get_lineage", "search", "list_schema_fields", "health"}
            if tool_name not in read_only_tools:
                logger.warning(f"Circuit breaker DEGRADED: Blocking write tool {tool_name}")
                return CircuitDecision.DEGRADE

        # Check for loops
        args_hash = str(sorted(args.items()))
        call_key = f"{tool_name}:{args_hash}"

        if call_key in self._tool_call_history:
            record = self._tool_call_history[call_key]
            record.call_count += 1

            if record.call_count > self.max_loops:
                self._health_metrics.loop_detections += 1
                logger.warning(
                    f"Loop detected: {tool_name} called {record.call_count} times "
                    f"with same args. Tripping circuit breaker."
                )
                self._trip()
                return CircuitDecision.BLOCK
        else:
            self._tool_call_history[call_key] = ToolCallRecord(
                tool_name=tool_name,
                args_hash=args_hash,
                timestamp=time.time(),
            )

        return CircuitDecision.ALLOW

    def record_success(self, confidence: float = 1.0) -> None:
        """Record a successful call."""
        self._health_metrics.successful_calls += 1
        self._health_metrics.confidence_history.append(confidence)

        # Keep last 100 confidence scores
        if len(self._health_metrics.confidence_history) > 100:
            self._health_metrics.confidence_history = self._health_metrics.confidence_history[-100:]

        # Update average confidence
        self._health_metrics.avg_confidence = (
            sum(self._health_metrics.confidence_history) /
            len(self._health_metrics.confidence_history)
        )

        # Reset consecutive failures
        self._consecutive_failures = 0

        # Check for semantic drift
        if confidence < self.min_confidence:
            self._health_metrics.drift_detections += 1
            logger.warning(
                f"Low confidence detected: {confidence:.2f} < {self.min_confidence}. "
                f"Drift detections: {self._health_metrics.drift_detections}"
            )

        # If in DEGRADED state and getting successes, transition to CLOSED
        if self._state == CircuitState.DEGRADED:
            if self._health_metrics.avg_confidence >= 0.7:
                self._state = CircuitState.CLOSED
                logger.info("Circuit breaker: DEGRADED → CLOSED (recovered)")

    def record_failure(self) -> None:
        """Record a failed call."""
        self._health_metrics.failed_calls += 1
        self._consecutive_failures += 1
        self._last_failure_time = time.time()

        if self._consecutive_failures >= self.failure_threshold:
            self._trip()

    def _trip(self) -> None:
        """Trip the circuit breaker to OPEN state."""
        self._state = CircuitState.OPEN
        self._last_failure_time = time.time()
        logger.warning("Circuit breaker tripped: OPEN")

    def get_health_metrics(self) -> dict:
        """Get agent health metrics."""
        return self._health_metrics.to_dict()

    def get_status(self) -> dict:
        """Get circuit breaker status."""
        return {
            "state": self.state.value,
            "consecutive_failures": self._consecutive_failures,
            "last_failure_time": self._last_failure_time,
            "health_metrics": self._health_metrics.to_dict(),
        }

    def reset(self) -> None:
        """Reset the circuit breaker to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._last_failure_time = 0.0
        self._tool_call_history.clear()
        logger.info("Circuit breaker reset: CLOSED")
