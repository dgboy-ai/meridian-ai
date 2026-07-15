"""Replay mode — streams pre-recorded incident data with realistic delays."""
import json
import asyncio
import logging
from pathlib import Path
from collections.abc import AsyncIterator
from datetime import datetime, timezone

logger = logging.getLogger("meridian-ai.replay")


class ReplayDriver:
    def __init__(self, data_path: str | None = None):
        if data_path is None:
            data_path = str(Path(__file__).parent / "replay_data.json")
        try:
            with open(data_path) as f:
                self._data = json.load(f)
        except FileNotFoundError:
            logger.warning(f"Replay data file not found at {data_path}. Using empty dataset.")
            self._data = {"incidents": {}, "resolution_times": []}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse replay data at {data_path}: {e}. Using empty dataset.")
            self._data = {"incidents": {}, "resolution_times": []}

    def list_incidents(self) -> list[dict]:
        incidents = []
        for inc_id, inc in self._data.get("incidents", {}).items():
            incidents.append({
                "id": inc_id,
                "title": inc.get("title", ""),
                "severity": inc.get("severity", ""),
                "status": inc.get("status", ""),
                "detected": inc.get("detected", ""),
                "duration_seconds": inc.get("duration_seconds", 0),
                "affected_models": inc.get("affected_models", []),
                "pattern_id": inc.get("pattern_id", ""),
            })
        return incidents

    def get_incident(self, incident_id: str) -> dict | None:
        return self._data.get("incidents", {}).get(incident_id)

    def get_resolution_times(self) -> list[dict]:
        return self._data.get("resolution_times", [])

    async def stream_investigation(self, incident_id: str, delay: float = 0.5) -> AsyncIterator[dict]:
        incident = self.get_incident(incident_id)
        if not incident:
            yield {"step": "error", "status": "failed", "message": f"Incident {incident_id} not found"}
            return

        timeline = incident.get("timeline", [])
        for event in timeline:
            yield {
                "step": event.get("step", "unknown"),
                "status": event.get("status", "completed"),
                "timestamp": event.get("time", datetime.now(timezone.utc).strftime("%H:%M:%S")),
                "finding": event.get("finding", ""),
                "confidence": event.get("confidence", 0.9),
                "message": event.get("message", ""),
                "evidence": event.get("evidence"),
                "severity": event.get("severity"),
                "business_impact": event.get("business_impact"),
            }
            await asyncio.sleep(delay)

        yield {
            "step": "complete",
            "status": "done",
            "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            "message": f"Investigation #{incident_id} complete. {len(timeline)} steps executed.",
            "incident_id": incident_id,
            "blast_radius": incident.get("blast_radius"),
            "writeback": incident.get("writeback"),
            "duration_seconds": incident.get("duration_seconds", 0),
        }
