# Meridian AI — API Reference

> REST API endpoints, MCP Server tools, and CLI commands.

## REST API Endpoints

### Health & Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/ready` | Readiness probe (dependencies) |
| GET | `/health/live` | Liveness probe |
| GET | `/metrics` | Prometheus-compatible metrics |

### Incidents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/incidents` | List all incidents |
| GET | `/api/incidents/{id}` | Get incident details |
| POST | `/api/investigate` | Start a live investigation |

### Models

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/models/{name}` | Get model metadata |
| GET | `/api/health-scores` | Get health scores for all models |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/resolution-times` | Get resolution time trends |
| GET | `/api/costs` | Get cost/ROI summary |
| GET | `/api/costs/{incident_id}` | Get investigation cost |
| GET | `/api/provenance/{incident_id}` | Get investigation provenance |

### Actions Framework

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/actions/investigate` | Receive Actions Framework event |
| GET | `/api/actions/events` | Get all received events |
| GET | `/api/actions/stats` | Get Actions Framework statistics |

### Compliance

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/compliance/scan-pii` | Scan dataset for PII |
| GET | `/api/compliance/eu-ai-act/{id}` | Get EU AI Act Technical File |
| GET | `/api/compliance/audit-trail` | Get full audit trail |

### Discovery

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/discovery/shadow-ai` | Scan for ungoverned models |

### Code Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/generate/dbt` | Generate dbt model from metadata |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/system/architecture` | System architecture info |
| GET | `/api/system/health` | Detailed system health |

### SSE Streaming

| Endpoint | Description |
|----------|-------------|
| `/stream/replay?incident_id={id}` | Stream pre-recorded investigation |
| `/stream/investigate?dataset_urn={urn}&mode=live` | Stream live investigation |

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Authenticate, get JWT token |
| POST | `/api/auth/register` | Register new user |
| GET | `/api/auth/me` | Get current user info |

## MCP Server Tools

### Read-Only Tools

| Tool | Description |
|------|-------------|
| `search` | Search DataHub with keyword/boolean logic |
| `get_entities` | Fetch metadata for entities by URN |
| `get_lineage` | Upstream/downstream lineage with hop control |
| `get_lineage_paths_between` | Exact paths between two assets |
| `list_schema_fields` | Column-level metadata |
| `get_dataset_queries` | Real SQL queries referencing a dataset |
| `search_documents` | Search knowledge base articles |

### Mutation Tools

| Tool | Description |
|------|-------------|
| `add_tags` / `remove_tags` | Manage tags on entities |
| `add_terms` / `remove_terms` | Manage glossary terms |
| `add_owners` / `remove_owners` | Manage ownership |
| `set_domains` / `remove_domains` | Manage domain membership |
| `update_description` | Update entity descriptions |
| `add_structured_properties` | Manage typed metadata |
| `save_document` | Save documents to knowledge base |
| `propose_lifecycle_stage` | Submit lifecycle stage proposal |

## CLI Commands

| Command | Description | Example |
|---------|-------------|---------|
| `meridian investigate <urn>` | Run full investigation | `meridian investigate "urn:li:mlModel:..."` |
| `meridian health <urn>` | Check model health | `meridian health "urn:li:mlModel:..."` |
| `meridian playbook <id>` | View reflexion playbook | `meridian playbook schema-change-type-mismatch` |
| `meridian seed` | Seed demo data | `meridian seed` |
| `meridian serve` | Start API server | `meridian serve --port 8000` |

## Response Formats

### Investigation Result

```json
{
  "incident_id": "42",
  "status": "completed",
  "dataset_urn": "urn:li:dataset:...",
  "workers_fired": ["data_sentinel", "feature_drift", ...],
  "resolution_time_minutes": 3.0,
  "health_score": 89,
  "datahub_mutations": 17,
  "timeline_steps": 36,
  "blast_radius_nodes": 3,
  "writeback_artifacts": 5
}
```

### Health Score

```json
{
  "score": 89,
  "assessment": "reliable",
  "confidence": 0.94,
  "metrics": {
    "data_quality": 0.72,
    "drift_magnitude": 0.61,
    "prediction_quality": 0.96,
    "latency": 0.94,
    "cost": 0.85,
    "fairness": 0.88
  }
}
```

### EU AI Act Audit Record

```json
{
  "record_id": "audit-2026-07-12T14:32:00Z",
  "article": "12",
  "decision_type": "ROOT_CAUSE_ANALYSIS",
  "confidence": 0.96,
  "hash_sha256": "a1b2c3d4...",
  "previous_hash": "e5f6g7h8..."
}
```
