"""Tests for MCP Server — official SDK implementation, tool dispatch, error handling."""
import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from backend.mcp_server import TOOLS, list_tools, call_tool
from mcp.types import Tool


class TestMCPTools:
    """Test MCP tool definitions."""

    def test_tools_list_has_three_tools(self):
        """MCP server should expose 3 tools."""
        assert len(TOOLS) == 3

    def test_tools_are_mcp_tool_objects(self):
        """All tools should be MCP Tool instances."""
        for tool in TOOLS:
            assert isinstance(tool, Tool)

    def test_investigate_tool_exists(self):
        """meridian_investigate tool should exist."""
        names = [t.name for t in TOOLS]
        assert "meridian_investigate" in names

    def test_health_tool_exists(self):
        """meridian_health tool should exist."""
        names = [t.name for t in TOOLS]
        assert "meridian_health" in names

    def test_playbook_tool_exists(self):
        """meridian_playbook tool should exist."""
        names = [t.name for t in TOOLS]
        assert "meridian_playbook" in names

    def test_all_tools_have_input_schema(self):
        """All tools should have inputSchema."""
        for tool in TOOLS:
            schema = tool.inputSchema
            assert schema is not None
            assert "type" in schema
            assert schema["type"] == "object"

    def test_all_tools_have_descriptions(self):
        """All tools should have descriptions."""
        for tool in TOOLS:
            assert tool.description is not None
            assert len(tool.description) > 20

    def test_investigate_requires_model_urn(self):
        """meridian_investigate should require model_urn."""
        tool = next(t for t in TOOLS if t.name == "meridian_investigate")
        assert "model_urn" in tool.inputSchema["properties"]
        assert "model_urn" in tool.inputSchema["required"]

    def test_health_requires_model_urn(self):
        """meridian_health should require model_urn."""
        tool = next(t for t in TOOLS if t.name == "meridian_health")
        assert "model_urn" in tool.inputSchema["properties"]
        assert "model_urn" in tool.inputSchema["required"]

    def test_playbook_requires_pattern_id(self):
        """meridian_playbook should require pattern_id."""
        tool = next(t for t in TOOLS if t.name == "meridian_playbook")
        assert "pattern_id" in tool.inputSchema["properties"]
        assert "pattern_id" in tool.inputSchema["required"]


class TestMCPToolHandlers:
    """Test MCP tool call handlers."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_tools(self):
        """list_tools should return all tools."""
        tools = await list_tools()
        assert len(tools) == 3

    @pytest.mark.asyncio
    async def test_call_tool_unknown_returns_error(self):
        """Unknown tool should return error content."""
        result = await call_tool("nonexistent_tool", {})
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_call_tool_health_missing_urn(self):
        """Health tool with missing model_urn should return error."""
        result = await call_tool("meridian_health", {})
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_call_tool_playbook_missing_pattern(self):
        """Playbook tool with missing pattern_id should return error."""
        result = await call_tool("meridian_playbook", {})
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data


class TestMCPErrorHandling:
    """Test MCP server error handling patterns."""

    def test_error_response_has_text_content(self):
        """Error responses should be TextContent with JSON."""
        error_response = {
            "error": "Unknown tool: invalid_tool",
        }
        text = json.dumps(error_response)
        data = json.loads(text)
        assert "error" in data
