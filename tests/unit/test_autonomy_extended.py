"""Extended tests for Progressive Autonomy."""
import pytest
from backend.autonomy import (
    AutonomyLevel,
    AutonomyPolicy,
    AutonomyManager,
    WORKER_POLICIES,
)


class TestAutonomyExtended:
    def test_all_workers_have_policies(self):
        expected = [
            "data_sentinel", "feature_drift", "root_cause",
            "knowledge_writer", "lifecycle_governance", "contract_enforcer", "remediation"
        ]
        for worker in expected:
            assert worker in WORKER_POLICIES, f"Missing policy for {worker}"

    def test_policy_descriptions(self):
        for worker, policy in WORKER_POLICIES.items():
            desc = policy.describe()
            assert isinstance(desc, str)
            assert len(desc) > 0

    def test_manager_get_all_policies(self):
        manager = AutonomyManager()
        all_policies = manager.get_all_policies()
        assert len(all_policies) == len(WORKER_POLICIES)
        for worker_id, policy_dict in all_policies.items():
            assert "level" in policy_dict
            assert "level_name" in policy_dict
            assert "description" in policy_dict
            assert "requires_approval" in policy_dict
            assert "requires_review" in policy_dict

    def test_custom_policy_override(self):
        custom = {
            "custom_worker": AutonomyPolicy(
                level=AutonomyLevel.SELF_IMPROVING,
                requires_approval=False,
                requires_review=False,
                min_confidence_for_action=0.95,
            )
        }
        manager = AutonomyManager(custom_policies=custom)
        assert manager.get_level("custom_worker") == AutonomyLevel.SELF_IMPROVING
        assert manager.can_execute("custom_worker", 0.96) is True
        assert manager.can_execute("custom_worker", 0.90) is False

    def test_level_ordering(self):
        assert AutonomyLevel.ADVISORY < AutonomyLevel.SUPERVISED < AutonomyLevel.MONITORED
        assert AutonomyLevel.MONITORED < AutonomyLevel.AUTONOMOUS < AutonomyLevel.SELF_IMPROVING

    def test_all_levels_have_values(self):
        assert AutonomyLevel.ADVISORY.value == 0
        assert AutonomyLevel.SUPERVISED.value == 1
        assert AutonomyLevel.MONITORED.value == 2
        assert AutonomyLevel.AUTONOMOUS.value == 3
        assert AutonomyLevel.SELF_IMPROVING.value == 4
