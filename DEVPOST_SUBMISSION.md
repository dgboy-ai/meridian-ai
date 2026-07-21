# Devpost Submission — Meridian AI

## Project Name
Meridian AI

## Tagline
The AI Reliability Engineer that makes DataHub smarter with every ML incident.

## Challenge
Production ML Agents (primary) · Agents That Do Real Work (secondary)

## Description

Meridian AI is an AI Reliability Engineer that autonomously investigates production ML incidents, writes operational knowledge back into DataHub, and ensures every future engineer — and every future AI agent — starts with everything the previous investigation learned.

### The Problem

Production ML models fail silently. When they do, engineers spend 45+ minutes tracing lineage, reading stale docs, and searching Slack for context that should live in the metadata platform. The knowledge from each investigation vanishes — the next incident starts from zero.

| Statistic | Source |
|---|---|
| AI incidents rose **55% YoY** | Stanford HAI 2026 |
| **77% of ML teams** have no monitoring | Peer-reviewed study (37 practitioners) |
| Poor data quality costs **$12.9M–$13.95M/year** | Gartner / IBM / IDC |
| Context-aware platforms cut resolution by **58%** | IDC March 2026 |

### What Meridian AI Does

**Every investigation becomes organizational memory.** Meridian AI reads your DataHub context graph — lineage, schemas, ownership, ML metadata — detects anomalies, traces root cause through column-level lineage, and writes everything it learned back into DataHub permanently.

1. **Detect** — Schema changes, freshness violations, PII exposures, feature drift (real PSI/KS-test math)
2. **Diagnose** — Traverse DataHub lineage to find root cause, compute blast radius across models and dashboards
3. **Remediate** — Propose rollback, generate preventive assertions, enforce dataset contracts
4. **Learn** — Write root cause reports, reflexion playbooks, and AI Knowledge panels back to DataHub
5. **Comply** — EU AI Act SHA-256 audit chain for Articles 12, 13, 14 (enforcement: August 2, 2026)

### DataHub Integration

Meridian AI uses **15 DataHub capabilities** across the full read/write lifecycle:

**Read (MCP Server):**
- `search` — Find production assets by query
- `get_entities` — Batch metadata for any entity
- `get_lineage` — Upstream/downstream traversal (core of root cause analysis)
- `list_schema_fields` — Column-level metadata for feature drift
- `search_documents` — Find past playbooks for pattern matching

**Write (MCP + GraphQL):**
- `save_document` — Persist root cause reports and reflexion playbooks
- `add_structured_properties` — Update AI Knowledge panels on model entities
- `raise_incident` — Create incidents programmatically
- `batch_add_tags` — Tag all affected assets in bulk

**Orchestration:**
- DataHub Actions Framework YAML — auto-triggers investigation on schema change events
- Reflexion playbooks stored in DataHub Knowledge Base — improve after every resolution
- 5 artifacts written per investigation (root cause report, playbook, AI Knowledge panel, incident record, compliance file)

### Technical Execution

- **18 workers** with structured evidence objects — each computes real things (PSI, KS-test, schema diff, lineage traversal, blast radius)
- **Deterministic Validation Layer** — 4 checks (confidence > 0.7, entity exists, safe ops, no duplicates) before any write
- **Progressive Autonomy** — 5 levels from Advisory to Self-improving; agents ask permission for irreversible actions
- **Maker-Checker Verification** — VerifierAgent challenges RootCause conclusions before write-back
- **Health Score** — Computed from 6 weighted metrics with per-worker confidence
- **552 tests** (unit, integration, e2e) — CI on Python 3.11/3.12/3.13
- **MCP Server** — Meridian AI is itself an MCP tool; any agent can trigger investigations via Model Context Protocol

### Originality

- **Cumulative intelligence** — Resolution time improves: 18min → 8min → 3min (83% faster). The knowledge base compounds after every incident. No other monitoring tool does this.
- **AI Knowledge Panel** — DataHub entity pages gain intelligence. After an investigation, `churn_model_v3` shows resolved incidents, failure patterns, confidence, and recommended playbook — all maintained by AI.
- **EU AI Act compliance** — SHA-256 audit chain for Articles 12 (Record-Keeping), 13 (Transparency), 14 (Human Oversight). Technical File generated per investigation.
- **Self-healing assertions** — Generates preventive dataset contract assertions from incident patterns.
- **Reflexion loop** — Self-RAG playbook improvement: playbook for "schema-change-type-mismatch" gets refined after every occurrence.

### Real-World Usefulness

- **4 personas**: ML Platform Engineer (daily health checks), Data Engineer (investigation timeline), MLOps Lead (resolution time trends), Enterprise Data Architect (compliance audit trail)
- **$45K/day business impact** — 32K predictions/day × $1.41/prediction at risk during silent degradation
- **EU AI Act enforcement August 2, 2026** — hackathon deadline August 11. Compliance is no longer optional.
- **Dual-mode deployment** — Works instantly in mock mode (no dependencies) or with real DataHub via Docker Compose

## How to Run

```bash
# Option 1: Zero setup (30 seconds, no DataHub required)
git clone https://github.com/trueboy1123/meridian-ai
cd meridian-ai
pip install -e .
meridian investigate "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"

# Option 2: Full stack with real DataHub (5 minutes)
docker compose up -d
python scripts/seed_meridian.py
python -m backend.main
# Meridian UI:  http://localhost:3000
# DataHub UI:   http://localhost:9002
# API docs:     http://localhost:8000/docs
```

## Example Outputs

All examples in `examples/` are **generated by the system** — run `python scripts/regenerate_examples.py` to verify.

| File | What It Shows |
|---|---|
| `ai-knowledge/churn_model_v3.json` | AI Knowledge panel: 15 resolved incidents, health=89, confidence=0.94 |
| `resolution_times.json` | Flywheel proof: 18min → 8min → 3min (83% improvement) |
| `incident_42_timeline.json` | Full investigation: 36 events, 17 workers fired |
| `incident_42_summary.json` | Summary: 17 DataHub mutations, EU AI Act compliance |
| `reports/incident_042_root_cause.md` | Root cause report with evidence chain |
| `playbooks/schema_change_playbook.md` | Reflexion playbook (improves after every incident) |
| `incidents/incident_042_full.json` | Full incident record with blast radius |

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+ FastAPI (async) |
| LLM Inference | Groq (Llama 3 70B) — $0 via free tier |
| DataHub Integration | MCP Server + GraphQL (dual-mode: real + mock) |
| Statistical Computation | PSI, KS-test, schema diff (pure Python, no ML libs) |
| Compliance | EU AI Act SHA-256 audit chain |
| Frontend | Next.js 14 + Framer Motion |
| Deployment | Docker Compose (DataHub + MySQL + Kafka + ES) |
| Testing | 552 tests (pytest + pytest-asyncio) |

## Links

- **GitHub:** https://github.com/trueboy1123/meridian-ai
- **Demo:** http://localhost:3000 (after `docker compose up`)
- **Video:** [YouTube link — recording pending]

## License

Apache 2.0
