"""Tests for Actions Framework Auto-Trigger."""
import pytest
import asyncio
from backend.actions.auto_investigate import AutoInvestigateAction


class TestAutoInvestigateAction:
    def test_init_default(self):
        action = AutoInvestigateAction(config={})
        assert action.api_endpoint == "http://localhost:8000"
        assert action.autonomy_level == 2
        assert action.min_severity == "MEDIUM"

    def test_init_custom(self):
        action = AutoInvestigateAction(config={
            "api_endpoint": "http://custom:9000",
            "autonomy_level": 3,
            "min_severity": "HIGH",
        })
        assert action.api_endpoint == "http://custom:9000"
        assert action.autonomy_level == 3
        assert action.min_severity == "HIGH"

    @pytest.mark.asyncio
    async def test_handle_schema_change(self):
        action = AutoInvestigateAction(config={"min_severity": "MEDIUM"})
        result = await action.handle({
            "event_type": "EntityChangeEvent_v1",
            "entity_urn": "urn:li:dataset:test",
            "aspect": "schemaMetadata",
        })
        assert result["status"] == "investigation_started"
        assert "investigation_id" in result
        assert result["trigger_event"]["severity"] == "HIGH"

    @pytest.mark.asyncio
    async def test_handle_ownership_change(self):
        action = AutoInvestigateAction(config={"min_severity": "MEDIUM"})
        result = await action.handle({
            "event_type": "EntityChangeEvent_v1",
            "entity_urn": "urn:li:dataset:test",
            "aspect": "ownership",
        })
        assert result["status"] == "investigation_started"
        assert result["trigger_event"]["severity"] == "HIGH"

    @pytest.mark.asyncio
    async def test_handle_low_severity_skipped(self):
        action = AutoInvestigateAction(config={"min_severity": "HIGH"})
        result = await action.handle({
            "event_type": "EntityChangeEvent_v1",
            "entity_urn": "urn:li:dataset:test",
            "aspect": "description",
        })
        assert result["status"] == "skipped"
        assert "below threshold" in result["reason"]

    @pytest.mark.asyncio
    async def test_handle_medium_severity(self):
        action = AutoInvestigateAction(config={"min_severity": "MEDIUM"})
        result = await action.handle({
            "event_type": "EntityChangeEvent_v1",
            "entity_urn": "urn:li:dataset:test",
            "aspect": "editableSchemaMetadata",
        })
        assert result["status"] == "investigation_started"
        assert result["trigger_event"]["severity"] == "MEDIUM"

    def test_assess_severity_schema(self):
        action = AutoInvestigateAction(config={})
        assert action._assess_severity({"aspect": "schemaMetadata"}) == "HIGH"

    def test_assess_severity_ownership(self):
        action = AutoInvestigateAction(config={})
        assert action._assess_severity({"aspect": "ownership"}) == "HIGH"

    def test_assess_severity_description(self):
        action = AutoInvestigateAction(config={})
        assert action._assess_severity({"aspect": "description"}) == "LOW"

    def test_should_investigate_high(self):
        action = AutoInvestigateAction(config={"min_severity": "MEDIUM"})
        assert action._should_investigate("HIGH") is True

    def test_should_investigate_low(self):
        action = AutoInvestigateAction(config={"min_severity": "MEDIUM"})
        assert action._should_investigate("LOW") is False

    def test_get_stats(self):
        action = AutoInvestigateAction(config={})
        stats = action.get_stats()
        assert "total_investigations" in stats
        assert "autonomy_level" in stats
