"""E2E tests: Different investigation scenarios and edge cases."""
import pytest
import asyncio
from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.workers.planner import PlannerAgent
from backend.workers.data_sentinel import DataSentinel
from backend.workers.feature_drift import FeatureDrift
from backend.workers.root_cause import RootCause
from backend.workers.knowledge_writer import KnowledgeWriter
from backend.workers.lifecycle_governance import LifecycleGovernance
from backend.reflexion import ReflexionLoop
from backend.health_score import HealthScoreCalculator
from backend.models import Severity


@pytest.fixture
def mcp():
    return DataHubMCPClient(mock=True)


@pytest.fixture
def groq():
    return GroqClient(mock=True)


@pytest.fixture
def planner(mcp, groq):
    return PlannerAgent(mcp=mcp, groq=groq)


class TestInvestigationScenarios:
    @pytest.mark.asyncio
    async def test_investigation_with_high_severity(self, planner):
        """High severity incident triggers all workers."""
        events = []
        async for event in planner.investigate(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            incident_id="SCENARIO-HIGH",
        ):
            events.append(event)

        # Verify all workers fired
        worker_steps = ["data_sentinel", "feature_drift", "root_cause", "knowledge_writer", "lifecycle_governance"]
        fired = [e.get("step") for e in events if e.get("status") == "completed"]
        for worker in worker_steps:
            assert worker in fired, f"Worker {worker} did not fire"

    @pytest.mark.asyncio
    async def test_investigation_returns_confidence_scores(self, planner):
        """Every evidence object has a confidence score."""
        events = []
        async for event in planner.investigate(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            incident_id="SCENARIO-CONF",
        ):
            events.append(event)

        for e in events:
            if "evidence" in e and e["evidence"]:
                assert "confidence" in e["evidence"]
                assert 0 <= e["evidence"]["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_investigation_returns_timestamps(self, planner):
        """Every event has a timestamp."""
        events = []
        async for event in planner.investigate(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            incident_id="SCENARIO-TIME",
        ):
            events.append(event)

        for e in events:
            assert "timestamp" in e
            assert len(e["timestamp"]) > 0

    @pytest.mark.asyncio
    async def test_investigation_summary_has_workers_fired(self, planner):
        """Summary contains list of workers that fired."""
        events = []
        async for event in planner.investigate(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            incident_id="SCENARIO-SUMMARY",
        ):
            events.append(event)

        last = events[-1]
        assert "summary" in last
        assert "workers_fired" in last["summary"]
        assert len(last["summary"]["workers_fired"]) >= 4

    @pytest.mark.asyncio
    async def test_investigation_increments_incident_id(self, planner):
        """Different incident IDs work correctly."""
        for inc_id in ["INC-1", "INC-2", "INC-3"]:
            events = []
            async for event in planner.investigate(
                "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
                incident_id=inc_id,
            ):
                events.append(event)
            last = events[-1]
            assert last["summary"]["incident_id"] == inc_id


class TestDataSentinelScenarios:
    @pytest.mark.asyncio
    async def test_sentinel_detects_schema_change(self, mcp, groq):
        """Data Sentinel detects schema changes."""
        sentinel = DataSentinel(mcp=mcp, groq=groq)
        evidence = await sentinel.detect(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)"
        )
        assert evidence.worker_id == "data_sentinel"
        assert evidence.confidence > 0.5
        assert evidence.severity in [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]

    @pytest.mark.asyncio
    async def test_sentinel_has_lineage_data(self, mcp, groq):
        """Data Sentinel retrieves lineage information."""
        sentinel = DataSentinel(mcp=mcp, groq=groq)
        evidence = await sentinel.detect(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)"
        )
        # Should have evidence items with lineage info
        assert len(evidence.evidence) > 0

    @pytest.mark.asyncio
    async def test_sentinel_pii_scan(self, mcp, groq):
        """Data Sentinel scans for PII."""
        sentinel = DataSentinel(mcp=mcp, groq=groq)
        violation = await sentinel.scan_for_pii(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)"
        )
        assert violation is not None
        assert violation.total_violations > 0
        assert any(f.pattern_name == "email_address" for f in violation.findings)


class TestRootCauseScenarios:
    @pytest.mark.asyncio
    async def test_root_cause_traverses_lineage(self, mcp, groq):
        """Root Cause traverses the full lineage graph."""
        worker = RootCause(mcp=mcp, groq=groq)
        evidence = await worker.analyze(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            [
                "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
                "urn:li:mlModel:(urn:li:dataPlatform:mlflow,ltv_model_v2,PROD)",
            ],
        )
        assert evidence.worker_id == "root_cause"
        assert evidence.confidence > 0.5
        assert evidence.business_impact is not None

    @pytest.mark.asyncio
    async def test_root_cause_multiple_models(self, mcp, groq):
        """Root Cause handles multiple affected models."""
        worker = RootCause(mcp=mcp, groq=groq)
        models = [
            "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
            "urn:li:mlModel:(urn:li:dataPlatform:mlflow,ltv_model_v2,PROD)",
            "urn:li:mlModel:(urn:li:dataPlatform:mlflow,segment_model_v1,PROD)",
        ]
        evidence = await worker.analyze(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            models,
        )
        assert evidence.confidence > 0


class TestKnowledgeWriterScenarios:
    @pytest.mark.asyncio
    async def test_knowledge_writer_creates_documents(self, mcp, groq):
        """Knowledge Writer creates root cause reports."""
        from backend.models import EvidenceObject
        worker = KnowledgeWriter(mcp=mcp, groq=groq)
        root_cause = EvidenceObject(
            worker_id="root_cause",
            timestamp="2026-01-01T00:00:00Z",
            finding="Test root cause",
            confidence=0.95,
            severity=Severity.HIGH,
        )
        evidence = await worker.write(
            "99",
            root_cause,
            ["urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"],
        )
        assert evidence.worker_id == "knowledge_writer"
        # Should have created documents
        assert len(mcp._documents) > 0

    @pytest.mark.asyncio
    async def test_knowledge_writer_updates_model_properties(self, mcp, groq):
        """Knowledge Writer updates model entity properties."""
        from backend.models import EvidenceObject
        worker = KnowledgeWriter(mcp=mcp, groq=groq)
        root_cause = EvidenceObject(
            worker_id="root_cause",
            timestamp="2026-01-01T00:00:00Z",
            finding="Test",
            confidence=0.95,
            severity=Severity.HIGH,
        )
        model_urn = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"
        await worker.write("99", root_cause, [model_urn])
        # Verify properties were updated
        entities = await mcp.get_entities([model_urn])
        assert entities[0].get("ai_health_score") == 81

    @pytest.mark.asyncio
    async def test_knowledge_writer_tags_assets(self, mcp, groq):
        """Knowledge Writer tags affected assets."""
        from backend.models import EvidenceObject
        worker = KnowledgeWriter(mcp=mcp, groq=groq)
        root_cause = EvidenceObject(
            worker_id="root_cause",
            timestamp="2026-01-01T00:00:00Z",
            finding="Test",
            confidence=0.95,
            severity=Severity.HIGH,
        )
        model_urn = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"
        await worker.write("99", root_cause, [model_urn])
        entities = await mcp.get_entities([model_urn])
        assert "at-risk" in entities[0].get("tags", [])


class TestLifecycleGovernanceScenarios:
    @pytest.mark.asyncio
    async def test_lifecycle_proposes_deprecated(self, mcp, groq):
        """Lifecycle governance proposes DEPRECATED for failing models."""
        worker = LifecycleGovernance(mcp=mcp, groq=groq)
        evidence = await worker.evaluate(
            model_urn="urn:li:mlModel:test",
            model_name="failing_model",
            health_score=40,
            consecutive_failures=5,
            pattern_id="test-pattern",
            incident_id="99",
        )
        assert evidence.severity == Severity.HIGH
        assert len(evidence.datahub_mutations) == 1
        assert evidence.datahub_mutations[0].tool == "propose_lifecycle_stage"

    @pytest.mark.asyncio
    async def test_lifecycle_no_propose_when_healthy(self, mcp, groq):
        """Lifecycle governance does NOT propose when model is healthy."""
        worker = LifecycleGovernance(mcp=mcp, groq=groq)
        evidence = await worker.evaluate(
            model_urn="urn:li:mlModel:test",
            model_name="healthy_model",
            health_score=85,
            consecutive_failures=1,
            pattern_id="test-pattern",
            incident_id="99",
        )
        assert evidence.severity == Severity.LOW
        assert len(evidence.datahub_mutations) == 0


class TestReflexionScenarios:
    @pytest.mark.asyncio
    async def test_reflexion_creates_playbook(self, mcp, groq):
        """Reflexion loop creates a new playbook."""
        reflexion = ReflexionLoop(mcp=mcp, groq=groq)
        result = await reflexion.run(
            incident_id="42",
            pattern_id="schema-change",
            root_cause="Schema type change",
            resolution="Rollback model",
            resolution_time_minutes=3,
            affected_model_urn="urn:li:mlModel:test",
        )
        assert result.new_playbook is not None
        assert len(result.new_playbook) > 0
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_reflexion_improves_over_time(self, mcp, groq):
        """Reflexion shows improvement in resolution time."""
        reflexion = ReflexionLoop(mcp=mcp, groq=groq)
        # First incident - slow
        result1 = await reflexion.run(
            incident_id="1",
            pattern_id="schema-change",
            root_cause="Schema type change",
            resolution="Rollback",
            resolution_time_minutes=18,
            affected_model_urn="urn:li:mlModel:test",
        )
        # Second incident - faster
        result2 = await reflexion.run(
            incident_id="2",
            pattern_id="schema-change",
            root_cause="Schema type change",
            resolution="Rollback",
            resolution_time_minutes=3,
            affected_model_urn="urn:li:mlModel:test",
        )
        assert result2.resolution_time_after < result1.resolution_time_after


class TestHealthScoreScenarios:
    def test_health_score_perfect(self):
        """Perfect metrics yield score 100."""
        calc = HealthScoreCalculator()
        score = calc.calculate(
            model_urn="test", model_name="test",
            metrics={
                "Data Quality": 1.0,
                "Drift Magnitude": 1.0,
                "Prediction Quality": 1.0,
                "Latency": 1.0,
                "Cost": 1.0,
                "Fairness": 1.0,
            },
            worker_confidences=[0.95, 0.92, 0.98],
        )
        assert score.score == 100
        assert score.assessment.value == "reliable"

    def test_health_score_zero(self):
        """Zero metrics yield score 0."""
        calc = HealthScoreCalculator()
        score = calc.calculate(
            model_urn="test", model_name="test",
            metrics={
                "Data Quality": 0.0,
                "Drift Magnitude": 0.0,
                "Prediction Quality": 0.0,
                "Latency": 0.0,
                "Cost": 0.0,
                "Fairness": 0.0,
            },
        )
        assert score.score == 0

    def test_health_score_unreliable_with_low_confidence(self):
        """Low worker confidence flags assessment as unreliable."""
        calc = HealthScoreCalculator()
        score = calc.calculate(
            model_urn="test", model_name="test",
            metrics={"Data Quality": 0.8},
            worker_confidences=[0.9, 0.5, 0.9],
        )
        assert score.assessment.value == "unreliable"

    def test_health_score_incomplete_with_few_workers(self):
        """Fewer than 3 workers flags assessment as incomplete."""
        calc = HealthScoreCalculator()
        score = calc.calculate(
            model_urn="test", model_name="test",
            metrics={"Data Quality": 0.8},
            worker_confidences=[0.9, 0.8],
        )
        assert score.assessment.value == "incomplete"