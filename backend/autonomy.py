"""Progressive Autonomy — 5 levels of agent autonomy based on action severity.

Based on strategy document lines 251-259:
- Level 0: Advisory — Suggests; human executes
- Level 1: Supervised — Executes with pre-approval
- Level 2: Monitored — Executes; human reviews post-hoc
- Level 3: Autonomous — Executes without human involvement
- Level 4: Self-improving — Refines its own procedures via reflexion
"""
from dataclasses import dataclass
from enum import IntEnum


class AutonomyLevel(IntEnum):
    ADVISORY = 0      # Suggests; human executes
    SUPERVISED = 1    # Executes with pre-approval
    MONITORED = 2     # Executes; human reviews post-hoc
    AUTONOMOUS = 3    # Executes without human involvement
    SELF_IMPROVING = 4  # Refines its own procedures via reflexion


@dataclass
class AutonomyPolicy:
    """Policy for a specific worker's autonomy level."""
    level: AutonomyLevel
    requires_approval: bool = False
    requires_review: bool = False
    can_self_improve: bool = False
    max_confidence_for_action: float = 1.0
    min_confidence_for_action: float = 0.0

    def can_execute(self, confidence: float) -> bool:
        """Check if the worker can execute at given confidence level."""
        if confidence < self.min_confidence_for_action:
            return False
        if confidence > self.max_confidence_for_action:
            return False
        return True

    def describe(self) -> str:
        descriptions = {
            AutonomyLevel.ADVISORY: "Suggests; human executes",
            AutonomyLevel.SUPERVISED: "Executes with pre-approval",
            AutonomyLevel.MONITORED: "Executes; human reviews post-hoc",
            AutonomyLevel.AUTONOMOUS: "Executes without human involvement",
            AutonomyLevel.SELF_IMPROVING: "Refines its own procedures via reflexion",
        }
        return descriptions.get(self.level, "Unknown")


# Default policies for each worker
WORKER_POLICIES: dict[str, AutonomyPolicy] = {
    "data_sentinel": AutonomyPolicy(
        level=AutonomyLevel.MONITORED,
        requires_approval=False,
        requires_review=True,
        min_confidence_for_action=0.7,
    ),
    "feature_drift": AutonomyPolicy(
        level=AutonomyLevel.MONITORED,
        requires_approval=False,
        requires_review=True,
        min_confidence_for_action=0.7,
    ),
    "root_cause": AutonomyPolicy(
        level=AutonomyLevel.ADVISORY,
        requires_approval=False,
        requires_review=False,
        min_confidence_for_action=0.5,
    ),
    "knowledge_writer": AutonomyPolicy(
        level=AutonomyLevel.AUTONOMOUS,
        requires_approval=False,
        requires_review=False,
        min_confidence_for_action=0.8,
    ),
    "lifecycle_governance": AutonomyPolicy(
        level=AutonomyLevel.AUTONOMOUS,
        requires_approval=False,
        requires_review=False,
        min_confidence_for_action=0.85,
    ),
    "contract_enforcer": AutonomyPolicy(
        level=AutonomyLevel.AUTONOMOUS,
        requires_approval=False,
        requires_review=False,
        min_confidence_for_action=0.9,
    ),
    "remediation": AutonomyPolicy(
        level=AutonomyLevel.SUPERVISED,
        requires_approval=True,
        requires_review=False,
        min_confidence_for_action=0.8,
    ),
}


class AutonomyManager:
    """Manage autonomy levels for workers."""

    def __init__(self, custom_policies: dict[str, AutonomyPolicy] | None = None) -> None:
        self.policies = {**WORKER_POLICIES}
        if custom_policies:
            self.policies.update(custom_policies)

    def get_policy(self, worker_id: str) -> AutonomyPolicy:
        """Get autonomy policy for a worker."""
        return self.policies.get(worker_id, AutonomyPolicy(level=AutonomyLevel.ADVISORY))

    def can_execute(self, worker_id: str, confidence: float) -> bool:
        """Check if a worker can execute an action."""
        policy = self.get_policy(worker_id)
        return policy.can_execute(confidence)

    def requires_approval(self, worker_id: str) -> bool:
        """Check if a worker requires human approval."""
        policy = self.get_policy(worker_id)
        return policy.requires_approval

    def requires_review(self, worker_id: str) -> bool:
        """Check if a worker's action requires post-hoc review."""
        policy = self.get_policy(worker_id)
        return policy.requires_review

    def get_level(self, worker_id: str) -> AutonomyLevel:
        """Get autonomy level for a worker."""
        policy = self.get_policy(worker_id)
        return policy.level

    def get_all_policies(self) -> dict[str, dict]:
        """Get all worker policies as dicts."""
        return {
            worker_id: {
                "level": policy.level.value,
                "level_name": policy.level.name,
                "description": policy.describe(),
                "requires_approval": policy.requires_approval,
                "requires_review": policy.requires_review,
            }
            for worker_id, policy in self.policies.items()
        }
