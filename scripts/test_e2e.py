"""End-to-end test of Meridian AI investigation."""
import asyncio
from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.workers.planner import PlannerAgent


async def test():
    # Test with mock mode
    mcp = DataHubMCPClient(mock=True)
    groq = GroqClient()
    planner = PlannerAgent(mcp=mcp, groq=groq)

    print("=== End-to-End Test (Mock Mode) ===")
    print()

    events = []
    async for event in planner.investigate(
        "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
        "42"
    ):
        events.append(event)
        step = event.get("step", "unknown")
        status = event.get("status", "unknown")
        print(f"  {step}: {status}")

    print()
    print(f"Total events: {len(events)}")

    # Get summary
    summary_event = [e for e in events if "summary" in e]
    if summary_event:
        summary = summary_event[0]["summary"]
        workers = summary.get("workers_fired", [])
        print(f"Workers fired: {len(workers)}")
        print(f"  - {', '.join(workers[:5])}...")
        print(f"Health score: {summary.get('health_score', 'N/A')}")
        print(f"DataHub mutations: {summary.get('datahub_mutations', 0)}")
        print(f"Validation passed: {summary.get('validation_passed', False)}")

        compliance = summary.get("compliance", {})
        print(f"EU AI Act articles: {compliance.get('articles_covered', [])}")
        print(f"Audit chain length: {compliance.get('audit_chain_length', 0)}")

        cost = summary.get("cost_attribution", {})
        print(f"Resolution time: {summary.get('resolution_time_minutes', 0)} min")

    print()
    print("=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test())
