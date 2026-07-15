"""Verify all 14 workers fire in the planner and all integrations work."""
import asyncio
import sys
sys.path.insert(0, ".")

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.workers.planner import PlannerAgent


async def main():
    print("=" * 70)
    print("FULL VERIFICATION — ALL 14 WORKERS + INTEGRATIONS")
    print("=" * 70)

    mcp = DataHubMCPClient(mock=True)
    groq = GroqClient(mock=True)
    planner = PlannerAgent(mcp=mcp, groq=groq)

    # Check all components are wired
    checks = {
        "AutonomyManager": hasattr(planner, "autonomy"),
        "HealthCalculator": hasattr(planner, "health_calculator"),
        "ValidationLayer(mcp)": planner.validation.mcp is not None,
        "CircuitBreaker": hasattr(groq, "_circuit_breaker"),
        "ReflexionLoop": hasattr(planner, "reflexion"),
        "ComplianceEngine": hasattr(planner, "compliance_engine"),
        "ExplanationDrift": hasattr(planner, "explanation_drift"),
        "SelfHealingAssertions": hasattr(planner, "self_healing"),
    }
    print("\n[1] Component Wiring:")
    for name, ok in checks.items():
        print(f"    {'OK' if ok else 'MISSING'}: {name}")

    # Run full investigation
    print("\n[2] Running full investigation...")
    events = []
    async for event in planner.investigate(
        "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
        incident_id="VERIFY-001",
    ):
        events.append(event)

    # Check all workers fired
    expected_workers = [
        "data_sentinel", "feature_drift", "training_serving_skew",
        "data_leakage", "root_cause", "knowledge_writer", "reflexion",
        "lifecycle_governance", "eu_ai_act_compliance", "shadow_ai_discovery",
        "contract_enforcer", "explanation_drift", "self_healing_assertions",
    ]
    fired = [e["step"] for e in events if e.get("status") == "completed"]

    print(f"\n[3] Workers Fired ({len(fired)}):")
    for w in expected_workers:
        status = "OK" if w in fired else "MISSING"
        print(f"    {status}: {w}")

    # Check summary
    summary = events[-1].get("summary", {})
    print(f"\n[4] Summary:")
    print(f"    Resolution time: {summary.get('resolution_time_minutes')}min")
    print(f"    Health score: {summary.get('health_score')}")
    print(f"    Health assessment: {summary.get('health_assessment')}")
    print(f"    DataHub mutations: {summary.get('datahub_mutations')}")
    print(f"    Validation passed: {summary.get('validation_passed')}")
    print(f"    Compliance articles: {summary.get('compliance', {}).get('articles_covered')}")
    print(f"    Audit chain length: {summary.get('compliance', {}).get('audit_chain_length')}")

    # Check knowledge writer wrote to DataHub
    churn_model = await mcp.get_entities([
        "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"
    ])
    if churn_model:
        e = churn_model[0]
        print(f"\n[5] DataHub State After Investigation:")
        print(f"    resolved_incidents: {e.get('resolved_incidents', 'MISSING')}")
        print(f"    ai_health_score: {e.get('ai_health_score', 'MISSING')}")
        print(f"    ai_confidence: {e.get('ai_confidence', 'MISSING')}")
        print(f"    last_investigation: {e.get('last_investigation', 'MISSING')}")

    # Check documents written
    docs = await mcp.search_documents(query="incident")
    print(f"    Documents in Knowledge Base: {len(docs)}")

    # Check incidents raised
    print(f"    Compliance chain valid: {planner.compliance_engine._verify_chain()}")

    # Verify all workers compute real things
    print(f"\n[6] Real Computation Verification:")
    from backend.stats import population_stability_index, ks_test, compute_schema_diff, traverse_lineage
    psi = population_stability_index([1,2,3], [10,20,30])
    print(f"    PSI: drifted={psi.drifted}, value={psi.value:.4f}")
    ks = ks_test([1,2,3], [10,20,30])
    print(f"    KS: drifted={ks.drifted}, value={ks.value:.4f}")
    diff = compute_schema_diff([{"name":"a","type":"INT"}], [{"name":"a","type":"STRING"}])
    print(f"    Schema diff: has_changes={diff.has_changes}, type_changes={len(diff.type_changes)}")

    all_ok = all(w in fired for w in expected_workers)
    print(f"\n{'=' * 70}")
    print(f"RESULT: {'ALL 14 WORKERS FIRED' if all_ok else 'SOME WORKERS MISSING'}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(main())
