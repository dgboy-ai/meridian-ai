"""Tests for DataHub Client."""
import pytest
import asyncio
from backend.clients.datahub_client import DataHubMCPClient


class TestDataHubClient:
    def test_init_mock(self):
        client = DataHubMCPClient(mock=True)
        assert client.mock is True

    @pytest.mark.asyncio
    async def test_get_entities(self):
        client = DataHubMCPClient(mock=True)
        entities = await client.get_entities([
            "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"
        ])
        assert len(entities) == 1
        assert entities[0]["name"] == "churn_model_v3"

    @pytest.mark.asyncio
    async def test_get_lineage(self):
        client = DataHubMCPClient(mock=True)
        lineage = await client.get_lineage(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)"
        )
        assert "downstream" in lineage
        assert len(lineage["downstream"]) > 0

    @pytest.mark.asyncio
    async def test_list_schema_fields(self):
        client = DataHubMCPClient(mock=True)
        fields = await client.list_schema_fields(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)"
        )
        assert len(fields) > 0

    @pytest.mark.asyncio
    async def test_search_documents(self):
        client = DataHubMCPClient(mock=True)
        docs = await client.search_documents(query="playbook")
        assert isinstance(docs, list)

    @pytest.mark.asyncio
    async def test_save_document(self):
        client = DataHubMCPClient(mock=True)
        doc = await client.save_document(
            title="Test Doc",
            content="Test content",
            tags=["test"],
        )
        assert doc["title"] == "Test Doc"

    @pytest.mark.asyncio
    async def test_add_structured_properties(self):
        client = DataHubMCPClient(mock=True)
        result = await client.add_structured_properties(
            entity_urn="urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
            properties={"test_key": "test_value"},
        )
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_batch_add_tags(self):
        client = DataHubMCPClient(mock=True)
        result = await client.batch_add_tags(
            urns=["urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"],
            tags=["test-tag"],
        )
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_raise_incident(self):
        client = DataHubMCPClient(mock=True)
        incident = await client.raise_incident(
            type_="TEST",
            severity="MEDIUM",
            description="Test incident",
        )
        assert "id" in incident

    @pytest.mark.asyncio
    async def test_update_incident_status(self):
        client = DataHubMCPClient(mock=True)
        incident = await client.raise_incident(
            type_="TEST",
            severity="MEDIUM",
            description="Test",
        )
        updated = await client.update_incident_status(incident["id"], "RESOLVED")
        assert updated["status"] == "RESOLVED"

    @pytest.mark.asyncio
    async def test_list_pending_proposals(self):
        client = DataHubMCPClient(mock=True)
        proposals = await client.list_pending_proposals()
        assert isinstance(proposals, list)

    @pytest.mark.asyncio
    async def test_propose_lifecycle_stage(self):
        client = DataHubMCPClient(mock=True)
        result = await client.propose_lifecycle_stage(
            entity_urn="urn:li:mlModel:test",
            lifecycle_stage="DEPRECATED",
            reason="Test",
        )
        assert result["status"] == "ok"
