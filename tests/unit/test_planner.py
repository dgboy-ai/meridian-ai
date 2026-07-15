"""Tests for Planner Agent."""
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


class TestPlannerAgent:
    @pytest.mark.asyncio
    async def test_investigate_returns_events(self, planner):
        events = []
        async for event in planner.investigate(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            incident_id="TEST",
        ):
            events.append(event)
        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_investigate_has_all_workers(self, planner):
        events = []
        async for event in planner.investigate(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            incident_id="TEST",
        ):
            events.append(event)
        steps = [e.get("step") for e in events]
        assert "data_sentinel" in steps
        assert "feature_drift" in steps
        assert "root_cause" in steps
        assert "knowledge_writer" in steps
        assert "lifecycle_governance" in steps

    @pytest.mark.asyncio
    async def test_investigate_completes(self, planner):
        events = []
        async for event in planner.investigate(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            incident_id="TEST",
        ):
            events.append(event)
        assert events[-1].get("status") == "completed"

    @pytest.mark.asyncio
    async def test_investigate_has_summary(self, planner):
        events = []
        async for event in planner.investigate(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            incident_id="TEST",
        ):
            events.append(event)
        last = events[-1]
        assert "summary" in last
        assert "workers_fired" in last["summary"]
