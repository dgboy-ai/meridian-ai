"""Tests for Health Score Calculator."""
import pytest
from backend.health_score import HealthScoreCalculator, HealthScore, MetricScore, AssessmentLevel


class TestHealthScoreCalculator:
    def test_calculate_basic(self):
        calc = HealthScoreCalculator()
        score = calc.calculate(
            model_urn="urn:li:mlModel:test",
            model_name="test_model",
            metrics={"Data Quality": 0.8, "Drift Magnitude": 0.6, "Prediction Quality": 0.9},
        )
        assert 0 <= score.score <= 100
        assert score.model_name == "test_model"

    def test_calculate_all_metrics(self):
        calc = HealthScoreCalculator()
        score = calc.calculate(
            model_urn="urn:li:mlModel:test",
            model_name="test_model",
            metrics={
                "Data Quality": 1.0,
                "Drift Magnitude": 1.0,
                "Prediction Quality": 1.0,
                "Latency": 1.0,
                "Cost": 1.0,
                "Fairness": 1.0,
            },
        )
        assert score.score == 100

    def test_calculate_zero_metrics(self):
        calc = HealthScoreCalculator()
        score = calc.calculate(
            model_urn="urn:li:mlModel:test",
            model_name="test_model",
            metrics={
                "Data Quality": 0.0,
                "Drift Magnitude": 0.0,
                "Prediction Quality": 0.0,
                "Latency": 0.0,
                "Cost": 0.0,
                "Fairness": 0.0,
            },
        )
        assert score.score == 0

    def test_confidence_calculation(self):
        calc = HealthScoreCalculator()
        score = calc.calculate(
            model_urn="urn:li:mlModel:test",
            model_name="test_model",
            metrics={"Data Quality": 0.8},
            worker_confidences=[0.9, 0.85, 0.92],
        )
        assert score.confidence == 0.85  # min of confidences

    def test_assessment_reliable(self):
        calc = HealthScoreCalculator()
        score = calc.calculate(
            model_urn="urn:li:mlModel:test",
            model_name="test_model",
            metrics={"Data Quality": 0.8},
            worker_confidences=[0.9, 0.85, 0.92],
        )
        assert score.assessment == AssessmentLevel.RELIABLE

    def test_assessment_unreliable(self):
        calc = HealthScoreCalculator()
        score = calc.calculate(
            model_urn="urn:li:mlModel:test",
            model_name="test_model",
            metrics={"Data Quality": 0.8},
            worker_confidences=[0.9, 0.6, 0.92],
        )
        assert score.assessment == AssessmentLevel.UNRELIABLE

    def test_assessment_incomplete(self):
        calc = HealthScoreCalculator()
        score = calc.calculate(
            model_urn="urn:li:mlModel:test",
            model_name="test_model",
            metrics={"Data Quality": 0.8},
            worker_confidences=[0.9, 0.85],
        )
        assert score.assessment == AssessmentLevel.INCOMPLETE

    def test_calculate_from_workers(self):
        calc = HealthScoreCalculator()
        score = calc.calculate_from_workers(
            model_urn="urn:li:mlModel:test",
            model_name="test_model",
            data_quality=0.72,
            drift_magnitude=0.61,
            prediction_quality=0.91,
            latency=0.94,
        )
        assert 0 <= score.score <= 100
        assert len(score.metrics) == 6

    def test_metric_score_weighted(self):
        m = MetricScore(name="test", raw_value=0.8, normalized_value=0.8, weight=0.25)
        assert m.weighted_score == 0.2

    def test_metric_bar(self):
        m = MetricScore(name="test", raw_value=0.5, normalized_value=0.5, weight=0.25)
        bar = m.to_bar()
        assert "█" in bar
        assert "░" in bar
        assert len(bar) == 10

    def test_health_score_to_markdown(self):
        calc = HealthScoreCalculator()
        score = calc.calculate(
            model_urn="urn:li:mlModel:test",
            model_name="test_model",
            metrics={"Data Quality": 0.8},
            worker_confidences=[0.9, 0.85, 0.92],
        )
        md = score.to_markdown()
        assert "test_model" in md
        assert "Data Quality" in md
        assert "Worker Confidences" in md


class TestMetricNormalization:
    def test_clamp_above_one(self):
        calc = HealthScoreCalculator()
        score = calc.calculate(
            model_urn="urn:li:mlModel:test",
            model_name="test_model",
            metrics={"Data Quality": 1.5},
        )
        assert score.metrics[0].normalized_value == 1.0

    def test_clamp_below_zero(self):
        calc = HealthScoreCalculator()
        score = calc.calculate(
            model_urn="urn:li:mlModel:test",
            model_name="test_model",
            metrics={"Data Quality": -0.5},
        )
        assert score.metrics[0].normalized_value == 0.0
