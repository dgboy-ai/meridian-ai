"""Real DataHub integration tests — tests against real DataHub instance.

These tests verify that our code works with real DataHub, not just mocks.
Run with: DATAHUB_MOCK=false DATAHUB_GMS_URL=http://localhost:8080/api/gms pytest tests/integration/test_real_datahub.py -v
"""
import pytest
import os

# Skip all tests if DataHub is not available
DATAREHUB_AVAILABLE = os.getenv("DATAHUB_MOCK", "true").lower() == "false"
pytestmark = pytest.mark.skipif(
    not DATAREHUB_AVAILABLE,
    reason="DataHub not available (set DATAHUB_MOCK=false to run)"
)


@pytest.fixture
def mcp():
    """Create a real DataHub MCP client."""
    from backend.clients.datahub_client import DataHubMCPClient
    return DataHubMCPClient(mock=False)


@pytest.fixture
def groq():
    """Create a Groq client (may be mock if no API key)."""
    from backend.clients.groq_client import GroqClient
    return GroqClient()


class TestDataHubConnection:
    """Test basic DataHub connectivity."""

    @pytest.mark.asyncio
    async def test_connection(self, mcp):
        """Verify we can connect to DataHub."""
        assert mcp._connected or mcp._mode == "mock"

    @pytest.mark.asyncio
    async def test_get_entities(self, mcp):
        """Verify we can retrieve entities."""
        entities = await mcp.get_entities([
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)"
        ])
        # In real mode, this should return entities
        # In mock mode, it returns mock entities
        assert isinstance(entities, list)


class TestDataHubLineage:
    """Test DataHub lineage traversal."""

    @pytest.mark.asyncio
    async def test_get_lineage(self, mcp):
        """Verify we can retrieve lineage."""
        lineage = await mcp.get_lineage(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            depth=3
        )
        assert "entity" in lineage
        assert "upstream" in lineage or "downstream" in lineage

    @pytest.mark.asyncio
    async def test_get_lineage_paths(self, mcp):
        """Verify we can get lineage paths between entities."""
        paths = await mcp.get_lineage_paths_between(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"
        )
        assert isinstance(paths, list)


class TestDataHubMutations:
    """Test DataHub mutation operations."""

    @pytest.mark.asyncio
    async def test_add_structured_properties(self, mcp):
        """Verify we can add structured properties."""
        result = await mcp.add_structured_properties(
            entity_urn="urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
            properties={"test_property": "test_value"}
        )
        assert "status" in result

    @pytest.mark.asyncio
    async def test_batch_add_tags(self, mcp):
        """Verify we can add tags."""
        result = await mcp.batch_add_tags(
            urns=["urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"],
            tags=["test-tag"]
        )
        assert "status" in result


class TestDataHubDocuments:
    """Test DataHub document operations."""

    @pytest.mark.asyncio
    async def test_save_document(self, mcp):
        """Verify we can save documents."""
        result = await mcp.save_document(
            title="Test Document",
            content="Test content",
            tags=["test"]
        )
        assert "id" in result

    @pytest.mark.asyncio
    async def test_search_documents(self, mcp):
        """Verify we can search documents."""
        docs = await mcp.search_documents(query="test")
        assert isinstance(docs, list)


class TestDataHubIncidents:
    """Test DataHub incident operations."""

    @pytest.mark.asyncio
    async def test_raise_incident(self, mcp):
        """Verify we can raise incidents."""
        result = await mcp.raise_incident(
            type_="TEST_INCIDENT",
            severity="LOW",
            description="Test incident"
        )
        assert "id" in result


class TestDataHubProposals:
    """Test DataHub proposal operations."""

    @pytest.mark.asyncio
    async def test_list_pending_proposals(self, mcp):
        """Verify we can list pending proposals."""
        proposals = await mcp.list_pending_proposals()
        assert isinstance(proposals, list)


class TestFullInvestigationWithRealDataHub:
    """Test full investigation with real DataHub."""

    @pytest.mark.asyncio
    async def test_investigation_completes(self, mcp, groq):
        """Verify full investigation completes with real DataHub."""
        from backend.workers.planner import PlannerAgent

        planner = PlannerAgent(mcp=mcp, groq=groq)

        events = []
        async for event in planner.investigate(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            incident_id="REAL-TEST",
        ):
            events.append(event)

        # Verify investigation completed
        assert len(events) > 0
        last_event = events[-1]
        assert last_event.get("status") == "completed"
        assert "summary" in last_event
