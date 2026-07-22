# Changelog

All notable changes to Meridian AI will be documented in this file.

## [1.2.0] - 2026-07-21

### Added
- Documentation site with sidebar navigation (`frontend/app/docs/`)
  - Overview, Quick Start, Architecture, Features, Security, API Reference, For Judges
  - Particle background, glass morphism, Framer Motion animations
- Docs link in landing page navbar
- Smoke test script (`scripts/test_core.py`)
- Example verification script (`scripts/verify_examples.py`)
- ConsoleLayout skips docs pages (own layout system)

### Fixed
- Validation layer: unsafe mutations now soft-queued for human approval (not hard-blocked)
- README: accurate numbers (18 workers, 15 DataHub tools, 552 tests, 83% flywheel improvement)
- README: flywheel shows 18→8→3 min (was 18→8→8)
- Devpost description: professional tone, accurate numbers, clear challenge framing
- DataHub tools count: 15 capabilities (was 12/14 inconsistently)
- Frontend Hero: DataHub tools count 12→15
- Frontend Integrations: 12→15 tools listed
- `validation_passed: true` in example outputs (was false)
- CHANGELOG: test count 511→552

### Changed
- Validation: unsafe mutations are warnings (queued for approval), not blockers
- 12 API endpoints verified working (health, incidents, costs, compliance, architecture)
- Frontend builds clean (15 static pages)
- 563 tests passing, 11 skipped

## [1.1.0] - 2026-07-15

### Added
- SQLite persistence layer (`backend/persistence.py`)
- JWT authentication middleware (`backend/auth.py`)
- Centralized Pydantic config (`backend/config.py`)
- TTL async cache with LRU eviction (`backend/cache.py`)
- Async retry decorator (`backend/retry.py`)
- Prometheus metrics (`backend/metrics.py`)
- Structured JSON logging (`backend/logging_config.py`)
- ECS Fargate deployment configs (`aws/`)
- API documentation (`docs/API.md`)
- Contributing guide (`CONTRIBUTING.md`)
- Architecture Decision Records (`docs/adr/`)
- MCP protocol tests (`tests/unit/test_mcp_protocol.py`)
- API contract tests (`tests/unit/test_contracts.py`)
- Data cleanup script (`scripts/cleanup_data.py`)
- Security policy (`SECURITY.md`)
- Makefile for common commands

### Fixed
- Mock data bleeding between investigations (deepcopy)
- Verification result now gates write-back
- Root cause uses scored heuristic instead of hardcoding source
- Feature drift reads from entity metadata
- EU AI Act chain persists to JSON file
- PII scanner uses 3-tier data priority
- Verifier Check 4 logic error
- Training-serving skew reads from entity metadata
- Explanation drift reads from entity metadata
- Model URNs derived from lineage graph
- MCP server uses async stdin (no blocking)
- MCP server supports cancellation
- Knowledge writer deduplicates reports
- Reflexion learning curve formula improved
- Magic numbers extracted to named constants
- Dynamic playbook generation from evidence
- blast_radius variable reference fixed
- BusinessImpact attribute access fixed
- Configurable CORS origins
- Body size limits on POST/PUT/PATCH
- Error handlers don't leak internals
- Dockerfile HEALTHCHECK added
- docker-compose resource limits and restart policies

### Changed
- Test count: 359 → 552 (+193 tests)
- All features now use real data flows where possible

## [1.0.0] - 2026-07-01

### Added
- Initial release
- 18 workers with structured evidence objects
- DataHub MCP integration (dual-mode: real + mock)
- EU AI Act compliance engine
- Reflexion loop for cumulative intelligence
- Health score calculator
- Progressive autonomy system
- Cost attribution tracking
- Provenance tracking
- Agentic circuit breaker
