"""Comprehensive API endpoint tests using httpx AsyncClient."""
import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from backend.main import app


@pytest.fixture
async def client():
    with patch("backend.main.rate_limiter") as mock_rl:
        mock_rl.is_allowed.return_value = True
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


# ─── Health Endpoints ──────────────────────────────────────────────────────────

class TestHealthEndpoint:
    async def test_returns_200(self, client):
        response = await client.get("/health")
        assert response.status_code == 200

    async def test_status_healthy(self, client):
        data = (await client.get("/health")).json()
        assert data["status"] == "healthy"

    async def test_service_name(self, client):
        data = (await client.get("/health")).json()
        assert data["service"] == "meridian-ai"

    async def test_version_present(self, client):
        data = (await client.get("/health")).json()
        assert "version" in data

    async def test_mode_field(self, client):
        data = (await client.get("/health")).json()
        assert data["mode"] in ("mock", "live", "replay")

    async def test_groq_connected_field(self, client):
        data = (await client.get("/health")).json()
        assert isinstance(data["groq_connected"], bool)

    async def test_datahub_mock_field(self, client):
        data = (await client.get("/health")).json()
        assert isinstance(data["datahub_mock"], bool)


class TestReadinessEndpoint:
    async def test_returns_200(self, client):
        response = await client.get("/health/ready")
        assert response.status_code == 200

    async def test_status_field(self, client):
        data = (await client.get("/health/ready")).json()
        assert data["status"] in ("ready", "not_ready")

    async def test_checks_dict(self, client):
        data = (await client.get("/health/ready")).json()
        assert isinstance(data["checks"], dict)
        assert len(data["checks"]) > 0

    async def test_all_checks_are_booleans(self, client):
        data = (await client.get("/health/ready")).json()
        for key, value in data["checks"].items():
            assert isinstance(value, bool), f"Check '{key}' should be bool"

    async def test_replay_driver_check(self, client):
        data = (await client.get("/health/ready")).json()
        assert "replay_driver" in data["checks"]

    async def test_rate_limiter_check(self, client):
        data = (await client.get("/health/ready")).json()
        assert "rate_limiter" in data["checks"]


class TestLivenessEndpoint:
    async def test_returns_200(self, client):
        response = await client.get("/health/live")
        assert response.status_code == 200

    async def test_status_alive(self, client):
        data = (await client.get("/health/live")).json()
        assert data["status"] == "alive"


class TestMetricsEndpoint:
    async def test_returns_200(self, client):
        response = await client.get("/metrics")
        assert response.status_code == 200

    async def test_uptime_seconds(self, client):
        data = (await client.get("/metrics")).json()
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0

    async def test_request_count(self, client):
        data = (await client.get("/metrics")).json()
        assert "request_count" in data
        assert isinstance(data["request_count"], int)

    async def test_error_count(self, client):
        data = (await client.get("/metrics")).json()
        assert isinstance(data["error_count"], int)

    async def test_latency_percentiles(self, client):
        data = (await client.get("/metrics")).json()
        assert "p50_latency_ms" in data
        assert "p95_latency_ms" in data
        assert "p99_latency_ms" in data

    async def test_app_metadata(self, client):
        data = (await client.get("/metrics")).json()
        assert data["app"] == "meridian-ai"
        assert "version" in data
        assert data["mode"] in ("replay", "live")

    async def test_error_rate(self, client):
        data = (await client.get("/metrics")).json()
        assert "error_rate" in data
        assert 0 <= data["error_rate"] <= 1


# ─── Incidents Endpoints ──────────────────────────────────────────────────────

class TestIncidentsEndpoint:
    async def test_list_incidents_returns_200(self, client):
        response = await client.get("/api/incidents")
        assert response.status_code == 200

    async def test_list_incidents_has_array(self, client):
        data = (await client.get("/api/incidents")).json()
        assert "incidents" in data
        assert isinstance(data["incidents"], list)

    async def test_list_incidents_has_entries(self, client):
        data = (await client.get("/api/incidents")).json()
        assert len(data["incidents"]) > 0

    async def test_incident_summary_fields(self, client):
        data = (await client.get("/api/incidents")).json()
        inc = data["incidents"][0]
        assert "id" in inc
        assert "title" in inc
        assert "severity" in inc
        assert "status" in inc
        assert "detected" in inc


class TestIncidentDetailEndpoint:
    async def test_get_incident_42(self, client):
        response = await client.get("/api/incidents/42")
        assert response.status_code == 200

    async def test_incident_has_id(self, client):
        data = (await client.get("/api/incidents/42")).json()
        assert data["id"] == "42"

    async def test_incident_has_timeline(self, client):
        data = (await client.get("/api/incidents/42")).json()
        assert "timeline" in data

    async def test_incident_not_found(self, client):
        response = await client.get("/api/incidents/99999")
        assert response.status_code == 404

    async def test_incident_invalid_long_id(self, client):
        response = await client.get("/api/incidents/" + "x" * 100)
        assert response.status_code == 400


# ─── Models Endpoint ──────────────────────────────────────────────────────────

class TestModelEndpoint:
    async def test_get_model_returns_200(self, client):
        response = await client.get("/api/models/churn_model_v3")
        assert response.status_code == 200

    async def test_model_name_matches(self, client):
        data = (await client.get("/api/models/churn_model_v3")).json()
        assert data["name"] == "churn_model_v3"

    async def test_model_not_found(self, client):
        response = await client.get("/api/models/nonexistent_model_xyz")
        assert response.status_code == 404


# ─── Health Scores Endpoint ───────────────────────────────────────────────────

class TestHealthScoresEndpoint:
    async def test_returns_200(self, client):
        response = await client.get("/api/health-scores")
        assert response.status_code == 200

    async def test_has_models_array(self, client):
        data = (await client.get("/api/health-scores")).json()
        assert "models" in data
        assert isinstance(data["models"], list)


# ─── Resolution Times Endpoint ────────────────────────────────────────────────

class TestResolutionTimesEndpoint:
    async def test_returns_200(self, client):
        response = await client.get("/api/resolution-times")
        assert response.status_code == 200

    async def test_has_incidents(self, client):
        data = (await client.get("/api/resolution-times")).json()
        assert "incidents" in data
        assert len(data["incidents"]) > 0

    async def test_trend_decreasing(self, client):
        data = (await client.get("/api/resolution-times")).json()
        assert data["trend"] == "decreasing"

    async def test_predicted_next(self, client):
        data = (await client.get("/api/resolution-times")).json()
        assert "predicted_next" in data


# ─── Actions Endpoints ────────────────────────────────────────────────────────

class TestActionsInvestigateEndpoint:
    async def test_investigate_schema_change(self, client):
        response = await client.post("/api/actions/investigate", json={
            "event_type": "EntityChangeEvent_v1",
            "entity_urn": "urn:li:dataset:test",
            "aspect": "schemaMetadata",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "investigation_started"
        assert data["should_investigate"] is True

    async def test_investigate_low_severity(self, client):
        response = await client.post("/api/actions/investigate", json={
            "event_type": "EntityChangeEvent_v1",
            "entity_urn": "urn:li:dataset:test",
            "aspect": "description",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["should_investigate"] is False

    async def test_investigate_ownership_change(self, client):
        response = await client.post("/api/actions/investigate", json={
            "event_type": "EntityChangeEvent_v1",
            "entity_urn": "urn:li:dataset:test",
            "aspect": "ownership",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "investigation_started"

    async def test_investigate_invalid_json(self, client):
        response = await client.post(
            "/api/actions/investigate",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400


class TestActionsEventsEndpoint:
    async def test_returns_200(self, client):
        response = await client.get("/api/actions/events")
        assert response.status_code == 200

    async def test_has_events_and_stats(self, client):
        data = (await client.get("/api/actions/events")).json()
        assert "events" in data
        assert "stats" in data

    async def test_stats_has_total_events(self, client):
        data = (await client.get("/api/actions/events")).json()
        assert "total_events" in data["stats"]

    async def test_events_populated_after_trigger(self, client):
        await client.post("/api/actions/investigate", json={
            "event_type": "test", "entity_urn": "urn:li:dataset:t", "aspect": "schemaMetadata",
        })
        data = (await client.get("/api/actions/events")).json()
        assert data["stats"]["total_events"] >= 1


class TestActionsStatsEndpoint:
    async def test_returns_200(self, client):
        response = await client.get("/api/actions/stats")
        assert response.status_code == 200

    async def test_has_mode(self, client):
        data = (await client.get("/api/actions/stats")).json()
        assert "mode" in data

    async def test_has_total_events(self, client):
        data = (await client.get("/api/actions/stats")).json()
        assert "total_events" in data


# ─── Compliance Endpoints ─────────────────────────────────────────────────────

class TestComplianceAuditTrailEndpoint:
    async def test_returns_200(self, client):
        response = await client.get("/api/compliance/audit-trail")
        assert response.status_code == 200

    async def test_has_total_records(self, client):
        data = (await client.get("/api/compliance/audit-trail")).json()
        assert "total_records" in data
        assert isinstance(data["total_records"], int)

    async def test_has_chain_valid(self, client):
        data = (await client.get("/api/compliance/audit-trail")).json()
        assert "chain_valid" in data
        assert isinstance(data["chain_valid"], bool)

    async def test_has_last_hash(self, client):
        data = (await client.get("/api/compliance/audit-trail")).json()
        assert "last_hash" in data


class TestComplianceEuAiActEndpoint:
    async def test_returns_200(self, client):
        response = await client.get("/api/compliance/eu-ai-act/42")
        assert response.status_code == 200

    async def test_incident_id_matches(self, client):
        data = (await client.get("/api/compliance/eu-ai-act/42")).json()
        assert data["incident_id"] == "42"

    async def test_has_audit_records(self, client):
        data = (await client.get("/api/compliance/eu-ai-act/42")).json()
        assert "audit_records" in data

    async def test_has_chain_info(self, client):
        data = (await client.get("/api/compliance/eu-ai-act/42")).json()
        assert "chain_length" in data
        assert "chain_valid" in data


class TestComplianceScanPiiEndpoint:
    async def test_scan_pii_raw_events(self, client):
        response = await client.post("/api/compliance/scan-pii", json={
            "dataset_urn": "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "violations_found"
        assert data["total_violations"] > 0
        assert len(data["affected_columns"]) > 0

    async def test_scan_pii_clean_dataset(self, client):
        response = await client.post("/api/compliance/scan-pii", json={
            "dataset_urn": "urn:li:dataset:(urn:li:dataPlatform:snowflake,unknown,PROD)",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "clean"

    async def test_scan_pii_missing_urn(self, client):
        response = await client.post("/api/compliance/scan-pii", json={})
        assert response.status_code == 400

    async def test_scan_pii_invalid_json(self, client):
        response = await client.post(
            "/api/compliance/scan-pii",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

    async def test_scan_pii_has_regulations(self, client):
        response = await client.post("/api/compliance/scan-pii", json={
            "dataset_urn": "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
        })
        data = response.json()
        if data["status"] == "violations_found":
            assert "regulations" in data
            assert "severity" in data


# ─── Discovery Endpoint ──────────────────────────────────────────────────────

class TestDiscoveryShadowAiEndpoint:
    async def test_returns_200(self, client):
        response = await client.post("/api/discovery/shadow-ai")
        assert response.status_code == 200

    async def test_scan_complete(self, client):
        data = (await client.post("/api/discovery/shadow-ai")).json()
        assert data["status"] == "scan_complete"

    async def test_has_finding(self, client):
        data = (await client.post("/api/discovery/shadow-ai")).json()
        assert "finding" in data

    async def test_has_confidence(self, client):
        data = (await client.post("/api/discovery/shadow-ai")).json()
        assert "confidence" in data
        assert isinstance(data["confidence"], (int, float))

    async def test_has_severity(self, client):
        data = (await client.post("/api/discovery/shadow-ai")).json()
        assert "severity" in data


# ─── Error Handling ───────────────────────────────────────────────────────────

class TestNotFoundHandler:
    async def test_404_returns_json(self, client):
        response = await client.get("/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    async def test_404_includes_path(self, client):
        response = await client.get("/nonexistent")
        data = response.json()
        assert data["path"] == "/nonexistent"


class TestResponseHeaders:
    async def test_request_id_header(self, client):
        response = await client.get("/health")
        assert "X-Request-ID" in response.headers

    async def test_response_time_header(self, client):
        response = await client.get("/health")
        assert "X-Response-Time" in response.headers
        assert "ms" in response.headers["X-Response-Time"]
