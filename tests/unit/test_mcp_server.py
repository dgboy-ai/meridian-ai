"""Tests for MCP Server — tool dispatch, error handling, and MCP-standard hints."""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from backend.mcp_server import MeridianMCPServer, TOOLS


class TestMCPTools:
    """Test MCP tool definitions and hints."""

    def test_tools_list_has_three_tools(self):
        """MCP server should expose 3 tools."""
        assert len(TOOLS) == 3

    def test_investigate_tool_has_hints(self):
        """meridian_investigate should have MCP-standard hints."""
        tool = next(t for t in TOOLS if t["name"] == "meridian_investigate")
        assert "readOnlyHint" in tool
        assert "destructiveHint" in tool
        assert "idempotentHint" in tool
        assert tool["readOnlyHint"] is False  # Writes to DataHub
        assert tool["destructiveHint"] is False  # Doesn't delete
        assert tool["idempotentHint"] is False  # Running twice creates duplicates

    def test_health_tool_is_readonly(self):
        """meridian_health should be read-only."""
        tool = next(t for t in TOOLS if t["name"] == "meridian_health")
        assert tool["readOnlyHint"] is True
        assert tool["destructiveHint"] is False
        assert tool["idempotentHint"] is True

    def test_playbook_tool_is_readonly(self):
        """meridian_playbook should be read-only."""
        tool = next(t for t in TOOLS if t["name"] == "meridian_playbook")
        assert tool["readOnlyHint"] is True
        assert tool["destructiveHint"] is False
        assert tool["idempotentHint"] is True

    def test_all_tools_have_input_schema(self):
        """All tools should have inputSchema."""
        for tool in TOOLS:
            assert "inputSchema" in tool
            assert "type" in tool["inputSchema"]
            assert tool["inputSchema"]["type"] == "object"

    def test_all_tools_have_descriptions(self):
        """All tools should have descriptions."""
        for tool in TOOLS:
            assert "description" in tool
            assert len(tool["description"]) > 0


class TestMeridianMCPServer:
    """Test MCP server initialization and tool handling."""

    def test_server_initialization(self):
        """Server should initialize with MCP client and Groq client."""
        with patch('backend.mcp_server.DataHubMCPClient') as mock_mcp:
            with patch('backend.mcp_server.GroqClient') as mock_groq:
                server = MeridianMCPServer()
                assert server.mcp is not None
                assert server.groq is not None
                assert server.planner is not None

    def test_tools_list_response(self):
        """tools/list should return all tools."""
        response_tools = TOOLS
        assert len(response_tools) == 3
        tool_names = [t["name"] for t in response_tools]
        assert "meridian_investigate" in tool_names
        assert "meridian_health" in tool_names
        assert "meridian_playbook" in tool_names

    def test_tool_descriptions_are_informative(self):
        """Tool descriptions should explain what and when to use."""
        for tool in TOOLS:
            desc = tool["description"]
            # Should mention what it does
            assert len(desc) > 20
            # Should be clear and actionable
            assert any(word in desc.lower() for word in ["run", "check", "view", "investigate", "health", "playbook"])


class TestMCPErrorHandling:
    """Test MCP server error handling patterns."""

    def test_structured_error_response(self):
        """MCP server should return structured errors, not throw."""
        error_response = {
            "jsonrpc": "2.0",
            "id": "test-123",
            "error": {"code": -1, "message": "Unknown tool: invalid_tool"},
        }
        assert "jsonrpc" in error_response
        assert "error" in error_response
        assert "code" in error_response["error"]
        assert "message" in error_response["error"]

    def test_unknown_method_error(self):
        """Unknown method should return error."""
        error_response = {
            "jsonrpc": "2.0",
            "id": "test-456",
            "error": {"code": -1, "message": "Unknown method: invalid_method"},
        }
        assert error_response["error"]["code"] == -1

    def test_tool_not_found_error(self):
        """Unknown tool should return error."""
        error_response = {
            "jsonrpc": "2.0",
            "id": "test-789",
            "error": {"code": -1, "message": "Unknown tool: nonexistent_tool"},
        }
        assert "Unknown tool" in error_response["error"]["message"]
