"""Quick smoke test for backend.persistence."""
import asyncio
from backend.persistence import PersistenceManager


async def main() -> None:
    async with PersistenceManager() as pm:
        print(f"Backend type: {pm.backend_type}")

        # Incidents
        inc = await pm.record_incident(
            incident_id="test-1",
            title="Schema drift detected",
            severity="high",
            status="open",
            detected="2026-01-01T00:00:00Z",
        )
        fetched = await pm.get_incident("test-1")
        assert fetched is not None
        assert fetched.title == "Schema drift detected"
        print("Incident roundtrip: OK")

        # Investigations
        inv = await pm.record_investigation(
            investigation_id="inv-1",
            incident_id="test-1",
            mode="replay",
        )
        inv_list = await pm.list_investigations(incident_id="test-1")
        assert len(inv_list) == 1
        print("Investigation roundtrip: OK")

        # Costs
        await pm.record_cost(cost_id="c1", incident_id="test-1", worker_id="root-cause", tokens_in=500)
        summary = await pm.get_cost_summary("test-1")
        assert summary["record_count"] == 1
        print("Cost roundtrip: OK")

        # Provenance
        await pm.record_provenance(provenance_id="p1", incident_id="test-1", worker_id="root-cause", source_type="datahub_metadata")
        prov_summary = await pm.get_provenance_summary("test-1")
        assert prov_summary["total_sources"] == 1
        print("Provenance roundtrip: OK")

        # Listing
        incidents = await pm.list_incidents()
        assert len(incidents) >= 1
        print("Listing: OK")

    print("\nAll tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
