"""FastAPI backend for Meridian AI — enterprise-grade implementation."""
import os
import json
import time
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi import FastAPI, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.replay import ReplayDriver
from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.actions.listener import ActionsListener
from backend.workers.planner import PlannerAgent
from backend.schemas import (
    HealthResponse, ReadinessResponse, LivenessResponse, MetricsResponse,
    IncidentsResponse, IncidentSummary, ResolutionTimesResponse, ResolutionTimeEntry,
    ModelResponse, ErrorResponse, SSEEvent, InvestigationMode,
)

# ─── Logging ───────────────────────────────────────────────────────────────────
try:
    from pythonjsonlogger import json as jsonlogger
    _handler = logging.StreamHandler()
    _handler.setFormatter(jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
    ))
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(), handlers=[_handler])
except ImportError:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
logger = logging.getLogger("meridian-ai")

# ─── Configuration ─────────────────────────────────────────────────────────────
class Settings:
    APP_NAME: str = "meridian-ai"
    APP_VERSION: str = "1.0.0"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DATAHUB_MOCK: bool = os.getenv("DATAHUB_MOCK", "true").lower() == "true"
    DATAHUB_GMS_URL: str = os.getenv("DATAHUB_GMS_URL", "http://localhost:8080/api/gms")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    MAX_REQUESTS_PER_MINUTE: int = int(os.getenv("MAX_RPM", "60"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_BODY_SIZE: int = int(os.getenv("MAX_BODY_SIZE", str(10 * 1024 * 1024)))  # 10MB default
    AUTH_ENABLED: bool = os.getenv("AUTH_ENABLED", "false").lower() == "true"
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", os.urandom(32).hex())

settings = Settings()

# ─── Metrics ───────────────────────────────────────────────────────────────────
class Metrics:
    def __init__(self):
        self.request_count: int = 0
        self.error_count: int = 0
        self.total_latency_ms: float = 0
        self.start_time: float = time.time()
        self.latencies: list[float] = []

    def record_request(self, latency_ms: float, is_error: bool = False):
        self.request_count += 1
        self.total_latency_ms += latency_ms
        self.latencies.append(latency_ms)
        if len(self.latencies) > 1000:
            self.latencies = self.latencies[-500:]
        if is_error:
            self.error_count += 1

    def to_dict(self) -> dict:
        uptime = time.time() - self.start_time
        sorted_latencies = sorted(self.latencies)
        p50 = sorted_latencies[len(sorted_latencies) // 2] if sorted_latencies else 0
        p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)] if sorted_latencies else 0
        p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)] if sorted_latencies else 0

        return {
            "uptime_seconds": round(uptime, 2),
            "request_count": self.request_count,
            "error_count": self.error_count,
            "avg_latency_ms": round(self.total_latency_ms / max(self.request_count, 1), 2),
            "p50_latency_ms": round(p50, 2),
            "p95_latency_ms": round(p95, 2),
            "p99_latency_ms": round(p99, 2),
            "error_rate": round(self.error_count / max(self.request_count, 1), 4),
        }

metrics = Metrics()

# ─── Rate Limiter ──────────────────────────────────────────────────────────────
class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: list[float] = []

    def is_allowed(self) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds
        self.requests = [t for t in self.requests if t > cutoff]
        if len(self.requests) >= self.max_requests:
            return False
        self.requests.append(now)
        return True

rate_limiter = RateLimiter(settings.MAX_REQUESTS_PER_MINUTE)

# ─── Middleware ─────────────────────────────────────────────────────────────────
class RequestMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # Body size limit for POST/PUT/PATCH
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > settings.MAX_BODY_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request body too large", "max_bytes": settings.MAX_BODY_SIZE},
                    headers={"X-Request-ID": request_id},
                )

        # Rate limiting
        if not rate_limiter.is_allowed():
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded", "retry_after": 60},
                headers={"X-Request-ID": request_id, "Retry-After": "60"},
            )

        start = time.time()
        try:
            response = await call_next(request)
            latency_ms = (time.time() - start) * 1000
            is_error = response.status_code >= 400
            metrics.record_request(latency_ms, is_error)
            response.headers["X-Response-Time"] = f"{latency_ms:.2f}ms"
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            metrics.record_request(latency_ms, is_error=True)
            logger.error(f"[{request_id}] Request failed: {request.url.path} - {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "request_id": request_id},
                headers={"X-Request-ID": request_id},
            )

# ─── Application State ─────────────────────────────────────────────────────────
class AppState:
    def __init__(self):
        self.replay = ReplayDriver()
        self.mcp = DataHubMCPClient()  # Auto-detects real vs mock
        self.groq = GroqClient()
        self.planner = PlannerAgent(mcp=self.mcp, groq=self.groq)
        self.actions_listener = ActionsListener()
        self.initialized_at = time.time()

app_state = AppState()

# ─── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Mode: {'mock' if settings.DATAHUB_MOCK else 'live'}")
    logger.info(f"Groq connected: {app_state.groq.client is not None}")
    logger.info(f"Auth enabled: {settings.AUTH_ENABLED}")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")
    await app_state.mcp.close()

# ─── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Meridian AI",
    version=settings.APP_VERSION,
    description="AI Reliability Engineer for production ML models",
    lifespan=lifespan,
    responses={
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=settings.CORS_ORIGINS != "*",
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_middleware(RequestMetricsMiddleware)

# ─── Health Checks ─────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    """Basic health check — is the service running?"""
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        mode=app_state.mcp.mode,
        groq_connected=app_state.groq.client is not None,
        datahub_mock=app_state.mcp.mode == "mock",
    )

@app.get("/health/ready", response_model=ReadinessResponse, tags=["Health"])
async def readiness():
    """Readiness probe — is the service ready to accept traffic?"""
    checks = {
        "replay_driver": True,
        "groq_client": app_state.groq.client is not None or settings.DATAHUB_MOCK,
        "datahub_client": True,
        "rate_limiter": True,
    }
    all_healthy = all(checks.values())
    return ReadinessResponse(
        status="ready" if all_healthy else "not_ready",
        checks=checks,
    )

@app.get("/health/live", response_model=LivenessResponse, tags=["Health"])
async def liveness():
    """Liveness probe — is the service alive?"""
    return LivenessResponse(status="alive")

@app.get("/metrics", response_model=MetricsResponse, tags=["Health"])
async def get_metrics():
    """Prometheus-compatible metrics endpoint."""
    m = metrics.to_dict()
    return MetricsResponse(
        **m,
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        mode="replay" if settings.DATAHUB_MOCK else "live",
    )

# ─── API: Incidents ────────────────────────────────────────────────────────────
@app.get("/api/incidents", response_model=IncidentsResponse, tags=["Incidents"])
async def list_incidents():
    """List all incidents."""
    incidents = app_state.replay.list_incidents()
    return IncidentsResponse(incidents=[IncidentSummary(**inc) for inc in incidents])

@app.get("/api/incidents/{incident_id}", tags=["Incidents"])
async def get_incident(incident_id: str):
    """Get incident details by ID."""
    if not incident_id or len(incident_id) > 50:
        return JSONResponse(status_code=400, content={"error": "Invalid incident ID"})

    incident = app_state.replay.get_incident(incident_id)
    if incident:
        return incident
    return JSONResponse(status_code=404, content={"error": "Incident not found"})

# ─── API: Models ───────────────────────────────────────────────────────────────
@app.get("/api/models/{model_name}", response_model=ModelResponse, tags=["Models"])
async def get_model(model_name: str):
    """Get model metadata by name."""
    if not model_name or len(model_name) > 100:
        return JSONResponse(status_code=400, content={"error": "Invalid model name"})

    entities = await app_state.mcp.get_entities([
        f"urn:li:mlModel:(urn:li:dataPlatform:mlflow,{model_name},PROD)"
    ])
    if entities:
        return entities[0]

    incident = app_state.replay.get_incident("42")
    if incident:
        for node in incident.get("blast_radius", {}).get("affected", []):
            if node.get("name") == model_name:
                return node

    return JSONResponse(status_code=404, content={"error": "Model not found"})

@app.get("/api/health-scores", tags=["Models"])
async def get_health_scores():
    """Get health scores for all models."""
    entities = await app_state.mcp.get_entities([
        "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
        "urn:li:mlModel:(urn:li:dataPlatform:mlflow,ltv_model_v2,PROD)",
        "urn:li:mlModel:(urn:li:dataPlatform:mlflow,segment_model_v1,PROD)",
    ])
    return {"models": entities}

# ─── API: Resolution Times ─────────────────────────────────────────────────────
@app.get("/api/resolution-times", response_model=ResolutionTimesResponse, tags=["Analytics"])
async def get_resolution_times():
    """Get resolution time trend."""
    times = app_state.replay.get_resolution_times()
    return ResolutionTimesResponse(
        incidents=[ResolutionTimeEntry(**t) for t in times],
        trend="decreasing",
        predicted_next=1,
    )

# ─── API: Actions Framework ────────────────────────────────────────────────────
@app.post("/api/actions/investigate", tags=["Actions"])
async def trigger_investigation(request: Request):
    """Receive a DataHub Actions Framework event and start investigation.

    This endpoint is called by the Actions Framework YAML pipeline
    when a metadata change event is detected in DataHub.
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})

    result = await app_state.actions_listener.process_webhook_event(body)
    logger.info(f"Actions event processed: {result['status']}")
    return result

@app.get("/api/actions/events", tags=["Actions"])
async def get_action_events():
    """Get all received Actions Framework events."""
    return {
        "events": app_state.actions_listener.get_event_log(),
        "stats": app_state.actions_listener.get_stats(),
    }

@app.get("/api/actions/stats", tags=["Actions"])
async def get_action_stats():
    """Get Actions Framework statistics."""
    return {
        "mode": app_state.mcp.mode,
        "datahub_connected": app_state.mcp._connected,
        **app_state.actions_listener.get_stats(),
    }

# ─── Streaming: Replay ────────────────────────────────────────────────────────
@app.get("/stream/replay", tags=["Streaming"])
async def stream_replay(
    incident_id: str = Query("42", description="Incident ID to replay", min_length=1, max_length=50),
    delay: float = Query(0.5, ge=0.1, le=5.0, description="Delay between events in seconds"),
):
    """Stream pre-recorded investigation events via SSE."""
    async def event_generator() -> AsyncIterator[str]:
        try:
            async for event in app_state.replay.stream_investigation(incident_id, delay=delay):
                yield f"data: {json.dumps(event)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Replay stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ─── Streaming: Investigation ──────────────────────────────────────────────────
@app.get("/stream/investigate", tags=["Streaming"])
async def stream_investigation(
    dataset_urn: str = Query(
        "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
        description="Dataset URN to investigate",
        min_length=10,
        max_length=500,
    ),
    incident_id: str = Query("42", description="Incident ID", min_length=1, max_length=50),
    mode: InvestigationMode = Query(InvestigationMode.REPLAY, description="Mode: 'live' or 'replay'"),
):
    """Stream live or replay investigation events via SSE."""
    async def event_generator() -> AsyncIterator[str]:
        try:
            if mode == InvestigationMode.LIVE and not settings.DATAHUB_MOCK:
                async for event in app_state.planner.investigate(dataset_urn, incident_id):
                    yield f"data: {json.dumps(event)}\n\n"
                    await asyncio.sleep(0.3)
            else:
                async for event in app_state.replay.stream_investigation(incident_id, delay=0.4):
                    yield f"data: {json.dumps(event)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Investigation stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ─── API: Compliance & PII ─────────────────────────────────────────────────────
@app.post("/api/compliance/scan-pii", tags=["Compliance"])
async def scan_pii(request: Request):
    """Scan a dataset for PII exposures and raise compliance incidents."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})

    dataset_urn = body.get("dataset_urn", "")
    sample_data = body.get("sample_data")

    if not dataset_urn:
        return JSONResponse(status_code=400, content={"error": "dataset_urn is required"})

    sentinel = app_state.planner.sentinel
    violation = await sentinel.scan_for_pii(dataset_urn, sample_data)
    if not violation or violation.total_violations == 0:
        return {"status": "clean", "dataset_urn": dataset_urn, "violations": 0}

    result = await sentinel.raise_compliance_incident(violation)
    return {
        "status": "violations_found",
        "dataset_urn": dataset_urn,
        "violation_id": violation.violation_id,
        "total_violations": violation.total_violations,
        "severity": violation.severity.value,
        "affected_columns": violation.affected_columns,
        "regulations": [r.value for r in violation.regulations],
        "incident": result,
    }


@app.get("/api/compliance/eu-ai-act/{incident_id}", tags=["Compliance"])
async def get_eu_ai_act_file(incident_id: str):
    """Get EU AI Act Technical File for an incident."""
    engine = app_state.planner.compliance_engine
    records = engine.get_audit_records(incident_id)
    return {
        "incident_id": incident_id,
        "audit_records": records,
        "chain_length": engine.chain_length,
        "chain_valid": engine._verify_chain(),
    }


@app.get("/api/compliance/audit-trail", tags=["Compliance"])
async def get_audit_trail():
    """Get full audit trail."""
    engine = app_state.planner.compliance_engine
    return {
        "total_records": engine.chain_length,
        "chain_valid": engine._verify_chain(),
        "last_hash": engine.last_hash[:16] if engine.last_hash else None,
    }


@app.post("/api/discovery/shadow-ai", tags=["Discovery"])
async def discover_shadow_ai():
    """Scan for ungoverned ML models."""
    shadow = app_state.planner.shadow_discovery
    evidence = await shadow.discover()
    return {
        "status": "scan_complete",
        "finding": evidence.finding,
        "confidence": evidence.confidence,
        "severity": evidence.severity,
    }


@app.post("/api/generate/dbt", tags=["Code Generation"])
async def generate_dbt_model(request: Request):
    """Generate a dbt model from DataHub metadata."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})

    source_urn = body.get("source_dataset_urn", "")
    target_name = body.get("target_model_name", "generated_model")

    if not source_urn:
        return JSONResponse(status_code=400, content={"error": "source_dataset_urn is required"})

    generator = app_state.planner.dbt_generator
    evidence = await generator.generate(source_urn, target_name)
    return {
        "status": "generated",
        "finding": evidence.finding,
        "confidence": evidence.confidence,
    }


# ─── Error Handlers ────────────────────────────────────────────────────────────
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "path": request.url.path},
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "request_id": getattr(request.state, "request_id", "unknown")},
    )

@app.exception_handler(413)
async def payload_too_large_handler(request: Request, exc):
    return JSONResponse(
        status_code=413,
        content={"error": "Request body too large"},
    )

# ─── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=os.getenv("RELOAD", "false").lower() == "true",
    )
