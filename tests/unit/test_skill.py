"""Enterprise-grade tests for datahub-meridian-ai skill."""
import pytest
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "skill", "datahub-meridian-ai"))

from commands import (
    MeridianAI,
    InvestigationResult,
    HealthReport,
    Playbook,
    Severity,
    InvestigationStatus,
    retry_on_failure,
)


class TestInvestigationResult:
    def test_creation(self):
        result = InvestigationResult(
            model_urn="urn:li:mlModel:test",
            model_name="test_model",
            status=InvestigationStatus.COMPLETED,
            timestamp="2026-01-01 00:00:00 UTC",
        )
        assert result.model_name == "test_model"
        assert result.status == InvestigationStatus.COMPLETED
        assert result.findings == []
        assert result.errors == []

    def test_to_markdown(self):
        result = InvestigationResult(
            model_urn="urn:li:mlModel:test",
            model_name="test_model",
            status=InvestigationStatus.COMPLETED,
            timestamp="2026-01-01 00:00:00 UTC",
            findings=[
                {"worker": "data_sentinel", "message": "Schema change detected", "confidence": 0.94, "severity": "high"},
            ],
            lineage={"upstream": [{"name": "ds1"}], "downstream": [{"name": "model1"}]},
            mutations=[{"tool": "save_document", "success": True, "description": "Written"}],
        )
        md = result.to_markdown()
        assert "test_model" in md
        assert "Schema change detected" in md
        assert "Lineage" in md
        assert "save_document" in md

    def test_status_enum(self):
        assert InvestigationStatus.PENDING.value == "pending"
        assert InvestigationStatus.RUNNING.value == "running"
        assert InvestigationStatus.COMPLETED.value == "completed"
        assert InvestigationStatus.FAILED.value == "failed"

    def test_severity_enum(self):
        assert Severity.LOW.value == "low"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.HIGH.value == "high"
        assert Severity.CRITICAL.value == "critical"


class TestHealthReport:
    def test_creation(self):
        report = HealthReport(
            model_urn="urn:li:mlModel:test",
            model_name="test_model",
            health_score=81,
            confidence=0.97,
        )
        assert report.health_score == 81
        assert report.confidence == 0.97

    def test_to_markdown(self):
        report = HealthReport(
            model_urn="urn:li:mlModel:test",
            model_name="test_model",
            health_score=81,
            confidence=0.97,
            signals={"Data Quality": 0.72, "Prediction": 0.91},
            lineage_stats={"upstream": 2, "downstream": 3},
            metadata={"owner": "team-a", "tags": ["production"]},
            timestamp="2026-01-01 00:00:00 UTC",
        )
        md = report.to_markdown()
        assert "test_model" in md
        assert "81/100" in md
        assert "97%" in md
        assert "Data Quality" in md
        assert "Upstream assets: 2" in md

    def test_bar_visualization(self):
        report = HealthReport(
            model_urn="test",
            model_name="test",
            health_score=80,
            confidence=0.9,
            signals={"Score": 0.5},
        )
        md = report.to_markdown()
        assert "█" in md
        assert "░" in md


class TestPlaybook:
    def test_creation(self):
        playbook = Playbook(
            pattern_id="test-pattern",
            title="Test Playbook",
            content="Test content",
            confidence=0.95,
        )
        assert playbook.pattern_id == "test-pattern"
        assert playbook.confidence == 0.95

    def test_to_markdown(self):
        playbook = Playbook(
            pattern_id="schema-change",
            title="Schema Change Playbook",
            content="## Detection signals\n- Column type change",
            confidence=0.96,
            incidents=[
                {"id": "12", "resolution_time": "18 min", "date": "2026-03-10"},
                {"id": "42", "resolution_time": "3 min", "date": "2026-07-12"},
            ],
            tags=["playbook", "schema-change"],
            last_updated="2026-07-12",
        )
        md = playbook.to_markdown()
        assert "Schema Change Playbook" in md
        assert "96%" in md
        assert "Incident #12" in md
        assert "18 min" in md
        assert "playbook" in md


class TestMeridianAI:
    def test_init_defaults(self):
        ai = MeridianAI()
        assert "localhost" in ai.gms_url or "8080" in ai.gms_url
        assert ai.max_retries == 3
        assert ai.timeout_seconds == 30

    def test_init_custom(self):
        ai = MeridianAI(
            gms_url="http://custom:9000/api/gms",
            max_retries=5,
            timeout_seconds=60,
        )
        assert ai.gms_url == "http://custom:9000/api/gms"
        assert ai.max_retries == 5
        assert ai.timeout_seconds == 60

    def test_model_name_extraction(self):
        urn = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"
        model_name = urn.split(",")[-2]
        assert model_name == "churn_model_v3"

    def test_model_name_simple(self):
        urn = "simple_model"
        model_name = urn.split(",")[-2] if "," in urn else urn
        assert model_name == "simple_model"


class TestRetryLogic:
    @pytest.mark.asyncio
    async def test_retry_succeeds_after_failure(self):
        call_count = 0

        @retry_on_failure(max_retries=3, backoff_factor=0.01)
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await flaky_function()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        @retry_on_failure(max_retries=2, backoff_factor=0.01)
        async def always_fails():
            raise ValueError("Permanent failure")

        with pytest.raises(ValueError, match="Permanent failure"):
            await always_fails()
