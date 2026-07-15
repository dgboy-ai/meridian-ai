"""Tests for EvidenceObject, Severity, and related models."""
import pytest
from backend.models.evidence import (
    EvidenceObject,
    Severity,
    EvidenceItem,
    BusinessImpact,
    DataHubMutation,
)


class TestSeverity:
    def test_severity_values(self):
        assert Severity.LOW == "low"
        assert Severity.MEDIUM == "medium"
        assert Severity.HIGH == "high"
        assert Severity.CRITICAL == "critical"

    def test_severity_from_string(self):
        assert Severity("high") == Severity.HIGH
        assert Severity("critical") == Severity.CRITICAL

    def test_severity_is_str_subclass(self):
        assert isinstance(Severity.HIGH, str)

    def test_severity_invalid_value(self):
        with pytest.raises(ValueError):
            Severity("unknown")


class TestEvidenceItem:
    def test_minimal_item(self):
        item = EvidenceItem(type="schema_change")
        assert item.type == "schema_change"
        assert item.description is None
        assert item.entity_urn is None

    def test_full_item(self):
        item = EvidenceItem(
            type="distribution_shift",
            description="Feature collapsed",
            before={"entropy": 2.3},
            after={"entropy": 0.1},
            entity_urn="urn:li:dataset:123",
            downstream_count=5,
            affected_models=["model_a", "model_b"],
            affected_dashboards=12,
        )
        assert item.downstream_count == 5
        assert len(item.affected_models) == 2
        assert item.affected_dashboards == 12


class TestBusinessImpact:
    def test_impact_creation(self):
        impact = BusinessImpact(
            predictions_today=32000,
            estimated_revenue_at_risk="$45,000/day",
            affected_systems=["model_a", "model_b"],
        )
        assert impact.predictions_today == 32000
        assert len(impact.affected_systems) == 2

    def test_impact_defaults(self):
        impact = BusinessImpact()
        assert impact.predictions_today is None
        assert impact.estimated_revenue_at_risk is None
        assert impact.affected_systems is None


class TestDataHubMutation:
    def test_safe_mutation(self):
        m = DataHubMutation(tool="add_owner", params={"owner": "alice"}, safe=True)
        assert m.safe is True

    def test_unsafe_mutation(self):
        m = DataHubMutation(tool="delete_dataset", params={"urn": "urn:1"}, safe=False)
        assert m.safe is False

    def test_default_safe(self):
        m = DataHubMutation(tool="tag_entity", params={})
        assert m.safe is True


class TestEvidenceObject:
    def test_creation(self):
        obj = EvidenceObject(
            worker_id="data_sentinel",
            timestamp="2026-07-12T09:31:12Z",
            finding="Schema change detected",
            confidence=0.94,
            severity=Severity.CRITICAL,
        )
        assert obj.worker_id == "data_sentinel"
        assert obj.confidence == 0.94
        assert obj.severity == Severity.CRITICAL
        assert obj.evidence == []
        assert obj.datahub_mutations == []

    def test_confidence_bounds(self):
        EvidenceObject(
            worker_id="w", timestamp="t", finding="f",
            confidence=0.0, severity=Severity.LOW,
        )
        EvidenceObject(
            worker_id="w", timestamp="t", finding="f",
            confidence=1.0, severity=Severity.HIGH,
        )

    def test_confidence_below_zero_rejected(self):
        with pytest.raises(Exception):
            EvidenceObject(
                worker_id="w", timestamp="t", finding="f",
                confidence=-0.1, severity=Severity.LOW,
            )

    def test_confidence_above_one_rejected(self):
        with pytest.raises(Exception):
            EvidenceObject(
                worker_id="w", timestamp="t", finding="f",
                confidence=1.5, severity=Severity.LOW,
            )

    def test_full_object(self):
        obj = EvidenceObject(
            worker_id="root_cause",
            timestamp="2026-07-12T09:31:18Z",
            finding="3 models, 12 dashboards affected",
            confidence=0.96,
            severity=Severity.HIGH,
            evidence=[
                EvidenceItem(type="lineage_impact", description="downstream impact", downstream_count=3),
            ],
            business_impact=BusinessImpact(predictions_today=32000),
            next_action="Investigate feature drift",
            datahub_mutations=[DataHubMutation(tool="add_tag", params={})],
        )
        assert len(obj.evidence) == 1
        assert obj.business_impact.predictions_today == 32000
        assert obj.next_action == "Investigate feature drift"
        assert len(obj.datahub_mutations) == 1

    def test_serialization_roundtrip(self):
        obj = EvidenceObject(
            worker_id="w", timestamp="t", finding="f",
            confidence=0.88, severity=Severity.MEDIUM,
            evidence=[EvidenceItem(type="test")],
        )
        data = obj.model_dump()
        restored = EvidenceObject(**data)
        assert restored.worker_id == obj.worker_id
        assert restored.confidence == obj.confidence
        assert restored.evidence[0].type == "test"
