# Changelog

All notable changes to Meridian AI will be documented in this file.

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
- Test count: 359 → 511 (+152 tests)
- All features now use real data flows where possible

## [1.0.0] - 2026-07-01

### Added
- Initial release
- 21 workers with structured evidence objects
- DataHub MCP integration (dual-mode: real + mock)
- EU AI Act compliance engine
- Reflexion loop for cumulative intelligence
- Health score calculator
- Progressive autonomy system
- Cost attribution tracking
- Provenance tracking
- Agentic circuit breaker
