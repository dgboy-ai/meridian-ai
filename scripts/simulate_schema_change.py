"""Simulate a schema change incident for the demo."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.workers.planner import PlannerAgent


async def simulate():
    print("=" * 60)
    print("MERIDIAN AI — Simulating Schema Change Incident")
    print("=" * 60)

    mcp = DataHubMCPClient(mock=True)
    groq = GroqClient()
    planner = PlannerAgent(mcp=mcp, groq=groq)

    dataset_urn = "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)"

    print("\nTriggering investigation...")
    print("-" * 60)

    async for event in planner.investigate(dataset_urn, incident_id="42"):
        step = event.get("step", "")
        status = event.get("status", "")
        message = event.get("message", "")

        if status == "running":
            print(f"\n  [{step.upper()}] {message}")
        elif status == "completed":
            evidence = event.get("evidence", {})
            confidence = evidence.get("confidence", "N/A")
            finding = evidence.get("finding", message)
            print(f"  -> {finding}")
            if confidence != "N/A":
                print(f"     Confidence: {confidence}")
        elif status == "started":
            print(f"\n{message}")

    print("\n" + "=" * 60)
    print("Investigation complete. 4 artifacts written to DataHub.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(simulate())
