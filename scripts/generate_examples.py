"""Generate example investigation outputs for the examples/ folder."""
import asyncio
import json
import sys
sys.path.insert(0, ".")

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.workers.planner import PlannerAgent


async def run():
    mcp = DataHubMCPClient(mock=True)
    groq = GroqClient(mock=True)
    planner = PlannerAgent(mcp=mcp, groq=groq)

    events = []
    async for event in planner.investigate(
        "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
        incident_id="42",
    ):
        events.append(event)

    with open("examples/incident_42_timeline.json", "w") as f:
        json.dump(events, f, indent=2)
    print(f"Wrote {len(events)} events to examples/incident_42_timeline.json")

    summary = events[-1].get("summary", {})
    with open("examples/incident_42_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote summary to examples/incident_42_summary.json")
    print(f"Health score: {summary.get('health_score')}")
    print(f"Resolution time: {summary.get('resolution_time_minutes')}min")
    print(f"Workers fired: {len(summary.get('workers_fired', []))}")


if __name__ == "__main__":
    asyncio.run(run())
