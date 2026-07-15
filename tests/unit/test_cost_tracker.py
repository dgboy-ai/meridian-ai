"""Tests for Cost Attribution Tracker — tokens, compute cost, and ROI."""
import pytest
from backend.cost_tracker import (
    CostTracker,
    WorkerCost,
    InvestigationCost,
    TOKEN_PRICING,
)


class TestWorkerCost:
    def test_to_dict_fields(self):
        wc = WorkerCost(worker_id="root_cause", tokens_in=100, tokens_out=50, duration_ms=123.45, model_used="llama-3.3-70b-versatile", cost_usd=0.0)
        d = wc.to_dict()
        assert d["worker_id"] == "root_cause"
        assert d["tokens_in"] == 100
        assert d["tokens_out"] == 50
        assert d["duration_ms"] == 123.45
        assert d["model_used"] == "llama-3.3-70b-versatile"
        assert d["cost_usd"] == 0.0

    def test_defaults(self):
        wc = WorkerCost(worker_id="test")
        assert wc.tokens_in == 0
        assert wc.tokens_out == 0
        assert wc.duration_ms == 0.0
        assert wc.cost_usd == 0.0


class TestInvestigationCost:
    def test_to_dict_structure(self):
        ic = InvestigationCost(incident_id="42")
        d = ic.to_dict()
        assert d["incident_id"] == "42"
        assert "total_tokens_in" in d
        assert "total_cost_usd" in d
        assert "worker_costs" in d
        assert "roi_percentage" in d

    def test_calculate_roi_zero_cost(self):
        ic = InvestigationCost(incident_id="42")
        assert ic.calculate_roi() == 0.0

    def test_calculate_roi_positive(self):
        ic = InvestigationCost(incident_id="42", total_cost_usd=0.03, time_saved_minutes=45.0)
        roi = ic.calculate_roi()
        assert roi > 0

    def test_calculate_roi_no_time_saved(self):
        ic = InvestigationCost(incident_id="42", total_cost_usd=0.03, time_saved_minutes=0.0)
        assert ic.calculate_roi() == 0.0

    def test_cost_per_minute_saved_zero_time(self):
        ic = InvestigationCost(incident_id="42")
        assert ic.cost_per_minute_saved() == 0.0

    def test_cost_per_minute_saved(self):
        ic = InvestigationCost(incident_id="42", total_cost_usd=0.10, time_saved_minutes=10.0)
        assert ic.cost_per_minute_saved() == pytest.approx(0.01, abs=0.001)

    def test_manual_time_default(self):
        ic = InvestigationCost(incident_id="42")
        assert ic.manual_time_minutes == 45.0


class TestTokenPricing:
    def test_all_models_have_pricing(self):
        expected_models = [
            "openai/gpt-oss-120b", "qwen/qwen3.6-27b", "qwen/qwen3-32b",
            "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "default",
        ]
        for model in expected_models:
            assert model in TOKEN_PRICING

    def test_pricing_has_input_output(self):
        for model, pricing in TOKEN_PRICING.items():
            assert "input" in pricing
            assert "output" in pricing

    def test_free_tier_pricing(self):
        for model, pricing in TOKEN_PRICING.items():
            assert pricing["input"] >= 0
            assert pricing["output"] >= 0


class TestCostTracker:
    def test_init(self):
        tracker = CostTracker()
        assert tracker._total_cost_usd == 0.0
        assert tracker._total_investigations == 0

    def test_start_investigation(self):
        tracker = CostTracker()
        cost = tracker.start_investigation("42")
        assert cost.incident_id == "42"
        assert cost.start_time > 0
        assert tracker._total_investigations == 1

    def test_start_multiple_investigations(self):
        tracker = CostTracker()
        tracker.start_investigation("42")
        tracker.start_investigation("43")
        assert tracker._total_investigations == 2

    def test_record_worker_cost(self):
        tracker = CostTracker()
        tracker.start_investigation("42")
        wc = tracker.record_worker_cost(
            "42", "root_cause", tokens_in=100, tokens_out=50,
            model_used="llama-3.3-70b-versatile", duration_ms=500.0,
        )
        assert wc.worker_id == "root_cause"
        assert wc.tokens_in == 100
        assert wc.tokens_out == 50

    def test_record_worker_cost_accumulates(self):
        tracker = CostTracker()
        tracker.start_investigation("42")
        tracker.record_worker_cost("42", "w1", tokens_in=100, tokens_out=50)
        tracker.record_worker_cost("42", "w2", tokens_in=200, tokens_out=100)
        cost = tracker.get_investigation_cost("42")
        assert cost.total_tokens_in == 300
        assert cost.total_tokens_out == 150
        assert len(cost.worker_costs) == 2

    def test_record_worker_cost_unknown_investigation(self):
        tracker = CostTracker()
        wc = tracker.record_worker_cost("unknown", "w1", tokens_in=100)
        assert wc.worker_id == "w1"

    def test_end_investigation(self):
        tracker = CostTracker()
        tracker.start_investigation("42")
        tracker.record_worker_cost("42", "w1", tokens_in=100, tokens_out=50, duration_ms=100.0)
        result = tracker.end_investigation("42", manual_time_minutes=45.0)
        assert result.end_time > 0
        assert result.time_saved_minutes >= 0

    def test_end_investigation_unknown_returns_empty(self):
        tracker = CostTracker()
        result = tracker.end_investigation("unknown")
        assert result.incident_id == "unknown"
        assert result.total_cost_usd == 0.0

    def test_get_investigation_cost(self):
        tracker = CostTracker()
        tracker.start_investigation("42")
        cost = tracker.get_investigation_cost("42")
        assert cost is not None
        assert cost.incident_id == "42"

    def test_get_investigation_cost_not_found(self):
        tracker = CostTracker()
        assert tracker.get_investigation_cost("999") is None

    def test_get_summary(self):
        tracker = CostTracker()
        tracker.start_investigation("42")
        tracker.record_worker_cost("42", "w1", tokens_in=100, tokens_out=50)
        tracker.end_investigation("42")
        summary = tracker.get_summary()
        assert summary["total_investigations"] == 1
        assert "total_cost_usd" in summary
        assert "total_time_saved_minutes" in summary

    def test_get_roi_summary(self):
        tracker = CostTracker()
        tracker.start_investigation("42")
        tracker.record_worker_cost("42", "w1", tokens_in=100, tokens_out=50, duration_ms=50.0)
        tracker.end_investigation("42", manual_time_minutes=45.0, incidents_prevented=1)
        roi = tracker.get_roi_summary()
        assert "value_of_time_saved_usd" in roi
        assert "roi_percentage" in roi
        assert "engineer_hourly_rate" in roi
        assert roi["engineer_hourly_rate"] == 75.0

    def test_summary_defaults_empty(self):
        tracker = CostTracker()
        summary = tracker.get_summary()
        assert summary["total_investigations"] == 0
        assert summary["total_cost_usd"] == 0.0
        assert summary["avg_cost_per_investigation"] == 0.0
