# Meridian AI — Deployment Guide

> How to deploy Meridian AI in different environments.

## Option 1: CLI (Fastest — 30 seconds)

No Docker, no DataHub, no API keys needed.

```bash
git clone https://github.com/dgboy-ai/meridian-ai
cd meridian-ai
pip install -e .
meridian investigate "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"
```

## Option 2: API Server (Mock Mode)

```bash
pip install -e .
python -m backend.main
# Open http://localhost:8000/docs
```

## Option 3: Full Stack with Real DataHub

```bash
docker compose up -d
python scripts/seed_meridian.py

export DATAHUB_MOCK=false
export DATAHUB_GMS_URL=http://localhost:8080/api/gms
python -m backend.main
```

| URL | What It Shows |
|-----|---------------|
| http://localhost:3000 | Meridian AI — Investigation Dashboard |
| http://localhost:9002 | DataHub UI — Entity pages, AI Knowledge panel |
| http://localhost:8000/docs | FastAPI — Interactive API documentation |

## Option 4: Vercel (Frontend Only)

### Step 1: Deploy Backend on Render

1. Create account at render.com
2. New → Web Service → Connect GitHub repo `dgboy-ai/meridian-ai`
3. Settings:
   - **Root Directory**: `.` (repo root)
   - **Runtime**: Docker
   - **Dockerfile Path**: `Dockerfile`
   - **Port**: 8000
4. Add environment variable: `DATAHUB_MOCK=true`
5. Deploy

### Step 2: Deploy Frontend on Vercel

1. Create account at vercel.com
2. New Project → Import `dgboy-ai/meridian-ai`
3. Settings:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
4. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = `https://your-app.onrender.com`
5. Deploy

### Step 3: Verify

1. Open Vercel URL → landing page loads
2. Navigate to Dashboard → shows mock data (or real data if backend is connected)
3. Run investigation via CLI → results appear in dashboard

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATAHUB_MOCK` | `true` | Set to `false` for real DataHub |
| `DATAHUB_GMS_URL` | `http://localhost:8080/api/gms` | DataHub GMS endpoint |
| `GROQ_API_KEY` | (empty) | Groq API key for LLM inference |
| `AUTH_ENABLED` | `false` | Enable JWT authentication |
| `AUTH_SECRET_KEY` | (auto-generated) | JWT signing secret |
| `NEXT_PUBLIC_API_URL` | (empty) | Backend URL for Vercel deployment |
| `BACKEND_URL` | (empty) | Backend URL for Docker rewrites |

## Architecture by Deployment

### CLI (No Infrastructure)
```
User → CLI → Meridian Backend (mock) → Examples
```

### Full Stack (Docker)
```
User → Browser → Frontend (:3000) → Backend (:8000) → DataHub (:8080)
                                                    → MySQL
                                                    → Kafka
                                                    → Elasticsearch
```

### Vercel + Render
```
User → Browser → Vercel (frontend) → Render (backend) → DataHub (if configured)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `npm ci` fails | Use `npm install` instead (lock file may be stale) |
| Vercel 404 | Ensure Framework Preset is "Next.js" and Root Directory is `frontend` |
| DataHub won't start | Check `docker compose logs datahub-gms`, ensure MySQL is healthy first |
| Investigation hangs | Verify `GROQ_API_KEY` is set (optional but recommended) |
| Frontend shows blank | Check `docker compose logs frontend`, verify backend is running |
