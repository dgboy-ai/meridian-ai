"""Tests for API schemas."""
import pytest
from backend.schemas import (
    InvestigateRequest, ReplayRequest, HealthResponse, ReadinessResponse,
    LivenessResponse, MetricsResponse, IncidentSummary, IncidentsResponse,
    ResolutionTimeEntry, ResolutionTimesResponse, ModelResponse, ErrorResponse,
    SSEEvent, IncidentSeverity, InvestigationMode,
)


class TestInvestigateRequest:
    def test_valid_request(self):
        req = InvestigateRequest(
            dataset_urn="urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
        )
        assert req.incident_id == "42"
        assert req.mode == InvestigationMode.REPLAY

    def test_custom_incident_id(self):
        req = InvestigateRequest(
            dataset_urn="urn:li:dataset:test",
            incident_id="123",
        )
        assert req.incident_id == "123"

    def test_invalid_urn(self):
        with pytest.raises(Exception):
            InvestigateRequest(dataset_urn="invalid-urn")

    def test_mode_enum(self):
        req = InvestigateRequest(
            dataset_urn="urn:li:dataset:test",
            mode=InvestigationMode.LIVE,
        )
        assert req.mode == InvestigationMode.LIVE


class TestReplayRequest:
    def test_defaults(self):
        req = ReplayRequest()
        assert req.incident_id == "42"
        assert req.delay == 0.5

    def test_custom_values(self):
        req = ReplayRequest(incident_id="12", delay=1.0)
        assert req.incident_id == "12"
        assert req.delay == 1.0


class TestHealthResponse:
    def test_creation(self):
        resp = HealthResponse(
            status="healthy",
            service="meridian-ai",
            version="1.0.0",
            mode="replay",
            groq_connected=True,
            datahub_mock=True,
        )
        assert resp.status == "healthy"
        assert resp.groq_connected is True


class TestReadinessResponse:
    def test_creation(self):
        resp = ReadinessResponse(status="ready", checks={"replay": True})
        assert resp.status == "ready"
        assert resp.checks["replay"] is True


class TestMetricsResponse:
    def test_creation(self):
        resp = MetricsResponse(
            uptime_seconds=100.0,
            request_count=50,
            error_count=2,
            avg_latency_ms=15.5,
            p50_latency_ms=12.0,
            p95_latency_ms=45.0,
            p99_latency_ms=100.0,
            error_rate=0.04,
            app="meridian-ai",
            version="1.0.0",
            mode="replay",
        )
        assert resp.request_count == 50
        assert resp.error_rate == 0.04


class TestIncidentSummary:
    def test_creation(self):
        inc = IncidentSummary(
            id="42",
            title="Test Incident",
            severity="high",
            status="resolved",
            detected="2026-01-01",
            duration_seconds=300,
            affected_models=["model1"],
            pattern_id="test-pattern",
        )
        assert inc.id == "42"
        assert inc.severity == "high"


class TestModelResponse:
    def test_creation(self):
        model = ModelResponse(
            urn="urn:li:mlModel:test",
            name="test_model",
            type="mlModel",
            platform="mlflow",
            owner="team-a",
            tags=["production"],
        )
        assert model.name == "test_model"
        assert model.health_score is None


class TestErrorResponse:
    def test_creation(self):
        err = ErrorResponse(error="Not found", detail="Resource missing")
        assert err.error == "Not found"
        assert err.request_id is None


class TestSSEEvent:
    def test_creation(self):
        event = SSEEvent(
            step="data_sentinel",
            status="completed",
            timestamp="2026-01-01T00:00:00Z",
            finding="Test finding",
            confidence=0.94,
        )
        assert event.step == "data_sentinel"
        assert event.confidence == 0.94


class TestEnums:
    def test_severity_values(self):
        assert IncidentSeverity.LOW.value == "low"
        assert IncidentSeverity.CRITICAL.value == "critical"

    def test_mode_values(self):
        assert InvestigationMode.LIVE.value == "live"
        assert InvestigationMode.REPLAY.value == "replay"
