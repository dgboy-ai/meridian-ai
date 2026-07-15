"""Tests for MCP server JSON-RPC protocol handling."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.mcp_server import MeridianMCPServer, TOOLS


@pytest.fixture
def server():
    """Create a MeridianMCPServer with mocked dependencies."""
    with patch("backend.mcp_server.DataHubMCPClient") as mock_mcp, \
         patch("backend.mcp_server.GroqClient") as mock_groq:
        s = MeridianMCPServer()
        s.mcp = mock_mcp
        s.groq = mock_groq
        yield s


class TestMCPTools:
    def test_tools_list_returns_all_tools(self):
        assert len(TOOLS) == 3
        tool_names = [t["name"] for t in TOOLS]
        assert "meridian_investigate" in tool_names
        assert "meridian_health" in tool_names
        assert "meridian_playbook" in tool_names

    def test_tool_hints_present(self):
        for tool in TOOLS:
            assert "readOnlyHint" in tool
            assert "destructiveHint" in tool
            assert "idempotentHint" in tool

    def test_investigate_tool_is_not_readonly(self):
        inv = [t for t in TOOLS if t["name"] == "meridian_investigate"][0]
        assert inv["readOnlyHint"] is False

    def test_health_tool_is_readonly(self):
        health = [t for t in TOOLS if t["name"] == "meridian_health"][0]
        assert health["readOnlyHint"] is True

    def test_playbook_tool_is_readonly(self):
        pb = [t for t in TOOLS if t["name"] == "meridian_playbook"][0]
        assert pb["readOnlyHint"] is True


class TestMCPHandlers:
    @pytest.mark.asyncio
    async def test_handle_health_with_entity(self, server):
        server.mcp.get_entities = AsyncMock(return_value=[{
            "urn": "urn:li:mlModel:test",
            "name": "test_model",
            "health_score": 85,
            "confidence": 0.92,
            "resolved_incidents": 5,
            "resolution_time_minutes": 3.0,
        }])
        result = await server.handle_health("urn:li:mlModel:test")
        # model_name is extracted from URN, not entity
        assert "health_score" in result
        assert result["resolved_incidents"] == 5
        assert result["resolution_time_minutes"] == 3.0

    @pytest.mark.asyncio
    async def test_handle_health_without_entity(self, server):
        server.mcp.get_entities = AsyncMock(return_value=[])
        result = await server.handle_health("urn:li:mlModel:unknown")
        assert "health_score" in result
        assert "assessment" in result

    @pytest.mark.asyncio
    async def test_handle_playbook_found(self, server):
        server.mcp.search_documents = AsyncMock(return_value=[{
            "title": "Playbook: test-pattern",
            "content": "Test playbook content",
            "tags": ["playbook"],
        }])
        result = await server.handle_playbook("test-pattern")
        assert result["pattern_id"] == "test-pattern"
        assert "Test playbook content" in result["content"]

    @pytest.mark.asyncio
    async def test_handle_playbook_not_found(self, server):
        server.mcp.search_documents = AsyncMock(return_value=[])
        result = await server.handle_playbook("nonexistent")
        assert result["pattern_id"] == "nonexistent"
        assert "No playbook found" in result["content"]

    @pytest.mark.asyncio
    async def test_handle_investigate(self, server):
        async def mock_investigate(urn, incident_id):
            yield {"step": "planner", "status": "started"}
            yield {"step": "planner", "status": "completed"}
        server.planner = MagicMock()
        server.planner.investigate = mock_investigate
        result = await server.handle_investigate("urn:li:mlModel:test", "99")
        assert result["status"] == "completed"
        assert result["incident_id"] == "99"


class TestMCPSchema:
    def test_investigate_schema_has_required_fields(self):
        inv = [t for t in TOOLS if t["name"] == "meridian_investigate"][0]
        schema = inv["inputSchema"]
        assert "model_urn" in schema["properties"]
        assert "model_urn" in schema["required"]

    def test_health_schema_has_required_fields(self):
        health = [t for t in TOOLS if t["name"] == "meridian_health"][0]
        schema = health["inputSchema"]
        assert "model_urn" in schema["properties"]
        assert "model_urn" in schema["required"]

    def test_playbook_schema_has_required_fields(self):
        pb = [t for t in TOOLS if t["name"] == "meridian_playbook"][0]
        schema = pb["inputSchema"]
        assert "pattern_id" in schema["properties"]
        assert "pattern_id" in schema["required"]
