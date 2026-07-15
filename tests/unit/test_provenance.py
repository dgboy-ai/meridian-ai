"""Tests for Agent Provenance Tracking — context sources for every LLM call."""
import pytest
from backend.provenance_tracker import (
    ProvenanceTracker,
    ProvenanceRecord,
    WorkerProvenance,
    InvestigationProvenance,
    ContextSource,
)


class TestContextSource:
    def test_all_sources_defined(self):
        sources = [
            "datahub_metadata", "datahub_lineage", "datahub_document",
            "datahub_playbook", "schema_diff", "statistical_computation",
            "llm_inference", "user_input", "hardcoded_config",
        ]
        for s in sources:
            assert ContextSource(s) is not None

    def test_source_count(self):
        assert len(ContextSource) == 9


class TestProvenanceRecord:
    def test_to_dict_fields(self):
        rec = ProvenanceRecord(
            source_id="w1-0",
            source_type=ContextSource.DATAHUB_METADATA,
            source_urn="urn:li:dataset:test",
            source_name="test_dataset",
            confidence=0.95,
            verified=True,
        )
        d = rec.to_dict()
        assert d["source_id"] == "w1-0"
        assert d["source_type"] == "datahub_metadata"
        assert d["source_urn"] == "urn:li:dataset:test"
        assert d["confidence"] == 0.95
        assert d["verified"] is True

    def test_defaults(self):
        rec = ProvenanceRecord(source_id="x", source_type=ContextSource.USER_INPUT)
        assert rec.source_urn == ""
        assert rec.confidence == 1.0
        assert rec.verified is True
        assert rec.metadata == {}


class TestWorkerProvenance:
    def test_to_dict_fields(self):
        wp = WorkerProvenance(worker_id="root_cause")
        d = wp.to_dict()
        assert d["worker_id"] == "root_cause"
        assert d["context_sources"] == []
        assert d["verified_sources"] == 0
        assert d["source_count"] == 0


class TestInvestigationProvenance:
    def test_to_dict_fields(self):
        ip = InvestigationProvenance(incident_id="42")
        d = ip.to_dict()
        assert d["incident_id"] == "42"
        assert "provenance_score" in d

    def test_calculate_provenance_score_no_sources(self):
        ip = InvestigationProvenance(incident_id="42")
        assert ip.calculate_provenance_score() == 1.0

    def test_calculate_provenance_score_all_verified(self):
        ip = InvestigationProvenance(incident_id="42", total_context_sources=5, total_verified=5)
        assert ip.calculate_provenance_score() == 1.0

    def test_calculate_provenance_score_half_verified(self):
        ip = InvestigationProvenance(incident_id="42", total_context_sources=4, total_verified=2)
        assert ip.calculate_provenance_score() == 0.5

    def test_calculate_provenance_score_none_verified(self):
        ip = InvestigationProvenance(incident_id="42", total_context_sources=3, total_verified=0)
        assert ip.calculate_provenance_score() == 0.0


class TestProvenanceTracker:
    def test_init(self):
        tracker = ProvenanceTracker()
        assert len(tracker._investigations) == 0

    def test_start_investigation(self):
        tracker = ProvenanceTracker()
        prov = tracker.start_investigation("42")
        assert prov.incident_id == "42"
        assert prov.start_time > 0
        assert "42" in tracker._investigations

    def test_record_context_source(self):
        tracker = ProvenanceTracker()
        tracker.start_investigation("42")
        record = tracker.record_context_source(
            "42", "root_cause", ContextSource.DATAHUB_METADATA,
            source_urn="urn:li:dataset:test", source_name="test_ds",
        )
        assert record.source_type == ContextSource.DATAHUB_METADATA
        assert record.source_urn == "urn:li:dataset:test"

    def test_record_context_source_unknown_investigation(self):
        tracker = ProvenanceTracker()
        record = tracker.record_context_source(
            "unknown", "w1", ContextSource.USER_INPUT,
        )
        assert record.source_id == ""

    def test_record_context_source_accumulates(self):
        tracker = ProvenanceTracker()
        tracker.start_investigation("42")
        tracker.record_context_source("42", "w1", ContextSource.DATAHUB_METADATA)
        tracker.record_context_source("42", "w1", ContextSource.DATAHUB_LINEAGE)
        prov = tracker.get_investigation_provenance("42")
        assert prov.total_context_sources == 2
        assert prov.total_verified == 2

    def test_record_context_source_unverified(self):
        tracker = ProvenanceTracker()
        tracker.start_investigation("42")
        tracker.record_context_source(
            "42", "w1", ContextSource.LLM_INFERENCE, verified=False,
        )
        prov = tracker.get_investigation_provenance("42")
        assert prov.total_unverified == 1
        assert prov.total_verified == 0

    def test_record_llm_call(self):
        tracker = ProvenanceTracker()
        tracker.start_investigation("42")
        tracker.record_llm_call(
            "42", "w1", "llama-3.3-70b-versatile",
            context_sources_used=["w1-0", "w1-1"],
            tokens_in=100, tokens_out=50, confidence=0.9,
        )
        prov = tracker.get_investigation_provenance("42")
        wp = prov.worker_provenances["w1"]
        assert len(wp.llm_calls) == 1
        assert wp.llm_calls[0]["model"] == "llama-3.3-70b-versatile"

    def test_record_llm_call_unknown_investigation(self):
        tracker = ProvenanceTracker()
        # Should not raise
        tracker.record_llm_call("unknown", "w1", "model", [])

    def test_get_investigation_provenance(self):
        tracker = ProvenanceTracker()
        tracker.start_investigation("42")
        prov = tracker.get_investigation_provenance("42")
        assert prov is not None
        assert prov.incident_id == "42"

    def test_get_investigation_provenance_not_found(self):
        tracker = ProvenanceTracker()
        assert tracker.get_investigation_provenance("999") is None

    def test_calculate_worker_confidence_no_sources(self):
        tracker = ProvenanceTracker()
        tracker.start_investigation("42")
        assert tracker.calculate_worker_confidence("42", "w1") == 1.0

    def test_calculate_worker_confidence_verified(self):
        tracker = ProvenanceTracker()
        tracker.start_investigation("42")
        tracker.record_context_source(
            "42", "w1", ContextSource.DATAHUB_METADATA, confidence=0.9, verified=True,
        )
        tracker.record_context_source(
            "42", "w1", ContextSource.DATAHUB_LINEAGE, confidence=0.8, verified=True,
        )
        conf = tracker.calculate_worker_confidence("42", "w1")
        assert conf == pytest.approx(0.85, abs=0.01)

    def test_calculate_worker_confidence_unverified_penalty(self):
        tracker = ProvenanceTracker()
        tracker.start_investigation("42")
        tracker.record_context_source(
            "42", "w1", ContextSource.LLM_INFERENCE, confidence=1.0, verified=False,
        )
        conf = tracker.calculate_worker_confidence("42", "w1")
        assert conf == 0.5  # unverified gets 0.5 weight

    def test_get_unverified_sources(self):
        tracker = ProvenanceTracker()
        tracker.start_investigation("42")
        tracker.record_context_source(
            "42", "w1", ContextSource.LLM_INFERENCE, verified=False,
        )
        tracker.record_context_source(
            "42", "w1", ContextSource.DATAHUB_METADATA, verified=True,
        )
        unverified = tracker.get_unverified_sources("42")
        assert len(unverified) == 1
        assert unverified[0]["worker_id"] == "w1"

    def test_get_unverified_sources_empty(self):
        tracker = ProvenanceTracker()
        assert tracker.get_unverified_sources("42") == []

    def test_get_summary(self):
        tracker = ProvenanceTracker()
        tracker.start_investigation("42")
        tracker.record_context_source("42", "w1", ContextSource.DATAHUB_METADATA)
        tracker.record_context_source("42", "w1", ContextSource.DATAHUB_LINEAGE, verified=False)
        summary = tracker.get_summary("42")
        assert summary["incident_id"] == "42"
        assert summary["total_sources"] == 2
        assert summary["verified"] == 1
        assert summary["unverified"] == 1
        assert summary["provenance_score"] == 0.5
        assert "workers" in summary

    def test_get_summary_not_found(self):
        tracker = ProvenanceTracker()
        summary = tracker.get_summary("999")
        assert summary["no_data"] is True

    def test_worker_auto_created_on_llm_call(self):
        tracker = ProvenanceTracker()
        tracker.start_investigation("42")
        tracker.record_llm_call("42", "new_worker", "model", [])
        prov = tracker.get_investigation_provenance("42")
        assert "new_worker" in prov.worker_provenances
