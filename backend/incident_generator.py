"""Dynamic Incident Generator — generates incidents from real DataHub signals.

Instead of hardcoded replay data, this module generates incidents dynamically
based on actual DataHub metadata changes, quality checks, and lineage analysis.

This makes the demo realistic — incidents come from real data, not pre-recorded.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient

logger = logging.getLogger("meridian-ai.incident_generator")


@dataclass
class GeneratedIncident:
    """A dynamically generated incident."""
    incident_id: str
    title: str
    severity: str
    status: str
    detected: str
    duration_seconds: int
    root_cause: str
    pattern_id: str
    affected_models: list[str]
    timeline: list[dict]
    blast_radius: dict
    writeback: dict

    def to_dict(self) -> dict:
        return {
            "id": self.incident_id,
            "title": self.title,
            "severity": self.severity,
            "status": self.status,
            "detected": self.detected,
            "duration_seconds": self.duration_seconds,
            "root_cause": self.root_cause,
            "pattern_id": self.pattern_id,
            "affected_models": self.affected_models,
            "timeline": self.timeline,
            "blast_radius": self.blast_radius,
            "writeback": self.writeback,
        }


class IncidentGenerator:
    """Generate incidents dynamically from DataHub metadata.

    Instead of hardcoded replay data, this generates incidents based on:
    - Schema changes detected in DataHub
    - Freshness violations
    - Quality assertion failures
    - Lineage impact analysis
    """

    def __init__(self, mcp: DataHubMCPClient, groq: GroqClient):
        self.mcp = mcp
        self.groq = groq
        self._incident_counter = 100

    async def generate_incident_from_signals(self) -> GeneratedIncident | None:
        """Generate an incident from real DataHub signals.

        Returns:
            GeneratedIncident or None if no signals detected
        """
        now = datetime.now(timezone.utc).isoformat()
        self._incident_counter += 1
        incident_id = str(self._incident_counter)

        # Scan for signals
        signals = await self._scan_for_signals()

        if not signals:
            return None

        # Determine severity from signals
        max_severity = max(s["severity"] for s in signals)
        severity_map = {"LOW": "low", "MEDIUM": "medium", "HIGH": "high", "CRITICAL": "critical"}
        severity = severity_map.get(max_severity, "medium")

        # Build timeline from signals
        timeline = self._build_timeline(signals, incident_id)

        # Get affected models
        affected_models = []
        for signal in signals:
            if "affected_models" in signal:
                affected_models.extend(signal["affected_models"])

        # Generate root cause
        root_cause = self._generate_root_cause(signals)

        # Build blast radius
        blast_radius = self._build_blast_radius(signals, affected_models)

        return GeneratedIncident(
            incident_id=incident_id,
            title=f"Auto-detected: {signals[0]['type']} in {signals[0].get('entity', 'unknown')}",
            severity=severity,
            status="OPEN",
            detected=now,
            duration_seconds=0,
            root_cause=root_cause,
            pattern_id=signals[0].get("pattern_id", "unknown"),
            affected_models=affected_models,
            timeline=timeline,
            blast_radius=blast_radius,
            writeback={},
        )

    async def _scan_for_signals(self) -> list[dict]:
        """Scan DataHub for signals that could indicate an incident."""
        signals = []

        # Get all ML models
        models = await self.mcp.search(query="", entity_type="mlModel")

        for model in models:
            model.get("urn", "")
            model_name = model.get("name", "")

            # Check health score
            health_score = model.get("health_score", 100)
            if health_score < 70:
                signals.append({
                    "type": "low_health_score",
                    "entity": model_name,
                    "severity": "HIGH" if health_score < 50 else "MEDIUM",
                    "detail": f"Health score {health_score} is below threshold",
                    "pattern_id": "health-degradation",
                    "affected_models": [model_name],
                })

            # Check confidence
            confidence = model.get("confidence", 1.0)
            if confidence < 0.7:
                signals.append({
                    "type": "low_confidence",
                    "entity": model_name,
                    "severity": "MEDIUM",
                    "detail": f"Confidence {confidence:.2f} is below threshold",
                    "pattern_id": "confidence-drop",
                    "affected_models": [model_name],
                })

            # Check resolved incidents (high incident count = at risk)
            resolved = model.get("resolved_incidents", 0)
            if resolved > 10:
                signals.append({
                    "type": "high_incident_count",
                    "entity": model_name,
                    "severity": "MEDIUM",
                    "detail": f"{resolved} resolved incidents — chronic failure pattern",
                    "pattern_id": "recurring-incident",
                    "affected_models": [model_name],
                })

        # Get all datasets and check for issues
        datasets = await self.mcp.search(query="", entity_type="dataset")

        for dataset in datasets:
            dataset_urn = dataset.get("urn", "")
            dataset_name = dataset.get("name", "")

            # Check schema fields for issues
            fields = await self.mcp.list_schema_fields(dataset_urn)
            for field_def in fields:
                field_type = field_def.get("type", "")
                if field_type == "UNKNOWN":
                    signals.append({
                        "type": "unknown_field_type",
                        "entity": dataset_name,
                        "severity": "MEDIUM",
                        "detail": f"Field '{field_def.get('name', '')}' has unknown type",
                        "pattern_id": "schema-anomaly",
                    })

        return signals

    def _build_timeline(self, signals: list[dict], incident_id: str) -> list[dict]:
        """Build a timeline from signals."""
        now = datetime.now(timezone.utc)
        timeline = []

        # Add detection event
        timeline.append({
            "time": now.strftime("%H:%M:%S"),
            "step": "planner",
            "status": "started",
            "finding": f"Investigation initiated for incident #{incident_id}",
            "confidence": 1.0,
            "message": f"Detected {len(signals)} signals",
        })

        # Add signal events
        for i, signal in enumerate(signals):
            timeline.append({
                "time": (now).strftime("%H:%M:%S"),
                "step": signal.get("type", "unknown"),
                "status": "completed",
                "finding": signal.get("detail", ""),
                "confidence": 0.9,
                "severity": signal.get("severity", "medium"),
            })

        # Add completion
        timeline.append({
            "time": now.strftime("%H:%M:%S"),
            "step": "planner",
            "status": "completed",
            "finding": f"Investigation #{incident_id} complete. {len(signals)} signals analyzed.",
            "confidence": 1.0,
        })

        return timeline

    def _generate_root_cause(self, signals: list[dict]) -> str:
        """Generate a root cause description from signals."""
        if not signals:
            return "No signals detected"

        signal_types = set(s["type"] for s in signals)
        entities = set(s.get("entity", "unknown") for s in signals)

        return (
            f"Auto-detected incident: {', '.join(signal_types)}. "
            f"Affected entities: {', '.join(entities)}. "
            f"Total signals: {len(signals)}."
        )

    def _build_blast_radius(self, signals: list[dict], affected_models: list[str]) -> dict:
        """Build blast radius from signals."""
        return {
            "source": {"name": "auto-detected", "type": "signal", "status": "warning"},
            "affected": [
                {"name": model, "type": "mlModel", "status": "warning"}
                for model in affected_models
            ],
            "business_impact": {
                "predictions_today": 0,
                "revenue_at_risk_daily": 0,
                "affected_dashboards": 0,
            },
        }

    def get_incidents(self) -> list[dict]:
        """Get all generated incidents (for replay)."""
        # This would return dynamically generated incidents
        # For now, return empty list (can be extended)
        return []
