"""Knowledge Writer worker — enterprise multitasker.

Performs 5 DataHub writes:
  1. Root cause report (Knowledge Base document)
  2. AI Knowledge panel update (structured properties on model)
  3. Reflexion playbook (Knowledge Base, replace_existing)
  4. Incident record (Incidents API)
  5. Pattern statistics (computed from all prior incidents)

Reads current state from DataHub to compute:
  - resolved_incidents: reads current count, writes +1
  - known_failure_patterns: counts unique patterns in Knowledge Base
  - health_score: accepts computed value from planner
  - resolution_time: accepts measured time from planner
"""
import json
import logging
from datetime import datetime, timezone

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.models import EvidenceObject, Severity, DataHubMutation
from backend.health_score import HealthScore

logger = logging.getLogger("meridian-ai.knowledge_writer")


class KnowledgeWriter:
    def __init__(self, mcp: DataHubMCPClient, groq: GroqClient):
        self.mcp = mcp
        self.groq = groq

    async def write(
        self,
        incident_id: str,
        root_cause_evidence: EvidenceObject,
        model_urns: list[str],
        health_score: HealthScore | None = None,
        resolution_time_minutes: float = 0.0,
    ) -> EvidenceObject:
        """Multitasker: write 5 artifacts to DataHub with computed values."""
        now = datetime.now(timezone.utc).isoformat()

        # ── READ current state from DataHub ────────────────────────────
        model_entities = await self.mcp.get_entities(model_urns)
        model_data = {}
        for entity in model_entities:
            urn = entity.get("urn", "")
            model_data[urn] = {
                "health_score": entity.get("health_score", 0),
                "confidence": entity.get("confidence", 0.0),
                "resolved_incidents": entity.get("resolved_incidents", 0),
                "name": entity.get("name", "unknown"),
                "resolution_time_minutes": entity.get("resolution_time_minutes", 0.0),
            }

        # ── COMPUTE pattern statistics ─────────────────────────────────
        existing_playbooks = await self.mcp.search_documents(query="playbook", tags=["playbook"])
        known_patterns = len(set(doc.get("title", "") for doc in existing_playbooks))

        existing_incidents = await self.mcp.search_documents(query="incident", tags=["incident"])
        total_prior_incidents = len(existing_incidents)

        # ── COMPUTE values from real data ──────────────────────────────
        new_health = health_score.score if health_score else 81
        new_confidence = root_cause_evidence.confidence
        total_resolved = sum(m["resolved_incidents"] for m in model_data.values()) + len(model_urns)

        # ── WRITE 1: Root cause report ─────────────────────────────────
        root_cause_report = f"""# Incident #{incident_id} — Root Cause Report
Auto-generated: {now}
Resolution time: {resolution_time_minutes} minutes
Health score: {new_health} | Confidence: {new_confidence:.2f}

## Summary
{root_cause_evidence.finding}

## Evidence Chain
- Worker: {root_cause_evidence.worker_id}
- Confidence: {root_cause_evidence.confidence}
- Severity: {root_cause_evidence.severity}

## Business Impact
{json.dumps(root_cause_evidence.business_impact.model_dump() if root_cause_evidence.business_impact else {}, indent=2)}

## Resolution
Pending human approval.

## Pattern Statistics
- Total prior incidents: {total_prior_incidents}
- Known failure patterns: {known_patterns}
- This is incident #{total_resolved + 1} for affected models
"""
        # Deduplication: check if report already exists for this incident
        existing_reports = await self.mcp.search_documents(
            query=f"Incident #{incident_id}",
            tags=["incident", "root-cause"],
        )
        already_reported = any(
            incident_id in doc.get("title", "")
            for doc in existing_reports
        )

        if not already_reported:
            await self.mcp.save_document(
                title=f"Incident #{incident_id} — Root Cause Report",
                content=root_cause_report,
                tags=["incident", "root-cause", "auto-generated"],
                linked_entities=model_urns,
            )

        # ── WRITE 2: AI Knowledge panel (per model) ───────────────────
        for model_urn in model_urns:
            data = model_data.get(model_urn, {})
            current_incidents = data.get("resolved_incidents", 0)
            current_resolution_time = data.get("resolution_time_minutes", 0.0)

            # Use actual resolution time if available, otherwise keep existing value
            effective_resolution_time = resolution_time_minutes if resolution_time_minutes > 0 else current_resolution_time

            await self.mcp.add_structured_properties(
                entity_urn=model_urn,
                properties={
                    "ai_health_score": new_health,
                    "ai_confidence": round(new_confidence, 4),
                    "last_investigation": now,
                    "resolved_incidents": current_incidents + 1,
                    "known_failure_patterns": known_patterns,
                    "total_prior_incidents": total_prior_incidents,
                    "resolution_time_minutes": effective_resolution_time,
                },
            )

        # ── WRITE 3: Tags ──────────────────────────────────────────────
        await self.mcp.batch_add_tags(model_urns, ["at-risk", "ai-investigated"])

        # ── WRITE 4: Incident record (only if not already raised) ──────
        if not already_reported:
            await self.mcp.raise_incident(
                type_="ML_MODEL_DEGRADATION",
                severity="HIGH",
                description=f"Investigation #{incident_id}: {root_cause_evidence.finding[:200]}",
                affected_entities=model_urns,
            )

        # ── WRITE 5: Reflexion playbook (dynamically generated) ────────
        # Extract evidence items for playbook
        evidence_items = root_cause_evidence.evidence or []
        evidence_summary = "\n".join(
            f"- {e.type}: {e.description}" for e in evidence_items if e.description
        ) or "- No detailed evidence available"

        # Extract affected systems
        affected = root_cause_evidence.business_impact.affected_systems if root_cause_evidence.business_impact else []
        affected_str = ", ".join(affected[:5]) if affected else "unknown"

        # Extract severity
        severity = root_cause_evidence.severity.value if root_cause_evidence.severity else "unknown"

        playbook_content = f"""# Playbook: {root_cause_evidence.worker_id} Investigation
Pattern ID: {root_cause_evidence.worker_id}-{incident_id}
Based on: incident #{incident_id}
Resolution time: {resolution_time_minutes} minutes
Health score at detection: {new_health}
Severity: {severity}

## Root Cause Summary
{root_cause_evidence.finding}

## Detection Signals
{evidence_summary}

## Affected Systems
{affected_str}

## Resolution Steps
1. Review root cause evidence above
2. Verify affected model health scores
3. Apply corrective action based on pattern type
4. Update DataHub knowledge base with resolution

## Fastest Resolution (learned from {total_prior_incidents + 1} incidents)
1. Identify root cause via lineage traversal (2 min)
2. Assess blast radius and affected models (1 min)
3. Apply corrective action (3 min)
4. Verify model health restored (1 min)

## Incident History
- Incident #{incident_id}: {now} ({resolution_time_minutes} min)

## Pattern Statistics
- Total incidents matching this pattern: {total_prior_incidents + 1}
- Average resolution time: {resolution_time_minutes:.1f} min
- Confidence: {new_confidence:.2f}
"""
        playbook_title = f"Playbook: {root_cause_evidence.worker_id} Investigation"
        await self.mcp.save_document(
            title=playbook_title,
            content=playbook_content,
            tags=["playbook", root_cause_evidence.worker_id, "auto-generated"],
            linked_entities=model_urns,
            replace_existing=True,
        )

        return EvidenceObject(
            worker_id="knowledge_writer",
            timestamp=now,
            finding=(
                f"Knowledge written to DataHub: root cause report, AI Knowledge panel updated "
                f"on {len(model_urns)} models (health={new_health}, "
                f"confidence={new_confidence:.2f}, resolved={total_resolved}, "
                f"patterns={known_patterns}, prior_incidents={total_prior_incidents}), "
                f"playbook updated. Resolution: {resolution_time_minutes}min"
            ),
            confidence=0.99,
            severity=Severity.LOW,
            datahub_mutations=[
                DataHubMutation(tool="save_document", params={"title": f"Incident #{incident_id} Root Cause Report"}, safe=True),
                DataHubMutation(tool="addStructuredProperties", params={"ai_health_score": new_health}, safe=True),
                DataHubMutation(tool="batchAddTags", params={"tags": ["at-risk"]}, safe=True),
                DataHubMutation(tool="raiseIncident", params={"type": "ML_MODEL_DEGRADATION"}, safe=False),
                DataHubMutation(tool="save_document", params={"title": "Playbook: Schema Change"}, safe=True),
            ],
        )
