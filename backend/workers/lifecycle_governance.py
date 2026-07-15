"""Lifecycle Governance worker — proposes DEPRECATED for chronically failing models."""
from datetime import datetime, timezone

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.models import EvidenceObject, Severity, DataHubMutation


class LifecycleGovernance:
    def __init__(self, mcp: DataHubMCPClient, groq: GroqClient):
        self.mcp = mcp
        self.groq = groq

    async def evaluate(
        self,
        model_urn: str,
        model_name: str,
        health_score: int,
        consecutive_failures: int,
        pattern_id: str,
        incident_id: str,
    ) -> EvidenceObject:
        now = datetime.now(timezone.utc).isoformat()

        # Check if proposal already pending
        pending = await self.mcp.list_pending_proposals()
        already_proposed = any(
            p.get("entity_urn") == model_urn and p.get("stage") == "DEPRECATED"
            for p in pending
        )

        if already_proposed:
            return EvidenceObject(
                worker_id="lifecycle_governance",
                timestamp=now,
                finding=f"Lifecycle proposal for {model_name} already pending — skipped duplicate",
                confidence=1.0,
                severity=Severity.LOW,
                datahub_mutations=[],
            )

        # Determine if lifecycle change is warranted
        should_propose = health_score < 60 and consecutive_failures >= 3

        if should_propose:
            reason = (
                f"AI Sentinel: health score {health_score} for {consecutive_failures} "
                f"consecutive incidents. Pattern: {pattern_id}. See incident #{incident_id}."
            )

            await self.mcp.propose_lifecycle_stage(
                entity_urn=model_urn,
                lifecycle_stage="DEPRECATED",
                reason=reason,
            )

            return EvidenceObject(
                worker_id="lifecycle_governance",
                timestamp=now,
                finding=f"Proposed DEPRECATED lifecycle for {model_name} — health score {health_score} below threshold for {consecutive_failures} consecutive incidents",
                confidence=0.92,
                severity=Severity.HIGH,
                evidence=[],
                business_impact=None,
                next_action="Human approval required for lifecycle change",
                datahub_mutations=[
                    DataHubMutation(
                        tool="propose_lifecycle_stage",
                        params={"entity_urn": model_urn, "lifecycle_stage": "DEPRECATED", "reason": reason},
                        safe=False,
                    ),
                ],
            )
        else:
            reasons = []
            if health_score >= 60:
                reasons.append(f"health score {health_score} above threshold 60")
            if consecutive_failures < 3:
                reasons.append(f"{consecutive_failures} consecutive failures below threshold 3")

            return EvidenceObject(
                worker_id="lifecycle_governance",
                timestamp=now,
                finding=f"Lifecycle change not warranted for {model_name} — {', '.join(reasons)}",
                confidence=0.95,
                severity=Severity.LOW,
                datahub_mutations=[],
            )
