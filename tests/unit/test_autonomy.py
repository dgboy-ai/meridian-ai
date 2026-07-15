"""Tests for Progressive Autonomy."""
import pytest
from backend.autonomy import (
    AutonomyLevel,
    AutonomyPolicy,
    AutonomyManager,
    WORKER_POLICIES,
)


class TestAutonomyLevel:
    def test_level_values(self):
        assert AutonomyLevel.ADVISORY == 0
        assert AutonomyLevel.SUPERVISED == 1
        assert AutonomyLevel.MONITORED == 2
        assert AutonomyLevel.AUTONOMOUS == 3
        assert AutonomyLevel.SELF_IMPROVING == 4

    def test_level_ordering(self):
        assert AutonomyLevel.ADVISORY < AutonomyLevel.SUPERVISED
        assert AutonomyLevel.MONITORED < AutonomyLevel.AUTONOMOUS


class TestAutonomyPolicy:
    def test_advisory_policy(self):
        policy = AutonomyPolicy(level=AutonomyLevel.ADVISORY)
        assert policy.requires_approval is False
        assert policy.requires_review is False
        assert "Suggests" in policy.describe()

    def test_supervised_policy(self):
        policy = AutonomyPolicy(level=AutonomyLevel.SUPERVISED, requires_approval=True)
        assert policy.requires_approval is True

    def test_can_execute_within_range(self):
        policy = AutonomyPolicy(
            level=AutonomyLevel.AUTONOMOUS,
            min_confidence_for_action=0.7,
            max_confidence_for_action=0.95,
        )
        assert policy.can_execute(0.8) is True

    def test_can_execute_below_min(self):
        policy = AutonomyPolicy(
            level=AutonomyLevel.AUTONOMOUS,
            min_confidence_for_action=0.7,
        )
        assert policy.can_execute(0.5) is False

    def test_can_execute_above_max(self):
        policy = AutonomyPolicy(
            level=AutonomyLevel.AUTONOMOUS,
            max_confidence_for_action=0.9,
        )
        assert policy.can_execute(0.95) is False


class TestAutonomyManager:
    def test_get_policy_known_worker(self):
        manager = AutonomyManager()
        policy = manager.get_policy("data_sentinel")
        assert policy.level == AutonomyLevel.MONITORED

    def test_get_policy_unknown_worker(self):
        manager = AutonomyManager()
        policy = manager.get_policy("unknown_worker")
        assert policy.level == AutonomyLevel.ADVISORY

    def test_can_execute(self):
        manager = AutonomyManager()
        assert manager.can_execute("knowledge_writer", 0.9) is True

    def test_requires_approval(self):
        manager = AutonomyManager()
        assert manager.requires_approval("remediation") is True
        assert manager.requires_approval("knowledge_writer") is False

    def test_requires_review(self):
        manager = AutonomyManager()
        assert manager.requires_review("data_sentinel") is True
        assert manager.requires_review("root_cause") is False

    def test_get_level(self):
        manager = AutonomyManager()
        assert manager.get_level("data_sentinel") == AutonomyLevel.MONITORED
        assert manager.get_level("knowledge_writer") == AutonomyLevel.AUTONOMOUS

    def test_get_all_policies(self):
        manager = AutonomyManager()
        policies = manager.get_all_policies()
        assert "data_sentinel" in policies
        assert "knowledge_writer" in policies
        assert policies["data_sentinel"]["level"] == 2

    def test_custom_policies(self):
        custom = {
            "custom_worker": AutonomyPolicy(level=AutonomyLevel.SELF_IMPROVING)
        }
        manager = AutonomyManager(custom_policies=custom)
        assert manager.get_level("custom_worker") == AutonomyLevel.SELF_IMPROVING

    def test_default_policies_cover_all_workers(self):
        expected_workers = [
            "data_sentinel", "feature_drift", "root_cause",
            "knowledge_writer", "lifecycle_governance", "contract_enforcer", "remediation"
        ]
        for worker in expected_workers:
            assert worker in WORKER_POLICIES
