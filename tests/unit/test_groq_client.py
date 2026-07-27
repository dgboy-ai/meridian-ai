"""Tests for Groq Client."""
import pytest
from backend.clients.groq_client import GroqClient


@pytest.mark.asyncio
class TestGroqClient:
    def test_mock_mode(self):
        client = GroqClient(mock=True)
        assert client.client is None

    async def test_complete_mock(self):
        client = GroqClient(mock=True)
        result = await client.async_complete([{"role": "user", "content": "test"}])
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_complete_json_mock(self):
        client = GroqClient(mock=True)
        result = await client.async_complete_json([{"role": "user", "content": "test schema"}])
        assert isinstance(result, dict)

    async def test_model_fallback(self):
        client = GroqClient(mock=True)
        result = await client.async_complete([{"role": "user", "content": "test"}], model="reasoning")
        assert isinstance(result, str)

    async def test_mock_response_patterns(self):
        client = GroqClient(mock=True)
        # Schema detection
        r1 = await client.async_complete_json([{"role": "user", "content": "detect schema"}])
        assert "finding" in r1 or "status" in r1

        # Root cause
        r2 = await client.async_complete_json([{"role": "user", "content": "analyze root cause"}])
        assert "root_cause_explanation" in r2 or "status" in r2

        # Playbook
        r3 = await client.async_complete([{"role": "user", "content": "view playbook"}])
        assert isinstance(r3, str)
