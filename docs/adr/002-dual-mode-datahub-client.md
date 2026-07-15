# ADR 002: Dual-Mode DataHub Client (Mock/Real)

**Status:** Accepted
**Date:** 2026-07-14

## Context

Meridian AI needs DataHub metadata for investigations, but requiring a running DataHub instance for all development and demos creates friction. Developers need to work offline, and hackathon demos must work without infrastructure.

## Decision

Implement a single `DataHubMCPClient` that auto-detects real vs mock mode at startup and provides the same async API for both.

## How It Works

1. On instantiation, the client probes `DATAHUB_GMS_URL/health` with a synchronous HTTP request
2. If GMS responds 200, all subsequent calls go through async httpx to real GMS
3. If GMS is unreachable, the client uses in-memory mock data (hardcoded entities, lineage, etc.)
4. `DATAHUB_MOCK=true` forces mock mode; `DATAHUB_MOCK=false` forces real mode with probe

## Mock Data

Mock entities include:
- 3 datasets (raw_events, feature_pipeline, feature_store)
- 3 ML models (churn_model_v3, ltv_model_v2, segment_model_v1)
- Full lineage graph between them
- Pre-seeded schemas, queries, documents

All mutations (tags, incidents, structured properties) are tracked in-memory during mock sessions.

## Consequences

- **Positive**: Zero-config local development, reliable hackathon demos, CI runs without Docker
- **Positive**: Same API surface means no conditional logic in workers or planner
- **Negative**: Mock data is static; drift detection / schema change detection is deterministic
- **Mitigated**: Real DataHub integration tests exist in `tests/integration/` using docker-compose

## Auth Modes

- **PAT** (default): `DATAHUB_GMS_TOKEN` Bearer header
- **Service Account**: `DATAHUB_AUTH_MODE=service_account`

## Version Detection

The client detects DataHub version from `/config` and checks mutation tool support (requires v0.5.0+). Unsupported mutations fall back to mock with a warning.
