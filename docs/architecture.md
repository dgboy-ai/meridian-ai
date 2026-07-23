# Meridian AI — Architecture

> System design, data flow, and component interactions.

## High-Level Architecture

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

## Worker Pipeline

### Detection Phase

| Worker | Input | Output | Real Math |
|--------|-------|--------|-----------|
| Data Sentinel | Dataset URN | Schema diff, freshness, PII, quality | `compute_schema_diff`, `PIIScanner` |
| Feature Drift | Dataset + Model URN | PSI/KS per feature | `population_stability_index`, `ks_test` |
| Training-Serving Skew | Training + Serving schemas | Distribution comparison | `type_mismatch_check` |
| Data Leakage | Feature timestamps | Temporal violation detection | `check_temporal_leakage` |

### Diagnosis Phase

| Worker | Input | Output | Real Math |
|--------|-------|--------|-----------|
| Root Cause | Lineage graph | Root cause + blast radius | `traverse_column_lineage`, `compute_blast_radius` |

### Verification Phase

| Worker | Input | Output | Logic |
|--------|-------|--------|-------|
| VerifierAgent | RootCause evidence | Verified/rejected conclusion | Maker-checker pattern |

### Enforcement Phase

| Worker | Input | Output | DataHub Operations |
|--------|-------|--------|-------------------|
| Knowledge Writer | Investigation results | 5 artifacts written | save_document, add_structured_properties, raise_incident, batch_add_tags |
| Contract Enforcer | Assertion results | Quarantine decisions | Tag affected assets |
| Lifecycle Governance | Health scores | Lifecycle proposals | propose_lifecycle_stage |

### Learning Phase

| Worker | Input | Output | Logic |
|--------|-------|--------|-------|
| Reflexion Loop | Resolution + prior playbooks | Improved playbook | Self-RAG with LLM |
| Self-Healing Assertions | Incident patterns | Preventive assertions | Pattern-to-assertion mapping |

### Compliance Phase

| Worker | Input | Output | Logic |
|--------|-------|--------|-------|
| EU AI Act Compliance | All decisions | SHA-256 audit chain | Hash chaining |
| Shadow AI Discovery | Entity registry | Ungoverned model detection | Governance gap analysis |

## Data Flow

### Investigation Flow

```
1. Trigger (user/Actions Framework/schedule)
   ↓
2. Planner Agent decomposes goal
   ↓
3. Fire workers in parallel (Detection phase)
   ↓
4. Collect evidence objects
   ↓
5. Root Cause traversal (Diagnosis phase)
   ↓
6. Deterministic Validation (4 checks)
   ↓
7. VerifierAgent challenges conclusion
   ↓
8. Knowledge Writer writes 5 artifacts to DataHub
   ↓
9. Reflexion Loop improves playbook
   ↓
10. EU AI Act audit record appended
```

### Evidence Object Schema

Every worker returns this structured object:

```python
{
    "worker_id": "data_sentinel",
    "timestamp": "2026-07-12T14:32:00Z",
    "finding": "Schema change in raw_users — column 'age' changed INT → STRING",
    "confidence": 0.94,
    "severity": "high",
    "evidence": [...],
    "business_impact": {
        "predictions_today": 32000,
        "estimated_revenue_at_risk": "$45,000/day",
        "affected_systems": [...]
    },
    "next_action": "Notify Root Cause worker for lineage traversal",
    "datahub_mutations": [...]
}
```

## Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     FASTAPI SERVER                        │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ REST API │  │ SSE      │  │ MCP      │              │
│  │ Endpoints│  │ Streaming│  │ Server   │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │              │              │                    │
│  ┌────▼──────────────▼──────────────▼─────┐            │
│  │           PLANNER AGENT                  │            │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐   │            │
│  │  │Workers  │ │Validation│ │Reflexion│   │            │
│  │  │(18)     │ │Layer     │ │Loop     │   │            │
│  │  └─────────┘ └─────────┘ └─────────┘   │            │
│  └──────────────────┬──────────────────────┘            │
│                     │                                    │
│  ┌──────────────────▼──────────────────────┐            │
│  │         DATAHUB MCP CLIENT              │            │
│  │  Mock mode · Real mode · Dual-mode      │            │
│  └──────────────────┬──────────────────────┘            │
│                     │                                    │
│  ┌──────────────────▼──────────────────────┐            │
│  │         PERSISTENCE MANAGER              │            │
│  │  SQLite · In-memory fallback             │            │
│  └─────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────┘
```

## Dual-Mode Client

| Mode | When | How |
|------|------|-----|
| **Mock** | Default, no DataHub required | In-memory simulation of all operations |
| **Real** | `DATAHUB_MOCK=false` | HTTP calls to DataHub GMS endpoint |

Switch: `export DATAHUB_MOCK=false && export DATAHUB_GMS_URL=http://localhost:8080/api/gms`

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | Python 3.11+ FastAPI (async) | API server, worker orchestration |
| LLM | Groq (Llama 3 70B) | Natural language reasoning |
| DataHub | MCP Server + GraphQL | Metadata context + write-back |
| Statistics | PSI, KS-test, schema diff | Drift detection, quality analysis |
| Compliance | SHA-256 audit chain | EU AI Act Articles 12, 13, 14 |
| Frontend | Next.js 14 + Framer Motion | Investigation dashboard |
| Database | SQLite (via aiosqlite) | Incident persistence |
| Deployment | Docker Compose | Full stack with DataHub |
