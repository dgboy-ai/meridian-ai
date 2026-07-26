"""Tests for Data Sentinel worker."""
import pytest
import asyncio
from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.workers.data_sentinel import DataSentinel
from backend.models import Severity


@pytest.fixture
def mcp():
    return DataHubMCPClient(mock=True)


@pytest.fixture
def groq():
    return GroqClient(mock=True)


@pytest.fixture
def sentinel(mcp, groq):
    return DataSentinel(mcp=mcp, groq=groq)


class TestDataSentinel:
    @pytest.mark.asyncio
    async def test_detect_returns_evidence(self, sentinel):
        evidence = await sentinel.detect(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)"
        )
        assert evidence.worker_id == "data_sentinel"
        assert evidence.confidence > 0
        assert evidence.severity in [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]

    @pytest.mark.asyncio
    async def test_detect_has_evidence_items(self, sentinel):
        evidence = await sentinel.detect(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)"
        )
        assert len(evidence.evidence) > 0

    @pytest.mark.asyncio
    async def test_scan_for_pii_returns_violation(self, sentinel):
        sample_data = [
            {"user_id": "U001", "email": "john.doe@example.com", "ip_address": "192.168.1.100"},
            {"user_id": "U002", "email": "jane@company.org", "phone": "+1-555-123-4567"},
        ]
        violation = await sentinel.scan_for_pii(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            sample_data=sample_data,
        )
        assert violation is not None
        assert violation.total_violations > 0

    @pytest.mark.asyncio
    async def test_scan_for_pii_detects_email(self, sentinel):
        sample_data = [
            {"user_id": "U001", "email": "john.doe@example.com", "ip_address": "192.168.1.100"},
        ]
        violation = await sentinel.scan_for_pii(
            "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
            sample_data=sample_data,
        )
        assert any(f.pattern_name == "email_address" for f in violation.findings)
