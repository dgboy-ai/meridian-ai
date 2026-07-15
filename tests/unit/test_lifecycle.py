"""Tests for Lifecycle Governance worker."""
import pytest
import asyncio
from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.workers.lifecycle_governance import LifecycleGovernance
from backend.models import Severity


@pytest.fixture
def mcp():
    return DataHubMCPClient(mock=True)


@pytest.fixture
def groq():
    return GroqClient(mock=True)


@pytest.fixture
def lifecycle(mcp, groq):
    return LifecycleGovernance(mcp, groq)


class TestLifecycleGovernance:
    @pytest.mark.asyncio
    async def test_propose_deprecated_when_health_low(self, lifecycle):
        """Should propose DEPRECATED when health < 60 and failures >= 3."""
        result = await lifecycle.evaluate(
            model_urn="urn:li:mlModel:(urn:li:dataPlatform:mlflow,ltv_model_v2,PROD)",
            model_name="ltv_model_v2",
            health_score=45,
            consecutive_failures=4,
            pattern_id="schema-change-type-mismatch",
            incident_id="42",
        )
        assert result.worker_id == "lifecycle_governance"
        assert result.severity == Severity.HIGH
        assert len(result.datahub_mutations) == 1
        assert result.datahub_mutations[0].tool == "propose_lifecycle_stage"
        assert result.datahub_mutations[0].safe is False
        assert "DEPRECATED" in result.finding

    @pytest.mark.asyncio
    async def test_no_propose_when_health_ok(self, lifecycle):
        """Should NOT propose when health >= 60."""
        result = await lifecycle.evaluate(
            model_urn="urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
            model_name="churn_model_v3",
            health_score=81,
            consecutive_failures=1,
            pattern_id="schema-change-type-mismatch",
            incident_id="42",
        )
        assert result.severity == Severity.LOW
        assert len(result.datahub_mutations) == 0
        assert "not warranted" in result.finding

    @pytest.mark.asyncio
    async def test_no_propose_when_failures_insufficient(self, lifecycle):
        """Should NOT propose when failures < 3 even if health is low."""
        result = await lifecycle.evaluate(
            model_urn="urn:li:mlModel:(urn:li:dataPlatform:mlflow,ltv_model_v2,PROD)",
            model_name="ltv_model_v2",
            health_score=45,
            consecutive_failures=2,
            pattern_id="schema-change-type-mismatch",
            incident_id="42",
        )
        assert result.severity == Severity.LOW
        assert len(result.datahub_mutations) == 0
        assert "consecutive failures below threshold" in result.finding

    @pytest.mark.asyncio
    async def test_no_duplicate_proposal(self, lifecycle, mcp):
        """Should skip if proposal already pending."""
        # First call proposes
        await lifecycle.evaluate(
            model_urn="urn:li:mlModel:(urn:li:dataPlatform:mlflow,ltv_model_v2,PROD)",
            model_name="ltv_model_v2",
            health_score=45,
            consecutive_failures=4,
            pattern_id="schema-change-type-mismatch",
            incident_id="42",
        )

        # Add to pending proposals
        await mcp.propose_lifecycle_stage(
            entity_urn="urn:li:mlModel:(urn:li:dataPlatform:mlflow,ltv_model_v2,PROD)",
            lifecycle_stage="DEPRECATED",
            reason="test",
        )

        # Second call should skip
        result = await lifecycle.evaluate(
            model_urn="urn:li:mlModel:(urn:li:dataPlatform:mlflow,ltv_model_v2,PROD)",
            model_name="ltv_model_v2",
            health_score=45,
            consecutive_failures=4,
            pattern_id="schema-change-type-mismatch",
            incident_id="42",
        )
        assert "already pending" in result.finding
        assert len(result.datahub_mutations) == 0

    @pytest.mark.asyncio
    async def test_exact_threshold_boundary(self, lifecycle):
        """Health score exactly 60 should NOT trigger proposal."""
        result = await lifecycle.evaluate(
            model_urn="urn:li:mlModel:(urn:li:dataPlatform:mlflow,ltv_model_v2,PROD)",
            model_name="ltv_model_v2",
            health_score=60,
            consecutive_failures=3,
            pattern_id="schema-change-type-mismatch",
            incident_id="42",
        )
        assert result.severity == Severity.LOW
        assert len(result.datahub_mutations) == 0

    @pytest.mark.asyncio
    async def test_health_59_triggers(self, lifecycle):
        """Health score 59 should trigger proposal."""
        result = await lifecycle.evaluate(
            model_urn="urn:li:mlModel:(urn:li:dataPlatform:mlflow,ltv_model_v2,PROD)",
            model_name="ltv_model_v2",
            health_score=59,
            consecutive_failures=3,
            pattern_id="schema-change-type-mismatch",
            incident_id="42",
        )
        assert result.severity == Severity.HIGH
        assert len(result.datahub_mutations) == 1
