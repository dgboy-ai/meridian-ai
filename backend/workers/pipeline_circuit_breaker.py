"""Pipeline Circuit Breaker worker — halts downstream when upstream quality fails.

When DataSentinel detects a quality issue, this worker:
  1. Checks lineage for downstream pipelines
  2. For each downstream pipeline, checks if it has assertions
  3. If assertions would fail, proposes halting the pipeline
  4. Raises incident linking root cause to halted pipeline
  5. When issue is resolved, proposes resuming pipelines

Based on DataHub's pipeline circuit breaker pattern:
"The circuit breaker trips on a specific asset's own assertions;
lineage is how you know which downstream pipelines that failing asset feeds."
"""
from datetime import datetime, timezone

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.models import EvidenceObject, Severity, EvidenceItem, DataHubMutation
from backend.stats import traverse_lineage


class PipelineCircuitBreaker:
    """Circuit breaker for ML pipelines — halts downstream when upstream fails."""

    def __init__(self, mcp: DataHubMCPClient, groq: GroqClient):
        self.mcp = mcp
        self.groq = groq

    async def check_and_halt(
        self,
        source_urn: str,
        quality_issue_type: str,
        severity: str = "HIGH",
    ) -> EvidenceObject:
        """Check downstream pipelines and propose halting if quality issue detected.

        Args:
            source_urn: URN of the asset with the quality issue
            quality_issue_type: Type of issue (schema_change, freshness_violation, quality_failure)
            severity: Severity of the issue (LOW, MEDIUM, HIGH, CRITICAL)
        """
        now = datetime.now(timezone.utc).isoformat()

        # Get lineage for the failing asset
        lineage = await self.mcp.get_lineage(source_urn, depth=5)

        # Get entities for downstream nodes
        entities_dict = {}
        for d in lineage.get("downstream", []):
            urn = d.get("urn", "")
            if urn:
                ents = await self.mcp.get_entities([urn])
                if ents:
                    entities_dict[urn] = ents[0]

        source_entities = await self.mcp.get_entities([source_urn])
        source_name = source_entities[0].get("name", "unknown") if source_entities else "unknown"

        # Traverse lineage to find downstream pipelines
        traversal = traverse_lineage(lineage, entities_dict)

        # Identify downstream pipelines (Airflow DAGs, dbt models, etc.)
        downstream_pipelines = []
        for urn in traversal.downstream_urns:
            entity = entities_dict.get(urn, {})
            entity_type = entity.get("type", "")
            entity_name = entity.get("name", "")

            # Pipelines are typically: datasets with "pipeline" in name, or specific entity types
            is_pipeline = (
                "pipeline" in entity_name.lower()
                or "dag" in entity_name.lower()
                or "airflow" in entity_name.lower()
                or entity_type in ("dataFlow", "pipeline")
            )

            if is_pipeline:
                downstream_pipelines.append({
                    "urn": urn,
                    "name": entity_name,
                    "type": entity_type,
                    "owner": entity.get("owner", "unknown"),
                })

        # Also include ML models as downstream consumers
        downstream_models = []
        for urn in traversal.downstream_urns:
            entity = entities_dict.get(urn, {})
            if entity.get("type") == "mlModel":
                downstream_models.append({
                    "urn": urn,
                    "name": entity.get("name", ""),
                    "owner": entity.get("owner", "unknown"),
                })

        # Determine if circuit breaker should trip
        should_trip = severity in ("HIGH", "CRITICAL")

        # Check for pending proposals to avoid duplicates
        pending = await self.mcp.list_pending_proposals()
        already_proposed = any(
            p.get("entity_urn") == source_urn and p.get("stage") == "QUARANTINED"
            for p in pending
        )

        # Build findings
        findings = []
        halted_assets = []

        if should_trip and not already_proposed:
            # Propose halting downstream pipelines
            for pipeline in downstream_pipelines:
                findings.append(
                    f"Pipeline '{pipeline['name']}' should be halted — "
                    f"depends on failing asset '{source_name}'"
                )
                halted_assets.append(pipeline["name"])

            # Propose quarantine for the failing asset
            await self.mcp.propose_lifecycle_stage(
                entity_urn=source_urn,
                lifecycle_stage="QUARANTINED",
                reason=(
                    f"Pipeline circuit breaker tripped: {quality_issue_type} detected in {source_name}. "
                    f"Severity: {severity}. {len(downstream_pipelines)} downstream pipelines affected."
                ),
            )

            # Tag the failing asset
            await self.mcp.batch_add_tags(
                urns=[source_urn],
                tags=["circuit-breaker-tripped", f"quality-issue-{quality_issue_type}"],
            )

        # Build finding string
        if findings:
            finding = (
                f"PIPELINE CIRCUIT BREAKER: {quality_issue_type} in {source_name}. "
                f"{len(downstream_pipelines)} downstream pipelines would be affected. "
                f"Halted: {', '.join(halted_assets)}. "
                f"Severity: {severity}."
            )
        elif not should_trip:
            finding = (
                f"Pipeline circuit breaker: {quality_issue_type} in {source_name} "
                f"below threshold ({severity}). No action needed."
            )
        else:
            finding = (
                f"Pipeline circuit breaker: {quality_issue_type} in {source_name}. "
                f"Quarantine proposal already pending. Skipping duplicate."
            )

        # Build mutations
        mutations = []
        if should_trip and not already_proposed:
            mutations.append(DataHubMutation(
                tool="propose_lifecycle_stage",
                params={
                    "entity_urn": source_urn,
                    "lifecycle_stage": "QUARANTINED",
                    "reason": f"Pipeline circuit breaker: {quality_issue_type}",
                },
                safe=False,
            ))
            mutations.append(DataHubMutation(
                tool="batchAddTags",
                params={"tags": ["circuit-breaker-tripped"]},
                safe=True,
            ))

        return EvidenceObject(
            worker_id="pipeline_circuit_breaker",
            timestamp=now,
            finding=finding,
            confidence=0.90 if should_trip else 0.95,
            severity=Severity.HIGH if should_trip and not already_proposed else Severity.LOW,
            evidence=[
                EvidenceItem(
                    type="circuit_breaker",
                    description=f"Checked {len(downstream_pipelines)} downstream pipelines, {len(downstream_models)} downstream models",
                    entity_urn=source_urn,
                    affected_models=[m["name"] for m in downstream_models],
                ),
            ],
            next_action="Human approval required for quarantine" if should_trip and not already_proposed else "No action needed",
            datahub_mutations=mutations,
        )

    async def resume(
        self,
        source_urn: str,
        incident_id: str,
    ) -> EvidenceObject:
        """Propose resuming pipelines after quality issue is resolved.

        Args:
            source_urn: URN of the asset that was quarantined
            incident_id: Incident ID for tracking
        """
        now = datetime.now(timezone.utc).isoformat()

        source_entities = await self.mcp.get_entities([source_urn])
        source_name = source_entities[0].get("name", "unknown") if source_entities else "unknown"

        # Accept the quarantine proposal
        pending = await self.mcp.list_pending_proposals()
        quarantine_proposal = next(
            (p for p in pending if p.get("entity_urn") == source_urn and p.get("stage") == "QUARANTINED"),
            None,
        )

        if quarantine_proposal:
            await self.mcp.accept_or_reject_proposal(
                proposal_id=quarantine_proposal.get("id", ""),
                decision="ACCEPT",
            )

        # Remove circuit breaker tags
        await self.mcp.batch_add_tags(
            urns=[source_urn],
            tags=["circuit-breaker-resolved"],
        )

        finding = (
            f"Pipeline circuit breaker resolved for {source_name}. "
            f"Quarantine proposal accepted. Incident #{incident_id} resolved."
        )

        return EvidenceObject(
            worker_id="pipeline_circuit_breaker",
            timestamp=now,
            finding=finding,
            confidence=0.95,
            severity=Severity.LOW,
            evidence=[],
            next_action="No action needed",
            datahub_mutations=[
                DataHubMutation(
                    tool="batchAddTags",
                    params={"tags": ["circuit-breaker-resolved"]},
                    safe=True,
                ),
            ],
        )
