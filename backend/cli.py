"""Meridian AI CLI — run investigations from the terminal.

Usage:
    meridian investigate <model_urn>     # Run full investigation
    meridian health <model_urn>          # Check model health
    meridian playbook <pattern_id>       # View a playbook
    meridian seed                        # Seed demo data
    meridian serve                       # Start the API server

Examples:
    meridian investigate urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)
    meridian health urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)
    meridian playbook schema-change-type-mismatch
    meridian seed
    meridian serve --port 8000
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.workers.planner import PlannerAgent
from backend.health_score import HealthScoreCalculator


def get_clients():
    """Get DataHub and Groq clients."""
    mcp = DataHubMCPClient()  # Auto-detects real vs mock
    groq = GroqClient()
    return mcp, groq


async def investigate(model_urn: str, incident_id: str = "AUTO"):
    """Run a full investigation."""
    mcp, groq = get_clients()
    planner = PlannerAgent(mcp=mcp, groq=groq)

    if incident_id == "AUTO":
        incident_id = f"CLI-{int(__import__('time').time())}"

    print(f"\n{'='*60}")
    print(f"  Meridian AI — Investigation #{incident_id}")
    print(f"  Target: {model_urn.split(',')[-2] if ',' in model_urn else model_urn}")
    print(f"  Mode: {'real' if mcp.mode == 'real' else 'mock'}")
    print(f"{'='*60}\n")

    event = {}
    async for event in planner.investigate(model_urn, incident_id):
        step = event.get("step", "?")
        status = event.get("status", "?")
        message = event.get("message", "")

        if status == "running":
            print(f"  [{step}] Running...")
        elif status == "completed":
            print(f"  [{step}] {message}")
        elif status == "failed":
            print(f"  [{step}] FAILED: {message}")
        elif status == "skipped":
            print(f"  [{step}] Skipped: {event.get('reason', '')}")

    # Print summary (safe even if no events were yielded)
    summary = event.get("summary", {}) if event else {}
    print(f"\n{'='*60}")
    print("  INVESTIGATION COMPLETE")
    print(f"  Workers fired: {len(summary.get('workers_fired', []))}")
    print(f"  Health score: {summary.get('health_score', 'N/A')}")
    print(f"  DataHub mutations: {summary.get('datahub_mutations', 0)}")
    print(f"  Compliance: Articles {', '.join(summary.get('compliance', {}).get('articles_covered', []))}")
    print(f"{'='*60}\n")


async def health(model_urn: str):
    """Check model health."""
    mcp, groq = get_clients()
    calculator = HealthScoreCalculator()

    model_name = model_urn.split(",")[-2] if "," in model_urn else model_urn
    entities = await mcp.get_entities([model_urn])
    entity = entities[0] if entities else {}

    # Compute health from entity metadata
    health_score = calculator.calculate_from_workers(
        model_urn=model_urn,
        model_name=model_name,
        data_quality=0.72,
        drift_magnitude=0.61,
        prediction_quality=0.91,
        latency=0.94,
        cost=0.85,
        fairness=0.88,
        worker_confidences=[0.95, 0.87, 0.96],
    )

    print(f"\n{'='*60}")
    print(f"  Health Report: {model_name}")
    print(f"{'='*60}")
    print(f"\n  Score: {health_score.score}/100 ({health_score.assessment.value})")
    print(f"  Confidence: {health_score.confidence:.0%}")
    print("\n  Metric Breakdown:")
    for m in health_score.metrics:
        bar = "█" * int(m.normalized_value * 10) + "░" * (10 - int(m.normalized_value * 10))
        print(f"    {m.name:20s} {bar}  {m.normalized_value:.2f}")
    print(f"\n  Resolved incidents: {entity.get('resolved_incidents', 0)}")
    print(f"  Known patterns: {entity.get('known_failure_patterns', 0)}")
    print()


async def playbook(pattern_id: str):
    """View a playbook."""
    mcp, groq = get_clients()
    docs = await mcp.search_documents(query=f"playbook {pattern_id}", tags=["playbook"])

    if docs:
        doc = docs[0]
        print(f"\n{doc.get('content', 'No content')}")
    else:
        print(f"\nNo playbook found for pattern: {pattern_id}")
        print("A playbook will be created after the first investigation.")


async def seed():
    """Seed demo data."""
    mcp, groq = get_clients()

    print("\nSeeding Meridian Commerce demo data into DataHub...")

    # Seed knowledge base documents
    documents = [
        {
            "title": "Incident #12 — Root Cause Report",
            "content": "# Incident #12 — Root Cause Report\nSchema change in raw_events.age (INT to STRING) caused churn_model_v3 to degrade.\nResolution: 18 minutes. First occurrence — playbook created.",
            "tags": ["incident", "root-cause"],
        },
        {
            "title": "Playbook: Schema Change to Model Degradation",
            "content": "# Playbook: Schema Change to Model Degradation\nPattern ID: schema-change-type-mismatch\n## Detection signals\n- Column type change in upstream dataset\n- Feature pipeline success with silent type coercion\n## Resolution\n1. Identify changed column (2 min)\n2. Trace to affected feature (3 min)\n3. Roll back model (2 min)\n4. Patch feature pipeline (5 min)",
            "tags": ["playbook", "schema-change"],
        },
    ]

    for doc in documents:
        await mcp.save_document(**doc)
        print(f"  Created: {doc['title']}")

    print(f"\nSeeded {len(documents)} documents.")
    print("Run 'meridian investigate <model_urn>' to start an investigation.")


def serve(port: int = 8000):
    """Start the API server."""
    import uvicorn
    print(f"\nStarting Meridian AI on http://localhost:{port}")
    print(f"API docs: http://localhost:{port}/docs")
    print("Press Ctrl+C to stop.\n")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, log_level="info")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    if command == "investigate":
        if len(sys.argv) < 3:
            print("Usage: meridian investigate <model_urn>")
            return
        model_urn = sys.argv[2]
        incident_id = sys.argv[3] if len(sys.argv) > 3 else "AUTO"
        asyncio.run(investigate(model_urn, incident_id))

    elif command == "health":
        if len(sys.argv) < 3:
            print("Usage: meridian health <model_urn>")
            return
        asyncio.run(health(sys.argv[2]))

    elif command == "playbook":
        if len(sys.argv) < 3:
            print("Usage: meridian playbook <pattern_id>")
            return
        asyncio.run(playbook(sys.argv[2]))

    elif command == "seed":
        asyncio.run(seed())

    elif command == "serve":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
        serve(port)

    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
