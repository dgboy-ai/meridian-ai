"""Extended tests for Validation Layer."""
import pytest
from backend.validation import ValidationLayer, CheckResult, ValidationResult
from backend.models import EvidenceObject, Severity, DataHubMutation


class TestValidationLayerExtended:
    def test_all_checks_pass(self):
        v = ValidationLayer(known_entities={"urn:test"})
        e = EvidenceObject(
            worker_id="test",
            timestamp="2026-01-01T00:00:00Z",
            finding="Test",
            confidence=0.95,
            severity=Severity.HIGH,
            evidence=[],
            datahub_mutations=[DataHubMutation(tool="test", params={}, safe=True)],
        )
        result = v.validate(e)
        assert result.approved is True

    def test_low_confidence_rejects(self):
        v = ValidationLayer()
        e = EvidenceObject(
            worker_id="test",
            timestamp="2026-01-01T00:00:00Z",
            finding="Test",
            confidence=0.5,
            severity=Severity.LOW,
        )
        result = v.validate(e)
        assert result.approved is False
        assert any("confidence" in r.lower() for r in result.reasons)

    def test_unsafe_mutation_rejects(self):
        v = ValidationLayer()
        e = EvidenceObject(
            worker_id="test",
            timestamp="2026-01-01T00:00:00Z",
            finding="Test",
            confidence=0.95,
            severity=Severity.HIGH,
            datahub_mutations=[DataHubMutation(tool="delete", params={}, safe=False)],
        )
        result = v.validate(e)
        assert result.approved is False
        assert any("unsafe" in r.lower() for r in result.reasons)

    def test_safe_mutations_filtered(self):
        v = ValidationLayer()
        e = EvidenceObject(
            worker_id="test",
            timestamp="2026-01-01T00:00:00Z",
            finding="Test",
            confidence=0.95,
            severity=Severity.HIGH,
            datahub_mutations=[
                DataHubMutation(tool="safe_op", params={}, safe=True),
                DataHubMutation(tool="unsafe_op", params={}, safe=False),
            ],
        )
        result = v.validate(e)
        assert len(result.safe_mutations) == 1
        assert result.safe_mutations[0].tool == "safe_op"

    def test_empty_mutations_pass(self):
        v = ValidationLayer()
        e = EvidenceObject(
            worker_id="test",
            timestamp="2026-01-01T00:00:00Z",
            finding="Test",
            confidence=0.95,
            severity=Severity.HIGH,
            datahub_mutations=[],
        )
        result = v.validate(e)
        assert result.approved is True
