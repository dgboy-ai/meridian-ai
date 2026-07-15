"""Auto-Investigate Action — triggered by DataHub Actions Framework.

When DataHub detects a metadata change (schema update, freshness violation, etc.),
this action automatically starts a Meridian AI investigation.

Usage in YAML Actions Pipeline:
```yaml
name: meridian-auto-investigator
source:
  type: kafka
  config:
    connection:
      bootstrap: ${DATAHUB_KAFKA_BOOTSTRAP}
filter:
  event_type: "EntityChangeEvent_v1"
  aspect: "schemaMetadata"
action:
  type: custom
  config:
    class: "meridian.actions.auto_investigate.AutoInvestigateAction"
    config:
      api_endpoint: "http://localhost:8000"
      autonomy_level: 2
      max_investigation_time_seconds: 300
```
"""
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger("meridian-ai.actions")


class AutoInvestigateAction:
    """DataHub Actions Framework handler that triggers Meridian investigations.

    This action is triggered by metadata change events in DataHub.
    It analyzes the event, determines if investigation is needed,
    and starts the Meridian AI investigation pipeline.
    """

    def __init__(self, config: dict):
        self.api_endpoint = config.get("api_endpoint", "http://localhost:8000")
        self.autonomy_level = config.get("autonomy_level", 2)
        self.max_investigation_time = config.get("max_investigation_time_seconds", 300)
        self.min_severity = config.get("min_severity", "MEDIUM")
        self._investigation_count = 0

    async def handle(self, event: dict) -> dict:
        """Handle a DataHub metadata change event.

        Args:
            event: DataHub event payload containing:
                - event_type: Type of metadata change
                - entity_urn: URN of the affected entity
                - aspect: Which aspect changed
                - old_value: Previous aspect value
                - new_value: New aspect value

        Returns:
            Action result with investigation status
        """
        event_type = event.get("event_type", "unknown")
        entity_urn = event.get("entity_urn", "")
        aspect = event.get("aspect", "")

        logger.info(f"Auto-Investigate triggered: {event_type} on {entity_urn} (aspect: {aspect})")

        # Determine if this event warrants an investigation
        severity = self._assess_severity(event)
        if not self._should_investigate(severity):
            logger.info(f"Event severity {severity} below threshold {self.min_severity}. Skipping.")
            return {
                "status": "skipped",
                "reason": f"Severity {severity} below threshold",
                "event_type": event_type,
                "entity_urn": entity_urn,
            }

        # Start investigation
        self._investigation_count += 1
        investigation_id = f"AUTO-{self._investigation_count}"

        logger.info(f"Starting investigation {investigation_id} for {entity_urn}")

        # In production, this would call the FastAPI endpoint
        # For demo, we return a structured result
        result = {
            "status": "investigation_started",
            "investigation_id": investigation_id,
            "trigger_event": {
                "event_type": event_type,
                "entity_urn": entity_urn,
                "aspect": aspect,
                "severity": severity,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "autonomy_level": self.autonomy_level,
            "message": f"Auto-investigation {investigation_id} triggered for {entity_urn}",
        }

        logger.info(f"Investigation {investigation_id} started successfully")
        return result

    def _assess_severity(self, event: dict) -> str:
        """Assess the severity of a metadata change event."""
        aspect = event.get("aspect", "")
        event_type = event.get("event_type", "")

        # High severity: schema changes, ownership changes
        if aspect in ["schemaMetadata", "ownership", "globalTags"]:
            return "HIGH"

        # Medium severity: description changes, documentation updates
        if aspect in ["editableSchemaMetadata", "browsePaths"]:
            return "MEDIUM"

        # Low severity: everything else
        return "LOW"

    def _should_investigate(self, severity: str) -> bool:
        """Determine if an event warrants investigation based on severity."""
        severity_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        min_order = severity_order.get(self.min_severity, 1)
        event_order = severity_order.get(severity, 0)
        return event_order >= min_order

    def get_stats(self) -> dict:
        """Get action statistics."""
        return {
            "total_investigations": self._investigation_count,
            "autonomy_level": self.autonomy_level,
            "min_severity": self.min_severity,
            "api_endpoint": self.api_endpoint,
        }
