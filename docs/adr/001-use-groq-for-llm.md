# ADR 001: Use Groq as LLM Provider

**Status:** Accepted
**Date:** 2026-07-14

## Context

Meridian AI needs an LLM for root cause analysis, schema diff explanation, playbook generation, and evidence summarization. The LLM must be fast enough for real-time SSE streaming during investigations.

## Decision

Use Groq Cloud as the primary LLM provider with model fallback.

## Rationale

- **Latency**: Groq's inference speed (~50-150ms TTFB) enables real-time SSE streaming without buffering
- **Cost**: Free tier available for development; pay-per-token pricing for production
- **Model quality**: Access to llama-3.3-70b-versatile and other open models via Groq API
- **Simplicity**: OpenAI-compatible SDK (`groq` Python package), drop-in replacement
- **Rate limits handled by client**: The `GroqClient` implements circuit breaker + model fallback chain

## Consequences

- **Positive**: Real-time investigation streaming, fast development iteration, low barrier to entry
- **Negative**: Vendor lock-in to Groq's API (mitigated by OpenAI-compatible interface)
- **Risk**: Rate limits on free tier; mitigated by fallback chain: `openai/gpt-oss-120b` → `qwen/qwen3.6-27b` → `llama-3.3-70b-versatile`
- **Fallback**: If all Groq models fail, the client returns deterministic mock responses based on prompt keywords

## Configuration

```bash
GROQ_API_KEY=your-key        # Required for live mode
# Without key, falls back to mock mode automatically
```
