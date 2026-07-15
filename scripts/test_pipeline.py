"""Test the full investigation pipeline end-to-end."""
import asyncio
import sys
sys.path.insert(0, '.')

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.workers.planner import PlannerAgent


async def test():
    mcp = DataHubMCPClient(mock=True)
    groq = GroqClient(mock=True)
    planner = PlannerAgent(mcp=mcp, groq=groq)

    events = []
    async for event in planner.investigate(
        'urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)',
        'TEST-001'
    ):
        events.append(event)
        step = event.get('step', '?')
        status = event.get('status', '?')
        msg = event.get('message', '')
        print(f'  [{step}] {status}: {msg[:80]}')

    print(f'\nTotal events: {len(events)}')
    print(f'Steps: {list(set(e["step"] for e in events))}')

    summary = events[-1].get('summary', {})
    print(f'Health score: {summary.get("health_score")}')
    print(f'Resolution time: {summary.get("resolution_time_minutes")}min')
    print(f'Mutations: {summary.get("datahub_mutations")}')
    print(f'Compliance: {summary.get("compliance")}')

    # Check DataHub state
    entities = await mcp.get_entities([
        'urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)'
    ])
    if entities:
        e = entities[0]
        print(f'\nDataHub state:')
        print(f'  health_score: {e.get("health_score")}')
        print(f'  resolved_incidents: {e.get("resolved_incidents")}')
        print(f'  last_investigation: {e.get("last_investigation")}')


if __name__ == '__main__':
    asyncio.run(test())
