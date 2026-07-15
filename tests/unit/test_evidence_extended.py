"""Extended tests for Evidence Object schema."""
import pytest
from backend.models import EvidenceObject, Severity, EvidenceItem, BusinessImpact, DataHubMutation


class TestEvidenceObjectExtended:
    def test_confidence_boundary_zero(self):
        e = EvidenceObject(
            worker_id="test", timestamp="2026-01-01T00:00:00Z",
            finding="test", confidence=0.0, severity=Severity.LOW,
        )
        assert e.confidence == 0.0

    def test_confidence_boundary_one(self):
        e = EvidenceObject(
            worker_id="test", timestamp="2026-01-01T00:00:00Z",
            finding="test", confidence=1.0, severity=Severity.LOW,
        )
        assert e.confidence == 1.0

    def test_confidence_rejects_negative(self):
        with pytest.raises(Exception):
            EvidenceObject(
                worker_id="test", timestamp="2026-01-01T00:00:00Z",
                finding="test", confidence=-0.1, severity=Severity.LOW,
            )

    def test_confidence_rejects_above_one(self):
        with pytest.raises(Exception):
            EvidenceObject(
                worker_id="test", timestamp="2026-01-01T00:00:00Z",
                finding="test", confidence=1.1, severity=Severity.LOW,
            )

    def test_severity_all_values(self):
        for s in [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]:
            e = EvidenceObject(
                worker_id="test", timestamp="2026-01-01T00:00:00Z",
                finding="test", confidence=0.5, severity=s,
            )
            assert e.severity == s

    def test_evidence_item_minimal(self):
        item = EvidenceItem(type="test")
        assert item.type == "test"
        assert item.entity_urn is None

    def test_evidence_item_full(self):
        item = EvidenceItem(
            type="schema_diff",
            description="Column changed",
            before={"type": "INT"},
            after={"type": "STRING"},
            entity_urn="urn:test",
            downstream_count=3,
            affected_models=["model1"],
            affected_dashboards=5,
        )
        assert item.type == "schema_diff"
        assert item.entity_urn == "urn:test"
        assert item.downstream_count == 3

    def test_business_impact_defaults(self):
        impact = BusinessImpact()
        assert impact.predictions_today is None
        assert impact.estimated_revenue_at_risk is None

    def test_business_impact_full(self):
        impact = BusinessImpact(
            predictions_today=32000,
            estimated_revenue_at_risk="$45,000/day",
            affected_systems=["API", "Dashboard"],
        )
        assert impact.predictions_today == 32000

    def test_datahub_mutation_safe(self):
        m = DataHubMutation(tool="add_tags", params={"tags": ["test"]}, safe=True)
        assert m.safe is True

    def test_datahub_mutation_unsafe(self):
        m = DataHubMutation(tool="delete", params={}, safe=False)
        assert m.safe is False

    def test_datahub_mutation_default_safe(self):
        m = DataHubMutation(tool="test", params={})
        assert m.safe is True

    def test_full_object_serialization(self):
        e = EvidenceObject(
            worker_id="data_sentinel",
            timestamp="2026-07-12T14:32:00Z",
            finding="Schema change detected",
            confidence=0.94,
            severity=Severity.HIGH,
            evidence=[EvidenceItem(type="schema_diff", column="age")],
            business_impact=BusinessImpact(predictions_today=32000),
            next_action="Notify Root Cause",
            datahub_mutations=[DataHubMutation(tool="raiseIncident", params={}, safe=False)],
        )
        d = e.model_dump()
        assert d["worker_id"] == "data_sentinel"
        assert d["confidence"] == 0.94
        assert len(d["evidence"]) == 1
        assert d["business_impact"]["predictions_today"] == 32000

    def test_roundtrip(self):
        e = EvidenceObject(
            worker_id="test", timestamp="2026-01-01T00:00:00Z",
            finding="test", confidence=0.85, severity=Severity.MEDIUM,
        )
        json_str = e.model_dump_json()
        e2 = EvidenceObject.model_validate_json(json_str)
        assert e.worker_id == e2.worker_id
        assert e.confidence == e2.confidence
