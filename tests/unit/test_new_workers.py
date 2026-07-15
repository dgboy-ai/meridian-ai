"""Tests for new workers: Skew Detective, EU AI Act, Data Leakage, dbt Generator, Shadow AI, Contract Enforcer."""
import pytest
from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.workers.training_serving_skew import TrainingServingSkewDetective
from backend.workers.eu_ai_act_compliance import EUAIActComplianceEngine, AuditRecord
from backend.workers.data_leakage_detector import DataLeakageDetector
from backend.workers.dbt_code_generator import DbtCodeGenerator
from backend.workers.shadow_ai_discovery import ShadowAIDiscovery
from backend.workers.contract_enforcer import ContractEnforcer
from backend.models import Severity


@pytest.fixture
def mcp():
    return DataHubMCPClient(mock=True)


@pytest.fixture
def groq():
    return GroqClient(mock=True)


# ── Training-Serving Skew Detective ────────────────────────────────────────────


class TestTrainingServingSkew:
    @pytest.mark.asyncio
    async def test_detect_returns_evidence(self, mcp, groq):
        worker = TrainingServingSkewDetective(mcp=mcp, groq=groq)
        evidence = await worker.detect(
            "urn:li:dataset:(urn:li:dataPlatform:feast,meridian.feature_store,PROD)",
            "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
        )
        assert evidence.worker_id == "training_serving_skew"
        assert evidence.confidence > 0

    @pytest.mark.asyncio
    async def test_detect_has_severity(self, mcp, groq):
        worker = TrainingServingSkewDetective(mcp=mcp, groq=groq)
        evidence = await worker.detect(
            "urn:li:dataset:(urn:li:dataPlatform:feast,meridian.feature_store,PROD)",
            "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
        )
        assert evidence.severity in [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]

    @pytest.mark.asyncio
    async def test_detect_has_mutations(self, mcp, groq):
        worker = TrainingServingSkewDetective(mcp=mcp, groq=groq)
        evidence = await worker.detect(
            "urn:li:dataset:(urn:li:dataPlatform:feast,meridian.feature_store,PROD)",
            "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
        )
        assert len(evidence.datahub_mutations) > 0


# ── EU AI Act Compliance Engine ────────────────────────────────────────────────


class TestEUAIActCompliance:
    @pytest.mark.asyncio
    async def test_record_decision(self, mcp, groq):
        engine = EUAIActComplianceEngine(mcp=mcp, groq=groq)
        record = await engine.record_decision(
            article="12",
            decision_type="test_decision",
            input_summary="test input",
            output_summary="test output",
            confidence=0.95,
        )
        assert record.record_id.startswith("AI-AUDIT-")
        assert record.hash_sha256 != ""
        assert engine.chain_length == 1

    @pytest.mark.asyncio
    async def test_chain_integrity(self, mcp, groq):
        engine = EUAIActComplianceEngine(mcp=mcp, groq=groq)
        await engine.record_decision(article="12", decision_type="d1", input_summary="i1", output_summary="o1", confidence=0.9)
        await engine.record_decision(article="13", decision_type="d2", input_summary="i2", output_summary="o2", confidence=0.85)
        assert engine._verify_chain()
        assert engine.chain_length == 2

    @pytest.mark.asyncio
    async def test_generate_technical_file(self, mcp, groq):
        from backend.models import EvidenceObject, Severity as Sev
        engine = EUAIActComplianceEngine(mcp=mcp, groq=groq)
        evidence_obj = EvidenceObject(
            worker_id="root_cause",
            timestamp="2026-07-12T00:00:00Z",
            finding="Test root cause",
            confidence=0.95,
            severity=Sev.HIGH,
        )
        evidence = await engine.generate_technical_file(
            incident_id="TEST-123",
            model_urns=["urn:li:mlModel:test"],
            root_cause_evidence=evidence_obj,
        )
        assert evidence.worker_id == "eu_ai_act_compliance"
        assert evidence.confidence > 0.9
        assert engine.chain_length == 3  # 3 records from root_cause_evidence

    @pytest.mark.asyncio
    async def test_audit_records_filtered(self, mcp, groq):
        engine = EUAIActComplianceEngine(mcp=mcp, groq=groq)
        await engine.record_decision(article="12", decision_type="d1", input_summary="i", output_summary="o", confidence=0.9, incident_id="42")
        await engine.record_decision(article="13", decision_type="d2", input_summary="i", output_summary="o", confidence=0.9, incident_id="99")
        records_42 = engine.get_audit_records("42")
        assert len(records_42) == 1
        assert records_42[0]["record_id"].startswith("AI-AUDIT-42")


# ── Data Leakage Detector ─────────────────────────────────────────────────────


class TestDataLeakageDetector:
    @pytest.mark.asyncio
    async def test_detect_returns_evidence(self, mcp, groq):
        worker = DataLeakageDetector(mcp=mcp, groq=groq)
        evidence = await worker.detect(
            "urn:li:dataset:(urn:li:dataPlatform:feast,meridian.feature_store,PROD)",
            "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
        )
        assert evidence.worker_id == "data_leakage_detector"
        assert evidence.confidence > 0

    @pytest.mark.asyncio
    async def test_detect_has_severity(self, mcp, groq):
        worker = DataLeakageDetector(mcp=mcp, groq=groq)
        evidence = await worker.detect(
            "urn:li:dataset:(urn:li:dataPlatform:feast,meridian.feature_store,PROD)",
            "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
        )
        assert evidence.severity in [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]


# ── dbt Code Generator ────────────────────────────────────────────────────────


class TestDbtCodeGenerator:
    @pytest.mark.asyncio
    async def test_generate_returns_evidence(self, mcp, groq):
        worker = DbtCodeGenerator(mcp=mcp, groq=groq)
        evidence = await worker.generate(
            source_dataset_urn="urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            target_model_name="stg_raw_events",
        )
        assert evidence.worker_id == "dbt_code_generator"
        assert evidence.confidence > 0

    @pytest.mark.asyncio
    async def test_generate_has_mutations(self, mcp, groq):
        worker = DbtCodeGenerator(mcp=mcp, groq=groq)
        evidence = await worker.generate(
            source_dataset_urn="urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            target_model_name="stg_raw_events",
        )
        assert len(evidence.datahub_mutations) > 0


# ── Shadow AI Discovery ───────────────────────────────────────────────────────


class TestShadowAIDiscovery:
    @pytest.mark.asyncio
    async def test_discover_returns_evidence(self, mcp, groq):
        worker = ShadowAIDiscovery(mcp=mcp, groq=groq)
        evidence = await worker.discover()
        assert evidence.worker_id == "shadow_ai_discovery"
        assert evidence.confidence > 0

    @pytest.mark.asyncio
    async def test_discover_has_severity(self, mcp, groq):
        worker = ShadowAIDiscovery(mcp=mcp, groq=groq)
        evidence = await worker.discover()
        assert evidence.severity in [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]


# ── Contract Enforcer ─────────────────────────────────────────────────────────


class TestContractEnforcer:
    @pytest.mark.asyncio
    async def test_enforce_ok_when_compliant(self, mcp, groq):
        worker = ContractEnforcer(mcp=mcp, groq=groq)
        evidence = await worker.enforce(
            dataset_urn="urn:li:dataset:test",
            dataset_name="test_dataset",
            failed_assertions=0,
            total_assertions=5,
            consecutive_failures=0,
        )
        assert evidence.worker_id == "contract_enforcer"
        assert evidence.severity == Severity.LOW
        assert len(evidence.datahub_mutations) == 0

    @pytest.mark.asyncio
    async def test_enforce_quarantine_on_high_failure_rate(self, mcp, groq):
        worker = ContractEnforcer(mcp=mcp, groq=groq)
        evidence = await worker.enforce(
            dataset_urn="urn:li:dataset:test",
            dataset_name="test_dataset",
            failed_assertions=4,
            total_assertions=5,
            consecutive_failures=2,
        )
        assert evidence.severity == Severity.HIGH
        assert len(evidence.datahub_mutations) > 0

    @pytest.mark.asyncio
    async def test_enforce_quarantine_on_consecutive_failures(self, mcp, groq):
        worker = ContractEnforcer(mcp=mcp, groq=groq)
        evidence = await worker.enforce(
            dataset_urn="urn:li:dataset:test",
            dataset_name="test_dataset",
            failed_assertions=1,
            total_assertions=5,
            consecutive_failures=3,
        )
        assert evidence.severity == Severity.HIGH
        assert len(evidence.datahub_mutations) > 0

    @pytest.mark.asyncio
    async def test_enforce_no_duplicate_proposals(self, mcp, groq):
        worker = ContractEnforcer(mcp=mcp, groq=groq)
        # First call should propose quarantine
        e1 = await worker.enforce(
            dataset_urn="urn:li:dataset:dup",
            dataset_name="dup_dataset",
            failed_assertions=5,
            total_assertions=5,
            consecutive_failures=5,
        )
        assert e1.severity == Severity.HIGH
        # Manually add proposal to MCP to simulate pending state
        await mcp.propose_lifecycle_stage(
            entity_urn="urn:li:dataset:dup",
            lifecycle_stage="QUARANTINED",
            reason="test",
        )
        # Second call should skip duplicate
        e2 = await worker.enforce(
            dataset_urn="urn:li:dataset:dup",
            dataset_name="dup_dataset",
            failed_assertions=5,
            total_assertions=5,
            consecutive_failures=5,
        )
        assert "already pending" in e2.finding
        assert len(e2.datahub_mutations) == 0
