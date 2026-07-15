"""Contract Enforcer — auto-quarantine datasets violating data contracts.

Checks DataHub assertions (quality checks, schema contracts) and proposes
lifecycle stage changes for datasets that consistently violate their contracts.
Datasets that fail assertions repeatedly get quarantined automatically.
"""
from datetime import datetime, timezone

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.models import EvidenceObject, Severity, EvidenceItem, DataHubMutation


class ContractEnforcer:
    def __init__(self, mcp: DataHubMCPClient, groq: GroqClient):
        self.mcp = mcp
        self.groq = groq

    async def enforce(
        self,
        dataset_urn: str,
        dataset_name: str,
        failed_assertions: int = 0,
        total_assertions: int = 0,
        consecutive_failures: int = 0,
    ) -> EvidenceObject:
        """Check dataset contract compliance and enforce quarantine if needed.

        Args:
            dataset_urn: URN of the dataset to check
            dataset_name: Human-readable dataset name
            failed_assertions: Number of failed assertions
            total_assertions: Total number of assertions
            consecutive_failures: How many consecutive check cycles failed
        """
        now = datetime.now(timezone.utc).isoformat()

        # Calculate failure rate
        failure_rate = failed_assertions / max(total_assertions, 1)

        # Determine if quarantine is warranted
        should_quarantine = (
            failure_rate > 0.5  # More than 50% assertions failing
            or consecutive_failures >= 3  # 3+ consecutive failures
        )

        # Check for pending proposals to avoid duplicates
        pending = await self.mcp.list_pending_proposals()
        already_proposed = any(
            p.get("entity_urn") == dataset_urn and p.get("stage") == "QUARANTINED"
            for p in pending
        )

        if should_quarantine and not already_proposed:
            reason = (
                f"Contract enforcement: {failed_assertions}/{total_assertions} assertions failed "
                f"({failure_rate:.0%} failure rate). {consecutive_failures} consecutive failures. "
                f"Auto-quarantine proposed by Meridian AI."
            )

            await self.mcp.propose_lifecycle_stage(
                entity_urn=dataset_urn,
                lifecycle_stage="QUARANTINED",
                reason=reason,
            )

            await self.mcp.batch_add_tags(
                urns=[dataset_urn],
                tags=["contract-violation", "quarantined", "auto-enforced"],
            )

            return EvidenceObject(
                worker_id="contract_enforcer",
                timestamp=now,
                finding=(
                    f"Quarantine proposed for {dataset_name}: "
                    f"{failed_assertions}/{total_assertions} assertions failed, "
                    f"{consecutive_failures} consecutive failures"
                ),
                confidence=0.90,
                severity=Severity.HIGH,
                evidence=[
                    EvidenceItem(
                        type="contract_violation",
                        description=f"Dataset {dataset_name} violated {failed_assertions}/{total_assertions} assertions",
                        entity_urn=dataset_urn,
                    ),
                ],
                next_action="Human approval required for quarantine lifecycle change",
                datahub_mutations=[
                    DataHubMutation(
                        tool="propose_lifecycle_stage",
                        params={
                            "entity_urn": dataset_urn,
                            "lifecycle_stage": "QUARANTINED",
                            "reason": reason,
                        },
                        safe=False,
                    ),
                    DataHubMutation(
                        tool="batchAddTags",
                        params={"tags": ["contract-violation", "quarantined"]},
                        safe=True,
                    ),
                ],
            )
        elif already_proposed:
            return EvidenceObject(
                worker_id="contract_enforcer",
                timestamp=now,
                finding=f"Quarantine proposal for {dataset_name} already pending — skipped duplicate",
                confidence=1.0,
                severity=Severity.LOW,
                datahub_mutations=[],
            )
        else:
            return EvidenceObject(
                worker_id="contract_enforcer",
                timestamp=now,
                finding=f"Contract compliance OK for {dataset_name}: {failed_assertions}/{total_assertions} failures within tolerance",
                confidence=0.95,
                severity=Severity.LOW,
                datahub_mutations=[],
            )
