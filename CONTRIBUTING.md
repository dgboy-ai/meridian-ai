# Contributing to Meridian AI

## Prerequisites

- Python 3.11+
- Docker (for DataHub integration tests)
- Groq API key (free tier at console.groq.com)

## Dev Setup

```bash
# Clone and install
git clone <repo-url> && cd datahub_project
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env — set GROQ_API_KEY for live LLM, leave DATAHUB_MOCK=true for local dev

# Start the server
python -m backend.main
# API docs at http://localhost:8000/docs
```

## Running Tests

```bash
# All tests
python -m pytest tests/ --tb=short -q

# Unit only
python -m pytest tests/unit/ --tb=short -q

# Integration only (needs DataHub or mock mode)
python -m pytest tests/integration/ --tb=short -q

# With coverage
python -m pytest tests/ --cov=backend --cov-report=term-missing
```

## Linting

```bash
ruff check backend/
ruff format backend/
```

Line length: 120. Target: Python 3.11+. CI enforces both.

## Code Style

- **Type hints** on all public functions (3.10+ union syntax: `str | None`)
- **Pydantic** for all request/response schemas and domain models
- **Async/await** for all I/O-bound code (httpx, not requests)
- **EvidenceObject** — every worker returns this; never return raw dicts from workers
- **No `print()`** — use `logging` module, logger per module (`meridian-ai.<name>`)
- **Docstrings** — single line for modules, skip for obvious methods
- **Imports** — stdlib, third-party, local (enforced by ruff)

## Project Structure

```
backend/
  main.py              # FastAPI app, routes, middleware
  clients/             # DataHub + Groq clients (dual-mode)
  workers/             # Analysis workers (schema, drift, root cause, etc.)
  models/              # Pydantic domain models (EvidenceObject, etc.)
  actions/             # DataHub Actions Framework integration
  schemas.py           # API request/response schemas
tests/
  unit/                # Fast, no external deps
  integration/         # May need DataHub mock
  e2e/                 # Full investigation flow
scripts/               # Verification and seed scripts
```

## Adding a Worker

1. Create `backend/workers/your_worker.py`
2. Implement a class with an async method returning `EvidenceObject`
3. Register it in `backend/workers/planner.py`
4. Add tests in `tests/unit/`
5. Wire into the investigation pipeline in `PlannerAgent.investigate()`

```python
from backend.models import EvidenceObject, Severity

class YourWorker:
    def __init__(self, mcp, groq):
        self.mcp = mcp
        self.groq = groq

    async def detect(self, entity_urn: str) -> EvidenceObject:
        # ... your logic
        return EvidenceObject(
            worker_id="your_worker",
            timestamp=datetime.now(timezone.utc).isoformat(),
            finding="...",
            confidence=0.92,
            severity=Severity.HIGH,
        )
```

## PR Process

1. Fork, create a feature branch from `main`
2. Add/modify tests for any changed logic
3. Ensure `ruff check backend/` passes
4. Ensure `pytest tests/ --tb=short -q` passes
5. Open a PR against `main` with a clear description of the change
6. CI runs: lint, unit tests, integration tests, example regeneration check

## Running with Real DataHub

```bash
docker compose up -d          # Starts DataHub + Meridian
# Wait ~90s for DataHub GMS to be healthy
python scripts/seed_meridian.py  # Seed metadata
# DataHub UI: http://localhost:9002 (datahub/datahub)
# Meridian API: http://localhost:8000/docs
```

## CI

GitHub Actions runs on every push/PR to `main`:
- **test** — pytest on Python 3.11/3.12/3.13, worker verification, computation verification
- **lint** — ruff check
- **examples** — regenerate and verify example JSON files
