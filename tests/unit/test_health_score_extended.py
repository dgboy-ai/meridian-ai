"""Extended tests for Health Score Calculator."""
import pytest
from backend.health_score import HealthScoreCalculator, HealthScore, MetricScore, AssessmentLevel


class TestHealthScoreCalculatorExtended:
    def test_weights_sum_to_one(self):
        calc = HealthScoreCalculator()
        total = sum(calc.WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_all_metrics_covered(self):
        calc = HealthScoreCalculator()
        assert len(calc.WEIGHTS) == 6
        assert "Data Quality" in calc.WEIGHTS
        assert "Drift Magnitude" in calc.WEIGHTS
        assert "Prediction Quality" in calc.WEIGHTS
        assert "Latency" in calc.WEIGHTS
        assert "Cost" in calc.WEIGHTS
        assert "Fairness" in calc.WEIGHTS

    def test_score_range(self):
        calc = HealthScoreCalculator()
        for dq in [0.0, 0.5, 1.0]:
            for dm in [0.0, 0.5, 1.0]:
                for pq in [0.0, 0.5, 1.0]:
                    score = calc.calculate(
                        model_urn="test", model_name="test",
                        metrics={"Data Quality": dq, "Drift Magnitude": dm, "Prediction Quality": pq},
                    )
                    assert 0 <= score.score <= 100

    def test_confidence_below_threshold_flags_unreliable(self):
        calc = HealthScoreCalculator()
        score = calc.calculate(
            model_urn="test", model_name="test",
            metrics={"Data Quality": 0.8},
            worker_confidences=[0.9, 0.6, 0.9],
        )
        assert score.assessment == AssessmentLevel.UNRELIABLE

    def test_confidence_exactly_threshold(self):
        calc = HealthScoreCalculator()
        score = calc.calculate(
            model_urn="test", model_name="test",
            metrics={"Data Quality": 0.8},
            worker_confidences=[0.7, 0.8, 0.9],
        )
        assert score.assessment == AssessmentLevel.RELIABLE

    def test_incomplete_with_two_workers(self):
        calc = HealthScoreCalculator()
        score = calc.calculate(
            model_urn="test", model_name="test",
            metrics={"Data Quality": 0.8},
            worker_confidences=[0.9, 0.8],
        )
        assert score.assessment == AssessmentLevel.INCOMPLETE

    def test_metric_score_bar_visualization(self):
        m = MetricScore(name="test", raw_value=0.0, normalized_value=0.0, weight=0.25)
        assert m.to_bar() == "░░░░░░░░░░"

        m2 = MetricScore(name="test", raw_value=1.0, normalized_value=1.0, weight=0.25)
        assert m2.to_bar() == "██████████"

        m3 = MetricScore(name="test", raw_value=0.5, normalized_value=0.5, weight=0.25)
        assert m3.to_bar() == "█████░░░░░"

    def test_health_score_markdown_output(self):
        calc = HealthScoreCalculator()
        score = calc.calculate(
            model_urn="urn:li:mlModel:test",
            model_name="churn_model_v3",
            metrics={
                "Data Quality": 0.72,
                "Drift Magnitude": 0.61,
                "Prediction Quality": 0.91,
                "Latency": 0.94,
                "Cost": 0.85,
                "Fairness": 0.88,
            },
            worker_confidences=[0.95, 0.92, 0.88],
            timestamp="2026-07-12T00:00:00Z",
        )
        md = score.to_markdown()
        assert "churn_model_v3" in md
        assert "Data Quality" in md
        assert "Worker Confidences" in md
        assert "0.88" in md  # min confidence

    def test_calculate_from_workers_defaults(self):
        calc = HealthScoreCalculator()
        score = calc.calculate_from_workers(
            model_urn="test", model_name="test",
        )
        assert 0 <= score.score <= 100
        assert len(score.metrics) == 6
