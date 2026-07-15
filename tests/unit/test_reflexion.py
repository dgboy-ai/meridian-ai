"""Tests for Reflexion Loop."""
import pytest
from backend.reflexion import ReflexionLoop, ReflexionResult


class TestReflexionResult:
    def test_creation(self):
        result = ReflexionResult(
            incident_id="42",
            pattern_id="schema-change",
            previous_playbook="Old playbook",
            new_playbook="New playbook",
            improvement_notes="Time reduced",
            resolution_time_before=18,
            resolution_time_after=3,
            confidence=0.92,
        )
        assert result.incident_id == "42"
        assert result.resolution_time_before == 18
        assert result.resolution_time_after == 3

    def test_to_dict(self):
        result = ReflexionResult(
            incident_id="42",
            pattern_id="schema-change",
            previous_playbook=None,
            new_playbook="New",
            improvement_notes="Improved",
            resolution_time_before=18,
            resolution_time_after=3,
            confidence=0.92,
        )
        d = result.to_dict()
        assert d["incident_id"] == "42"
        assert d["previous_playbook"] is None
        assert d["confidence"] == 0.92

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
