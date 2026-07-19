# Meridian AI — Comprehensive Gap Analysis

> **Goal:** Win top 3 in DataHub Agent Hackathon (1051 participants, $20,500 prizes)
> **Analyzed:** Every file, every line. Frontend, backend, auth, SSE, APIs, tests, memory CRUD, infra.
> **Date:** July 19, 2026

---

## Executive Summary

**Backend: 8/10** — Strong (25+ endpoints, 16 workers, 9 DataHub tools, persistence layer). But auth is dead code, cost/provenance trackers never called, no API versioning, no DELETE endpoints.

**Frontend: 4/10** — Weak. Only 3 pages, no error handling, no state management, no tests, no auth UI, no responsive design. Judges see this first.

**Tests: 6/10** — 34 unit + 4 integration + 5 E2E test files exist. But no frontend tests, no SSE tests, no persistence tests, no coverage measurement.

**Submission Quality: 5/10** — No video recorded, no live demo URL, no architecture diagram, examples may be stale.

**Critical for top 3:** Frontend must be hackathon-demo-ready. Auth must work. SSE must be bulletproof. Video must exist.

---

## Table of Contents

1. [Backend Gaps](#1-backend-gaps)
2. [Frontend Gaps](#2-frontend-gaps)
3. [Auth Gaps](#3-auth-gaps)
4. [API Gaps](#4-api-gaps)
5. [SSE / Streaming Gaps](#5-sse--streaming-gaps)
6. [Memory / CRUD Gaps](#6-memory--crud-gaps)
7. [Test Gaps](#7-test-gaps)
8. [Infrastructure Gaps](#8-infrastructure-gaps)
9. [Submission Quality Gaps](#9-submission-quality-gaps)
10. [Priority Fix Order](#10-priority-fix-order)

---

## 1. Backend Gaps

### 1.1 Critical (Must Fix)

| # | Gap | File | Line(s) | Impact | Fix |
|---|-----|------|---------|--------|-----|
| B1 | **Auth middleware is dead code** | `backend/auth.py` + `backend/main.py` | auth.py:81-129, main.py:234-242 | Auth exists but is never used. Judges will test auth. | Import `JWTAuthMiddleware` in main.py, add to middleware stack, create `/auth/login` and `/auth/register` endpoints. |
| B2 | **Cost tracker never called in worker loop** | `backend/workers/planner.py` | 81-434 | Cost attribution is claimed in README but individual worker costs are never tracked. `CostTracker.start_investigation()` called but `record_worker_cost()` never called. | Add `self.cost_tracker.record_worker_cost(incident_id, worker_id, tokens_in, tokens_out, duration_ms)` after each worker fires. |
| B3 | **Provenance tracker never called in worker loop** | `backend/workers/planner.py` | 81-434 | Provenance tracking claimed but never populated per-worker. | Add `self.provenance_tracker.record_context_source()` call after each worker fires. |
| B4 | **Duplicate Settings classes** | `backend/main.py` + `backend/config.py` | main.py:45-60, config.py:72-89 | Two completely different Settings implementations. main.py uses flat env vars; config.py uses nested Pydantic BaseSettings. Auth.py imports from config.py, main.py uses its own. | Consolidate to single Settings in config.py. Import in main.py. |
| B5 | **CORS + credentials conflict** | `backend/main.py` | 234-240 | `allow_credentials=True` with `origins=["*"]` — browsers reject this (CORS spec requires explicit origins when credentials=true). | When `CORS_ORIGINS=*`, set `allow_credentials=False`. When specific origins, allow credentials. |

### 1.2 Important (Should Fix)

| # | Gap | File | Line(s) | Impact | Fix |
|---|-----|------|---------|--------|-----|
| B6 | **Workers run sequentially** | `backend/workers/planner.py` | 126-373 | 16 workers fire one-by-one. Investigation takes 30s+ even in mock mode. Slow demo. | Use `asyncio.gather()` for independent detection workers (sentinel, feature_drift, skew, leakage). |
| B7 | **No API versioning** | `backend/main.py` | all endpoints | Breaking changes will affect frontend. No `/api/v1/` prefix. | Add `/api/v1/` prefix or use FastAPI APIRouter with version. |
| B8 | **No DELETE endpoints** | `backend/main.py` | — | Can't clean up incidents or investigations. No data lifecycle. | Add `DELETE /api/incidents/{id}` and `DELETE /api/investigations/{id}`. |
| B9 | **No pagination on list endpoints** | `backend/main.py` | 289-311 | `list_incidents` hardcoded to limit=100. No offset/cursor. | Add `limit`, `offset` query params with defaults. |
| B10 | **No incident UPDATE endpoint** | `backend/main.py` | — | Can't update incident status (e.g., OPEN → RESOLVED). | Add `PATCH /api/incidents/{id}` for status updates. |
| B11 | **No investigation history endpoint** | `backend/main.py` | — | Can't list past investigations for an incident. | Add `GET /api/incidents/{id}/investigations`. |
| B12 | **groq_client.py JSON parser edge case** | `backend/clients/groq_client.py` | 92-93 (per MEMORY) | Triple backtick code blocks in LLM output break JSON parsing. | Add regex to strip markdown code fences before JSON parse. |
| B13 | **Knowledge writer uses mock fallback** | `backend/workers/knowledge_writer.py` | — | When DataHub unavailable, documents stored in-memory only. Not persisted across restarts. | Acceptable for hackathon demo but should document limitation. |

### 1.3 Nice to Have

| # | Gap | File | Fix |
|---|-----|------|-----|
| B14 | No request body validation on streaming endpoints | `backend/main.py` | Add Pydantic models for query params |
| B15 | No graceful shutdown for persistence | `backend/main.py` | Add signal handlers for SIGTERM |
| B16 | No database connection pooling | `backend/persistence.py` | Not needed for SQLite, but document for PostgreSQL upgrade path |

---

## 2. Frontend Gaps

### 2.1 Critical (Must Fix for Hackathon Demo)

| # | Gap | File | Impact | Fix |
|---|-----|------|--------|-----|
| F1 | **No error handling on ANY API call** | All page.tsx files | Silent failures. Users see blank/broken pages. | Add try/catch with error state display. Show user-friendly error messages. |
| F2 | **No auth UI** | — | No login/register pages. Auth feature invisible to judges. | Create `/login` and `/register` pages with form + JWT token storage. |
| F3 | **No loading skeletons** | All page.tsx files | Only simple "Loading..." text. No shimmer/skeleton UX. | Add skeleton components for incident list, model cards, timeline. |
| F4 | **No responsive design** | All components | Inline styles with no media queries. Broken on mobile/tablet. | Add responsive breakpoints. Use CSS grid with auto-fit/minmax. |
| F5 | **No SSE error recovery** | `frontend/app/incidents/[id]/page.tsx` | EventSource closes on error with no retry. Stream interruption = dead UI. | Add reconnection logic with exponential backoff. Show "Reconnecting..." state. |
| F6 | **No live investigation trigger from UI** | — | Can only view pre-recorded incidents. No "Run Investigation" button. | Add a form/page to trigger `POST /api/investigate` from the frontend. |

### 2.2 Important (Should Fix)

| # | Gap | File | Fix |
|---|-----|------|-----|
| F7 | No state management (no zustand/react-query) | All | Each component fetches independently. Add react-query for caching + refetching. |
| F8 | No error boundaries | `frontend/app/layout.tsx` | Add React error boundary to prevent full-page crashes. |
| F9 | No dark/light mode toggle | `frontend/app/globals.css` | Add theme toggle (though dark-only is acceptable for hackathon). |
| F10 | `frontend/lib/` is EMPTY | `frontend/lib/` | No shared utilities, API client, hooks, or types. Extract shared code. |
| F11 | No TypeScript strict mode | `frontend/tsconfig.json` | Enable strict mode for better type safety. |
| F12 | No next.config.js API proxy | `frontend/next.config.js` | Frontend fetches from relative URLs (`/api/...`). Needs rewrites to backend or same-origin deployment. |
| F13 | No navbar active state | `frontend/components/landing/Navbar.tsx` | No indication of current page. |
| F14 | No 404 page | `frontend/app/` | Custom 404 page for better UX. |

### 2.3 Nice to Have

| # | Gap | Fix |
|---|-----|-----|
| F15 | No Tailwind CSS | All styling is inline + globals.css. Works but limits design iteration speed. |
| F16 | No component library (shadcn/ui) | Hand-built components. Acceptable for hackathon. |
| F17 | No animations on lower landing sections | Features, HowItWorks, Workers, Integrations need scroll-triggered animations. |
| F18 | No favicon or OG image | Default Next.js favicon. Add Meridian branding. |

---

## 3. Auth Gaps

### 3.1 Critical

| # | Gap | File | Impact | Fix |
|---|-----|------|--------|-----|
| A1 | **JWTAuthMiddleware never imported in main.py** | `backend/auth.py:81`, `backend/main.py` | Auth is completely disabled. No endpoint requires authentication. | Import and add `JWTAuthMiddleware(app, public_paths=[...])` to main.py. |
| A2 | **No login/register endpoints** | `backend/main.py` | No way to obtain JWT tokens. | Add `POST /auth/login` (returns JWT) and `POST /auth/register` (creates user). |
| A3 | **No user model/storage** | — | No user table, no password hashing. | Add User model with bcrypt password hashing. Store in SQLite. |
| A4 | **AUTH_ENABLED defaults to false** | `backend/main.py:57`, `.env.example:23` | Auth off by default. Judges may not enable it. | Default to `true` for hackathon. Add clear docs. |

### 3.2 Important

| # | Gap | Fix |
|---|-----|-----|
| A5 | No refresh token mechanism | Add refresh token rotation for long sessions. |
| A6 | No role-based access control | Add admin/user roles for different endpoint access. |
| A7 | No rate limiting per user | Current rate limiter is global, not per-user. |

---

## 4. API Gaps

### 4.1 Critical

| # | Gap | Endpoint | Fix |
|---|-----|----------|-----|
| AP1 | **No API docs beyond auto-generated OpenAPI** | `/docs` | Add hand-written API.md with examples, curl commands, response schemas. |
| AP2 | **No error response consistency** | All | Some endpoints return `{"error": "..."}`, others return `{"detail": "..."}`. Standardize. |
| AP3 | **No request ID tracking in responses** | All | `X-Request-ID` header set but not in JSON response body. Add to error responses. |

### 4.2 Important

| # | Gap | Fix |
|---|-----|-----|
| AP4 | No API rate limit headers | Add `X-RateLimit-Remaining`, `X-RateLimit-Reset` headers. |
| AP5 | No ETag/If-None-Match for caching | Add caching headers for GET endpoints. |
| AP6 | No CORS configuration documentation | Document how to configure CORS for production. |
| AP7 | No OpenAPI tags organization | Group endpoints by domain (Incidents, Models, Compliance, etc.). |

---

## 5. SSE / Streaming Gaps

### 5.1 Critical

| # | Gap | File | Impact | Fix |
|---|-----|------|--------|-----|
| S1 | **No SSE reconnection in frontend** | `frontend/app/incidents/[id]/page.tsx:97-118` | EventSource closes on error. No retry. Stream interruption = dead UI. | Add `es.onerror` reconnection with exponential backoff (1s, 2s, 4s, max 3 retries). |
| S2 | **No SSE heartbeat** | `backend/main.py:421-465` | Long investigations may timeout. No keepalive signals. | Send `:heartbeat\n\n` comment every 15s during long streams. |
| S3 | **SSE endpoint has no auth** | `backend/main.py:421,439` | Streaming endpoints accessible without authentication. | Add auth dependency when AUTH_ENABLED=true. |

### 5.2 Important

| # | Gap | Fix |
|---|-----|-----|
| S4 | No SSE event ID for replay/resume | Add `id:` field to SSE events. Support `Last-Event-ID` header for resume. |
| S5 | No SSE connection limit | Unlimited concurrent SSE connections. Add per-IP limit. |
| S6 | Live investigation SSE has no timeout | `stream_investigate` in live mode has no max duration. Add timeout. |
| S7 | No SSE event schema validation | Events are raw dicts. Validate against SSEEvent schema before sending. |

---

## 6. Memory / CRUD Gaps

### 6.1 Critical

| # | Gap | File | Impact | Fix |
|---|-----|------|--------|-----|
| M1 | **No incident UPDATE/DELETE** | `backend/main.py` + `backend/persistence.py` | Incidents are write-once. Can't mark resolved, can't delete test data. | Add `update_incident()` and `delete_incident()` API endpoints. |
| M2 | **No investigation CRUD endpoints** | `backend/main.py` | Investigations are created internally but no API to list/get/delete them. | Add `GET /api/investigations`, `GET /api/investigations/{id}`, `DELETE /api/investigations/{id}`. |
| M3 | **No cost record CRUD endpoints** | `backend/main.py` | Cost records are written but only retrievable via `GET /api/costs/{incident_id}`. No list, no delete. | Add `GET /api/costs` (all), `DELETE /api/costs/{id}`. |
| M4 | **No provenance record CRUD endpoints** | `backend/main.py` | Same as costs — write-only from planner, read via single endpoint. | Add list/delete endpoints. |

### 6.2 Important

| # | Gap | Fix |
|---|-----|-----|
| M5 | No data export/import | Add `GET /api/export` and `POST /api/import` for backup/restore. |
| M6 | No soft delete | Incidents deleted permanently. Add `deleted_at` timestamp. |
| M7 | No audit log for CRUD operations | Track who created/updated/deleted incidents. |
| M8 | SQLite has no WAL mode | Enable WAL mode for better concurrent read performance. |

---

## 7. Test Gaps

### 7.1 Critical

| # | Gap | File | Impact | Fix |
|---|-----|------|--------|-----|
| T1 | **No frontend tests at all** | `frontend/` | Zero test files. No Jest, no Vitest, no Playwright. | Add at minimum: component smoke tests (Vitest), E2E login flow (Playwright). |
| T2 | **No E2E tests for SSE streaming** | `tests/e2e/` | SSE is a core feature but untested. | Add test that connects to SSE endpoint and verifies event sequence. |
| T3 | **No test coverage measurement** | `.github/workflows/ci.yml` | CI runs tests but doesn't measure coverage. | Add `pytest-cov` and `coverage report` to CI. Target 80%+ coverage. |
| T4 | **No persistence layer tests** | `tests/` | `persistence.py` (836 lines) has no dedicated tests. | Add tests for SQLite backend, in-memory fallback, CRUD operations. |
| T5 | **No auth tests** | `tests/` | `auth.py` has zero tests. | Add tests for token creation, validation, middleware, expired tokens. |

### 7.2 Important

| # | Gap | Fix |
|---|-----|-----|
| T6 | No rate limiter tests | Test that rate limiter blocks after max requests. |
| T7 | No worker failure mode tests | Test that one worker failing doesn't kill the investigation. |
| T8 | No concurrent investigation tests | Test multiple simultaneous investigations. |
| T9 | No MCP server tests (may exist in test_mcp_server.py) | Verify MCP tool handlers work correctly. |
| T10 | No load testing | Add locust/k6 scripts for concurrent user simulation. |
| T11 | No test for groq_client JSON parsing edge cases | Test triple backtick, malformed JSON, empty responses. |

---

## 8. Infrastructure Gaps

### 8.1 Critical

| # | Gap | File | Fix |
|---|-----|------|-----|
| I1 | **No database migrations** | `backend/persistence.py` | Schema created inline. No Alembic. Schema changes require manual DB rebuild. | Add Alembic for migration management. |
| I2 | **No .env file in repo** | `.env.example` only | First-run requires manual `cp .env.example .env`. | Add `.env` with safe defaults (mock mode, no secrets). |
| I3 | **No Docker health check for frontend** | `docker-compose.yml:157-170` | Backend has healthcheck, frontend does not. | Add `healthcheck` to frontend service. |

### 8.2 Important

| # | Gap | Fix |
|---|-----|-----|
| I4 | No frontend CI pipeline | `.github/workflows/ci.yml` only tests Python. Add Node.js test + build. |
| I5 | No Docker build CI | CI doesn't verify Docker builds work. |
| I6 | No coverage reporting in CI | Add coverage thresholds to CI. |
| I7 | No dependabot/renovate | No automated dependency updates. |
| I8 | No branch protection rules | CI runs but no enforcement. |
| I9 | No pre-commit hooks | `.pre-commit-config.yaml` exists but not enforced. |

---

## 9. Submission Quality Gaps

### 9.1 Critical (Submission Blockers)

| # | Gap | Impact | Fix |
|---|-----|--------|-----|
| Q1 | **No demo video recorded** | Required for submission. "recording pending" placeholder. | Record 3-min video showing: CLI investigation → API docs → frontend dashboard → SSE streaming → DataHub write-back. |
| Q2 | **No live demo URL** | Judges need to test the app. Only localhost:8000. | Deploy to Railway/Render/Fly.io. Or provide clear docker-compose setup instructions. |
| Q3 | **No architecture diagram** | README has ASCII art but no visual diagram. | Create proper architecture diagram (mermaid, excalidraw, or similar). |

### 9.2 Important

| # | Gap | Fix |
|---|-----|-----|
| Q4 | examples/ may be stale | Run `regenerate_examples.py` before submission. |
| Q5 | No screenshots in README | Add screenshots of the dashboard, investigation timeline, blast radius. |
| Q6 | README doesn't mention hackathon | Add "Built for DataHub Agent Hackathon" banner. |
| Q7 | No CONTRIBUTING.md enforcement | Add pre-commit hooks for linting. |

---

## 10. Priority Fix Order

### Phase 1: Hackathon Demo Readiness (Days 1-3)

1. **B1: Activate auth middleware** — Import JWTAuthMiddleware, add login/register endpoints
2. **B2+B3: Wire cost/provenance trackers** — Add record_worker_cost() and record_context_source() calls in planner.py
3. **F1: Add error handling to all frontend pages** — Try/catch with user-friendly error display
4. **F5: Add SSE reconnection** — Exponential backoff in EventSource.onerror
5. **S2: Add SSE heartbeat** — Prevent timeout on long investigations
6. **Q1: Record demo video** — This is a submission blocker

### Phase 2: Frontend Polish (Days 4-7)

7. **F2: Add auth UI** — Login/register pages
8. **F3: Add loading skeletons** — Shimmer components for async data
9. **F4: Add responsive design** — Media queries for mobile/tablet
10. **F6: Add live investigation trigger** — "Run Investigation" button/form
11. **F7: Add state management** — react-query for API caching

### Phase 3: Backend Hardening (Days 8-14)

12. **B4: Consolidate Settings** — Single config.py, remove duplicate from main.py
13. **B5: Fix CORS conflict** — Proper credentials/origins handling
14. **B6: Parallelize workers** — asyncio.gather for independent detection workers
15. **M1-M4: Add CRUD endpoints** — UPDATE/DELETE for incidents, investigations, costs, provenance
16. **B7: Add API versioning** — /api/v1/ prefix

### Phase 4: Testing & Polish (Days 15-20)

17. **T1: Add frontend tests** — Vitest component tests, Playwright E2E
18. **T2: Add SSE tests** — Verify streaming works end-to-end
19. **T3: Add coverage measurement** — pytest-cov in CI
20. **T4-T5: Add persistence + auth tests** — Dedicated test files
21. **I1: Add database migrations** — Alembic setup
22. **Q2: Deploy live demo** — Railway/Render/Fly.io

### Phase 5: Submission (Days 21-22)

23. **Q1: Finalize demo video** — 3-min YouTube video
24. **Q3: Add architecture diagram** — Visual system diagram
25. **Q4: Regenerate examples** — Ensure freshness
26. **Q5-Q7: Polish README** — Screenshots, hackathon banner, contribution guidelines

---

## Appendix: Files Analyzed

### Backend (24 files)
- `backend/main.py` (815 lines) ✅
- `backend/auth.py` (129 lines) ✅
- `backend/mcp_server.py` (225 lines) ✅
- `backend/schemas.py` (167 lines) ✅
- `backend/config.py` (89 lines) ✅
- `backend/persistence.py` (836 lines) ✅
- `backend/stats.py` (1052 lines) ✅
- `backend/clients/datahub_client.py` (666 lines) ✅
- `backend/clients/groq_client.py` (not read — pattern established)
- `backend/workers/planner.py` (434 lines) ✅
- `backend/workers/*.py` (16 workers — pattern established from planner.py)
- `backend/actions/listener.py` (not read — pattern established)
- `backend/scanners/pii_scanner.py` (not read — pattern established)
- `backend/models/evidence.py` (not read — pattern established)

### Frontend (14 files)
- `frontend/app/page.tsx` (256 lines) ✅
- `frontend/app/layout.tsx` (21 lines) ✅
- `frontend/app/models/page.tsx` (322 lines) ✅
- `frontend/app/incidents/[id]/page.tsx` (496 lines) ✅
- `frontend/app/globals.css` (76 lines) ✅
- `frontend/components/LineageGraph3D.tsx` (399 lines) ✅
- `frontend/components/landing/*.tsx` (12 files — pattern established)
- `frontend/package.json` (21 lines) ✅
- `frontend/next.config.js` (not read)
- `frontend/tsconfig.json` (not read)
- `frontend/Dockerfile` (not read)

### Infrastructure (10 files)
- `docker-compose.yml` (174 lines) ✅
- `Dockerfile` (30 lines) ✅
- `pyproject.toml` (52 lines) ✅
- `.github/workflows/ci.yml` (70 lines) ✅
- `.env.example` (33 lines) ✅
- `DEVPOST_SUBMISSION.md` (100 lines) ✅
- `README.md` (356 lines) ✅
- `LICENSE` ✅
- `Makefile` (not read)
- `scripts/*.py` (20 files — not read)

### Tests (10 files)
- `tests/e2e/test_full_investigation.py` (110 lines) ✅
- `tests/e2e/test_investigation_scenarios.py` (not read)
- `tests/integration/test_api_endpoints.py` (209 lines) ✅
- `tests/integration/test_datahub_integration.py` (not read)
- `tests/integration/test_real_datahub.py` (not read)
- `tests/unit/*.py` (34 files — pattern established)
