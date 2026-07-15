"""Real API endpoint tests using FastAPI TestClient.

These tests exercise the actual HTTP endpoints, not just worker internals.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


class TestHealthEndpoints:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "meridian-ai"

    def test_readiness_returns_200(self, client):
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data

    def test_liveness_returns_200(self, client):
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    def test_metrics_returns_200(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data
        assert "request_count" in data
        assert "p50_latency_ms" in data
        assert "p95_latency_ms" in data
        assert "p99_latency_ms" in data


class TestIncidentsEndpoints:
    def test_list_incidents(self, client):
        response = client.get("/api/incidents")
        assert response.status_code == 200
        data = response.json()
        assert "incidents" in data
        assert len(data["incidents"]) > 0

    def test_get_incident_42(self, client):
        response = client.get("/api/incidents/42")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "42"
        assert "timeline" in data

    def test_get_incident_not_found(self, client):
        response = client.get("/api/incidents/99999")
        assert response.status_code == 404

    def test_get_incident_invalid_id(self, client):
        response = client.get("/api/incidents/" + "x" * 100)
        assert response.status_code == 400


class TestModelsEndpoints:
    def test_get_model(self, client):
        response = client.get("/api/models/churn_model_v3")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "churn_model_v3"

    def test_get_health_scores(self, client):
        response = client.get("/api/health-scores")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data


class TestResolutionTimes:
    def test_resolution_times(self, client):
        response = client.get("/api/resolution-times")
        assert response.status_code == 200
        data = response.json()
        assert "incidents" in data
        assert data["trend"] == "decreasing"
        assert len(data["incidents"]) > 0


class TestActionsEndpoints:
    def test_investigate_trigger(self, client):
        response = client.post("/api/actions/investigate", json={
            "event_type": "EntityChangeEvent_v1",
            "entity_urn": "urn:li:dataset:test",
            "aspect": "schemaMetadata",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "investigation_started"
        assert data["should_investigate"] is True

    def test_investigate_low_severity(self, client):
        response = client.post("/api/actions/investigate", json={
            "event_type": "EntityChangeEvent_v1",
            "entity_urn": "urn:li:dataset:test",
            "aspect": "description",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["should_investigate"] is False

    def test_actions_events_log(self, client):
        client.post("/api/actions/investigate", json={
            "event_type": "test", "entity_urn": "urn:li:dataset:t", "aspect": "schemaMetadata",
        })
        response = client.get("/api/actions/events")
        assert response.status_code == 200
        data = response.json()
        assert data["stats"]["total_events"] >= 1

    def test_actions_stats(self, client):
        response = client.get("/api/actions/stats")
        assert response.status_code == 200
        data = response.json()
        assert "mode" in data


class TestComplianceEndpoints:
    def test_scan_pii_raw_events(self, client):
        response = client.post("/api/compliance/scan-pii", json={
            "dataset_urn": "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "violations_found"
        assert data["total_violations"] > 0
        assert len(data["affected_columns"]) > 0

    def test_scan_pii_clean_dataset(self, client):
        response = client.post("/api/compliance/scan-pii", json={
            "dataset_urn": "urn:li:dataset:(urn:li:dataPlatform:snowflake,unknown,PROD)",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "clean"

    def test_scan_pii_missing_urn(self, client):
        response = client.post("/api/compliance/scan-pii", json={})
        assert response.status_code == 400

    def test_eu_ai_act_file(self, client):
        response = client.get("/api/compliance/eu-ai-act/42")
        assert response.status_code == 200
        data = response.json()
        assert data["incident_id"] == "42"

    def test_audit_trail(self, client):
        response = client.get("/api/compliance/audit-trail")
        assert response.status_code == 200
        data = response.json()
        assert "total_records" in data


class TestDiscoveryEndpoints:
    def test_shadow_ai_scan(self, client):
        response = client.post("/api/discovery/shadow-ai")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "scan_complete"
        assert "finding" in data


class TestCodeGenerationEndpoints:
    def test_generate_dbt(self, client):
        response = client.post("/api/generate/dbt", json={
            "source_dataset_urn": "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            "target_model_name": "stg_raw_events",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "generated"

    def test_generate_dbt_missing_urn(self, client):
        response = client.post("/api/generate/dbt", json={})
        assert response.status_code == 400


class TestStreamingEndpoints:
    def test_replay_stream(self, client):
        response = client.get("/stream/replay?incident_id=42&delay=0.1")
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

    def test_investigate_stream_replay_mode(self, client):
        response = client.get("/stream/investigate?mode=replay&delay=0.1")
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]


class TestNotFoundHandler:
    def test_404_returns_json(self, client):
        response = client.get("/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
