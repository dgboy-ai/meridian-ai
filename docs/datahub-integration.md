# How Meridian AI Uses DataHub

> This document explains exactly how Meridian AI integrates with DataHub to solve both hackathon challenges. Every DataHub capability is mapped to a specific problem it solves.

---

## Challenge 1: Production ML Agents

> *"Build agents for ML teams that protect models in production. Use DataHub's end-to-end ML lineage — the path from training data to features to models to deployments — to catch silent problems that can break ML systems before they cost money."*

### The Problem We Solve

ML models fail silently. A schema change in an upstream dataset breaks a feature pipeline, which degrades model accuracy from 89% to 71% — and nobody notices for 3 days. The model keeps serving predictions, but they're wrong. Revenue bleeds quietly.

**Why DataHub is essential:** DataHub has the lineage graph that connects training data → features → models → deployments. Without this graph, you can't trace WHY a model degraded. Meridian AI reads this graph via the MCP Server, traverses it to find root cause, and writes the investigation back so the next incident is faster.

### How We Use DataHub for Production ML

| DataHub Capability | How Meridian Uses It | ML Problem It Solves |
|-------------------|---------------------|---------------------|
| **MCP: get_lineage** | Traverses upstream from model to find which dataset changed | Root cause: "raw_events.age changed INT → STRING" |
| **MCP: get_lineage_paths_between** | Finds exact path: raw_events → feature_pipeline → churn_model_v3 | Blast radius: "3 models, 12 dashboards affected" |
| **MCP: list_schema_fields** | Compares column types before/after schema change | Detects type mismatch that broke feature pipeline |
| **MCP: get_dataset_queries** | Reads real SQL that references the dataset | Understands how data is actually used in production |
| **MCP: get_entities** | Fetches MLModel, MLFeatureTable, MLModelDeployment metadata | Gets full ML lineage context |
| **GraphQL: raise_incident** | Creates incident linked to affected model entity | Tracks model health in DataHub |
| **GraphQL: add_structured_properties** | Writes AI Knowledge panel to model entity | Model page shows health score, confidence, resolved incidents |
| **GraphQL: batch_add_tags** | Tags all affected assets (models, dashboards, datasets) | Impact visualization across data stack |
| **Actions Framework YAML** | Auto-triggers investigation on schema change event | Zero-human-intervention detection |
| **MCP: save_document** | Writes root cause report to Knowledge Base | Investigation findings persist for future reference |

### The Write-Back Story (What Makes Us Different)

Every other submission READS DataHub. We READ AND WRITE. After every investigation:

1. **Root Cause Report** → `save_document` → DataHub Knowledge Base
2. **Reflexion Playbook** → `save_document` → DataHub Knowledge Base (improves after every incident)
3. **AI Knowledge Panel** → `add_structured_properties` → MLModel entity page
4. **Incident Record** → `raise_incident` → Linked to all affected entities
5. **EU AI Act Technical File** → `save_document` → Compliance audit trail

**Result:** DataHub itself becomes smarter. The next time this model breaks, the agent already knows what to do.

### The Flywheel (Proof It Works)

```
Incident #12:  18 min  (first occurrence — playbook created)
Incident #28:   8 min  (same pattern — playbook retrieved)
Incident #42:   3 min  (pattern matched instantly — knowledge applied)
```

This is ONLY possible because:
- DataHub stores the playbooks (via `save_document`)
- DataHub stores the AI Knowledge panel (via `add_structured_properties`)
- DataHub stores the incident history (via `raise_incident`)
- Future investigations READ these back (via `search_documents`, `get_entities`)

**Without DataHub, this flywheel doesn't exist.**

---

## Challenge 2: Agents That Do Real Work

> *"Build AI agents that handle data problems — alone or as a team. Your agent reads DataHub through the MCP Server or Agent Context Kit to understand what's connected to what, takes action, and writes results back so the next person or agent inherits the knowledge."*

### The Problem We Solve

Data engineers spend 45+ minutes investigating each incident — reading stale docs, searching Slack, tracing lineage manually. The knowledge from each investigation vanishes. The next engineer starts from zero.

**Why DataHub is essential:** DataHub is the organizational memory. Without it, agents have no context — they don't know what's connected to what, who owns what, or what happened before. Meridian AI gives agents this context AND writes knowledge back so the next agent inherits everything.

### How We Use DataHub for Agents That Do Real Work

| DataHub Capability | How Meridian Uses It | Agent Problem It Solves |
|-------------------|---------------------|------------------------|
| **MCP: search** | Finds production assets by query, tags, ownership | Agent discovers relevant datasets without guessing |
| **MCP: get_entities** | Batch metadata for any entity | Agent understands what each asset is and who owns it |
| **MCP: get_lineage** | Upstream/downstream traversal | Agent traces impact of changes across the data stack |
| **MCP: list_schema_fields** | Column-level metadata | Agent understands data structure at granular level |
| **MCP: search_documents** | Finds past playbooks in Knowledge Base | Agent retrieves institutional knowledge from prior investigations |
| **MCP: save_document** | Persists root cause reports + playbooks | Agent writes findings back so next agent inherits knowledge |
| **MCP: add_structured_properties** | Updates AI Knowledge panels | Agent enriches entity metadata with investigation insights |
| **GraphQL: raise_incident** | Creates incidents programmatically | Agent tracks issues in DataHub's incident system |
| **GraphQL: batch_add_tags** | Tags all affected assets in bulk | Agent marks impacted assets for visibility |
| **GraphQL: update_incident_status** | Closes/resolves incidents | Agent completes investigation lifecycle |
| **Actions Framework YAML** | Auto-trigger on schema change events | Agent responds to data problems without human intervention |

### The "Next Agent Inherits" Story

This is the core of "Agents That Do Real Work" — the write-back.

**Before Meridian:**
```
Agent A investigates → finds root cause → fixes it → knowledge disappears
Agent B investigates same problem → starts from zero → wastes 45 minutes
```

**After Meridian:**
```
Agent A investigates → finds root cause → writes to DataHub
Agent B investigates same problem → reads playbook from DataHub → resolves in 3 minutes
```

The knowledge compounds because DataHub stores it permanently.

### How Agents Trigger Investigations

Meridian AI is itself an MCP tool. Any agent can trigger investigations:

```python
# Via MCP Server
agent.call_tool("meridian_investigate", {
    "model_urn": "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"
})

# Via Actions Framework (automatic)
# Schema change in DataHub → triggers investigation automatically
# No human intervention needed

# Via CLI
meridian investigate "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"
```

### What Gets Written Back (5 Artifacts)

| Artifact | DataHub Location | Who Reads It Next |
|----------|-----------------|-------------------|
| Root Cause Report | Knowledge Base | Next engineer investigating same model |
| Reflexion Playbook | Knowledge Base | Next agent encountering same pattern |
| AI Knowledge Panel | MLModel entity page | Anyone browsing DataHub |
| Incident Record | Incidents API | Team tracking model health |
| EU AI Act Technical File | Knowledge Base | Compliance auditors |

---

## DataHub Integration Summary

### Read Operations (What We Learn From DataHub)

| Capability | Purpose | Challenge |
|------------|---------|-----------|
| `search` | Find production assets | Agents That Do Real Work |
| `get_entities` | Batch metadata | Both |
| `get_lineage` | Upstream/downstream traversal | Production ML Agents |
| `get_lineage_paths_between` | Exact paths between assets | Production ML Agents |
| `list_schema_fields` | Column-level metadata | Both |
| `get_dataset_queries` | Real SQL referencing datasets | Agents That Do Real Work |
| `search_documents` | Find past playbooks | Both |

### Write Operations (What We Contribute Back)

| Capability | Purpose | Challenge |
|------------|---------|-----------|
| `save_document` | Persist root cause reports + playbooks | Both |
| `add_structured_properties` | Update AI Knowledge panels | Production ML Agents |
| `raise_incident` | Create incidents programmatically | Both |
| `batch_add_tags` | Tag all affected assets | Both |
| `update_incident_status` | Close/resolved incidents | Both |

### Governance Operations

| Capability | Purpose | Challenge |
|------------|---------|-----------|
| `propose_lifecycle_stage` | Propose DEPRECATED for failing models | Production ML Agents |
| `list_pending_proposals` | Check queued governance proposals | Production ML Agents |

### Orchestration

| Capability | Purpose | Challenge |
|------------|---------|-----------|
| Actions Framework YAML | Auto-trigger on schema change | Both |
| MCP Server as MCP tool | Meridian exposes itself for other agents | Agents That Do Real Work |

---

## Why This Wins

### For "Production ML Agents" (Primary Challenge)

1. **End-to-end ML lineage** — We use `get_lineage` and `get_lineage_paths_between` to trace from training data through features to models to deployments
2. **Catches silent problems** — Schema changes that break feature pipelines are detected via Actions Framework auto-trigger
3. **Writes back to DataHub** — AI Knowledge panel on model entities, incident records, compliance audit trail
4. **Gets faster every time** — Reflexion playbooks stored in DataHub Knowledge Base improve resolution time

### For "Agents That Do Real Work" (Secondary Challenge)

1. **Reads DataHub context** — 7 read tools give agents complete understanding of the data stack
2. **Writes results back** — 5 write tools ensure knowledge persists in DataHub
3. **Next agent inherits** — Playbooks, knowledge panels, and incident records are permanent
4. **Auto-trigger** — Actions Framework fires investigations without human intervention

### What Makes This Different From Other Submissions

| Other Submissions | Meridian AI |
|-------------------|-------------|
| Read DataHub metadata | Read AND write knowledge back |
| Detect problems | Investigate, diagnose, AND remediate |
| One-time analysis | Cumulative intelligence (flywheel) |
| No compliance | EU AI Act SHA-256 audit chain |
| Manual triggering | Actions Framework auto-trigger |
| No agent safety | Progressive Autonomy + Maker-Checker |
