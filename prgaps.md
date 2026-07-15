# Meridian AI — Complete Gap Analysis & Honest Audit

Generated: 2026-07-15
Last Updated: 2026-07-15 (Critical fixes applied)

---

## Part 0: Critical Feature Fixes Applied (2026-07-15)

### P1 Fixes (Core Functionality)

| Bug | Fix | File |
|-----|-----|------|
| Mock data bleeding between investigations | `copy.deepcopy` instead of shallow copy + `reset_mock()` | `datahub_client.py` |
| Verification result ignored | Planner now checks verification confidence before write-back | `planner.py` |
| Root cause always = source node | New `compute_root_cause_score` with entity type, downstream impact, schema changes | `root_cause.py` |
| Feature drift uses hardcoded arrays | 3-tier priority: entity metadata → schema-derived → fallback | `feature_drift.py` |
| EU AI Act chain in-memory only | JSON file persistence + full field hashing | `eu_ai_act_compliance.py` |
| PII scanner fed hardcoded data | Priority: entity metadata → hardcoded for known entities → synthetic from fields | `data_sentinel.py` |
| Verifier Check 4 always passes | Removed always-true condition | `verifier_agent.py` |

### P2 Fixes (Production Quality)

| Bug | Fix | File |
|-----|-----|------|
| MCP health uses hardcoded metrics | Computes from real entity metadata | `mcp_server.py` |
| Magic numbers (32000, $1.41) | Extracted to module constants with comments | `stats.py` |
| Hardcoded playbook template | Dynamically generated from root cause evidence | `knowledge_writer.py` |
| Undefined `blast_radius` variable | Extracted from `root_cause_evidence.business_impact` | `planner.py` |
| `BusinessImpact.get()` error | Fixed Pydantic model attribute access + regex parsing | `planner.py` |

### P3 Fixes (Polish & Completeness)

| Bug | Fix | File |
|-----|-----|------|
| Verifier Check 4 always passes | Removed always-true condition | `verifier_agent.py` |
| Training-serving skew hardcoded distributions | 3-tier: entity metadata → schema-derived → fallback | `training_serving_skew.py` |
| Explanation drift hardcoded importance | Reads from entity metadata, derives from reference | `explanation_drift.py` |
| Hardcoded model URNs | Derived from lineage graph, fallback to demo | `planner.py` |
| MCP sync stdin blocking | Async StreamReader with proper try/except | `mcp_server.py` |
| MCP no cancellation support | Added notifications/cancelled handler | `mcp_server.py` |
| Knowledge writer no deduplication | Checks for existing report before writing | `knowledge_writer.py` |

### Additional Fixes

| Fix | File |
|-----|------|
| Reflexion learning curve improved (decay formula) | `reflexion.py` |
| Incident raising conditional on deduplication | `knowledge_writer.py` |
| manual_time_minutes configurable via env var | `planner.py` |
| MCP protocol tests (15 tests) | `tests/unit/test_mcp_protocol.py` |
| API contract tests (18 tests) | `tests/unit/test_contracts.py` |

### Test Results After All Fixes
- 511 tests passing (all pass)
- 0 regressions

---

## Part 1: Infrastructure & Production Gaps (Fixed)

### What Was Fixed

| Gap | Fix | Status |
|-----|-----|--------|
| No persistence layer | SQLite persistence (backend/persistence.py) | ✅ Done |
| No authentication | JWT middleware (backend/auth.py) | ✅ Done |
| No structured logging | JSON logging (backend/logging_config.py) | ✅ Done |
| No metrics | Prometheus (backend/metrics.py) | ✅ Done |
| No caching | TTL async cache (backend/cache.py) | ✅ Done |
| No retry logic | async_retry decorator (backend/retry.py) | ✅ Done |
| CORS `*` | Configurable via CORS_ORIGINS env var | ✅ Done |
| No body size limits | 10MB limit on POST/PUT/PATCH | ✅ Done |
| Error details leaked | Removed internal details from 500 responses | ✅ Done |
| No type annotations | Added to 8 modules + mypy config | ✅ Done |
| No API tests | 71 endpoint tests + 55 unit tests | ✅ Done |
| No deployment configs | ECS Fargate task def + service + deploy script | ✅ Done |
| No documentation | API docs, CONTRIBUTING, 3 ADRs | ✅ Done |
| No Docker resource limits | Added to all services | ✅ Done |
| No Makefile | Common commands for dev workflow | ✅ Done |
| No SECURITY.md | Security policy and reporting | ✅ Done |
| No CHANGELOG.md | Version history and changes | ✅ Done |
| No pre-commit hooks | ruff + mypy + trailing whitespace | ✅ Done |
| No PEP 561 marker | py.typed for type checkers | ✅ Done |
| No data cleanup script | scripts/cleanup_data.py | ✅ Done |

### Test Results
- Before: 359 tests passing
- After: 511 tests passing (+152 new)
- Infrastructure: 28 files created/modified
- Features: 19 critical bug fixes

---

## Part 2: Feature Quality Audit — The Honest Truth

### Feature-by-Feature Assessment

| # | Feature | Real Math? | Real Data? | Production Grade? | Verdict |
|---|---------|-----------|-----------|-------------------|---------|
| 1 | PSI/KS Drift Detection | YES | NO — hardcoded arrays | Demo | FAKE |
| 2 | Schema Diff | YES | PARTIAL — 1 hardcoded baseline | Demo | PARTIAL |
| 3 | PII Scanner | YES | NO — feeds fake records | Demo | PARTIAL |
| 4 | Lineage Traversal | YES | MOCK — 3-edge toy graph | Demo | PARTIAL |
| 5 | Root Cause Analysis | TRIVIAL | NO — always "source node" | Demo | FAKE |
| 6 | EU AI Act SHA-256 | YES | PARTIAL — in-memory only | Near-real | PARTIAL |
| 7 | Verifier Agent | STRUCTURE | NO — Check 4 always passes | Broken | BROKEN |
| 8 | Knowledge Writer | YES | REAL writes | Partial | PARTIAL |
| 9 | Health Score | YES | HARDCODED inputs | Demo | FAKE |
| 10 | MCP Server | YES | MOCK | Partial | PARTIAL |

### Honest Rating: 6/10
Strong architecture, real math, but demo-grade data flow.

---

## Part 3: Critical Bugs Found

### BUG 1: Mock Data Bleeds Between Investigations
- **File**: `backend/clients/datahub_client.py:167`
- **Issue**: `dict(MOCK_ENTITIES)` is a shallow copy. Inner dicts are shared references.
- **Impact**: When `knowledge_writer` adds tags or updates properties, those changes permanently mutate the mock for all future calls. Investigation #2 sees data corrupted by investigation #1.
- **Severity**: HIGH — breaks multi-incident scenarios

### BUG 2: Verification Result Is Ignored
- **File**: `backend/workers/planner.py:216-223`
- **Issue**: The verifier agent runs, produces a result, and the planner never checks it. It always proceeds to write knowledge regardless.
- **Impact**: The maker-checker pattern is decorative. Bad root causes get written to DataHub.
- **Severity**: HIGH — safety check is non-functional

### BUG 3: Root Cause = "The Source Node"
- **File**: `backend/workers/root_cause.py:68`
- **Issue**: The root cause is always `entities_dict.get(source_urn, {})`. No causal inference, no anomaly correlation, no change-point detection.
- **Impact**: The system always says "the thing you pointed at is the cause" — no actual analysis.
- **Severity**: HIGH — core feature is trivial

### BUG 4: Feature Drift Uses Fake Data
- **File**: `backend/workers/feature_drift.py:47-56`
- **Issue**: The PSI/KS math is real, but input arrays are hardcoded:
  ```python
  reference_distributions = [10, 12, 15, 8, 11, ...]  # line 48
  current_distributions = [18, 22, 25, 14, 19, ...]   # line 54
  ```
- **Impact**: Designed to always show drift. No real feature data is ever read.
- **Severity**: HIGH — feature is demo-only

### BUG 5: PII Scanner Fed Fake Data
- **File**: `backend/workers/data_sentinel.py:281-291`
- **Issue**: The scanner is real (real regex), but `_get_sample_data()` returns hardcoded dummy records with `john.doe@example.com` and `123-45-6789`. Only works for entities named `"raw_events"`.
- **Impact**: PII detection never runs on real data.
- **Severity**: MEDIUM — scanner works, data is fake

### BUG 6: EU AI Act Hash Chain Is In-Memory
- **File**: `backend/workers/eu_ai_act_compliance.py:74`
- **Issue**: The audit chain lives in a Python list. Server restart = chain lost.
- **Impact**: For EU AI Act compliance, this would fail a real audit. No persistence.
- **Severity**: HIGH — regulatory compliance gap

### BUG 7: Verifier Check 4 Always Passes
- **File**: `backend/workers/verifier_agent.py:117`
- **Issue**: The condition `len(traversal.downstream_urns) == 0` is in an OR chain, making the whole expression always true when there are 0 downstream entities.
- **Impact**: Verification is weaker than intended — one check is always true.
- **Severity**: MEDIUM — logic error

### BUG 8: `blast_radius` Is Undefined
- **File**: `backend/workers/planner.py:346`
- **Issue**: `blast_radius.get("revenue_at_risk_daily", 0)` references a variable never defined in the `investigate` method. Always evaluates to `0`.
- **Impact**: Cost tracking never records actual revenue at risk.
- **Severity**: MEDIUM — dead code with logic error

### BUG 9: Hardcoded Magic Numbers Everywhere
- `32000` predictions/day — appears in 3+ files
- `$1.41` revenue per prediction — appears in 3 files
- `81` health score fallback — hardcoded
- `0.95, 0.87, 0.96` worker confidences — hardcoded
- **Impact**: Undermines credibility. Judges will notice.
- **Severity**: MEDIUM — presentation issue

### BUG 10: MCP Health Endpoint Uses All Hardcoded Data
- **File**: `backend/mcp_server.py:67-73`
- **Issue**: Every metric is hardcoded. The health endpoint doesn't compute anything real.
- **Impact**: MCP health check is meaningless.
- **Severity**: LOW — demo only

---

## Part 4: What Judges Will See

### Strengths (Genuinely Impressive)
- Architecture is excellent — worker pipeline, evidence objects, validation layer
- PSI/KS/schema-diff math is correct and production-grade
- EU AI Act SHA-256 chain is genuinely implemented
- MCP server protocol is correctly structured
- Dual-mode DataHub client is a good pattern
- Test coverage is thorough (485 tests)
- 21 workers with structured evidence objects
- Reflexion loop for cumulative intelligence

### Weaknesses (What Judges Will Notice)
- Every feature works on hardcoded demo data, not real DataHub data
- Root cause analysis is trivial (source node = cause)
- The verifier doesn't actually gate anything
- Mock data contaminates between runs
- No real feature store integration for drift detection
- EU AI Act chain isn't persisted
- Magic numbers everywhere undermine credibility

---

## Part 5: Priority Fixes Needed

### Priority 1: Core Functionality (Must Fix)
1. Fix mock data bleeding (mutable shared refs in datahub_client.py)
2. Make verification result actually gate write-back in planner.py
3. Derive root cause from lineage graph instead of hardcoding source
4. Make feature drift read from entity metadata instead of hardcoded arrays
5. Persist the EU AI Act chain to DataHub or database

### Priority 2: Data Flow (Should Fix)
6. PII scanner should read sample data from DataHub, not hardcoded records
7. Health score should use real worker outputs, not hardcoded values
8. MCP health endpoint should compute real metrics
9. Extract magic numbers (32000, $1.41, etc.) to config
10. Fix undefined `blast_radius` variable in planner.py

### Priority 3: Polish (Nice to Have)
11. Fix verifier Check 4 logic error
12. Add deduplication to knowledge writer
13. Make model URNs configurable, not hardcoded
14. Fix synchronous stdin reading in MCP server
15. Add cancellation support to MCP server

---

## Part 6: Files That Need Changes

| File | Issues | Priority |
|------|--------|----------|
| backend/clients/datahub_client.py | Mutable mock data, sync probe | P1 |
| backend/workers/planner.py | Ignore verification, undefined blast_radius, hardcoded URNs | P1 |
| backend/workers/root_cause.py | Trivial root cause (always source node) | P1 |
| backend/workers/feature_drift.py | Hardcoded distributions | P1 |
| backend/workers/eu_ai_act_compliance.py | In-memory chain only | P1 |
| backend/workers/verifier_agent.py | Check 4 always passes, dead LLM code | P2 |
| backend/workers/data_sentinel.py | Hardcoded sample data | P2 |
| backend/workers/knowledge_writer.py | Hardcoded playbook template | P2 |
| backend/mcp_server.py | Hardcoded health metrics, sync stdin | P2 |
| backend/stats.py | Hardcoded revenue defaults | P3 |
