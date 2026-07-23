# Meridian AI — Features

> Complete catalog of every capability in Meridian AI.

## Core Investigation Pipeline

| Feature | Description | Worker |
|---------|-------------|--------|
| Schema Change Detection | Detects column type changes, new/removed columns via DataHub schema diff | Data Sentinel |
| Feature Drift Detection | PSI/KS-test per feature, type mismatch detection | Feature Drift |
| Training-Serving Skew | Compares training data schema vs production serving schema | Training-Serving Skew |
| Data Leakage Detection | Temporal pattern detection for target leakage | Data Leakage |
| Column-Level Lineage | Traces exact column dependencies through lineage graph (BFS/DFS) | Root Cause |
| Blast Radius Calculation | Computes affected models, dashboards, revenue at risk | Root Cause |
| Root Cause Explanation | LLM-generated explanation of why the model degraded | Root Cause |

## Intelligence & Learning

| Feature | Description | Worker |
|---------|-------------|--------|
| Reflexion Loop | Self-RAG playbook improvement after every incident | Reflexion Loop |
| Semantic Search | Vector-based playbook retrieval from DataHub Knowledge Base | Reflexion Loop |
| Adaptive Assertions | Generates preventive dataset contract assertions from patterns | Self-Healing |
| Training Data Versioning | Records training data versions for reproducibility | ML Metadata |

## Compliance & Governance

| Feature | Description | Worker |
|---------|-------------|--------|
| EU AI Act Compliance | SHA-256 audit chain for Articles 12, 13, 14 | EU AI Act Compliance |
| Bias Detection Lineage | Checks for demographic skew, label imbalance in training data | Data Sentinel |
| PII Propagation | Tracks PII flow through lineage to downstream columns | Data Sentinel |
| SLA Compliance Tracking | Tracks model health SLAs against thresholds | Lifecycle Governance |
| Shadow AI Discovery | Finds ungoverned ML models without owners or documentation | Shadow AI Discovery |

## Agent Safety

| Feature | Description | Worker |
|---------|-------------|--------|
| Progressive Autonomy | 5 levels from Advisory to Self-improving | AutonomyManager |
| Maker-Checker Verification | VerifierAgent challenges RootCause before write-back | VerifierAgent |
| Agentic Circuit Breaker | Monitors agent reasoning health, detects loops/drift | Circuit Breaker |
| Provenance Validation | Validates context before LLM calls | Provenance Tracker |
| Deterministic Validation | 4 checks before any write: confidence, entity, safety, duplicates | Validation Layer |

## DataHub Integration

| Feature | Description | Direction |
|---------|-------------|-----------|
| MCP Search | Find production assets by query/tags | Read |
| MCP Get Entities | Batch metadata for any entity | Read |
| MCP Get Lineage | Upstream/downstream traversal | Read |
| MCP Get Lineage Paths | Exact path between two entities | Read |
| MCP List Schema Fields | Column-level metadata | Read |
| MCP Get Dataset Queries | Real SQL referencing datasets | Read |
| MCP Search Documents | Find past playbooks in Knowledge Base | Read |
| Save Document | Persist root cause reports + playbooks | Write |
| Add Structured Properties | Update AI Knowledge panels | Write |
| Raise Incident | Create incidents programmatically | Write |
| Batch Add Tags | Tag all affected assets in bulk | Write |
| Update Incident Status | Close/resolved incidents | Write |
| Propose Lifecycle Stage | Propose DEPRECATED for failing models | Governance |
| List Pending Proposals | Check queued governance proposals | Governance |
| Actions Framework YAML | Auto-trigger on schema change events | Orchestration |

## Statistical Computation

| Algorithm | Complexity | Purpose |
|-----------|------------|---------|
| PSI (Population Stability Index) | O(n × bins) | Feature drift detection |
| KS-Test | O((n+m)log(n+m)) | Distribution shift detection |
| Schema Diff | O(n+m) | Before/after column comparison |
| BFS Lineage | O(V+E) | Multi-hop lineage traversal |
| DFS Lineage | O(V+E) | Deep graph exploration |
| Topological Sort | O(V+E) | Pipeline dependency ordering |
| Cycle Detection | O(V+E) | Graph validation |
| Shortest Path | O(V+E) | Fastest propagation path |
| Connected Components | O(V+E) | Lineage grouping |
| Union-Find | O(α(n)) | Connectivity queries |
| Trie | O(m) | Entity prefix search |

## Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| Landing | `/` | Product overview, hero, features, integrations |
| Dashboard | `/dashboard` | Analytics, resolution times, cost tracking |
| Models | `/models` | ML model health scores, investigation triggers |
| Playbooks | `/playbooks` | Reflexion playbooks, flywheel visualization |
| Compliance | `/compliance` | EU AI Act audit trail, PII scanning |
| Incident Detail | `/incidents/[id]` | Investigation timeline, evidence chain |
| Docs Overview | `/docs` | Documentation home, problem/solution |
| Quick Start | `/docs/getting-started` | Setup instructions, CLI commands |
| Architecture | `/docs/architecture` | System design, workers, validation |
| Features | `/docs/features` | All capabilities explained |
| Security | `/docs/security` | EU AI Act, SHA-256, validation |
| API Reference | `/docs/api` | REST endpoints, MCP tools, CLI |
| For Judges | `/docs/judges` | Verification guide, key files |

## CLI Commands

| Command | Description |
|---------|-------------|
| `meridian investigate <model_urn>` | Run full investigation |
| `meridian health <model_urn>` | Check model health score |
| `meridian playbook <pattern_id>` | View reflexion playbook |
| `meridian seed` | Seed demo data |
| `meridian serve --port 8000` | Start API server |
