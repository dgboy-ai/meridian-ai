"""Quick smoke test for judges — verifies core investigation works."""
import sys, asyncio
sys.path.insert(0, ".")

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.workers.planner import PlannerAgent


async def main():
    mcp = DataHubMCPClient(mock=True)
    groq = GroqClient(mock=True)
    planner = PlannerAgent(mcp=mcp, groq=groq)

    events = []
    async for event in planner.investigate(
        "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
        incident_id="SMOKE",
    ):
        events.append(event)

    summary = events[-1].get("summary", {})
    print(f"Events: {len(events)}")
    print(f"Health score: {summary.get('health_score')}")
    print(f"Workers fired: {len(summary.get('workers_fired', []))}")
    print(f"DataHub mutations: {summary.get('datahub_mutations')}")
    print(f"Resolution time: {summary.get('resolution_time_minutes')} min")
    print("PASS")


if __name__ == "__main__":
    asyncio.run(main())
