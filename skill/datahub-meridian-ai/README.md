# datahub-meridian-ai

AI Reliability Engineer for production ML models. A DataHub Skill that investigates incidents, writes root cause reports, and updates model entities with operational knowledge.

## What It Does

Meridian AI uses DataHub's lineage graph to trace ML failures from source to impact, then writes everything it learns back into DataHub permanently. Every investigation makes the next one faster.

## Commands

| Command | Description |
|---|---|
| `/datahub-meridian-ai:investigate-model [model_urn]` | Full investigation: detect → diagnose → validate → write-back |
| `/datahub-meridian-ai:check-health [model_urn]` | ML health score with 24 supporting signals |
| `/datahub-meridian-ai:view-playbook [pattern_id]` | Latest reflexion playbook for a failure pattern |

## Installation

```bash
pip install datahub-meridian-ai
```

## Quick Start

```python
from datahub_meridian_ai.commands import investigate_model, check_health, view_playbook

# Investigate a model
report = investigate_model("urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)")
print(report)

# Check health
health = check_health("urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)")
print(health)

# View playbook
playbook = view_playbook("schema-change-type-mismatch")
print(playbook)
```

## How It Works

1. **Reads from DataHub** — schema metadata, lineage graph, entity details, past playbooks
2. **Analyzes with LLM** — root cause analysis, drift detection, pattern matching
3. **Writes back to DataHub** — root cause reports, AI Knowledge panels, playbooks, incidents
4. **Learns from every incident** — reflexion loop improves playbooks after each resolution

## DataHub Integration

| Capability | How It's Used |
|---|---|
| `list_schema_fields` | Detect schema changes at column level |
| `get_lineage` | Traverse upstream/downstream impact |
| `get_lineage_paths_between` | Calculate blast radius |
| `search_documents` | Find past playbooks for pattern matching |
| `save_document` | Persist root cause reports and playbooks |
| `addStructuredProperties` | Write AI Knowledge panel to model entities |
| `raiseIncident` | Create incidents programmatically |
| `batchAddTags` | Tag affected assets in bulk |
| `propose_lifecycle_stage` | Propose DEPRECATED for chronically failing models |

## License

Apache 2.0
