"""Tests for Groq Client."""
import pytest
from backend.clients.groq_client import GroqClient


class TestGroqClient:
    def test_mock_mode(self):
        client = GroqClient(mock=True)
        assert client.client is None

    def test_complete_mock(self):
        client = GroqClient(mock=True)
        result = client.complete([{"role": "user", "content": "test"}])
        assert isinstance(result, str)
        assert len(result) > 0

    def test_complete_json_mock(self):
        client = GroqClient(mock=True)
        result = client.complete_json([{"role": "user", "content": "test schema"}])
        assert isinstance(result, dict)

    def test_model_fallback(self):
        client = GroqClient(mock=True)
        result = client.complete([{"role": "user", "content": "test"}], model="reasoning")
        assert isinstance(result, str)

    def test_mock_response_patterns(self):
        client = GroqClient(mock=True)
        # Schema detection
        r1 = client.complete_json([{"role": "user", "content": "detect schema"}])
        assert "finding" in r1 or "status" in r1

        # Root cause
        r2 = client.complete_json([{"role": "user", "content": "analyze root cause"}])
        assert "root_cause_explanation" in r2 or "status" in r2

        # Playbook
        r3 = client.complete([{"role": "user", "content": "view playbook"}])
        assert isinstance(r3, str)
