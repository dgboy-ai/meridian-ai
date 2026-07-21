# Playbook: Schema Change to Model Degradation
Pattern ID: schema-change-type-mismatch
Based on: incident #42
Resolution time: 0.0 minutes
Health score at detection: 89

## Detection signals
- Column type change in upstream dataset
- Feature pipeline success with silent type coercion
- Model accuracy drop 2-4 hours after pipeline run

## Fastest resolution (learned from incidents)
1. Identify changed column via schema diff (2 min)
2. Trace to affected feature via lineage (3 min)
3. Roll back model to last known-good version (2 min)
4. Patch feature pipeline type casting (5 min)

## Incident history
- Incident #42: 0.0 min (this investigation)

## Pattern Statistics
- Confidence: 17 mutations
- Workers fired: 17
