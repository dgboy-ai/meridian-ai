# Example: /datahub-meridian-ai:investigate-model

## Input
```
/datahub-meridian-ai:investigate-model urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)
```

## Output
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

Investigation complete. Generated: 2026-07-12 09:39 UTC
```

## What Happened Behind the Scenes

1. **Data Sentinel** read schema metadata via `list_schema_fields` and detected the INT→STRING change
2. **Root Cause** traversed 5 hops of lineage via `get_lineage` to find 3 affected models and 12 dashboards
3. **Knowledge Writer** wrote 4 artifacts:
   - Root cause report to Knowledge Base (`save_document`)
   - AI Knowledge panel to model entity (`addStructuredProperties`)
   - Updated playbook to Knowledge Base (`save_document`)
   - Incident record to Incidents API (`raiseIncident`)
