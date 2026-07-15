---
name: datahub-meridian-ai
version: 1.0.0
description: |
  AI Reliability Engineer for production ML models.
  Investigates incidents, writes root cause reports, updates model entities.
  Uses DataHub's lineage graph to trace failures and writes knowledge back.
author: meridian-ai
license: Apache-2.0
tags:
  - ml-observability
  - incident-response
  - root-cause-analysis
  - lineage
  - knowledge-management
---

# datahub-meridian-ai

AI Reliability Engineer for production ML models. Investigates incidents, writes root cause reports, and updates model entities with operational knowledge.

## Commands

### /datahub-meridian-ai:investigate-model [model_urn]

Triggers a full investigation workflow:
1. **Detect** — Data Sentinel checks for schema changes, freshness violations
2. **Diagnose** — Root Cause traverses lineage to find why the model degraded
3. **Validate** — Deterministic layer verifies confidence and safety
4. **Write-back** — Knowledge Writer persists root cause report, playbook, and AI Knowledge panel

**Example:**
```
/datahub-meridian-ai:investigate-model urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)
```

**Output:**
```
Investigation initiated for churn_model_v3

[Data Sentinel] Schema change detected: raw_events.age INT → STRING
  Confidence: 0.94 · Severity: HIGH

[Root Cause] Lineage traversal complete: 3 models, 12 dashboards affected
  Confidence: 0.96

[Knowledge Writer] 4 artifacts written to DataHub:
  ✓ Root cause report → Knowledge Base
  ✓ AI Knowledge panel → churn_model_v3 entity
  ✓ Playbook updated → Knowledge Base
  ✓ Incident #42 raised → Incidents API

Investigation complete in 3 minutes.
```

### /datahub-meridian-ai:check-health [model_urn]

Returns ML health score with supporting signals:
- Data Quality (freshness, completeness, schema stability)
- Drift Magnitude (feature drift, concept drift)
- Prediction Quality (accuracy, calibration)
- Latency (p50, p95, p99)
- Confidence rating across all signals

**Example:**
```
/datahub-meridian-ai:check-health urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)
```

**Output:**
```
churn_model_v3 · Health Score: 81 · Confidence: 97%

Data Quality     ████████░░  0.72
Drift Magnitude  ██████░░░░  0.61
Prediction       █████████░  0.91
Latency          █████████░  0.94

Known failure patterns: 3
Resolved incidents: 14
Last investigation: 2026-07-12 09:31 UTC
```

### /datahub-meridian-ai:view-playbook [pattern_id]

Retrieves the latest reflexion playbook for a failure pattern. Playbooks improve after every incident — this is cumulative intelligence in action.

**Example:**
```
/datahub-meridian-ai:view-playbook schema-change-type-mismatch
```

**Output:**
```
# Playbook: Schema Change → Model Degradation
Pattern ID: schema-change-type-mismatch
Confidence: 0.96 · Based on: incidents #12, #28, #42

## Detection signals
- Column type change in upstream dataset
- Feature pipeline success with silent type coercion
- Model accuracy drop 2–4 hours after pipeline run

## Fastest resolution (learned from 3 incidents)
1. Identify changed column via list_schema_fields diff (2 min)
2. Trace to affected feature via get_lineage (3 min)
3. Roll back model to last known-good version (2 min)
4. Patch feature pipeline type casting (5 min)
Total: ~12 min first occurrence. ~3 min with this playbook.

## Incident history
- Incident #12: 18 min resolution (playbook created)
- Incident #28: 8 min (playbook referenced)
- Incident #42: 3 min (pattern matched instantly)
```

## Installation

```bash
# From the datahub-skills repository
pip install datahub-meridian-ai

# Or from source
git clone https://github.com/trueboy1123/meridian-ai
cd meridian-ai/skill/datahub-meridian-ai
pip install -e .
```

## Configuration

Set the following environment variables:

```bash
export DATAHUB_GMS_URL=http://localhost:8080/api/gms
export DATAHUB_GMS_TOKEN=your-token
export GROQ_API_KEY=your-groq-key  # Optional, for live LLM analysis
```

## How It Works

1. **Reads from DataHub** — schema metadata, lineage graph, entity details, past playbooks
2. **Analyzes with LLM** — root cause analysis, drift detection, pattern matching
3. **Writes back to DataHub** — root cause reports, AI Knowledge panels, playbooks, incidents
4. **Learns from every incident** — reflexion loop improves playbooks after each resolution

## License

Apache 2.0
