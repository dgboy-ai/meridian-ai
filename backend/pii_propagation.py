"""PII Propagation Through Lineage — tracks PII flow through downstream columns.

"PII tag on source flows to every downstream column that carries that field's data."

This module:
  1. After PII scan, traverses lineage to find all downstream columns
  2. Identifies which downstream columns derive from PII source columns
  3. Propagates PII tags to all affected downstream assets
  4. Generates a PII propagation report

Based on DataHub's metadata propagation pattern:
"Document once at the source, and all relevant data assets downstream inherit
that context through the lineage graph."
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.models import EvidenceObject, Severity, EvidenceItem, DataHubMutation
from backend.stats import traverse_lineage
from backend.scanners.pii_scanner import PIIScanner

logger = logging.getLogger("meridian-ai.pii_propagation")


@dataclass
class PIIPropagationPath:
    """A path showing how PII propagates through lineage."""
    source_column: str
    source_table: str
    target_column: str
    target_table: str
    target_urn: str
    transformation: str = ""
    propagated: bool = False

    def to_dict(self) -> dict:
        return {
            "source_column": self.source_column,
            "source_table": self.source_table,
            "target_column": self.target_column,
            "target_table": self.target_table,
            "target_urn": self.target_urn,
            "transformation": self.transformation,
            "propagated": self.propagated,
        }


class PIIPropagationTracker:
    """Track and propagate PII through lineage graph."""

    def __init__(self, mcp: DataHubMCPClient, groq: GroqClient):
        self.mcp = mcp
        self.groq = groq
        self.pii_scanner = PIIScanner()

    async def propagate_pii_tags(
        self,
        source_urn: str,
        pii_columns: list[str],
        severity: str = "high",
    ) -> EvidenceObject:
        """Propagate PII tags to all downstream columns that inherit PII.

        Args:
            source_urn: URN of the dataset with PII columns
            pii_columns: List of column names containing PII
            severity: Severity level for PII findings

        Returns:
            EvidenceObject with propagation results
        """
        now = datetime.now(timezone.utc).isoformat()

        # Get lineage for the source dataset
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

        # Traverse lineage
        traversal = traverse_lineage(lineage, entities_dict)

        # Build propagation paths
        propagation_paths = []
        affected_assets = []

        for urn in traversal.downstream_urns:
            entity = entities_dict.get(urn, {})
            entity_name = entity.get("name", "")
            entity.get("type", "")

            # For each PII column, create a propagation path
            for pii_col in pii_columns:
                path = PIIPropagationPath(
                    source_column=pii_col,
                    source_table=source_name,
                    target_column=pii_col,  # Same column name propagates
                    target_table=entity_name,
                    target_urn=urn,
                    transformation="LINEAGE",
                    propagated=True,
                )
                propagation_paths.append(path)

                if urn not in affected_assets:
                    affected_assets.append(urn)

        # Tag all affected assets with PII
        tags = ["pii-propagated", f"pii-severity-{severity}"]
        mutations = []

        if affected_assets:
            # Tag affected assets
            await self.mcp.batch_add_tags(urns=affected_assets, tags=tags)
            mutations.append(DataHubMutation(
                tool="batchAddTags",
                params={"tags": tags, "urns": affected_assets},
                safe=True,
            ))

            # Write propagation metadata to each affected asset
            for urn in affected_assets:
                entity = entities_dict.get(urn, {})
                entity_name = entity.get("name", "unknown")

                await self.mcp.add_structured_properties(
                    entity_urn=urn,
                    properties={
                        "pii_propagated": True,
                        "pii_source": source_name,
                        "pii_source_urn": source_urn,
                        "pii_columns": pii_columns,
                        "pii_severity": severity,
                        "propagation_timestamp": now,
                    },
                )
                mutations.append(DataHubMutation(
                    tool="addStructuredProperties",
                    params={"pii_propagated": True, "pii_source": source_name},
                    safe=True,
                ))

        # Build finding
        if affected_assets:
            finding = (
                f"PII PROPAGATION: {len(pii_columns)} PII columns from {source_name} "
                f"propagated to {len(affected_assets)} downstream assets. "
                f"Columns: {', '.join(pii_columns)}. "
                f"Assets tagged: {len(affected_assets)}."
            )
            severity_level = Severity.HIGH if severity in ("high", "critical") else Severity.MEDIUM
        else:
            finding = (
                f"PII PROPAGATION: {len(pii_columns)} PII columns from {source_name} "
                f"identified, but no downstream assets found."
            )
            severity_level = Severity.LOW

        return EvidenceObject(
            worker_id="pii_propagation",
            timestamp=now,
            finding=finding,
            confidence=0.90 if affected_assets else 0.95,
            severity=severity_level,
            evidence=[
                EvidenceItem(
                    type="pii_propagation",
                    description=f"Propagated {len(pii_columns)} PII columns to {len(affected_assets)} downstream assets via {len(propagation_paths)} paths",
                    entity_urn=source_urn,
                    downstream_count=len(affected_assets),
                ),
            ],
            next_action="Review PII propagation and apply masking" if affected_assets else "No action needed",
            datahub_mutations=mutations,
        )

    async def scan_and_propagate(
        self,
        dataset_urn: str,
        sample_data: list[dict] | None = None,
    ) -> EvidenceObject:
        """Scan for PII and propagate tags to downstream assets.

        Args:
            dataset_urn: URN of the dataset to scan
            sample_data: Optional sample data for PII scanning

        Returns:
            EvidenceObject with scan and propagation results
        """
        now = datetime.now(timezone.utc).isoformat()

        # Get entity metadata
        entities = await self.mcp.get_entities([dataset_urn])
        entity = entities[0] if entities else {}
        entity_name = entity.get("name", "unknown")

        # Get schema fields
        fields = await self.mcp.list_schema_fields(dataset_urn)

        # Scan for PII in field names
        pii_columns = []
        for field_def in fields:
            field_name = field_def.get("name", "").lower()
            # Check for common PII column patterns
            pii_patterns = ["email", "phone", "ssn", "address", "name", "ip_address", "credit_card"]
            for pattern in pii_patterns:
                if pattern in field_name:
                    pii_columns.append(field_def.get("name", ""))
                    break

        # Also scan sample data if provided
        if sample_data:
            violation = self.pii_scanner.scan_records(sample_data)
            if violation.total_violations > 0:
                # Extract PII column names from findings
                for finding in violation.findings:
                    if finding.column and finding.column not in pii_columns:
                        pii_columns.append(finding.column)

        # Propagate PII tags if PII columns found
        if pii_columns:
            return await self.propagate_pii_tags(
                source_urn=dataset_urn,
                pii_columns=pii_columns,
                severity="high",
            )
        else:
            return EvidenceObject(
                worker_id="pii_propagation",
                timestamp=now,
                finding=f"No PII columns detected in {entity_name}. Scan complete.",
                confidence=0.95,
                severity=Severity.LOW,
                evidence=[],
                datahub_mutations=[],
            )
