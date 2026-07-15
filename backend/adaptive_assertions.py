"""Adaptive Assertions — learn from historical patterns.

"AI analyzes historical patterns to suggest freshness thresholds, volume
expectations, and quality checks with one-click setup. Assertions adapt
automatically as your data evolves."

This module:
  1. Tracks historical patterns for each dataset
  2. Computes dynamic thresholds based on historical data
  3. Adapts assertions as data patterns change
  4. Generates quality checks that learn from past incidents
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import mean, stdev

logger = logging.getLogger("meridian-ai.adaptive_assertions")


@dataclass
class HistoricalPattern:
    """Historical pattern for a dataset metric."""
    metric_name: str
    values: list[float] = field(default_factory=list)
    timestamps: list[str] = field(default_factory=list)
    threshold: float = 0.0
    is_anomaly: bool = False

    def add_observation(self, value: float, timestamp: str):
        """Add a new observation to the pattern."""
        self.values.append(value)
        self.timestamps.append(timestamp)
        # Keep last 100 observations
        if len(self.values) > 100:
            self.values = self.values[-100:]
            self.timestamps = self.timestamps[-100:]

    def compute_threshold(self) -> float:
        """Compute dynamic threshold based on historical data."""
        if len(self.values) < 3:
            # Not enough data, use default
            return 0.0

        # Compute mean and standard deviation
        avg = mean(self.values)
        std = stdev(self.values) if len(self.values) > 1 else 0.0

        # Threshold = mean + 2 * std (95% confidence interval)
        self.threshold = avg + 2 * std
        return self.threshold

    def check_anomaly(self, current_value: float) -> bool:
        """Check if current value is an anomaly based on threshold."""
        if self.threshold == 0:
            self.compute_threshold()

        self.is_anomaly = abs(current_value - mean(self.values)) > 2 * (stdev(self.values) if len(self.values) > 1 else 0.0)
        return self.is_anomaly

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "observations": len(self.values),
            "threshold": round(self.threshold, 4),
            "is_anomaly": self.is_anomaly,
            "latest_value": self.values[-1] if self.values else 0.0,
            "mean": round(mean(self.values), 4) if self.values else 0.0,
            "std": round(stdev(self.values), 4) if len(self.values) > 1 else 0.0,
        }


@dataclass
class AdaptiveAssertion:
    """An assertion that adapts based on historical patterns."""
    assertion_id: str
    dataset_urn: str
    metric_name: str
    pattern: HistoricalPattern
    enabled: bool = True
    created_at: str = ""
    last_checked: str = ""
    violation_count: int = 0

    def to_dict(self) -> dict:
        return {
            "assertion_id": self.assertion_id,
            "dataset_urn": self.dataset_urn,
            "metric_name": self.metric_name,
            "enabled": self.enabled,
            "pattern": self.pattern.to_dict(),
            "violation_count": self.violation_count,
        }


class AdaptiveAssertionManager:
    """Manage adaptive assertions that learn from historical patterns."""

    def __init__(self):
        self._patterns: dict[str, HistoricalPattern] = {}
        self._assertions: dict[str, AdaptiveAssertion] = {}

    def record_observation(
        self,
        dataset_urn: str,
        metric_name: str,
        value: float,
        timestamp: str | None = None,
    ):
        """Record an observation for a dataset metric."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()

        pattern_key = f"{dataset_urn}:{metric_name}"
        if pattern_key not in self._patterns:
            self._patterns[pattern_key] = HistoricalPattern(metric_name=metric_name)

        self._patterns[pattern_key].add_observation(value, timestamp)

        # Update threshold if we have enough data
        if len(self._patterns[pattern_key].values) >= 3:
            self._patterns[pattern_key].compute_threshold()

    def check_assertion(
        self,
        dataset_urn: str,
        metric_name: str,
        current_value: float,
    ) -> dict:
        """Check if current value violates adaptive assertion.

        Returns:
            dict with assertion result
        """
        pattern_key = f"{dataset_urn}:{metric_name}"
        pattern = self._patterns.get(pattern_key)

        if not pattern:
            return {
                "status": "no_pattern",
                "message": f"No historical pattern for {metric_name}",
                "assertion_id": None,
            }

        # Check for anomaly
        is_anomaly = pattern.check_anomaly(current_value)

        # Get or create assertion
        assertion_id = f"assertion-{dataset_urn.split(':')[-2]}-{metric_name}"
        if assertion_id not in self._assertions:
            self._assertions[assertion_id] = AdaptiveAssertion(
                assertion_id=assertion_id,
                dataset_urn=dataset_urn,
                metric_name=metric_name,
                pattern=pattern,
                created_at=datetime.now(timezone.utc).isoformat(),
            )

        assertion = self._assertions[assertion_id]
        assertion.last_checked = datetime.now(timezone.utc).isoformat()

        if is_anomaly:
            assertion.violation_count += 1

        return {
            "status": "violation" if is_anomaly else "passed",
            "assertion_id": assertion_id,
            "metric_name": metric_name,
            "current_value": current_value,
            "threshold": pattern.threshold,
            "mean": mean(pattern.values) if pattern.values else 0.0,
            "is_anomaly": is_anomaly,
            "violation_count": assertion.violation_count,
            "observations": len(pattern.values),
        }

    def get_assertions_for_dataset(self, dataset_urn: str) -> list[dict]:
        """Get all assertions for a dataset."""
        assertions = []
        for assertion in self._assertions.values():
            if assertion.dataset_urn == dataset_urn:
                assertions.append(assertion.to_dict())
        return assertions

    def get_pattern_stats(self, dataset_urn: str) -> dict:
        """Get pattern statistics for a dataset."""
        patterns = {}
        for key, pattern in self._patterns.items():
            if key.startswith(dataset_urn):
                metric_name = key.split(":")[-1]
                patterns[metric_name] = pattern.to_dict()
        return patterns

    def suggest_assertions(self, dataset_urn: str, fields: list[dict]) -> list[dict]:
        """Suggest assertions based on dataset schema.

        Args:
            dataset_urn: URN of the dataset
            fields: List of field definitions

        Returns:
            List of suggested assertions
        """
        suggestions = []

        for field_def in fields:
            field_name = field_def.get("name", "")
            field_type = field_def.get("type", "")

            # Suggest freshness assertion for timestamp columns
            if "TIMESTAMP" in field_type.upper() or "DATE" in field_type.upper():
                suggestions.append({
                    "type": "freshness",
                    "metric": f"{field_name}_freshness",
                    "description": f"Check freshness of {field_name}",
                    "threshold": "1 hour",
                })

            # Suggest null check for required columns
            if field_name in ["user_id", "event_id", "timestamp"]:
                suggestions.append({
                    "type": "null_check",
                    "metric": f"{field_name}_null_rate",
                    "description": f"Check null rate of {field_name}",
                    "threshold": "0%",
                })

            # Suggest range check for numeric columns
            if "INT" in field_type.upper() or "FLOAT" in field_type.upper():
                suggestions.append({
                    "type": "range_check",
                    "metric": f"{field_name}_range",
                    "description": f"Check value range of {field_name}",
                    "threshold": "adaptive",
                })

        return suggestions
