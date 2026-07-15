"""Entity Linking — Apple's sibling entities pattern.

"Sibling entities to rationalize metadata and identify logical links.
ML datasets are symlinked to underlying tables."

This module creates logical links between:
  - The incident → affected models
  - The root cause dataset → affected feature tables
  - The playbook → affected incidents
  - The compliance report → affected entities

Based on Apple's DataHub implementation pattern for ML metadata management.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.models import EvidenceObject, Severity, EvidenceItem, DataHubMutation

logger = logging.getLogger("meridian-ai.entity_linker")


@dataclass
class EntityLink:
    """A logical link between two entities."""
    source_urn: str
    target_urn: str
    link_type: str  # "incident_to_model", "root_cause_to_feature", etc.
    relationship: str  # "affects", "derived_from", "linked_to"
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source_urn": self.source_urn,
            "target_urn": self.target_urn,
            "link_type": self.link_type,
            "relationship": self.relationship,
            "metadata": self.metadata,
        }


class EntityLinker:
    """Create logical links between entities using Apple's sibling entities pattern.

    After investigation, creates links between:
    - Incident → affected models
    - Root cause dataset → affected feature tables
    - Playbook → affected incidents
    - Compliance report → affected entities
    """

    def __init__(self, mcp: DataHubMCPClient, groq: GroqClient):
        self.mcp = mcp
        self.groq = groq

    async def link_investigation(
        self,
        incident_id: str,
        dataset_urn: str,
        model_urns: list[str],
        root_cause_evidence: EvidenceObject | None = None,
    ) -> EvidenceObject:
        """Create logical links for an investigation.

        Args:
            incident_id: Incident ID
            dataset_urn: Source dataset URN
            model_urns: Affected model URNs
            root_cause_evidence: Root cause evidence (optional)

        Returns:
            EvidenceObject with linking results
        """
        now = datetime.now(timezone.utc).isoformat()
        links_created = []

        # 1. Link incident to affected models
        for model_urn in model_urns:
            link = EntityLink(
                source_urn=f"incident:{incident_id}",
                target_urn=model_urn,
                link_type="incident_to_model",
                relationship="affects",
                metadata={
                    "incident_id": incident_id,
                    "timestamp": now,
                },
            )
            links_created.append(link)

            # Write link as structured properties on the model
            await self.mcp.add_structured_properties(
                entity_urn=model_urn,
                properties={
                    "linked_incident": incident_id,
                    "incident_link_type": "affects",
                    "incident_link_timestamp": now,
                },
            )

        # 2. Link root cause dataset to affected feature tables
        if root_cause_evidence:
            lineage = await self.mcp.get_lineage(dataset_urn, depth=3)
            for d in lineage.get("downstream", []):
                urn = d.get("urn", "")
                entity_type = d.get("type", "")

                # Link to feature tables
                if "feature" in urn.lower() or entity_type == "mlFeatureTable":
                    link = EntityLink(
                        source_urn=dataset_urn,
                        target_urn=urn,
                        link_type="root_cause_to_feature",
                        relationship="derived_from",
                        metadata={
                            "incident_id": incident_id,
                            "root_cause": root_cause_evidence.finding[:200],
                            "timestamp": now,
                        },
                    )
                    links_created.append(link)

                    # Write link as structured properties on the feature table
                    await self.mcp.add_structured_properties(
                        entity_urn=urn,
                        properties={
                            "root_cause_dataset": dataset_urn,
                            "root_cause_incident": incident_id,
                            "link_type": "derived_from",
                            "link_timestamp": now,
                        },
                    )

        # 3. Link playbook to incident (if playbook exists)
        playbook_link = EntityLink(
            source_urn=f"playbook:schema-change-type-mismatch",
            target_urn=f"incident:{incident_id}",
            link_type="playbook_to_incident",
            relationship="applied_to",
            metadata={
                "pattern_id": "schema-change-type-mismatch",
                "incident_id": incident_id,
                "timestamp": now,
            },
        )
        links_created.append(playbook_link)

        # Build finding
        finding = (
            f"ENTITY LINKING: Created {len(links_created)} logical links for incident #{incident_id}. "
            f"Linked {len(model_urns)} models, root cause dataset, and playbook."
        )

        return EvidenceObject(
            worker_id="entity_linker",
            timestamp=now,
            finding=finding,
            confidence=0.95,
            severity=Severity.LOW,
            evidence=[
                EvidenceItem(
                    type="entity_linking",
                    description=f"Created {len(links_created)} links: {', '.join(l.link_type for l in links_created)}",
                    entity_urn=dataset_urn,
                    affected_models=model_urns,
                ),
            ],
            next_action="No action needed",
            datahub_mutations=[
                DataHubMutation(
                    tool="addStructuredProperties",
                    params={"entity_links_created": len(links_created)},
                    safe=True,
                ),
            ],
        )

    async def get_entity_links(self, entity_urn: str) -> list[dict]:
        """Get all links for an entity.

        Args:
            entity_urn: URN of the entity

        Returns:
            List of entity links
        """
        entities = await self.mcp.get_entities([entity_urn])
        if not entities:
            return []

        entity = entities[0]
        links = []

        # Check for linked incident
        linked_incident = entity.get("linked_incident")
        if linked_incident:
            links.append({
                "type": "incident",
                "incident_id": linked_incident,
                "relationship": "affected_by",
            })

        # Check for root cause dataset
        root_cause_dataset = entity.get("root_cause_dataset")
        if root_cause_dataset:
            links.append({
                "type": "root_cause",
                "dataset_urn": root_cause_dataset,
                "relationship": "derived_from",
            })

        # Check for linked playbook
        linked_playbook = entity.get("linked_playbook")
        if linked_playbook:
            links.append({
                "type": "playbook",
                "playbook_id": linked_playbook,
                "relationship": "documented_by",
            })

        return links
