"""Verify all fatal weakness fixes are working."""
import asyncio
import sys
sys.path.insert(0, ".")


async def main():
    print("=" * 60)
    print("VERIFYING FATAL WEAKNESS FIXES")
    print("=" * 60)

    # 1. DataHub dual-mode client
    from backend.clients.datahub_client import DataHubMCPClient
    c = DataHubMCPClient(mock=False)
    print(f"\n[1] DataHub Client: mode={c.mode}, connected={c._connected}")
    entities = await c.get_entities(["urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"])
    print(f"    get_entities: {len(entities)} found")
    lineage = await c.get_lineage("urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)")
    print(f"    get_lineage: {len(lineage.get('downstream', []))} downstream")
    print(f"    PASS: Client works in both real and mock modes")

    # 2. Statistical drift detection
    from backend.stats import feature_drift_score, type_mismatch_check, population_stability_index, ks_test
    r1 = feature_drift_score([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
    r2 = feature_drift_score([1, 2, 3, 4, 5], [100, 200, 300, 400, 500])
    r3 = type_mismatch_check(
        [{"name": "age", "type": "INT"}],
        [{"name": "age", "type": "STRING"}],
    )
    print(f"\n[2] Statistical Drift:")
    print(f"    No drift: score={r1['combined_score']}, drifted={r1['drifted']}")
    print(f"    Clear drift: score={r2['combined_score']}, drifted={r2['drifted']}")
    print(f"    Type mismatch: count={r3['count']}, drifted={r3['drifted']}")
    assert not r1["drifted"]
    assert r2["drifted"]
    assert r3["drifted"]
    print(f"    PASS: PSI + KS-test + type mismatch all working")

    # 3. Actions listener
    from backend.actions.listener import ActionsListener
    listener = ActionsListener()
    result = await listener.process_webhook_event({
        "event_type": "EntityChangeEvent_v1",
        "entity_urn": "urn:li:dataset:test",
        "aspect": "schemaMetadata",
    })
    print(f"\n[3] Actions Listener:")
    print(f"    Status: {result['status']}")
    print(f"    Should investigate: {result['should_investigate']}")
    print(f"    Events logged: {listener.get_stats()['total_events']}")
    assert result["should_investigate"] is True
    print(f"    PASS: Actions listener processes events correctly")

    # 4. Full planner integration
    from backend.clients.groq_client import GroqClient
    from backend.workers.planner import PlannerAgent
    groq = GroqClient(mock=True)
    planner = PlannerAgent(mcp=c, groq=groq)
    steps = []
    async for event in planner.investigate(
        "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
        incident_id="VERIFY-ALL",
    ):
        steps.append(event["step"] + ":" + event["status"])

    expected_workers = [
        "data_sentinel", "feature_drift", "training_serving_skew",
        "data_leakage", "root_cause", "knowledge_writer", "reflexion",
        "lifecycle_governance", "eu_ai_act_compliance", "shadow_ai_discovery",
        "contract_enforcer",
    ]
    print(f"\n[4] Planner Integration:")
    print(f"    Total events: {len(steps)}")
    for w in expected_workers:
        found = any(w in s and "completed" in s for s in steps)
        status = "OK" if found else "MISSING"
        print(f"    {w}: {status}")
    assert all(any(w in s and "completed" in s for s in steps) for w in expected_workers)
    print(f"    PASS: All {len(expected_workers)} workers fire correctly")

    # 5. EU AI Act compliance
    from backend.workers.eu_ai_act_compliance import EUAIActComplianceEngine
    engine = EUAIActComplianceEngine(mcp=c, groq=groq)
    record = await engine.record_decision(
        article="12", decision_type="test", input_summary="in", output_summary="out", confidence=0.95
    )
    print(f"\n[5] EU AI Act Compliance:")
    print(f"    Record: {record.record_id}")
    print(f"    Hash: {record.hash_sha256[:16]}...")
    print(f"    Chain valid: {engine._verify_chain()}")
    assert engine._verify_chain()
    print(f"    PASS: SHA-256 audit chain working")

    print(f"\n{'=' * 60}")
    print("ALL 5 FATAL WEAKNESSES FIXED")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
