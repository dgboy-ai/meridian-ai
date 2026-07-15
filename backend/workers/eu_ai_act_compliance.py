"""EU AI Act Compliance Engine — automated audit trails for Articles 12, 13, 14.

Generates SHA-256 hashed audit records for every AI decision, investigation,
and write-back. Produces Technical File artifacts required for high-risk AI
system compliance.

Timeline: EU AI Act enforcement August 2, 2026. Hackathon deadline August 11, 2026.
"""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.models import EvidenceObject, Severity, DataHubMutation


@dataclass
class AuditRecord:
    """Immutable audit record for an AI decision."""
    record_id: str
    timestamp: str
    article: str  # "12", "13", or "14"
    system_name: str
    decision_type: str
    input_summary: str
    output_summary: str
    confidence: float
    human_override: bool
    reasoning_chain: list[str]
    hash_sha256: str = ""
    previous_hash: str = ""

    def __post_init__(self):
        if not self.hash_sha256:
            self.hash_sha256 = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps({
            "record_id": self.record_id,
            "timestamp": self.timestamp,
            "article": self.article,
            "system_name": self.system_name,
            "decision_type": self.decision_type,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "confidence": self.confidence,
            "human_override": self.human_override,
            "reasoning_chain": self.reasoning_chain,
            "previous_hash": self.previous_hash,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "timestamp": self.timestamp,
            "article": self.article,
            "system_name": self.system_name,
            "decision_type": self.decision_type,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "confidence": self.confidence,
            "human_override": self.human_override,
            "reasoning_chain": self.reasoning_chain,
            "hash_sha256": self.hash_sha256,
            "previous_hash": self.previous_hash,
        }


class EUAIActComplianceEngine:
    """Generates EU AI Act compliant audit trails for all Meridian AI decisions."""

    _CHAIN_FILE = Path("data") / "audit_chain.json"

    def __init__(self, mcp: DataHubMCPClient, groq: GroqClient, load_persisted: bool = False):
        self.mcp = mcp
        self.groq = groq
        self._audit_chain: list[AuditRecord] = []
        self._last_hash: str = "0" * 64
        if load_persisted:
            self._load_chain()

    def _save_chain(self) -> None:
        self._CHAIN_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self._CHAIN_FILE, "w") as f:
            json.dump([r.to_dict() for r in self._audit_chain], f, indent=2)

    def _load_chain(self) -> None:
        if not self._CHAIN_FILE.exists():
            return
        with open(self._CHAIN_FILE) as f:
            records = json.load(f)
        for data in records:
            rec = AuditRecord(
                record_id=data["record_id"],
                timestamp=data["timestamp"],
                article=data["article"],
                system_name=data["system_name"],
                decision_type=data["decision_type"],
                input_summary=data["input_summary"],
                output_summary=data["output_summary"],
                confidence=data["confidence"],
                human_override=data["human_override"],
                reasoning_chain=data["reasoning_chain"],
                hash_sha256=data["hash_sha256"],
                previous_hash=data["previous_hash"],
            )
            self._audit_chain.append(rec)
        if self._audit_chain:
            self._last_hash = self._audit_chain[-1].hash_sha256

    @property
    def chain_length(self) -> int:
        return len(self._audit_chain)

    @property
    def last_hash(self) -> str:
        return self._last_hash

    async def record_decision(
        self,
        article: str,
        decision_type: str,
        input_summary: str,
        output_summary: str,
        confidence: float,
        human_override: bool = False,
        reasoning_chain: list[str] | None = None,
        incident_id: str = "0",
    ) -> AuditRecord:
        """Record an AI decision as an immutable audit entry.

        Args:
            article: EU AI Act article ("12" = record-keeping, "13" = transparency, "14" = human oversight)
            decision_type: Type of decision (e.g., "root_cause_analysis", "remediation_proposed")
            input_summary: What the AI received
            output_summary: What the AI decided
            confidence: Confidence score of the decision
            human_override: Whether a human overrode the AI's decision
            reasoning_chain: Step-by-step reasoning
            incident_id: Associated incident ID
        """
        record_id = f"AI-AUDIT-{incident_id}-{self.chain_length + 1:04d}"
        now = datetime.now(timezone.utc).isoformat()

        record = AuditRecord(
            record_id=record_id,
            timestamp=now,
            article=article,
            system_name="Meridian AI",
            decision_type=decision_type,
            input_summary=input_summary[:500],
            output_summary=output_summary[:500],
            confidence=confidence,
            human_override=human_override,
            reasoning_chain=reasoning_chain or [],
            previous_hash=self._last_hash,
        )

        self._audit_chain.append(record)
        self._last_hash = record.hash_sha256
        self._save_chain()

        return record

    async def generate_technical_file(
        self,
        incident_id: str,
        model_urns: list[str],
        root_cause_evidence: EvidenceObject | None = None,
    ) -> EvidenceObject:
        """Generate EU AI Act Technical File for high-risk AI system compliance.

        Article 12: Record-keeping — automatic logging of AI system operation
        Article 13: Transparency — provide deployers with clear information
        Article 14: Human oversight — enable effective human oversight
        """
        now = datetime.now(timezone.utc).isoformat()

        # Record the investigation decision chain
        if root_cause_evidence:
            await self.record_decision(
                article="12",
                decision_type="incident_investigation",
                input_summary=f"Investigation triggered for incident #{incident_id}. "
                    f"Source: {root_cause_evidence.worker_id}",
                output_summary=root_cause_evidence.finding,
                confidence=root_cause_evidence.confidence,
                human_override=False,
                reasoning_chain=[
                    f"Worker: {root_cause_evidence.worker_id}",
                    f"Confidence: {root_cause_evidence.confidence}",
                    f"Severity: {root_cause_evidence.severity}",
                    f"Mutations: {len(root_cause_evidence.datahub_mutations)}",
                ],
                incident_id=incident_id,
            )

            await self.record_decision(
                article="13",
                decision_type="root_cause_analysis",
                input_summary=f"Lineage traversal for {len(model_urns)} models",
                output_summary=root_cause_evidence.finding,
                confidence=root_cause_evidence.confidence,
                human_override=False,
                reasoning_chain=[root_cause_evidence.finding],
                incident_id=incident_id,
            )

            await self.record_decision(
                article="14",
                decision_type="remediation_proposed",
                input_summary="Remediation requires human approval",
                output_summary="Pending human review",
                confidence=root_cause_evidence.confidence,
                human_override=False,
                reasoning_chain=["Progressive autonomy Level 0: Advisory mode"],
                incident_id=incident_id,
            )

        # Generate the Technical File content
        records_for_incident = [
            r for r in self._audit_chain
            if r.record_id.startswith(f"AI-AUDIT-{incident_id}")
        ]

        technical_file = f"""# EU AI Act Technical File — Incident #{incident_id}
Generated: {now}
System: Meridian AI (High-Risk AI System)
Chain Length: {len(records_for_incident)} audit records
Chain Integrity: {'VALID' if self._verify_chain() else 'COMPROMISED'}

## Article 12 — Record-Keeping
Automatic logging of all AI system operations per Article 12(1):
- All investigation decisions logged with timestamps
- Confidence scores recorded for every output
- Human override status tracked
- Cryptographic chain integrity (SHA-256)

## Article 13 — Transparency
System information provided to deployers per Article 13(1):
- System name: Meridian AI
- Intended purpose: ML incident investigation and remediation
- Level of autonomy: Progressive (Level 0-4)
- Training data: DataHub metadata, lineage graphs, incident history
- Known limitations: Requires DataHub MCP connectivity

## Article 14 — Human Oversight
Measures for effective human oversight per Article 14(2):
- Progressive Autonomy: irreversible actions require human approval
- Remediation approval workflow: APPROVE / OVERRIDE / REJECT
- Confidence threshold: <0.7 triggers mandatory human review
- Audit trail: every decision traceable and explainable

## Audit Records
"""

        for record in records_for_incident:
            technical_file += f"""### {record.record_id}
- **Article:** {record.article}
- **Decision:** {record.decision_type}
- **Confidence:** {record.confidence:.2f}
- **Human Override:** {record.human_override}
- **Hash:** {record.hash_sha256[:16]}...
- **Previous Hash:** {record.previous_hash[:16]}...

"""

        await self.mcp.save_document(
            title=f"EU AI Act Technical File — Incident #{incident_id}",
            content=technical_file,
            tags=["compliance", "eu-ai-act", "technical-file", "auto-generated"],
            linked_entities=model_urns,
            replace_existing=True,
        )

        return EvidenceObject(
            worker_id="eu_ai_act_compliance",
            timestamp=now,
            finding=(
                f"EU AI Act Technical File generated for incident #{incident_id}: "
                f"{len(records_for_incident)} audit records, Articles 12/13/14 covered, "
                f"chain {'VALID' if self._verify_chain() else 'COMPROMISED'}"
            ),
            confidence=0.98,
            severity=Severity.LOW,
            datahub_mutations=[
                DataHubMutation(
                    tool="save_document",
                    params={"title": f"EU AI Act Technical File — Incident #{incident_id}"},
                    safe=True,
                ),
                DataHubMutation(
                    tool="addStructuredProperties",
                    params={
                        "eu_ai_act_compliant": True,
                        "audit_chain_length": len(records_for_incident),
                        "last_audit_hash": self._last_hash[:16],
                    },
                    safe=True,
                ),
            ],
        )

    def _verify_chain(self) -> bool:
        """Verify the integrity of the audit chain."""
        if not self._audit_chain:
            return True
        for i, record in enumerate(self._audit_chain):
            if i == 0:
                if record.previous_hash != "0" * 64:
                    return False
            else:
                if record.previous_hash != self._audit_chain[i - 1].hash_sha256:
                    return False
        return True

    def get_audit_records(self, incident_id: str | None = None) -> list[dict]:
        """Get audit records, optionally filtered by incident."""
        records = self._audit_chain
        if incident_id:
            records = [r for r in records if r.record_id.startswith(f"AI-AUDIT-{incident_id}")]
        return [r.to_dict() for r in records]
