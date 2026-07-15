"""Extended tests for Reflexion Loop."""
import pytest
from backend.reflexion import ReflexionLoop, ReflexionResult
from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient


@pytest.fixture
def mcp():
    return DataHubMCPClient(mock=True)


@pytest.fixture
def groq():
    return GroqClient(mock=True)


@pytest.fixture
def reflexion(mcp, groq):
    return ReflexionLoop(mcp=mcp, groq=groq)


class TestReflexionLoop:
    @pytest.mark.asyncio
    async def test_run_returns_result(self, reflexion):
        result = await reflexion.run(
            incident_id="42",
            pattern_id="schema-change",
            root_cause="Schema type change",
            resolution="Rollback model",
            resolution_time_minutes=3,
            affected_model_urn="urn:li:mlModel:test",
        )
        assert result.incident_id == "42"
        assert result.pattern_id == "schema-change"
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_run_writes_playbook(self, reflexion, mcp):
        await reflexion.run(
            incident_id="42",
            pattern_id="schema-change",
            root_cause="Schema type change",
            resolution="Rollback model",
            resolution_time_minutes=3,
            affected_model_urn="urn:li:mlModel:test",
        )
        # Check that at least one document was written
        assert len(mcp._documents) > 0

    @pytest.mark.asyncio
    async def test_run_with_previous_playbook(self, reflexion, mcp):
        # Create initial playbook
        await mcp.save_document(
            title="Playbook: schema-change",
            content="Old playbook content",
            tags=["playbook"],
        )

        result = await reflexion.run(
            incident_id="42",
            pattern_id="schema-change",
            root_cause="Schema type change",
            resolution="Rollback model",
            resolution_time_minutes=3,
            affected_model_urn="urn:li:mlModel:test",
        )
        # Verify result has new playbook
        assert result.new_playbook is not None
        assert len(result.new_playbook) > 0

    def test_result_to_dict(self):
        result = ReflexionResult(
            incident_id="42",
            pattern_id="schema-change",
            previous_playbook="Old",
            new_playbook="New",
            improvement_notes="Faster",
            resolution_time_before=18,
            resolution_time_after=3,
            confidence=0.92,
        )
        d = result.to_dict()
        assert d["incident_id"] == "42"
        assert d["resolution_time_before"] == 18
        assert d["resolution_time_after"] == 3

    def test_improvement_calculation(self):
        result = ReflexionResult(
            incident_id="42",
            pattern_id="test",
            previous_playbook=None,
            new_playbook="playbook",
            improvement_notes="",
            resolution_time_before=18,
            resolution_time_after=3,
            confidence=0.9,
        )
        improvement = result.resolution_time_before - result.resolution_time_after
        assert improvement == 15
        assert improvement > 0
