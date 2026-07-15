"""Tests for all workers."""
import pytest
from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.workers.feature_drift import FeatureDrift
from backend.workers.root_cause import RootCause
from backend.workers.knowledge_writer import KnowledgeWriter
from backend.workers.lifecycle_governance import LifecycleGovernance
from backend.models import Severity


@pytest.fixture
def mcp():
    return DataHubMCPClient(mock=True)


@pytest.fixture
def groq():
    return GroqClient(mock=True)


class TestFeatureDrift:
    @pytest.mark.asyncio
    async def test_detect_returns_evidence(self, mcp, groq):
        worker = FeatureDrift(mcp=mcp, groq=groq)
        evidence = await worker.detect(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
        )
        assert evidence.worker_id == "feature_drift"
        assert evidence.confidence > 0

    @pytest.mark.asyncio
    async def test_detect_has_severity(self, mcp, groq):
        worker = FeatureDrift(mcp=mcp, groq=groq)
        evidence = await worker.detect(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
        )
        assert evidence.severity in [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]


class TestRootCause:
    @pytest.mark.asyncio
    async def test_analyze_returns_evidence(self, mcp, groq):
        worker = RootCause(mcp=mcp, groq=groq)
        evidence = await worker.analyze(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            ["urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"],
        )
        assert evidence.worker_id == "root_cause"
        assert evidence.confidence > 0

    @pytest.mark.asyncio
    async def test_analyze_has_business_impact(self, mcp, groq):
        worker = RootCause(mcp=mcp, groq=groq)
        evidence = await worker.analyze(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            ["urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"],
        )
        assert evidence.business_impact is not None


class TestKnowledgeWriter:
    @pytest.mark.asyncio
    async def test_write_returns_evidence(self, mcp, groq):
        from backend.models import EvidenceObject
        worker = KnowledgeWriter(mcp=mcp, groq=groq)
        root_cause = EvidenceObject(
            worker_id="root_cause",
            timestamp="2026-01-01T00:00:00Z",
            finding="Test finding",
            confidence=0.95,
            severity=Severity.HIGH,
        )
        evidence = await worker.write(
            "42",
            root_cause,
            ["urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"],
        )
        assert evidence.worker_id == "knowledge_writer"
        assert len(evidence.datahub_mutations) > 0


class TestLifecycleGovernance:
    @pytest.mark.asyncio
    async def test_evaluate_low_health(self, mcp, groq):
        worker = LifecycleGovernance(mcp=mcp, groq=groq)
        evidence = await worker.evaluate(
            model_urn="urn:li:mlModel:test",
            model_name="test_model",
            health_score=45,
            consecutive_failures=4,
            pattern_id="test-pattern",
            incident_id="42",
        )
        assert evidence.severity == Severity.HIGH
        assert len(evidence.datahub_mutations) == 1

    @pytest.mark.asyncio
    async def test_evaluate_ok_health(self, mcp, groq):
        worker = LifecycleGovernance(mcp=mcp, groq=groq)
        evidence = await worker.evaluate(
            model_urn="urn:li:mlModel:test",
            model_name="test_model",
            health_score=80,
            consecutive_failures=1,
            pattern_id="test-pattern",
            incident_id="42",
        )
        assert evidence.severity == Severity.LOW
        assert len(evidence.datahub_mutations) == 0
