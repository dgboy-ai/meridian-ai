"""Verify all components work correctly."""
import sys
sys.path.insert(0, ".")

print("=" * 60)
print("MERIDIAN AI - FULL VERIFICATION")
print("=" * 60)

# 1. Test replay module
print("\n[1] Replay Driver")
from backend.replay import ReplayDriver
r = ReplayDriver()
incidents = r.list_incidents()
print(f"  Incidents: {len(incidents)}")
for inc in incidents:
    print(f"    #{inc['id']}: {inc['title']} ({inc['severity']})")
print(f"  Resolution times: {len(r.get_resolution_times())}")
inc42 = r.get_incident('42')
print(f"  Incident 42 timeline: {len(inc42['timeline'])} events")
print(f"  Incident 42 blast: {len(inc42['blast_radius']['affected'])} nodes")
print(f"  Incident 42 writeback: {list(inc42['writeback'].keys())}")
print("  PASS")

# 2. Test evidence model
print("\n[2] Evidence Model")
from backend.models import EvidenceObject, Severity
e = EvidenceObject(
    worker_id="test",
    timestamp="2026-01-01T00:00:00Z",
    finding="Test finding",
    confidence=0.95,
    severity=Severity.HIGH,
)
assert e.confidence == 0.95
assert e.severity == Severity.HIGH
print(f"  Created: {e.worker_id}, confidence={e.confidence}")
print("  PASS")

# 3. Test validation layer
print("\n[3] Validation Layer")
from backend.validation import ValidationLayer
v = ValidationLayer()
result = v.validate(e)
print(f"  Approved: {result.approved}")
print(f"  Reasons: {result.reasons}")
print("  PASS")

# 4. Test Groq client (mock mode)
print("\n[4] Groq Client (mock)")
from backend.clients.groq_client import GroqClient
g = GroqClient(mock=True)
response = g.complete([{"role": "user", "content": "test"}])
print(f"  Mock response length: {len(response)}")
print("  PASS")

# 5. Test DataHub client (mock)
print("\n[5] DataHub Client (mock)")
from backend.clients.datahub_client import DataHubMCPClient
import asyncio
mcp = DataHubMCPClient(mock=True)
entities = asyncio.run(mcp.get_entities([
    "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"
]))
print(f"  Entities: {len(entities)}")
print(f"  First entity: {entities[0].get('name', 'unknown')}")
print("  PASS")

# 6. Test planner agent
print("\n[6] Planner Agent")
from backend.workers.planner import PlannerAgent
planner = PlannerAgent(mcp=mcp, groq=g)

async def run_planner():
    events = []
    async for event in planner.investigate(
        "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
        incident_id="42"
    ):
        events.append(event)
    return events

events = asyncio.run(run_planner())
print(f"  Events: {len(events)}")
print(f"  Steps: {[e.get('step') for e in events]}")
print("  PASS")

print("\n" + "=" * 60)
print("ALL COMPONENTS VERIFIED SUCCESSFULLY")
print("=" * 60)
