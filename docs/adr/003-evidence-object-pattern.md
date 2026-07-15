# ADR 003: EvidenceObject Pattern for Worker Outputs

**Status:** Accepted
**Date:** 2026-07-14

## Context

Meridian AI has 15+ analysis workers (DataSentinel, FeatureDrift, RootCause, etc.) that each produce findings. Without a common output schema, the planner must handle ad-hoc dicts, validation is fragile, and downstream consumers (KnowledgeWriter, EU AI Act compliance, Reflexion) can't reliably extract structured data.

## Decision

Every worker must return an `EvidenceObject` — a Pydantic model with a fixed schema.

## Schema

```python
class EvidenceObject(BaseModel):
    worker_id: str           # e.g. "data_sentinel"
    timestamp: str           # ISO 8601 UTC
    finding: str             # Human-readable summary
    confidence: float        # 0.0-1.0
    severity: Severity       # low | medium | high | critical
    evidence: list[EvidenceItem]  # Typed evidence items
    business_impact: Optional[BusinessImpact]
    next_action: Optional[str]
    datahub_mutations: list[DataHubMutation]  # Queued mutations
```

Evidence items are typed:
```python
class EvidenceItem(BaseModel):
    type: str               # "schema_diff", "lineage_impact", etc.
    description: Optional[str]
    before: Optional[dict]  # State before change
    after: Optional[dict]   # State after change
    entity_urn: Optional[str]
    downstream_count: Optional[int]
    affected_models: Optional[list[str]]
```

## Consequences

- **Positive**: Uniform interface for planner to aggregate, validate, and forward findings
- **Positive**: Validation layer can check confidence thresholds and severity escalation rules
- **Positive**: KnowledgeWriter and EU AI Act compliance engine extract structured data without parsing
- **Positive**: `datahub_mutations` field lets workers queue DataHub writes without direct client access
- **Positive**: Reflexion loop compares resolution times against worker confidence scores
- **Trade-off**: Workers must construct EvidenceObject explicitly (more boilerplate than returning a dict)

## Usage in Planner

The `PlannerAgent` collects EvidenceObjects from each worker phase:
1. **Detection** — DataSentinel, FeatureDrift, TrainingServingSkew, DataLeakage
2. **Diagnosis** — RootCause (uses detection evidence as input)
3. **Validation** — ValidationLayer checks EvidenceObject fields
4. **Verification** — VerifierAgent challenges RootCause conclusion
5. **Enforcement** — KnowledgeWriter writes back to DataHub

Each worker is wrapped in `fire_worker()` which catches exceptions and yields status events, ensuring one worker failure doesn't kill the investigation.
