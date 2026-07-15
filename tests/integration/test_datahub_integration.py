"""Integration tests — test full pipeline against real/mock DataHub."""
import pytest
import asyncio
import os
from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.workers.planner import PlannerAgent
from backend.workers.data_sentinel import DataSentinel
from backend.workers.lifecycle_governance import LifecycleGovernance
from backend.scanners.pii_scanner import PIIScanner


@pytest.fixture
def mcp():
    return DataHubMCPClient(mock=True)


@pytest.fixture
def groq():
    return GroqClient(mock=True)


@pytest.fixture
def planner(mcp, groq):
    return PlannerAgent(mcp=mcp, groq=groq)


class TestDataHubIntegration:
    """Test full DataHub integration pipeline."""

    @pytest.mark.asyncio
    async def test_full_investigation_pipeline(self, planner):
        """Test complete investigation: detect → diagnose → validate → write-back."""
        events = []
        async for event in planner.investigate(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            incident_id="TEST-001"
        ):
            events.append(event)

        # Verify all workers fired
        steps = [e.get("step") for e in events]
        assert "data_sentinel" in steps
        assert "feature_drift" in steps
        assert "root_cause" in steps
        assert "validation" in steps
        assert "knowledge_writer" in steps
        assert "lifecycle_governance" in steps

        # Verify completion
        assert events[-1].get("status") == "completed"

    @pytest.mark.asyncio
    async def test_datahub_entity_operations(self, mcp):
        """Test DataHub entity CRUD operations."""
        # Read
        entities = await mcp.get_entities([
            "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"
        ])
        assert len(entities) == 1
        assert entities[0]["name"] == "churn_model_v3"

        # Write
        await mcp.add_structured_properties(
            entity_urn="urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
            properties={"test_key": "test_value"}
        )
        entities = await mcp.get_entities([
            "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"
        ])
        assert entities[0].get("test_key") == "test_value"

    @pytest.mark.asyncio
    async def test_datahub_lineage_traversal(self, mcp):
        """Test lineage graph traversal."""
        lineage = await mcp.get_lineage(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            depth=5
        )
        assert "downstream" in lineage
        assert len(lineage["downstream"]) > 0

    @pytest.mark.asyncio
    async def test_datahub_document_operations(self, mcp):
        """Test Knowledge Base document operations."""
        # Write
        doc = await mcp.save_document(
            title="Test Document",
            content="Test content",
            tags=["test"],
            linked_entities=["urn:li:mlModel:test"]
        )
        assert doc["title"] == "Test Document"

        # Search
        docs = await mcp.search_documents(query="Test")
        assert len(docs) > 0

    @pytest.mark.asyncio
    async def test_datahub_incident_lifecycle(self, mcp):
        """Test incident create → update → resolve lifecycle."""
        # Create
        incident = await mcp.raise_incident(
            type_="TEST_INCIDENT",
            severity="MEDIUM",
            description="Test incident"
        )
        assert "id" in incident

        # Update
        updated = await mcp.update_incident_status(incident["id"], "RESOLVED")
        assert updated["status"] == "RESOLVED"

    @pytest.mark.asyncio
    async def test_datahub_tag_operations(self, mcp):
        """Test batch tagging."""
        await mcp.batch_add_tags(
            urns=[
                "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
                "urn:li:mlModel:(urn:li:dataPlatform:mlflow,ltv_model_v2,PROD)",
            ],
            tags=["integration-test"]
        )
        entities = await mcp.get_entities([
            "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"
        ])
        assert "integration-test" in entities[0].get("tags", [])


class TestPIIScannerIntegration:
    """Test PII scanner with real data patterns."""

    def test_scan_mixed_pii_record(self):
        """Test scanning a record with multiple PII types."""
        scanner = PIIScanner()
        record = {
            "user_id": "U001",
            "email": "john.doe@company.com",
            "ip_address": "192.168.1.100",
            "phone": "+1-555-123-4567",
            "ssn": "123-45-6789",
        }
        findings = scanner.scan_dict(record)
        assert len(findings) >= 4  # email, ip, phone, ssn

    def test_scan_clean_record(self):
        """Test scanning a record with no PII."""
        scanner = PIIScanner()
        record = {
            "product_id": "P123",
            "name": "Widget",
            "price": "29.99",
            "category": "electronics",
        }
        findings = scanner.scan_dict(record)
        assert len(findings) == 0

    def test_compliance_report_generation(self):
        """Test full compliance report generation."""
        scanner = PIIScanner()
        records = [
            {"email": "a@test.com", "ssn": "111-22-3333"},
            {"email": "b@test.com", "ip": "10.0.0.1"},
        ]
        violation = scanner.scan_records(records)
        assert violation.total_violations > 0
        report = violation.to_markdown()
        assert "GDPR" in report or "CCPA" in report
