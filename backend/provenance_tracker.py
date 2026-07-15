"""Agent Provenance Tracking — traces context sources for every LLM call.

"Agents without provenance are hallucination factories. Agents with
lineage-grounded retrieval are the first generation of AI tools that
business users actually trust."

This module tracks:
  - Which DataHub documents/playbooks were retrieved for each investigation
  - Which context sources were injected into each LLM call
  - Which worker outputs are grounded in verified context vs. LLM guesses
  - Provenance metadata for every decision made during investigation

Based on DataHub's context management pattern:
"Every piece of context delivered to an agent should carry metadata about
its source, freshness, and the policies that permitted access."
"""
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger("meridian-ai.provenance")


class ContextSource(str, Enum):
    """Source of context delivered to an agent."""
    DATAHUB_METADATA = "datahub_metadata"
    DATAHUB_LINEAGE = "datahub_lineage"
    DATAHUB_DOCUMENT = "datahub_document"
    DATAHUB_PLAYBOOK = "datahub_playbook"
    SCHEMA_DIFF = "schema_diff"
    STATISTICAL_COMPUTATION = "statistical_computation"
    LLM_INFERENCE = "llm_inference"
    USER_INPUT = "user_input"
    HARDCODED_CONFIG = "hardcoded_config"


@dataclass
class ProvenanceRecord:
    """Provenance record for a single context source."""
    source_id: str
    source_type: ContextSource
    source_urn: str = ""  # DataHub URN if applicable
    source_name: str = ""
    retrieved_at: float = 0.0
    freshness_seconds: float = 0.0  # How old is this context?
    confidence: float = 1.0  # How trustworthy is this source?
    verified: bool = True  # Has this been verified against DataHub?
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type.value,
            "source_urn": self.source_urn,
            "source_name": self.source_name,
            "retrieved_at": self.retrieved_at,
            "freshness_seconds": round(self.freshness_seconds, 2),
            "confidence": self.confidence,
            "verified": self.verified,
            "metadata": self.metadata,
        }


@dataclass
class WorkerProvenance:
    """Provenance tracking for a single worker invocation."""
    worker_id: str
    context_sources: list[ProvenanceRecord] = field(default_factory=list)
    llm_calls: list[dict] = field(default_factory=list)
    total_confidence: float = 1.0
    verified_sources: int = 0
    unverified_sources: int = 0

    def to_dict(self) -> dict:
        return {
            "worker_id": self.worker_id,
            "context_sources": [cs.to_dict() for cs in self.context_sources],
            "llm_calls": self.llm_calls,
            "total_confidence": round(self.total_confidence, 4),
            "verified_sources": self.verified_sources,
            "unverified_sources": self.unverified_sources,
            "source_count": len(self.context_sources),
        }


@dataclass
class InvestigationProvenance:
    """Full provenance tracking for an investigation."""
    incident_id: str
    worker_provenances: dict[str, WorkerProvenance] = field(default_factory=dict)
    total_context_sources: int = 0
    total_verified: int = 0
    total_unverified: int = 0
    overall_confidence: float = 1.0
    start_time: float = 0.0

    def to_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "worker_provenances": {k: v.to_dict() for k, v in self.worker_provenances.items()},
            "total_context_sources": self.total_context_sources,
            "total_verified": self.total_verified,
            "total_unverified": self.total_unverified,
            "overall_confidence": round(self.overall_confidence, 4),
            "provenance_score": self.calculate_provenance_score(),
        }

    def calculate_provenance_score(self) -> float:
        """Calculate a provenance score (0-1) based on verified sources."""
        if self.total_context_sources == 0:
            return 1.0  # No context = no provenance risk
        return round(self.total_verified / self.total_context_sources, 4)


class ProvenanceTracker:
    """Track provenance for all context sources across an investigation."""

    def __init__(self) -> None:
        self._investigations: dict[str, InvestigationProvenance] = {}

    def start_investigation(self, incident_id: str) -> InvestigationProvenance:
        """Start tracking provenance for an investigation."""
        prov = InvestigationProvenance(
            incident_id=incident_id,
            start_time=time.time(),
        )
        self._investigations[incident_id] = prov
        return prov

    def record_context_source(
        self,
        incident_id: str,
        worker_id: str,
        source_type: ContextSource,
        source_urn: str = "",
        source_name: str = "",
        confidence: float = 1.0,
        verified: bool = True,
        metadata: dict | None = None,
    ) -> ProvenanceRecord:
        """Record a context source used by a worker."""
        prov = self._investigations.get(incident_id)
        if not prov:
            return ProvenanceRecord(source_id="", source_type=source_type)

        # Get or create worker provenance
        worker_prov = prov.worker_provenances.get(worker_id)
        if not worker_prov:
            worker_prov = WorkerProvenance(worker_id=worker_id)
            prov.worker_provenances[worker_id] = worker_prov

        # Create provenance record
        record = ProvenanceRecord(
            source_id=f"{worker_id}-{len(worker_prov.context_sources)}",
            source_type=source_type,
            source_urn=source_urn,
            source_name=source_name,
            retrieved_at=time.time(),
            confidence=confidence,
            verified=verified,
            metadata=metadata or {},
        )

        worker_prov.context_sources.append(record)
        prov.total_context_sources += 1
        if verified:
            prov.total_verified += 1
            worker_prov.verified_sources += 1
        else:
            prov.total_unverified += 1
            worker_prov.unverified_sources += 1

        return record

    def record_llm_call(
        self,
        incident_id: str,
        worker_id: str,
        model: str,
        context_sources_used: list[str],
        tokens_in: int = 0,
        tokens_out: int = 0,
        confidence: float = 0.0,
    ) -> None:
        """Record an LLM call with its context sources."""
        prov = self._investigations.get(incident_id)
        if not prov:
            return

        worker_prov = prov.worker_provenances.get(worker_id)
        if not worker_prov:
            worker_prov = WorkerProvenance(worker_id=worker_id)
            prov.worker_provenances[worker_id] = worker_prov

        worker_prov.llm_calls.append({
            "model": model,
            "context_sources": context_sources_used,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "confidence": confidence,
            "timestamp": time.time(),
        })

    def get_investigation_provenance(self, incident_id: str) -> InvestigationProvenance | None:
        """Get provenance for a specific investigation."""
        return self._investigations.get(incident_id)

    def calculate_worker_confidence(self, incident_id: str, worker_id: str) -> float:
        """Calculate confidence for a worker based on provenance."""
        prov = self._investigations.get(incident_id)
        if not prov:
            return 1.0

        worker_prov = prov.worker_provenances.get(worker_id)
        if not worker_prov or not worker_prov.context_sources:
            return 1.0  # No context = no provenance risk

        # Confidence is average of all source confidences, weighted by verification
        total_confidence = 0.0
        for source in worker_prov.context_sources:
            weight = 1.0 if source.verified else 0.5
            total_confidence += source.confidence * weight

        return round(total_confidence / len(worker_prov.context_sources), 4)

    def get_unverified_sources(self, incident_id: str) -> list[dict]:
        """Get all unverified context sources for an investigation."""
        prov = self._investigations.get(incident_id)
        if not prov:
            return []

        unverified = []
        for worker_id, worker_prov in prov.worker_provenances.items():
            for source in worker_prov.context_sources:
                if not source.verified:
                    unverified.append({
                        "worker_id": worker_id,
                        "source": source.to_dict(),
                    })

        return unverified

    def get_summary(self, incident_id: str) -> dict:
        """Get provenance summary for an investigation."""
        prov = self._investigations.get(incident_id)
        if not prov:
            return {"incident_id": incident_id, "no_data": True}

        return {
            "incident_id": incident_id,
            "total_sources": prov.total_context_sources,
            "verified": prov.total_verified,
            "unverified": prov.total_unverified,
            "provenance_score": prov.calculate_provenance_score(),
            "workers_with_provenance": len(prov.worker_provenances),
            "workers": {
                worker_id: {
                    "sources": len(wp.context_sources),
                    "verified": wp.verified_sources,
                    "unverified": wp.unverified_sources,
                    "llm_calls": len(wp.llm_calls),
                }
                for worker_id, wp in prov.worker_provenances.items()
            },
        }
