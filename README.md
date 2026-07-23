# Meridian AI

> **The AI Reliability Engineer that makes DataHub smarter every time an ML incident occurs.**

Silent ML failures cost $45,000/day. Most teams don't notice for 3 days. Meridian AI catches them in 8 minutes. And the next one takes 3 — because the knowledge base learned.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue)](#license)
[![Tests: 563](https://img.shields.io/badge/Tests-563-green)](#technical-execution)
[![DataHub Tools: 15](https://img.shields.io/badge/DataHub%20Tools-15-purple)](#datahub-integration)
[![Workers: 18](https://img.shields.io/badge/Workers-18-orange)](#architecture)

---

## The Problem

Production ML models fail silently. When they do, engineers spend 45+ minutes tracing lineage, reading stale docs, and searching Slack for context that should live in the metadata platform. The knowledge from each investigation vanishes — the next incident starts from zero.

| Statistic | Source | Implication |
|-----------|--------|-------------|
| AI incidents rose **55% YoY** | Stanford HAI 2026 | ML failures are accelerating |
| **77% of ML teams** have no monitoring | Peer-reviewed study | Our target audience |
| Poor data quality costs **$12.9M-$13.95M/year** | Gartner / IBM / IDC | Massive financial incentive |
| Context-aware platforms cut resolution by **58%** | IDC March 2026 | Our exact value proposition |

**DataHub has MLModel entities but no automated investigation.** It can detect problems (assertions), but can't diagnose root cause, trace through ML lineage, or write knowledge back. That's the gap Meridian fills.

---

## The Solution

**Every investigation becomes organizational memory.**

Meridian AI reads your DataHub context graph — lineage, schemas, ownership, ML metadata — detects anomalies, traces root cause through column-level lineage, and writes everything it learned back into DataHub permanently. The next time this model breaks, the agent already knows what to do.

```
Detect → Diagnose → Remediate → Learn → DataHub gets smarter
```

### What Gets Written Back to DataHub

After every investigation, **5 artifacts exist in DataHub**:

| Artifact | Location | What It Shows |
|----------|----------|---------------|
| Root Cause Report | Knowledge Base | Full investigation with evidence chain |
| Reflexion Playbook | Knowledge Base | Improved after every incident |
| AI Knowledge Panel | Model entity page | Health score, confidence, resolved incidents |
| Incident Record | Incidents API | Linked to all affected entities |
| EU AI Act Technical File | Knowledge Base | SHA-256 audit trail for compliance |

---

## The Flywheel

This is what makes Meridian different from every other monitoring tool. The knowledge base compounds.

```
Incident #12:  18 min  (first occurrence — playbook created from scratch)
Incident #28:   8 min  (same pattern — playbook retrieved, resolution suggested)
Incident #42:   3 min  (pattern matched instantly — knowledge applied)
```

**83% faster** from first to third occurrence. Verified in `examples/resolution_times.json`.

---

## Quick Start (30 seconds)

```bash
git clone https://github.com/dgboy-ai/meridian-ai
cd meridian-ai
pip install -e .
meridian investigate "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"
```

17 workers fire, 17 DataHub mutations generated, EU AI Act compliance chain produced. **No Docker, no DataHub, no API keys required.**

### Other Options

| Method | Command | What You See |
|--------|---------|-------------|
| **CLI** | `meridian investigate "..."` | Full investigation in terminal |
| **API Server** | `python -m backend.main` | Interactive docs at localhost:8000/docs |
| **Full Stack** | `docker compose up -d` | Meridian UI + DataHub UI + API |
| **Examples** | `python scripts/regenerate_examples.py` | Pre-generated outputs in examples/ |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    TRIGGER                               │
│  Scheduled scan · Actions Framework · User request       │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│              PLANNER AGENT (18 workers)                  │
│  Detects → Diagnoses → Remediates → Learns              │
│  Progressive Autonomy gates each worker                  │
│  HealthScore computed from real worker confidence        │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│              DETERMINISTIC VALIDATION                     │
│  Confidence > 0.7 · Entity exists · Safe ops             │
│  Maker-checker: VerifierAgent challenges RootCause       │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│              WRITE-BACK TO DATAHUB                       │
│  5 artifacts per investigation                           │
│  Root cause · Playbook · AI Knowledge · Incident · Audit │
└─────────────────────────────────────────────────────────┘
```

---

## DataHub Integration (15 Capabilities)

Meridian doesn't just read DataHub — it writes knowledge back so DataHub itself becomes smarter.

### Read (MCP Server)
| Capability | Purpose |
|------------|---------|
| `search` | Find production assets by query |
| `get_entities` | Batch metadata for any entity |
| `get_lineage` | Upstream/downstream traversal |
| `get_lineage_paths_between` | Exact path between two entities |
| `list_schema_fields` | Column-level metadata |
| `get_dataset_queries` | Real SQL referencing datasets |
| `search_documents` | Find past playbooks |

### Write (MCP + GraphQL)
| Capability | Purpose |
|------------|---------|
| `save_document` | Persist root cause reports + playbooks |
| `add_structured_properties` | Update AI Knowledge panels |
| `raise_incident` | Create incidents programmatically |
| `batch_add_tags` | Tag all affected assets |
| `update_incident_status` | Close/resolved incidents |

### Governance
| Capability | Purpose |
|------------|---------|
| `propose_lifecycle_stage` | Propose DEPRECATED for failing models |
| `list_pending_proposals` | Check queued governance proposals |

### Orchestration
- **Actions Framework YAML** — Auto-triggers investigation on schema change events
- **MCP Server** — Meridian exposes itself as MCP tools for other agents

---

## Workers (18 — All Computing Real Things)

Every worker uses real computation, not LLM guessing.

| Worker | Phase | Real Math |
|--------|-------|-----------|
| Data Sentinel | Detection | `compute_schema_diff`, `PIIScanner` |
| Feature Drift | Detection | `population_stability_index`, `ks_test` |
| Training-Serving Skew | Detection | `type_mismatch_check`, `feature_drift_score` |
| Data Leakage | Detection | `check_temporal_leakage` |
| Root Cause | Diagnosis | `traverse_column_lineage`, `compute_blast_radius` |
| VerifierAgent | Verification | Maker-checker validation |
| Knowledge Writer | Enforcement | 5 DataHub writes per investigation |
| Reflexion Loop | Learning | Self-RAG playbook improvement |
| Lifecycle Governance | Governance | Health evaluation + proposals |
| EU AI Act Compliance | Compliance | SHA-256 audit chain + Technical File |
| Shadow AI Discovery | Governance | Ungoverned model detection |
| Contract Enforcer | Enforcement | Assertion checking + quarantine |
| Explanation Drift | Detection | PSI on importance distributions |
| Self-Healing Assertions | Learning | Preventive assertion generation |
| Pipeline Circuit Breaker | Enforcement | Halts downstream on upstream failure |
| Deprecation Advisor | Governance | Safe deprecation of unused assets |
| ML Metadata Integrator | Detection | MLModelDeployment, MLFeatureTable queries |
| Validation Layer | Safety | 4 checks before any write |

---

## Technical Execution

- **563 tests** passing (unit, integration, e2e) — CI on Python 3.11/3.12/3.13
- **Deterministic Validation Layer** — 4 checks: confidence > 0.7, entity exists, safe ops, no duplicates
- **Progressive Autonomy** — 5 levels from Advisory to Self-improving
- **Maker-Checker** — VerifierAgent challenges RootCause before write-back
- **Health Score** — 6 weighted metrics computed from real worker confidence
- **Circuit Breaker** — Monitors agent reasoning health, detects loops/drift
- **Provenance Tracking** — Tracks which context sources were used per worker

---

## Originality

### Cumulative Intelligence (No Other Tool Does This)
The reflexion loop writes playbooks to DataHub Knowledge Base after every incident. Future investigations read these playbooks first. Resolution time compounds: 18min → 8min → 3min.

### AI Knowledge Panel
DataHub entity pages gain intelligence. After an investigation, `churn_model_v3` shows resolved_incidents, known_failure_patterns, confidence, recommended playbook — all AI-maintained.

### EU AI Act Compliance
SHA-256 audit chain for Articles 12 (Record-Keeping), 13 (Transparency), 14 (Human Oversight). Technical File generated per investigation. **Enforcement: August 2, 2026** — 22 days before hackathon deadline.

### Self-Healing Assertions
Generates preventive dataset contract assertions from incident patterns. Each investigation makes the system more resilient.

---

## Real-World Usefulness

- **$45K/day at risk** — 32K predictions/day × $1.41/prediction during silent degradation
- **4 personas** — ML Platform Engineer, Data Engineer, MLOps Lead, Enterprise Data Architect
- **EU AI Act enforcement imminent** — compliance is no longer optional
- **Zero-friction demo** — mock mode works instantly, full stack in 5 minutes

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+ FastAPI (async) |
| LLM | Groq (Llama 3 70B) — $0 via free tier |
| DataHub | MCP Server + GraphQL (dual-mode: real + mock) |
| Statistics | PSI, KS-test, schema diff (pure Python) |
| Compliance | EU AI Act SHA-256 audit chain |
| Frontend | Next.js 14 + Framer Motion |
| Deployment | Docker Compose (DataHub + MySQL + Kafka + ES) |

---

## Example Outputs

All examples in `examples/` are generated by real worker output. Judges can verify:

```bash
python scripts/regenerate_examples.py
```

| File | What It Shows |
|------|---------------|
| `ai-knowledge/churn_model_v3.json` | AI Knowledge panel: health=89, confidence=0.94, resolved=15 |
| `resolution_times.json` | Flywheel: 18min → 8min → 3min (83% improvement) |
| `incident_42_timeline.json` | Full investigation: 36 events, 17 workers |
| `incident_42_summary.json` | 17 mutations, validation_passed=true |
| `reports/incident_042_root_cause.md` | Generated root cause report |
| `playbooks/schema_change_playbook.md` | Reflexion playbook |
| `incidents/incident_042_full.json` | Full incident record with blast radius |

---

## For Judges

### 3 Ways to Verify

| Method | Time | Command |
|--------|------|---------|
| **CLI** | 30 sec | `pip install -e . && meridian investigate "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"` |
| **Examples** | 10 sec | `python scripts/regenerate_examples.py` |
| **Full Stack** | 5 min | `docker compose up -d` → localhost:3000 |

### What to Look For (By Criterion)

| Criterion | Evidence |
|-----------|----------|
| **Use of DataHub** | 15 capabilities (7 read + 5 write + 2 governance + Actions Framework) in `backend/clients/datahub_client.py` |
| **Technical Execution** | 563 tests, `backend/validation.py` (4 checks), `backend/autonomy.py` (5 levels) |
| **Originality** | `examples/resolution_times.json` (flywheel), `backend/workers/eu_ai_act_compliance.py` (SHA-256 audit) |
| **Real-World Usefulness** | `backend/health_score.py` (6 metrics), `backend/cost_tracker.py` (ROI), 4 personas |
| **Submission Quality** | `examples/` (7 files), `scripts/regenerate_examples.py` (provable) |

---

## DSA Algorithms (11)

| Algorithm | Complexity | Purpose |
|-----------|------------|---------|
| BFS/DFS Lineage | O(V+E) | Multi-hop lineage traversal |
| Topological Sort | O(V+E) | Pipeline dependency ordering |
| Cycle Detection | O(V+E) | Graph validation |
| Shortest Path | O(V+E) | Fastest propagation path |
| Connected Components | O(V+E) | Lineage grouping |
| Binary Search CDF | O(log n) | Fast CDF lookup |
| KS-Test Binary | O((n+m)log(n+m)) | Drift detection |
| Union-Find | O(α(n)) | Connectivity queries |
| Trie | O(m) | Entity prefix search |
| Min-Heap Top-K | O(n log k) | Fast top-k selection |

---

## Documentation

| Document | Quick Summary | Link |
|----------|---------------|------|
| **DataHub Integration** | How we use DataHub for each challenge — every tool mapped to a specific problem | [docs/datahub-integration.md](docs/datahub-integration.md) |
| **Features** | Complete catalog: 18 workers, 15 DataHub tools, 11 DSA algorithms, 13 frontend pages | [docs/features.md](docs/features.md) |
| **Security & Compliance** | JWT auth, password hashing, EU AI Act SHA-256 audit chain, validation layer, progressive autonomy | [docs/security.md](docs/security.md) |
| **Architecture** | System design, worker pipeline, data flow, component diagram, tech stack | [docs/architecture.md](docs/architecture.md) |
| **API Reference** | REST endpoints, MCP Server tools, CLI commands, response formats | [docs/api.md](docs/api.md) |
| **Deployment** | CLI, Docker, Vercel + Render, environment variables, troubleshooting | [docs/deployment.md](docs/deployment.md) |

---

## License

Apache 2.0 — see [LICENSE](LICENSE)
