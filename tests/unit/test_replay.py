"""Tests for Replay Driver."""
import pytest
import asyncio
from backend.replay import ReplayDriver


class TestReplayDriver:
    def test_list_incidents(self):
        driver = ReplayDriver()
        incidents = driver.list_incidents()
        assert len(incidents) == 6
        assert any(i["id"] == "42" for i in incidents)
        assert any(i["id"] == "55" for i in incidents)
        assert any(i["id"] == "61" for i in incidents)
        assert any(i["id"] == "68" for i in incidents)

    def test_get_incident(self):
        driver = ReplayDriver()
        incident = driver.get_incident("42")
        assert incident is not None
        assert incident["id"] == "42"
        assert len(incident["timeline"]) > 0

    def test_get_incident_not_found(self):
        driver = ReplayDriver()
        incident = driver.get_incident("999")
        assert incident is None

    def test_get_resolution_times(self):
        driver = ReplayDriver()
        times = driver.get_resolution_times()
        assert len(times) == 6
        assert all("duration_minutes" in t for t in times)

    @pytest.mark.asyncio
    async def test_stream_investigation(self):
        driver = ReplayDriver()
        events = []
        async for event in driver.stream_investigation("42", delay=0.01):
            events.append(event)
        assert len(events) > 0
        assert events[-1].get("status") == "done"

    @pytest.mark.asyncio
    async def test_stream_investigation_not_found(self):
        driver = ReplayDriver()
        events = []
        async for event in driver.stream_investigation("999", delay=0.01):
            events.append(event)
        assert len(events) == 1
        assert events[0]["step"] == "error"
        assert events[0]["status"] == "failed"
