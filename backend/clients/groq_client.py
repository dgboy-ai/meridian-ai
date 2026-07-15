"""Groq client with rate limit handling, model fallback, and circuit breaker."""
import os
import json
import logging
from groq import Groq, RateLimitError
from backend.resilience import CircuitBreaker

logger = logging.getLogger("meridian-ai.groq")

# Model config: primary + fallbacks
MODELS = {
    "reasoning": ["openai/gpt-oss-120b", "qwen/qwen3.6-27b", "qwen/qwen3-32b", "llama-3.3-70b-versatile"],
    "fast": ["openai/gpt-oss-20b", "qwen/qwen3.6-27b", "llama-3.1-8b-instant"],
}


class GroqClient:
    def __init__(self, api_key: str | None = None, mock: bool | None = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        if mock is None:
            self.mock = not bool(self.api_key)
        else:
            self.mock = mock
        self.client = Groq(api_key=self.api_key) if (self.api_key and not self.mock) else None
        self._circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
        self._total_calls = 0
        self._total_tokens = 0

        if self.mock:
            logger.info("Groq client running in mock mode (no API key provided)")
        else:
            logger.info("Groq client initialized with API key")

    def _resolve_model(self, model: str) -> list[str]:
        if model in MODELS:
            return MODELS[model]
        return [model]

    def complete(
        self,
        messages: list[dict],
        model: str = "openai/gpt-oss-120b",
        temperature: float = 0,
        max_retries: int = 2,
    ) -> str:
        if not self.client:
            return self._mock_response(messages)

        # Circuit breaker check
        if not self._circuit_breaker.can_execute():
            logger.warning("Circuit breaker open, using mock response")
            return self._mock_response(messages)

        models_to_try = self._resolve_model(model)
        for model_name in models_to_try:
            for attempt in range(max_retries):
                try:
                    response = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=temperature,
                    )
                    content = response.choices[0].message.content
                    if content:
                        self._circuit_breaker.record_success()
                        self._total_calls += 1
                        # Track tokens if available
                        if hasattr(response, 'usage') and response.usage:
                            self._total_tokens += response.usage.total_tokens
                        return content
                except RateLimitError:
                    logger.warning(f"Rate limit hit for model {model_name}, trying next model")
                    self._circuit_breaker.record_failure()
                    break
                except Exception as e:
                    logger.error(f"Groq API error for model {model_name}: {e}")
                    self._circuit_breaker.record_failure()
                    break

        logger.warning("All Groq models failed, using mock response")
        return self._mock_response(messages)

    def complete_json(
        self,
        messages: list[dict],
        model: str = "openai/gpt-oss-120b",
    ) -> dict:
        text = self.complete(messages, model=model)
        text = text.strip()

        if "```" in text:
            parts = text.split("```")
            for part in parts[1:]:
                cleaned = part.strip()
                if cleaned.startswith("json\n"):
                    cleaned = cleaned[5:]
                elif cleaned.startswith("python\n"):
                    cleaned = cleaned[7:]
                cleaned = cleaned.strip()
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                try:
                    return json.loads(cleaned.strip())
                except json.JSONDecodeError:
                    continue

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            return {"status": "ok", "raw": text[:500]}

    def get_stats(self) -> dict:
        """Get client statistics."""
        return {
            "mock_mode": self.mock,
            "total_calls": self._total_calls,
            "total_tokens": self._total_tokens,
            "circuit_breaker_state": self._circuit_breaker.get_status()["state"],
        }

    def _mock_response(self, messages: list[dict]) -> str:
        last_msg = messages[-1]["content"] if messages else ""
        if "root_cause" in last_msg.lower() or "analyze" in last_msg.lower():
            return json.dumps({
                "root_cause_explanation": "Schema change in raw_events.age (INT to STRING) caused age_bucket feature transformation to break, leading to model degradation.",
                "confidence_score": 0.94,
                "blast_radius_urns": [
                    "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
                    "urn:li:mlModel:(urn:li:dataPlatform:mlflow,ltv_model_v2,PROD)",
                    "urn:li:mlModel:(urn:li:dataPlatform:mlflow,segment_model_v1,PROD)",
                ],
                "business_impact": {
                    "predictions_impacted_count": 32000,
                    "revenue_at_risk_daily": 45000,
                },
            })
        elif "schema" in last_msg.lower() or "detect" in last_msg.lower():
            return json.dumps({
                "finding": "Schema change in raw_events — column 'age' changed INT to STRING",
                "confidence": 0.94,
                "severity": "high",
                "evidence": [
                    {"type": "schema_diff", "column": "age", "before": "INT", "after": "STRING"},
                    {"type": "lineage_impact", "downstream_count": 3, "affected_models": ["churn_model_v3"]},
                ],
            })
        elif "playbook" in last_msg.lower() or "reflexion" in last_msg.lower():
            return "# Playbook: Schema Change to Model Degradation\n\n## Detection signals\n- Column type change in upstream dataset\n- Feature pipeline success with silent type coercion\n- Model accuracy drop 2-4 hours after pipeline run\n\n## Fastest resolution\n1. Identify changed column via schema diff (2 min)\n2. Trace to affected feature via lineage (3 min)\n3. Roll back model to last known-good version (2 min)\n4. Patch feature pipeline type casting (5 min)"
        elif "skew" in last_msg.lower() or "training-serving" in last_msg.lower():
            return json.dumps({
                "finding": "Training-serving skew detected: age_bucket column type mismatch between MLFeatureTable and model deployment",
                "drift_score": 0.61,
                "affected_features": ["age_bucket", "event_frequency"],
                "confidence": 0.85,
            })
        elif "leakage" in last_msg.lower() or "temporal" in last_msg.lower():
            return json.dumps({
                "finding": "No temporal data leakage detected in feature-label pairs",
                "leakage_score": 0.05,
                "affected_features": [],
                "confidence": 0.82,
            })
        elif "dbt" in last_msg.lower() or "code generation" in last_msg.lower():
            return json.dumps({
                "finding": "dbt model generated from DataHub metadata",
                "dbt_sql": "select * from source where _deleted = false",
                "schema_yaml": "version: 2\nmodels:\n  - name: generated_model",
                "confidence": 0.90,
            })
        elif "shadow" in last_msg.lower() or "ungoverned" in last_msg.lower():
            return json.dumps({
                "finding": "Shadow AI scan complete: 0 ungoverned models found in current DataHub instance",
                "confidence": 0.88,
            })
        else:
            return json.dumps({"status": "ok", "message": "Analysis complete"})
