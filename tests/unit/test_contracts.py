"""Contract tests — verify API response schemas match expected shapes."""
import pytest
from backend.schemas import (
    HealthResponse, ReadinessResponse, LivenessResponse, MetricsResponse,
    IncidentsResponse, IncidentSummary, ResolutionTimesResponse,
    ResolutionTimeEntry, ModelResponse, ErrorResponse, SSEEvent,
)


class TestHealthContracts:
    def test_health_response_shape(self):
        r = HealthResponse(
            status="healthy", service="test", version="1.0.0",
            mode="mock", groq_connected=True, datahub_mock=True,
        )
        d = r.model_dump()
        assert d["status"] == "healthy"
        assert d["service"] == "test"
        assert d["groq_connected"] is True

    def test_readiness_response_shape(self):
        r = ReadinessResponse(status="ready", checks={"db": True})
        d = r.model_dump()
        assert d["status"] == "ready"
        assert "db" in d["checks"]

    def test_liveness_response_shape(self):
        r = LivenessResponse(status="alive")
        assert r.model_dump()["status"] == "alive"

    def test_metrics_response_shape(self):
        r = MetricsResponse(
            uptime_seconds=100.0, request_count=10, error_count=1,
            avg_latency_ms=50.0, p50_latency_ms=40.0, p95_latency_ms=80.0,
            p99_latency_ms=95.0, error_rate=0.1, app="test", version="1.0.0",
            mode="mock",
        )
        d = r.model_dump()
        assert d["uptime_seconds"] == 100.0
        assert d["request_count"] == 10
        assert d["p99_latency_ms"] == 95.0


class TestIncidentContracts:
    def test_incident_summary_shape(self):
        s = IncidentSummary(
            id="42", title="Test", severity="high", status="open",
            detected="2026-01-01", duration_seconds=300,
            affected_models=["model_a"], pattern_id="test-pattern",
        )
        d = s.model_dump()
        assert d["id"] == "42"
        assert d["severity"] == "high"
        assert len(d["affected_models"]) == 1

    def test_incidents_response_shape(self):
        r = IncidentsResponse(incidents=[])
        assert r.model_dump()["incidents"] == []

    def test_resolution_time_entry_shape(self):
        e = ResolutionTimeEntry(
            id="1", duration_minutes=5, date="2026-01-01", pattern="test",
        )
        d = e.model_dump()
        assert d["duration_minutes"] == 5

    def test_resolution_times_response_shape(self):
        r = ResolutionTimesResponse(
            incidents=[], trend="decreasing", predicted_next=3,
        )
        d = r.model_dump()
        assert d["trend"] == "decreasing"
        assert d["predicted_next"] == 3


class TestModelContracts:
    def test_model_response_shape(self):
        r = ModelResponse(
            urn="urn:li:mlModel:test", name="test", type="mlModel",
            platform="mlflow", owner="team", tags=["prod"],
            health_score=85, confidence=0.9,
        )
        d = r.model_dump()
        assert d["health_score"] == 85
        assert d["confidence"] == 0.9


class TestErrorContracts:
    def test_error_response_shape(self):
        r = ErrorResponse(error="not found", detail="missing")
        d = r.model_dump()
        assert d["error"] == "not found"
        assert d["detail"] == "missing"

    def test_error_response_optional_fields(self):
        r = ErrorResponse(error="fail")
        d = r.model_dump()
        assert d["detail"] is None
        assert d["path"] is None


class TestSSEContracts:
    def test_sse_event_shape(self):
        e = SSEEvent(
            step="planner", status="completed", timestamp="2026-01-01T00:00:00Z",
            finding="test", confidence=0.9, message="done",
        )
        d = e.model_dump()
        assert d["step"] == "planner"
        assert d["confidence"] == 0.9

    def test_sse_event_optional_fields(self):
        e = SSEEvent(step="test", status="ok", timestamp="2026-01-01")
        d = e.model_dump()
        assert d["finding"] is None
        assert d["evidence"] is None
