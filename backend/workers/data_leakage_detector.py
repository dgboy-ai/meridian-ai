"""Data Leakage Detector — real temporal pattern detection.

Checks schema for suspicious column naming patterns and SQL queries for
look-ahead bias. Pure code, no LLM guessing.
"""
from datetime import datetime, timezone

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.models import EvidenceObject, Severity, EvidenceItem, DataHubMutation
from backend.stats import check_temporal_leakage


class DataLeakageDetector:
    def __init__(self, mcp: DataHubMCPClient, groq: GroqClient):
        self.mcp = mcp
        self.groq = groq

    async def detect(self, feature_table_urn: str, model_urn: str) -> EvidenceObject:
        """Check for temporal data leakage using real pattern detection."""
        now = datetime.now(timezone.utc).isoformat()

        feature_fields = await self.mcp.list_schema_fields(feature_table_urn)
        feature_entity = (await self.mcp.get_entities([feature_table_urn])) or [{}]
        feature_name = feature_entity[0].get("name", "unknown") if feature_entity else "unknown"

        model_entities = await self.mcp.get_entities([model_urn])
        model_name = model_entities[0].get("name", "unknown") if model_entities else "unknown"

        # Get SQL queries that reference this feature table
        queries = await self.mcp.get_dataset_queries(feature_table_urn)

        # ── REAL COMPUTATION: temporal leakage detection ───────────────
        leakage_check = check_temporal_leakage(feature_fields, queries)

        # Determine severity from real computation
        if leakage_check.has_leakage:
            severity = Severity.CRITICAL if leakage_check.leakage_score > 0.7 else Severity.HIGH
            finding = (
                f"TEMPORAL DATA LEAKAGE detected in {feature_name} for {model_name}: "
                f"{len(leakage_check.suspicious_patterns)} suspicious patterns found. "
                f"Timestamp columns: {', '.join(leakage_check.timestamp_columns)}. "
                f"Patterns: {'; '.join(leakage_check.suspicious_patterns)}. "
                f"Leakage score: {leakage_check.leakage_score:.2f}"
            )
        else:
            severity = Severity.LOW
            finding = (
                f"No temporal data leakage detected in {feature_name} for {model_name}. "
                f"Timestamp columns: {', '.join(leakage_check.timestamp_columns) or 'none'}. "
                f"No suspicious patterns found."
            )

        mutations = []
        if leakage_check.has_leakage:
            mutations.append(
                DataHubMutation(
                    tool="raiseIncident",
                    params={
                        "type": "DATA_LEAKAGE",
                        "severity": severity.value.upper(),
                        "description": f"Temporal data leakage in {feature_name}: {len(leakage_check.suspicious_patterns)} patterns",
                    },
                    safe=False,
                )
            )
            mutations.append(
                DataHubMutation(
                    tool="batchAddTags",
                    params={"tags": ["data-leakage", "temporal-integrity"]},
                    safe=True,
                )
            )

        return EvidenceObject(
            worker_id="data_leakage_detector",
            timestamp=now,
            finding=finding,
            confidence=0.95 if not leakage_check.has_leakage else 0.90,
            severity=severity,
            evidence=[
                EvidenceItem(
                    type="temporal_leakage",
                    description=f"Checked {len(feature_fields)} fields and {len(queries)} queries for temporal leakage",
                    entity_urn=feature_table_urn,
                    affected_models=[model_name],
                ),
            ],
            next_action="Notify Root Cause worker with leakage evidence" if leakage_check.has_leakage else "No action needed",
            datahub_mutations=mutations,
        )
