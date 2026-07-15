# Meridian AI API Reference

Base URL: `http://localhost:8000`

All responses include `X-Request-ID` and `X-Response-Time` headers. Rate limit: 60 req/min (configurable via `MAX_RPM`).

---

## Authentication

Meridian AI supports two auth modes for DataHub GMS:

- **PAT (default)** — Bearer token from `DATAHUB_GMS_TOKEN`
- **Service Account** — set `DATAHUB_AUTH_MODE=service_account`

When `DATAHUB_MOCK=true` (default), no DataHub connection is needed.

Groq LLM calls use `GROQ_API_KEY` from environment. Without it, the client falls back to mock responses.

---

## Health Checks

### `GET /health`
Basic liveness check.

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "healthy",
  "service": "meridian-ai",
  "version": "1.0.0",
  "mode": "mock",
  "groq_connected": true,
  "datahub_mock": true
}
```

### `GET /health/ready`
Readiness probe — checks all subsystems.

```bash
curl http://localhost:8000/health/ready
```

### `GET /health/live`
Simple liveness probe for k8s.

### `GET /metrics`
Prometheus-compatible metrics (p50/p95/p99 latency, error rate, uptime).

```bash
curl http://localhost:8000/metrics
```

---

## Incidents

### `GET /api/incidents`
List all known incidents.

```bash
curl http://localhost:8000/api/incidents
```

### `GET /api/incidents/{incident_id}`
Get a single incident by ID.

```bash
curl http://localhost:8000/api/incidents/42
```

---

## Models

### `GET /api/models/{model_name}`
Get ML model metadata (health score, confidence, tags).

```bash
curl http://localhost:8000/api/models/churn_model_v3
```

### `GET /api/health-scores`
Health scores for all registered models.

```bash
curl http://localhost:8000/api/health-scores
```

---

## Analytics

### `GET /api/resolution-times`
Resolution time trend across incidents.

```bash
curl http://localhost:8000/api/resolution-times
```

---

## Actions Framework

### `POST /api/actions/investigate`
Receive a DataHub Actions Framework event. Triggers investigation for HIGH/CRITICAL severity.

```bash
curl -X POST http://localhost:8000/api/actions/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "UPSTREAM_LINEAGE_CHANGE",
    "entityUrn": "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
    "aspectName": "schemaMetadata"
  }'
```

### `GET /api/actions/events`
List all received events.

### `GET /api/actions/stats`
Event statistics (total, high-severity, investigations triggered).

---

## Compliance

### `POST /api/compliance/scan-pii`
Scan a dataset for PII exposures.

```bash
curl -X POST http://localhost:8000/api/compliance/scan-pii \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_urn": "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)"
  }'
```

### `GET /api/compliance/eu-ai-act/{incident_id}`
Get EU AI Act Technical File for an incident.

### `GET /api/compliance/audit-trail`
Get the full immutable audit trail.

---

## Discovery

### `POST /api/discovery/shadow-ai`
Scan for ungoverned (shadow) ML models.

```bash
curl -X POST http://localhost:8000/api/discovery/shadow-ai
```

---

## Code Generation

### `POST /api/generate/dbt`
Generate a dbt model from DataHub metadata.

```bash
curl -X POST http://localhost:8000/api/generate/dbt \
  -H "Content-Type: application/json" \
  -d '{
    "source_dataset_urn": "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
    "target_model_name": "stg_raw_events"
  }'
```

---

## Streaming (SSE)

### `GET /stream/replay`
Stream a pre-recorded investigation via Server-Sent Events.

```bash
curl "http://localhost:8000/stream/replay?incident_id=42&delay=0.5"
```

### `GET /stream/investigate`
Stream a live or replay investigation.

```bash
curl "http://localhost:8000/stream/investigate?incident_id=42&mode=replay"
```

Parameters:
- `dataset_urn` — URN to investigate (default: `urn:li:dataset:(...snowflake,meridian.raw_events,PROD)`)
- `incident_id` — ID for tracking (default: `42`)
- `mode` — `live` (real DataHub) or `replay` (pre-recorded, default)

---

## Error Responses

| Status | Meaning |
|--------|---------|
| 400 | Invalid request body or parameters |
| 404 | Resource not found |
| 429 | Rate limit exceeded (check `Retry-After` header) |
| 500 | Internal server error |

```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60,
  "request_id": "a1b2c3d4"
}
```
