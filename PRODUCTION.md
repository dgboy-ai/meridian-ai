# Meridian AI — Production Deployment Guide

## Quick Start (5 minutes)

### Prerequisites
- Docker Desktop running
- 8GB RAM available (DataHub + MySQL + Kafka + Elasticsearch)
- Ports 3000, 8000, 8080, 9002 available

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/trueboy1123/meridian-ai
cd meridian-ai

# 2. Start all services
docker compose up -d

# 3. Wait for DataHub to be healthy (~90 seconds)
docker compose logs -f datahub-gms  # Watch for "Started" message

# 4. Seed demo data
python scripts/seed_meridian.py

# 5. Open the apps
# Meridian AI:  http://localhost:3000
# DataHub UI:   http://localhost:9002
# API docs:     http://localhost:8000/docs
```

### Verify It Works

1. Open `http://localhost:3000`
2. Click "Run Investigation" → select `raw_events`
3. Wait ~30 seconds for investigation to complete
4. Open `http://localhost:9002` → navigate to churn_model_v3
5. Verify AI Knowledge panel appears on the entity page

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Docker Compose                     │
├─────────────────────────────────────────────────────┤
│  Frontend (Next.js)     → localhost:3000             │
│  Backend API (FastAPI)  → localhost:8000             │
│  DataHub GMS            → localhost:8080             │
│  DataHub UI             → localhost:9002             │
│  MySQL                  → localhost:3307             │
│  Kafka                  → localhost:9092             │
│  Elasticsearch          → localhost:9200             │
└─────────────────────────────────────────────────────┘
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATAHUB_MOCK` | `true` | Set to `false` for real DataHub |
| `DATAHUB_GMS_URL` | `http://localhost:8080/api/gms` | DataHub GMS endpoint |
| `GROQ_API_KEY` | (empty) | Groq API key for LLM |
| `LOG_LEVEL` | `INFO` | Logging level |

## Mock vs Real Mode

### Mock Mode (Default)
- No external dependencies required
- In-memory DataHub simulation
- All workers fire with computed results
- Write-backs update in-memory state
- Best for: development, demos, CI

### Real Mode
- Requires DataHub running via docker-compose
- Real HTTP calls to DataHub GMS
- Write-backs create real entities in DataHub
- EU AI Act audit chain persisted to disk
- Best for: production deployment, judge demos

To switch: `export DATAHUB_MOCK=false`

## Scaling Considerations

### Current Limits
- SQLite persistence (single-writer)
- In-memory rate limiter (per-process)
- Synchronous investigation (blocks request)

### Production Upgrades
- PostgreSQL for persistence (configurable via `PERSIST_BACKEND`)
- Redis for rate limiting
- Background task queue (Celery/RQ) for investigations
- Horizontal scaling via load balancer

## Monitoring

- Health: `GET /health`
- Readiness: `GET /health/ready`
- Liveness: `GET /health/live`
- Metrics: `GET /metrics` (Prometheus-compatible)
- System: `GET /api/system/health`

## Troubleshooting

### DataHub GMS won't start
- Check `docker compose logs datahub-gms`
- Ensure MySQL is healthy first
- Increase `start_period` in docker-compose.yml if needed

### Investigation hangs
- Check backend logs: `docker compose logs backend-api`
- Verify Groq API key is set (optional but recommended)
- In mock mode, investigations should complete in ~30 seconds

### Frontend shows blank page
- Check `docker compose logs frontend`
- Verify backend is running: `curl http://localhost:8000/health`
- Check browser console for CORS errors
