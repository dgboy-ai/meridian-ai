"""SLA Compliance Tracking — tracks model health SLAs.

"DataHub tracks SLA; we could add model SLA tracking."

This module:
  1. Defines SLA policies for ML models
  2. Tracks compliance against SLA thresholds
  3. Detects SLA violations and raises alerts
  4. Computes SLA compliance metrics
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger("meridian-ai.sla_tracker")


class SLAStatus(str, Enum):
    COMPLIANT = "compliant"
    VIOLATED = "violated"
    WARNING = "warning"
    UNKNOWN = "unknown"


@dataclass
class SLAPolicy:
    """SLA policy for a model or dataset."""
    policy_id: str
    name: str
    description: str
    metric_name: str  # e.g., "health_score", "freshness_hours", "accuracy"
    threshold: float  # e.g., 80.0 for health_score
    operator: str = "gte"  # "gte", "lte", "eq", "gt", "lt"
    severity: str = "high"  # "low", "medium", "high", "critical"
    entity_type: str = "mlModel"  # "mlModel", "dataset", etc.
    enabled: bool = True

    def check(self, value: float) -> SLAStatus:
        """Check if a value meets the SLA threshold."""
        if self.operator == "gte":
            return SLAStatus.COMPLIANT if value >= self.threshold else SLAStatus.VIOLATED
        elif self.operator == "lte":
            return SLAStatus.COMPLIANT if value <= self.threshold else SLAStatus.VIOLATED
        elif self.operator == "gt":
            return SLAStatus.COMPLIANT if value > self.threshold else SLAStatus.VIOLATED
        elif self.operator == "lt":
            return SLAStatus.COMPLIANT if value < self.threshold else SLAStatus.VIOLATED
        elif self.operator == "eq":
            return SLAStatus.COMPLIANT if value == self.threshold else SLAStatus.VIOLATED
        return SLAStatus.UNKNOWN

    def to_dict(self) -> dict:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "description": self.description,
            "metric_name": self.metric_name,
            "threshold": self.threshold,
            "operator": self.operator,
            "severity": self.severity,
            "entity_type": self.entity_type,
            "enabled": self.enabled,
        }


@dataclass
class SLACheckResult:
    """Result of an SLA check."""
    policy_id: str
    entity_urn: str
    entity_name: str
    metric_name: str
    current_value: float
    threshold: float
    status: SLAStatus
    checked_at: str = ""

    def to_dict(self) -> dict:
        return {
            "policy_id": self.policy_id,
            "entity_urn": self.entity_urn,
            "entity_name": self.entity_name,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "status": self.status.value,
            "checked_at": self.checked_at,
        }


class SLATracker:
    """Track SLA compliance for ML models and datasets."""

    def __init__(self):
        self._policies: dict[str, SLAPolicy] = {}
        self._results: dict[str, list[SLACheckResult]] = {}
        self._violations: list[SLACheckResult] = []

        # Default policies
        self._add_default_policies()

    def _add_default_policies(self):
        """Add default SLA policies for common metrics."""
        self.add_policy(SLAPolicy(
            policy_id="health_score_minimum",
            name="Minimum Health Score",
            description="Model health score must be at least 60",
            metric_name="health_score",
            threshold=60.0,
            operator="gte",
            severity="high",
            entity_type="mlModel",
        ))

        self.add_policy(SLAPolicy(
            policy_id="health_score_target",
            name="Target Health Score",
            description="Model health score should be at least 80",
            metric_name="health_score",
            threshold=80.0,
            operator="gte",
            severity="medium",
            entity_type="mlModel",
        ))

        self.add_policy(SLAPolicy(
            policy_id="confidence_minimum",
            name="Minimum Confidence",
            description="Model confidence must be at least 0.7",
            metric_name="confidence",
            threshold=0.7,
            operator="gte",
            severity="high",
            entity_type="mlModel",
        ))

        self.add_policy(SLAPolicy(
            policy_id="freshness_dataset",
            name="Dataset Freshness",
            description="Dataset must be updated within 24 hours",
            metric_name="freshness_hours",
            threshold=24.0,
            operator="lte",
            severity="medium",
            entity_type="dataset",
        ))

    def add_policy(self, policy: SLAPolicy):
        """Add an SLA policy."""
        self._policies[policy.policy_id] = policy

    def remove_policy(self, policy_id: str):
        """Remove an SLA policy."""
        self._policies.pop(policy_id, None)

    def check_entity(
        self,
        entity_urn: str,
        entity_name: str,
        entity_type: str,
        metrics: dict[str, float],
    ) -> list[SLACheckResult]:
        """Check all applicable SLA policies for an entity.

        Args:
            entity_urn: URN of the entity
            entity_name: Name of the entity
            entity_type: Type of entity (mlModel, dataset, etc.)
            metrics: Dict of metric_name -> current_value

        Returns:
            List of SLACheckResult objects
        """
        results = []
        now = datetime.now(timezone.utc).isoformat()

        for policy in self._policies.values():
            if not policy.enabled:
                continue
            if policy.entity_type != entity_type:
                continue
            if policy.metric_name not in metrics:
                continue

            current_value = metrics[policy.metric_name]
            status = policy.check(current_value)

            result = SLACheckResult(
                policy_id=policy.policy_id,
                entity_urn=entity_urn,
                entity_name=entity_name,
                metric_name=policy.metric_name,
                current_value=current_value,
                threshold=policy.threshold,
                status=status,
                checked_at=now,
            )

            results.append(result)

            # Track violations
            if status == SLAStatus.VIOLATED:
                self._violations.append(result)
                logger.warning(
                    f"SLA violation: {policy.name} for {entity_name} "
                    f"({policy.metric_name}={current_value}, threshold={policy.threshold})"
                )

            # Store result
            if entity_urn not in self._results:
                self._results[entity_urn] = []
            self._results[entity_urn].append(result)

        return results

    def get_violations(self, entity_urn: str | None = None) -> list[dict]:
        """Get SLA violations, optionally filtered by entity."""
        if entity_urn:
            return [v.to_dict() for v in self._violations if v.entity_urn == entity_urn]
        return [v.to_dict() for v in self._violations]

    def get_compliance_summary(self, entity_urn: str | None = None) -> dict:
        """Get SLA compliance summary."""
        results = []
        if entity_urn:
            results = self._results.get(entity_urn, [])
        else:
            for entity_results in self._results.values():
                results.extend(entity_results)

        if not results:
            return {
                "total_checks": 0,
                "compliant": 0,
                "violated": 0,
                "compliance_rate": 100.0,
            }

        compliant = sum(1 for r in results if r.status == SLAStatus.COMPLIANT)
        violated = sum(1 for r in results if r.status == SLAStatus.VIOLATED)

        return {
            "total_checks": len(results),
            "compliant": compliant,
            "violated": violated,
            "compliance_rate": round(compliant / len(results) * 100, 2),
        }

    def get_policies(self) -> list[dict]:
        """Get all SLA policies."""
        return [p.to_dict() for p in self._policies.values()]
