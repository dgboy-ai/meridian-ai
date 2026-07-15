"""OpenLineage Emission — emits investigation lineage as OpenLineage events.

"Meridian emits its own investigation lineage as OpenLineage events."

This module creates a lineage graph showing:
  [incident_trigger] → [evidence_collection] → [root_cause] → [remediation] → [knowledge_base]

Based on OpenLineage specification:
- eventType: START, COMPLETE, FAIL
- run: Investigation metadata
- job: Investigation workflow
- inputs: Datasets read during investigation
- outputs: Knowledge written to DataHub
"""
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger("meridian-ai.openlineage")


@dataclass
class OpenLineageRun:
    """An OpenLineage run representing an investigation."""
    run_id: str
    event_type: str  # "START", "COMPLETE", "FAIL"
    event_time: str
    namespace: str
    job_name: str
    run_facets: dict = field(default_factory=dict)
    inputs: list[dict] = field(default_factory=list)
    outputs: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "eventType": self.event_type,
            "eventTime": self.event_time,
            "run": {
                "runId": self.run_id,
                "facets": self.run_facets,
            },
            "job": {
                "namespace": self.namespace,
                "name": self.job_name,
            },
            "inputs": self.inputs,
            "outputs": self.outputs,
        }


class OpenLineageEmitter:
    """Emit OpenLineage events for investigation workflows.

    Creates a lineage graph showing:
    [incident_trigger] → [evidence_collection] → [root_cause] → [remediation] → [knowledge_base]
    """

    def __init__(self, namespace: str = "meridian-ai"):
        self.namespace = namespace
        self._events: list[OpenLineageRun] = []

    def _generate_run_id(self, incident_id: str) -> str:
        """Generate a deterministic run ID from incident ID."""
        return hashlib.sha256(f"meridian-{incident_id}".encode()).hexdigest()[:16]

    def emit_investigation_start(
        self,
        incident_id: str,
        dataset_urn: str,
        model_urns: list[str],
    ) -> OpenLineageRun:
        """Emit investigation start event."""
        run_id = self._generate_run_id(incident_id)
        now = datetime.now(timezone.utc).isoformat()

        # Build inputs (datasets read during investigation)
        inputs = [
            {
                "namespace": self.namespace,
                "name": dataset_urn,
                "facets": {
                    "dataSource": {"uri": f"datahub://{dataset_urn}"},
                },
            }
        ]

        run = OpenLineageRun(
            run_id=run_id,
            event_type="START",
            event_time=now,
            namespace=self.namespace,
            job_name=f"investigation_{incident_id}",
            run_facets={
                "meridianInvestigation": {
                    "incidentId": incident_id,
                    "status": "started",
                    "datasetUrn": dataset_urn,
                    "modelUrns": model_urns,
                },
            },
            inputs=inputs,
        )

        self._events.append(run)
        logger.info(f"OpenLineage: Investigation {incident_id} START emitted")
        return run

    def emit_investigation_complete(
        self,
        incident_id: str,
        dataset_urn: str,
        model_urns: list[str],
        workers_fired: list[str],
        health_score: int,
        resolution_time_minutes: float,
        datahub_mutations: int,
    ) -> OpenLineageRun:
        """Emit investigation complete event."""
        run_id = self._generate_run_id(incident_id)
        now = datetime.now(timezone.utc).isoformat()

        # Build inputs
        inputs = [
            {
                "namespace": self.namespace,
                "name": dataset_urn,
                "facets": {
                    "dataSource": {"uri": f"datahub://{dataset_urn}"},
                },
            }
        ]

        # Build outputs (knowledge written to DataHub)
        outputs = [
            {
                "namespace": self.namespace,
                "name": f"knowledge_base/investigation_{incident_id}",
                "facets": {
                    "dataSource": {"uri": f"datahub://knowledge_base/investigation_{incident_id}"},
                },
            }
        ]

        run = OpenLineageRun(
            run_id=run_id,
            event_type="COMPLETE",
            event_time=now,
            namespace=self.namespace,
            job_name=f"investigation_{incident_id}",
            run_facets={
                "meridianInvestigation": {
                    "incidentId": incident_id,
                    "status": "completed",
                    "datasetUrn": dataset_urn,
                    "modelUrns": model_urns,
                    "workersFired": workers_fired,
                    "healthScore": health_score,
                    "resolutionTimeMinutes": resolution_time_minutes,
                    "datahubMutations": datahub_mutations,
                },
            },
            inputs=inputs,
            outputs=outputs,
        )

        self._events.append(run)
        logger.info(f"OpenLineage: Investigation {incident_id} COMPLETE emitted")
        return run

    def emit_investigation_fail(
        self,
        incident_id: str,
        dataset_urn: str,
        error: str,
    ) -> OpenLineageRun:
        """Emit investigation fail event."""
        run_id = self._generate_run_id(incident_id)
        now = datetime.now(timezone.utc).isoformat()

        inputs = [
            {
                "namespace": self.namespace,
                "name": dataset_urn,
                "facets": {
                    "dataSource": {"uri": f"datahub://{dataset_urn}"},
                },
            }
        ]

        run = OpenLineageRun(
            run_id=run_id,
            event_type="FAIL",
            event_time=now,
            namespace=self.namespace,
            job_name=f"investigation_{incident_id}",
            run_facets={
                "meridianInvestigation": {
                    "incidentId": incident_id,
                    "status": "failed",
                    "datasetUrn": dataset_urn,
                    "error": error,
                },
            },
            inputs=inputs,
        )

        self._events.append(run)
        logger.info(f"OpenLineage: Investigation {incident_id} FAIL emitted")
        return run

    def get_events(self) -> list[dict]:
        """Get all emitted OpenLineage events."""
        return [e.to_dict() for e in self._events]

    def get_investigation_lineage(self, incident_id: str) -> dict:
        """Get the lineage graph for a specific investigation."""
        run_id = self._generate_run_id(incident_id)
        events = [e for e in self._events if e.run_id == run_id]

        if not events:
            return {"incident_id": incident_id, "events": [], "status": "not_found"}

        # Build lineage graph
        start_event = next((e for e in events if e.event_type == "START"), None)
        complete_event = next((e for e in events if e.event_type == "COMPLETE"), None)
        fail_event = next((e for e in events if e.event_type == "FAIL"), None)

        return {
            "incident_id": incident_id,
            "run_id": run_id,
            "status": "completed" if complete_event else ("failed" if fail_event else "in_progress"),
            "start_time": start_event.event_time if start_event else None,
            "end_time": (complete_event or fail_event).event_time if (complete_event or fail_event) else None,
            "events": [e.to_dict() for e in events],
        }
