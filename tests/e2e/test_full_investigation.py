"""E2E test: Full investigation pipeline from trigger to DataHub write-back."""
import pytest
import asyncio
from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.workers.planner import PlannerAgent


@pytest.fixture
def mcp():
    return DataHubMCPClient(mock=True)


@pytest.fixture
def groq():
    return GroqClient(mock=True)


@pytest.fixture
def planner(mcp, groq):
    return PlannerAgent(mcp=mcp, groq=groq)


class TestFullInvestigation:
    @pytest.mark.asyncio
    async def test_trigger_to_writeback(self, planner, mcp):
        """Full E2E: trigger → workers → validation → write-back."""
        events = []
        async for event in planner.investigate(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            incident_id="E2E-TEST",
        ):
            events.append(event)

        # Verify all steps completed
        steps = [e.get("step") for e in events]
        assert "planner" in steps
        assert "data_sentinel" in steps
        assert "feature_drift" in steps
        assert "root_cause" in steps
        assert "validation" in steps
        assert "knowledge_writer" in steps
        assert "lifecycle_governance" in steps

        # Verify completion
        last = events[-1]
        assert last.get("status") == "completed"
        assert "summary" in last

    @pytest.mark.asyncio
    async def test_evidence_objects_have_required_fields(self, planner):
        """Every worker returns valid evidence objects."""
        events = []
        async for event in planner.investigate(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            incident_id="E2E-FIELDS",
        ):
            events.append(event)

        evidence_events = [e for e in events if "evidence" in e and e.get("evidence")]
        for ev in evidence_events:
            evidence = ev["evidence"]
            assert "worker_id" in evidence
            assert "timestamp" in evidence
            assert "finding" in evidence
            assert "confidence" in evidence
            assert "severity" in evidence

    @pytest.mark.asyncio
    async def test_datahub_mutations_occurred(self, planner, mcp):
        """Write-back to DataHub actually happens."""
        events = []
        async for event in planner.investigate(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            incident_id="E2E-MUTATIONS",
        ):
            events.append(event)

        # Knowledge writer should have written documents
        docs = await mcp.search_documents(query="E2E-MUTATIONS")
        assert len(docs) > 0

    @pytest.mark.asyncio
    async def test_timeline_events_chronological(self, planner):
        """Events arrive in chronological order."""
        events = []
        async for event in planner.investigate(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            incident_id="E2E-CHRONO",
        ):
            events.append(event)

        timestamps = [e.get("timestamp", "") for e in events]
        assert timestamps == sorted(timestamps)

    @pytest.mark.asyncio
    async def test_validation_runs(self, planner):
        """Validation layer runs and produces result."""
        events = []
        async for event in planner.investigate(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            incident_id="E2E-VALIDATION",
        ):
            events.append(event)

        validation_events = [e for e in events if e.get("step") == "validation"]
        assert len(validation_events) == 2  # running + completed
        completed = [e for e in validation_events if e.get("status") == "completed"]
        assert len(completed) == 1
        assert "approved" in completed[0]
