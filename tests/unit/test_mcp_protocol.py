"""Tests for MCP server — official SDK tool definitions and schemas."""
import json
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from backend.mcp_server import TOOLS, list_tools, call_tool
from mcp.types import Tool


class TestMCPTools:
    def test_tools_list_returns_all_tools(self):
        assert len(TOOLS) == 3
        tool_names = [t.name for t in TOOLS]
        assert "meridian_investigate" in tool_names
        assert "meridian_health" in tool_names
        assert "meridian_playbook" in tool_names

    def test_tools_are_mcp_tool_instances(self):
        for tool in TOOLS:
            assert isinstance(tool, Tool)

    def test_all_tools_have_descriptions(self):
        for tool in TOOLS:
            assert tool.description is not None
            assert len(tool.description) > 20

    def test_investigate_tool_description_mentions_writes(self):
        inv = next(t for t in TOOLS if t.name == "meridian_investigate")
        assert "modif" in inv.description.lower() or "write" in inv.description.lower()

    def test_health_tool_description_mentions_readonly(self):
        health = next(t for t in TOOLS if t.name == "meridian_health")
        assert "read" in health.description.lower()


class TestMCPSchema:
    def test_investigate_schema_has_required_fields(self):
        inv = next(t for t in TOOLS if t.name == "meridian_investigate")
        schema = inv.inputSchema
        assert "model_urn" in schema["properties"]
        assert "model_urn" in schema["required"]

    def test_health_schema_has_required_fields(self):
        health = next(t for t in TOOLS if t.name == "meridian_health")
        schema = health.inputSchema
        assert "model_urn" in schema["properties"]
        assert "model_urn" in schema["required"]

    def test_playbook_schema_has_required_fields(self):
        pb = next(t for t in TOOLS if t.name == "meridian_playbook")
        schema = pb.inputSchema
        assert "pattern_id" in schema["properties"]
        assert "pattern_id" in schema["required"]

    def test_all_schemas_are_object_type(self):
        for tool in TOOLS:
            assert tool.inputSchema["type"] == "object"

    def test_all_schemas_have_properties(self):
        for tool in TOOLS:
            assert "properties" in tool.inputSchema
            assert len(tool.inputSchema["properties"]) > 0


class TestMCPHandlers:
    @pytest.mark.asyncio
    async def test_call_tool_investigate_missing_urn(self):
        """Investigate with missing model_urn should return error."""
        result = await call_tool("meridian_investigate", {})
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_call_tool_health_returns_result(self):
        """Health tool should return a result."""
        result = await call_tool("meridian_health", {
            "model_urn": "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"
        })
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "health_score" in data
        assert "assessment" in data

    @pytest.mark.asyncio
    async def test_call_tool_playbook_not_found(self):
        """Playbook for nonexistent pattern should return message."""
        result = await call_tool("meridian_playbook", {
            "pattern_id": "nonexistent-pattern"
        })
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "No playbook found" in data.get("content", "")

    @pytest.mark.asyncio
    async def test_call_tool_unknown_returns_error(self):
        """Unknown tool should return error."""
        result = await call_tool("unknown_tool", {})
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data
