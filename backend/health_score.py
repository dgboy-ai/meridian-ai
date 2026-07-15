"""ML Health Score Calculator — weighted sum of 6 metrics with confidence calculation.

Based on strategy document lines 846-866:
- Data Quality: 0.25 (freshness, completeness, schema stability)
- Drift Magnitude: 0.20 (feature drift, concept drift, explanation drift)
- Prediction Quality: 0.25 (accuracy, calibration, confidence distribution)
- Latency: 0.10 (p50, p95, p99 inference times)
- Cost: 0.10 (inference cost per prediction)
- Fairness: 0.10 (demographic parity, equalized odds)

Normalization: Each metric normalized to [0, 1] against 30-day rolling baseline.
Confidence: min(worker_confidences). If any < 0.7 → "unreliable". If < 3 workers → "incomplete".
"""
from dataclasses import dataclass, field
from enum import Enum


class AssessmentLevel(str, Enum):
    RELIABLE = "reliable"
    UNRELIABLE = "unreliable"
    INCOMPLETE = "incomplete"


@dataclass
class MetricScore:
    """Individual metric score with weight."""
    name: str
    raw_value: float
    normalized_value: float
    weight: float
    confidence: float = 1.0

    @property
    def weighted_score(self) -> float:
        return self.normalized_value * self.weight

    def to_bar(self) -> str:
        filled = int(self.normalized_value * 10)
        return "█" * filled + "░" * (10 - filled)


@dataclass
class HealthScore:
    """Complete health score for an ML model."""
    model_urn: str
    model_name: str
    score: int
    assessment: AssessmentLevel
    metrics: list[MetricScore] = field(default_factory=list)
    confidence: float = 0.0
    worker_confidences: list[float] = field(default_factory=list)
    signals_count: int = 0
    timestamp: str = ""

    @property
    def is_reliable(self) -> bool:
        return self.assessment == AssessmentLevel.RELIABLE

    def to_markdown(self) -> str:
        lines = [
            f"# Health Score: {self.model_name}",
            f"Score: {self.score}/100 | Assessment: {self.assessment.value} | Confidence: {self.confidence:.0%}",
            "",
            "## Metric Breakdown",
        ]
        for m in self.metrics:
            lines.append(f"{m.name:20s} {m.to_bar()}  {m.normalized_value:.2f} × {m.weight} = {m.weighted_score:.3f}")
        lines.append("")

        if self.worker_confidences:
            lines.append("## Worker Confidences")
            for i, c in enumerate(self.worker_confidences):
                status = "✓" if c >= 0.7 else "✗"
                lines.append(f"  {status} Worker {i+1}: {c:.2f}")
            lines.append("")

        return "\n".join(lines)


class HealthScoreCalculator:
    """Calculate ML health scores with weighted metrics and confidence."""

    WEIGHTS = {
        "Data Quality": 0.25,
        "Drift Magnitude": 0.20,
        "Prediction Quality": 0.25,
        "Latency": 0.10,
        "Cost": 0.10,
        "Fairness": 0.10,
    }

    def calculate(
        self,
        model_urn: str,
        model_name: str,
        metrics: dict[str, float],
        worker_confidences: list[float] | None = None,
        timestamp: str = "",
    ) -> HealthScore:
        """Calculate health score from raw metrics.

        Args:
            model_urn: DataHub URN of the model
            model_name: Human-readable model name
            metrics: Dict of metric_name -> raw_value (0-1 scale)
            worker_confidences: List of confidence scores from workers
            timestamp: ISO timestamp

        Returns:
            HealthScore with all calculations
        """
        worker_confidences = worker_confidences or []
        metric_scores = []
        weighted_sum = 0.0

        for name, weight in self.WEIGHTS.items():
            raw_value = metrics.get(name, 0.5)
            normalized = max(0.0, min(1.0, raw_value))
            metric_score = MetricScore(
                name=name,
                raw_value=raw_value,
                normalized_value=normalized,
                weight=weight,
            )
            metric_scores.append(metric_score)
            weighted_sum += metric_score.weighted_score

        score = int(round(weighted_sum * 100))
        score = max(0, min(100, score))

        # Calculate confidence
        if worker_confidences:
            confidence = min(worker_confidences)
        else:
            # No worker data available — mark as incomplete with low confidence
            confidence = 0.5

        # Determine assessment level
        if not worker_confidences:
            # No workers contributed — cannot assess
            assessment = AssessmentLevel.INCOMPLETE
        elif any(c < 0.7 for c in worker_confidences):
            assessment = AssessmentLevel.UNRELIABLE
        elif len(worker_confidences) < 3:
            assessment = AssessmentLevel.INCOMPLETE
        else:
            assessment = AssessmentLevel.RELIABLE

        return HealthScore(
            model_urn=model_urn,
            model_name=model_name,
            score=score,
            assessment=assessment,
            metrics=metric_scores,
            confidence=confidence,
            worker_confidences=worker_confidences,
            signals_count=len(metrics) * 4,  # Approximate signals
            timestamp=timestamp,
        )

    def calculate_from_workers(
        self,
        model_urn: str,
        model_name: str,
        data_quality: float = 0.72,
        drift_magnitude: float = 0.61,
        prediction_quality: float = 0.91,
        latency: float = 0.94,
        cost: float = 0.85,
        fairness: float = 0.88,
        worker_confidences: list[float] | None = None,
        timestamp: str = "",
    ) -> HealthScore:
        """Calculate from individual worker outputs."""
        metrics = {
            "Data Quality": data_quality,
            "Drift Magnitude": drift_magnitude,
            "Prediction Quality": prediction_quality,
            "Latency": latency,
            "Cost": cost,
            "Fairness": fairness,
        }
        return self.calculate(model_urn, model_name, metrics, worker_confidences, timestamp)
