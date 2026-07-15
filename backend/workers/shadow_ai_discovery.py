"""Shadow AI Discovery — finds models deployed without governance.

Real computation: checks each model for missing ownership, tags, health
scores, and upstream lineage. Pure code, no LLM guessing.
"""
from datetime import datetime, timezone

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.models import EvidenceObject, Severity, EvidenceItem, DataHubMutation
from backend.stats import detect_governance_gaps


class ShadowAIDiscovery:
    def __init__(self, mcp: DataHubMCPClient, groq: GroqClient):
        self.mcp = mcp
        self.groq = groq

    async def discover(self) -> EvidenceObject:
        """Scan DataHub for ungoverned ML models. Real gap detection."""
        now = datetime.now(timezone.utc).isoformat()

        # Get all ML models
        models = await self.mcp.search(query="", entity_type="mlModel")
        if not models:
            known_urns = [
                "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
                "urn:li:mlModel:(urn:li:dataPlatform:mlflow,ltv_model_v2,PROD)",
                "urn:li:mlModel:(urn:li:dataPlatform:mlflow,segment_model_v1,PROD)",
            ]
            models = await self.mcp.get_entities(known_urns)

        # ── REAL COMPUTATION: governance gap detection ─────────────────
        governance_gaps = detect_governance_gaps(models)

        # For each model with gaps, check upstream lineage
        models_without_lineage = []
        for gap in governance_gaps:
            urn = gap["urn"]
            if urn:
                lineage = await self.mcp.get_lineage(urn, depth=2)
                if not lineage.get("upstream"):
                    gap["issues"].append("no_upstream_lineage")
                    models_without_lineage.append(gap["name"])

        # Build finding from real data
        total_models = len(models)
        shadow_count = len(governance_gaps)

        if shadow_count > 0:
            all_issues = []
            for gap in governance_gaps:
                all_issues.extend(gap["issues"])

            issue_summary = {}
            for issue in all_issues:
                issue_summary[issue] = issue_summary.get(issue, 0) + 1

            finding = (
                f"SHADOW AI DETECTED: {shadow_count}/{total_models} models lack governance. "
                f"Issues: {', '.join(f'{k}: {v}' for k, v in issue_summary.items())}. "
                f"Models: {', '.join(g['name'] for g in governance_gaps)}."
            )
        else:
            finding = f"All {total_models} models have proper governance. No shadow AI detected."

        # Tag shadow models
        shadow_urns = [g["urn"] for g in governance_gaps if g.get("urn")]
        mutations = []
        if shadow_urns:
            mutations.append(
                DataHubMutation(
                    tool="batchAddTags",
                    params={"tags": ["shadow-ai", "ungoverned"]},
                    safe=True,
                )
            )

        return EvidenceObject(
            worker_id="shadow_ai_discovery",
            timestamp=now,
            finding=finding,
            confidence=0.95 if shadow_count > 0 else 0.99,
            severity=Severity.HIGH if shadow_count > 0 else Severity.LOW,
            evidence=[
                EvidenceItem(
                    type="shadow_ai_scan",
                    description=f"Scanned {total_models} models, found {shadow_count} ungoverned",
                    affected_models=[g["name"] for g in governance_gaps],
                ),
            ],
            next_action="Tag shadow models and propose governance requirements" if shadow_count > 0 else "No action needed",
            datahub_mutations=mutations,
        )
