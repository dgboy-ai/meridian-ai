# Meridian AI — Production Deployment Guide

> **Enterprise-grade deployment for production ML incident investigation.**

## Prerequisites

- DataHub v0.5.0+ (for mutation tools)
- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- Groq API key (or OpenAI-compatible provider)

## Authentication

### Service Accounts (Recommended)

For production deployments, **always use service accounts** instead of personal access tokens (PATs).

**Why service accounts?**
- PATs belong to individual humans — they expire when the employee leaves
- Service accounts belong to systems — they persist and can be audited
- Service accounts support **Default Views** (DataHub v1.0.0+) — scope agent visibility

**Setup:**
1. Create a service account in DataHub (Settings → Users & Groups → Service Accounts)
2. Generate an access token for the service account
3. Configure Meridian AI:
   ```bash
   export DATAHUB_GMS_URL=http://your-datahub:8080/api/gms
   export DATAHUB_GMS_TOKEN=<service-account-token>
   export DATAHUB_AUTH_MODE=service_account
   ```

### Personal Access Tokens (Development Only)

For local development and testing:
```bash
export DATAHUB_GMS_URL=http://localhost:8080/api/gms
export DATAHUB_GMS_TOKEN=your-pat-token
export DATAHUB_AUTH_MODE=pat
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATAHUB_GMS_URL` | Yes | `http://localhost:8080/api/gms` | DataHub GMS endpoint |
| `DATAHUB_GMS_TOKEN` | Yes | — | Authentication token |
| `DATAHUB_AUTH_MODE` | No | `pat` | `pat` or `service_account` |
| `DATAHUB_MOCK` | No | `true` | Set to `false` for real DataHub |
| `GROQ_API_KEY` | No | — | Groq API key (free tier available) |
| `HOST` | No | `0.0.0.0` | Server bind address |
| `PORT` | No | `8000` | Server port |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `MAX_RPM` | No | `60` | Max requests per minute |
| `REQUEST_TIMEOUT` | No | `30` | Request timeout in seconds |

## Deployment Options

### Option 1: Docker Compose (Recommended)

```bash
# Clone and configure
git clone https://github.com/trueboy1123/meridian-ai
cd meridian-ai
cp .env.example .env
# Edit .env with your credentials

# Start all services
docker compose up -d

# Wait for DataHub to initialize (~90 seconds)
# Seed demo data
python scripts/seed_meridian.py

# Access services
# Meridian AI: http://localhost:8000/docs
# DataHub UI: http://localhost:9002
```

### Option 2: Kubernetes (Helm)

```bash
# Add DataHub Helm repo
helm repo add datahub https://helm.datahubproject.io/
helm repo update

# Install DataHub
helm install datahub datahub/datahub

# Install Meridian AI
helm install meridian-ai ./charts/meridian-ai
```

### Option 3: Direct Installation

```bash
# Install dependencies
pip install -e .

# Configure
export DATAHUB_GMS_URL=http://your-datahub:8080/api/gms
export DATAHUB_GMS_TOKEN=your-token
export DATAHUB_AUTH_MODE=service_account

# Start server
python -m backend.main
```

## Security Configuration

### RBAC Integration

Meridian AI respects DataHub's RBAC policies. Configure access controls in DataHub:

1. **Service Account Permissions:**
   - Read: `search`, `get_entities`, `get_lineage`, `list_schema_fields`
   - Write: `addStructuredProperties`, `batchAddTags`, `raiseIncident`

2. **Default Views** (DataHub v1.0.0+):
   - Scope agent visibility to specific domains
   - Limit which entities the agent can read/write

3. **Audit Logging:**
   - All mutations logged to DataHub audit trail
   - EU AI Act SHA-256 chain provides tamper-evident record

### Network Security

- Run Meridian AI in the same VPC as DataHub
- Use private endpoints for DataHub GMS
- Enable TLS for all connections
- Configure firewall rules to restrict access

### Secret Management

- Store tokens in environment variables or secret managers
- Never commit tokens to version control
- Rotate service account tokens regularly
- Use least-privilege permissions

## Monitoring & Observability

### Health Checks

```bash
# Basic health
curl http://localhost:8000/health

# Readiness probe
curl http://localhost:8000/health/ready

# Liveness probe
curl http://localhost:8000/health/live

# Metrics
curl http://localhost:8000/metrics
```

### Key Metrics

| Metric | Description | Alert Threshold |
|---|---|---|
| `request_count` | Total requests | — |
| `error_count` | Total errors | > 1% of requests |
| `avg_latency_ms` | Average latency | > 1000ms |
| `p95_latency_ms` | 95th percentile latency | > 5000ms |
| `error_rate` | Error rate | > 0.05 |

### Logging

```bash
# Set log level
export LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR

# View logs
docker compose logs -f backend-api
```

## Performance Tuning

### Rate Limiting

Default: 60 requests per minute. Adjust via `MAX_RPM`:

```bash
export MAX_RPM=120  # Higher for production
```

### Caching

- Investigation results are cached in-memory
- Playbook retrieval uses keyword search (upgrade to semantic search for v1.6.0+)
- Health scores are computed on-demand

### Scaling

- Single instance handles ~100 concurrent investigations
- For higher load, deploy multiple instances behind a load balancer
- Use Redis for shared caching across instances

## Backup & Recovery

### DataHub State

All investigation artifacts are stored in DataHub:
- Root cause reports (Knowledge Base)
- Playbooks (Knowledge Base)
- AI Knowledge panels (Structured Properties)
- Incidents (Incidents API)
- EU AI Act audit chain (Knowledge Base)

Backup DataHub regularly to preserve investigation history.

### Local State

- Cost tracker: In-memory (not persisted)
- Provenance tracker: In-memory (not persisted)
- Circuit breaker state: In-memory (resets on restart)

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|---|---|---|
| `Connection refused` | DataHub GMS not running | Check `docker compose ps` |
| `Authentication failed` | Invalid token | Verify token and auth_mode |
| `Mutation tools not supported` | DataHub < v0.5.0 | Upgrade DataHub or use mock mode |
| `Rate limit exceeded` | Too many requests | Increase `MAX_RPM` or add delay |
| `Context too old` | Stale metadata | Check DataHub ingestion status |

### Debug Mode

```bash
export LOG_LEVEL=DEBUG
python -m backend.main 2>&1 | tee meridian-debug.log
```

### Verify Installation

```bash
# Run all tests
python -m pytest tests/ -v

# Verify workers
python scripts/verify_all_workers.py

# Verify real computation
python scripts/verify_real_computation.py
```

## Support

- **Documentation:** See `README.md` and `QUICKSTART.md`
- **Issues:** https://github.com/trueboy1123/meridian-ai/issues
- **DataHub Slack:** https://datahub.com/slack

---

*Last updated: July 14, 2026*
