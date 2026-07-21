"""Tests for the Deterministic Validation Layer."""
import pytest
from backend.validation import ValidationLayer, CheckResult, ValidationResult
from backend.models.evidence import (
    EvidenceObject,
    Severity,
    EvidenceItem,
    DataHubMutation,
)


def _make_evidence(
    confidence: float = 0.9,
    severity: Severity = Severity.HIGH,
    evidence_items: list | None = None,
    mutations: list | None = None,
) -> EvidenceObject:
    return EvidenceObject(
        worker_id="test_worker",
        timestamp="2026-07-12T09:31:00Z",
        finding="test finding",
        confidence=confidence,
        severity=severity,
        evidence=evidence_items or [],
        datahub_mutations=mutations or [],
    )


class TestCheckResult:
    def test_creation(self):
        r = CheckResult(name="confidence_threshold", passed=True, reason="OK")
        assert r.name == "confidence_threshold"
        assert r.passed is True
        assert r.safe is True

    def test_failed_check(self):
        r = CheckResult(name="action_safety", passed=False, reason="unsafe mutations", safe=False)
        assert r.passed is False
        assert r.safe is False


class TestValidationResult:
    def test_approved(self):
        r = ValidationResult(approved=True)
        assert r.approved is True
        assert r.reasons == []
        assert r.safe_mutations == []

    def test_rejected(self):
        r = ValidationResult(approved=False, reasons=["confidence too low"])
        assert r.approved is False
        assert len(r.reasons) == 1


class TestConfidenceThreshold:
    def test_above_threshold_passes(self):
        layer = ValidationLayer()
        evidence = _make_evidence(confidence=0.9)
        result = layer.validate(evidence)
        assert result.approved is True

    def test_exactly_at_threshold_passes(self):
        layer = ValidationLayer()
        evidence = _make_evidence(confidence=0.7)
        result = layer.validate(evidence)
        assert result.approved is True

    def test_below_threshold_fails(self):
        layer = ValidationLayer()
        evidence = _make_evidence(confidence=0.5)
        result = layer.validate(evidence)
        assert result.approved is False
        assert any("confidence" in r.lower() for r in result.reasons)

    def test_zero_confidence_fails(self):
        layer = ValidationLayer()
        evidence = _make_evidence(confidence=0.0)
        result = layer.validate(evidence)
        assert result.approved is False


class TestEntityExistence:
    def test_no_registry_passes(self):
        layer = ValidationLayer(known_entities=set())
        evidence = _make_evidence(evidence_items=[
            EvidenceItem(type="test", entity_urn="urn:li:dataset:abc"),
        ])
        result = layer.validate(evidence)
        assert result.approved is True

    def test_entity_in_registry_passes(self):
        layer = ValidationLayer(known_entities={"urn:li:dataset:abc", "urn:li:dataset:def"})
        evidence = _make_evidence(evidence_items=[
            EvidenceItem(type="test", entity_urn="urn:li:dataset:abc"),
        ])
        result = layer.validate(evidence)
        assert result.approved is True

    def test_unknown_entity_fails(self):
        layer = ValidationLayer(known_entities={"urn:li:dataset:abc"})
        evidence = _make_evidence(evidence_items=[
            EvidenceItem(type="test", entity_urn="urn:li:dataset:unknown"),
        ])
        result = layer.validate(evidence)
        assert result.approved is False
        assert any("entity" in r.lower() for r in result.reasons)

    def test_multiple_entities_all_known(self):
        layer = ValidationLayer(known_entities={"urn:a", "urn:b"})
        evidence = _make_evidence(evidence_items=[
            EvidenceItem(type="test", entity_urn="urn:a"),
            EvidenceItem(type="test", entity_urn="urn:b"),
        ])
        result = layer.validate(evidence)
        assert result.approved is True


class TestActionSafety:
    def test_all_safe_mutations(self):
        layer = ValidationLayer()
        mutations = [
            DataHubMutation(tool="add_tag", params={}, safe=True),
            DataHubMutation(tool="add_owner", params={}, safe=True),
        ]
        evidence = _make_evidence(mutations=mutations)
        result = layer.validate(evidence)
        assert result.approved is True
        assert len(result.safe_mutations) == 2

    def test_unsafe_mutation_fails(self):
        layer = ValidationLayer()
        mutations = [
            DataHubMutation(tool="delete_dataset", params={}, safe=False),
        ]
        evidence = _make_evidence(mutations=mutations)
        result = layer.validate(evidence)
        # Unsafe mutations are now soft checks — they don't block approval
        # but are reported as warnings queued for human approval
        assert result.approved is True
        assert any("unsafe" in r.lower() for r in result.reasons)
        assert any("queued" in r.lower() for r in result.reasons)
        assert len(result.safe_mutations) == 0

    def test_mixed_safe_and_unsafe(self):
        layer = ValidationLayer()
        mutations = [
            DataHubMutation(tool="add_tag", params={}, safe=True),
            DataHubMutation(tool="delete_dataset", params={}, safe=False),
        ]
        evidence = _make_evidence(mutations=mutations)
        result = layer.validate(evidence)
        # Mixed: hard checks pass, unsafe mutations are warnings
        assert result.approved is True
        assert len(result.safe_mutations) == 1
        assert any("queued" in r.lower() for r in result.reasons)

    def test_no_mutations(self):
        layer = ValidationLayer()
        evidence = _make_evidence(mutations=[])
        result = layer.validate(evidence)
        assert result.approved is True


class TestFullValidationFlow:
    def test_high_quality_evidence_passes_all_checks(self):
        layer = ValidationLayer(known_entities={"urn:li:dataset:raw_events"})
        evidence = _make_evidence(
            confidence=0.94,
            severity=Severity.CRITICAL,
            evidence_items=[
                EvidenceItem(type="schema_change", entity_urn="urn:li:dataset:raw_events"),
            ],
            mutations=[
                DataHubMutation(tool="add_tag", params={"tag": "schema-change"}, safe=True),
            ],
        )
        result = layer.validate(evidence)
        assert result.approved is True
        assert result.reasons == []
        assert len(result.safe_mutations) == 1

    def test_low_confidence_and_unknown_entity(self):
        layer = ValidationLayer(known_entities={"urn:known"})
        evidence = _make_evidence(
            confidence=0.3,
            evidence_items=[
                EvidenceItem(type="test", entity_urn="urn:unknown"),
            ],
        )
        result = layer.validate(evidence)
        assert result.approved is False
        assert len(result.reasons) >= 2

    def test_duplicate_check_always_passes(self):
        layer = ValidationLayer()
        evidence = _make_evidence(confidence=0.99)
        result = layer.validate(evidence)
        assert result.approved is True

    def test_check_result_names(self):
        layer = ValidationLayer(known_entities={"urn:a"})
        evidence = _make_evidence(
            confidence=0.5,
            evidence_items=[EvidenceItem(type="t", entity_urn="urn:b")],
            mutations=[DataHubMutation(tool="x", params={}, safe=False)],
        )
        result = layer.validate(evidence)
        failed_names = [r.split(":")[0] for r in result.reasons]
        assert "confidence_threshold" in failed_names
        assert "entity_exists" in failed_names
        assert "action_safety" in failed_names
