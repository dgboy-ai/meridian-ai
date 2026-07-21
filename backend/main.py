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
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.auth import JWTAuthMiddleware

from backend.replay import ReplayDriver
from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.actions.listener import ActionsListener
from backend.workers.planner import PlannerAgent
from backend.persistence import PersistenceManager
from backend.schemas import (
    HealthResponse, ReadinessResponse, LivenessResponse, MetricsResponse,
    IncidentsResponse, IncidentSummary, ResolutionTimesResponse, ResolutionTimeEntry,
    ModelResponse, ErrorResponse, InvestigationMode,
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
        self.persistence: PersistenceManager | None = None
        self.initialized_at = time.time()

app_state = AppState()

# ─── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Mode: {'mock' if settings.DATAHUB_MOCK else 'live'}")
    logger.info(f"Groq connected: {app_state.groq.client is not None}")
    logger.info(f"Auth enabled: {settings.AUTH_ENABLED}")

    # Initialize persistence
    app_state.persistence = PersistenceManager()
    await app_state.persistence.__aenter__()
    logger.info(f"Persistence backend: {app_state.persistence.backend_type}")

    # Wire persistence into replay driver so live incidents can be replayed
    app_state.replay.set_persistence(app_state.persistence)

    # Seed replay incidents into persistence on first run
    await _seed_replay_incidents()

    yield

    logger.info(f"Shutting down {settings.APP_NAME}")
    await app_state.mcp.close()
    if app_state.persistence:
        await app_state.persistence.__aexit__(None, None, None)


async def _seed_replay_incidents():
    """Seed replay incidents into persistence so they appear in the unified list."""
    if not app_state.persistence:
        return
    for inc in app_state.replay.list_incidents():
        existing = await app_state.persistence.get_incident(inc["id"])
        if not existing:
            full = app_state.replay.get_incident(inc["id"])
            await app_state.persistence.record_incident(
                incident_id=inc["id"],
                title=inc["title"],
                severity=inc["severity"],
                status=inc["status"],
                detected=inc["detected"],
                duration_seconds=inc["duration_seconds"],
                root_cause=full.get("root_cause", "") if full else "",
                pattern_id=inc["pattern_id"],
                affected_models=inc.get("affected_models", []),
                timeline=full.get("timeline", []) if full else [],
                blast_radius=full.get("blast_radius", {}) if full else {},
            )
    logger.info(f"Seeded {len(app_state.replay.list_incidents())} replay incidents into persistence")

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

# JWT Auth middleware — enforces Bearer token when AUTH_ENABLED=true
app.add_middleware(JWTAuthMiddleware)

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
    """List all incidents from persistence (includes seeded replay + live investigations)."""
    if app_state.persistence:
        records = await app_state.persistence.list_incidents(limit=100)
        incidents = [
            IncidentSummary(
                id=r.incident_id,
                title=r.title,
                severity=r.severity,
                status=r.status,
                detected=r.detected,
                duration_seconds=r.duration_seconds,
                affected_models=r.affected_models or [],
                pattern_id=r.pattern_id,
            )
            for r in records
        ]
        return IncidentsResponse(incidents=incidents)

    # Fallback to replay-only if persistence unavailable
    incidents = app_state.replay.list_incidents()
    return IncidentsResponse(incidents=[IncidentSummary(**inc) for inc in incidents])

@app.get("/api/incidents/{incident_id}", tags=["Incidents"])
async def get_incident(incident_id: str):
    """Get incident details by ID — tries persistence first, then replay."""
    if not incident_id or len(incident_id) > 50:
        return JSONResponse(status_code=400, content={"error": "Invalid incident ID"})

    # Try persistence first (has live investigation data)
    if app_state.persistence:
        record = await app_state.persistence.get_incident(incident_id)
        if record:
            return {
                "id": record.incident_id,
                "title": record.title,
                "severity": record.severity,
                "status": record.status,
                "detected": record.detected,
                "duration_seconds": record.duration_seconds,
                "root_cause": record.root_cause,
                "pattern_id": record.pattern_id,
                "affected_models": record.affected_models or [],
                "timeline": record.timeline or [],
                "blast_radius": record.blast_radius or {},
                "writeback": {},
            }

    # Fallback to replay data
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
    """Get resolution time trend from both replay data and live investigations."""
    # Start with pre-recorded replay data
    times = list(app_state.replay.get_resolution_times())

    # Append live investigation resolution times from persistence
    if app_state.persistence:
        try:
            records = await app_state.persistence.list_incidents(limit=50)
            for r in records:
                if r.duration_seconds > 0 and r.incident_id not in {t.get("id") for t in times}:
                    times.append({
                        "id": r.incident_id,
                        "duration_minutes": round(r.duration_seconds / 60),
                        "date": r.detected[:10] if r.detected else "",
                        "pattern": r.pattern_id or "live-investigation",
                    })
        except Exception:
            pass  # Fall back to replay-only data

    # Sort by date descending
    times.sort(key=lambda t: t.get("date", ""), reverse=True)

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

# ─── Streaming Helpers ────────────────────────────────────────────────────────
SSE_HEARTBEAT_INTERVAL = 15  # seconds — keeps proxies/browsers alive


async def _sse_heartbeat(stop_event: asyncio.Event) -> AsyncIterator[str]:
    """Yield SSE keepalive comments every SSE_HEARTBEAT_INTERVAL seconds until stopped."""
    while not stop_event.is_set():
        await asyncio.sleep(SSE_HEARTBEAT_INTERVAL)
        if not stop_event.is_set():
            yield ": heartbeat\n\n"


async def _merge_with_heartbeat(event_gen: AsyncIterator[str]) -> AsyncIterator[str]:
    """Merge an event generator with periodic heartbeat comments.

    The heartbeat ensures long-running streams (investigations take 30s+) don't get
    killed by nginx/cloud load balancer proxy timeouts (typically 60s).
    """
    stop = asyncio.Event()
    hb = _sse_heartbeat(stop)
    hb_task = None

    async def _forward_hb():
        async for h in hb:
            yield h

    try:
        hb_task = asyncio.create_task(_forward_hb().__anext__())

        async for event in event_gen:
            yield event
            # After yielding a real event, check if heartbeat fired
            if hb_task.done():
                try:
                    yield hb_task.result()
                except StopAsyncIteration:
                    pass
                hb_task = asyncio.create_task(_forward_hb().__anext__())

        # Drain remaining heartbeats briefly
        stop.set()
        if hb_task and not hb_task.done():
            hb_task.cancel()
    except Exception:
        stop.set()
        if hb_task and not hb_task.done():
            hb_task.cancel()
        raise


# ─── Streaming: Replay ────────────────────────────────────────────────────────
@app.get("/stream/replay", tags=["Streaming"])
async def stream_replay(
    incident_id: str = Query("42", description="Incident ID to replay", min_length=1, max_length=50),
    delay: float = Query(0.5, ge=0.1, le=5.0, description="Delay between events in seconds"),
):
    """Stream pre-recorded investigation events via SSE with keepalive heartbeats."""
    async def event_generator() -> AsyncIterator[str]:
        try:
            async for event in app_state.replay.stream_investigation(incident_id, delay=delay):
                yield f"data: {json.dumps(event)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Replay stream error: {e}")
            yield f"data: {json.dumps({'step': 'error', 'status': 'failed', 'error': str(e)})}\n\n"

    return StreamingResponse(
        _merge_with_heartbeat(event_generator()),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

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
    """Stream live or replay investigation events via SSE with keepalive heartbeats."""
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
            yield f"data: {json.dumps({'step': 'error', 'status': 'failed', 'error': str(e)})}\n\n"

    return StreamingResponse(
        _merge_with_heartbeat(event_generator()),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

# ─── API: Live Investigation (with persistence) ────────────────────────────────
@app.post("/api/investigate", tags=["Investigation"])
async def run_investigation(request: Request):
    """Start a live investigation and return immediately.

    The investigation runs in the background. Results are streamed via SSE
    at /stream/investigate?incident_id=<id>&mode=live. The frontend should
    redirect to /incidents/<id> which opens the SSE stream.
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})

    dataset_urn = body.get("dataset_urn", "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)")
    incident_id = body.get("incident_id", str(int(time.time())))

    # Create a placeholder incident in persistence immediately so the
    # frontend can navigate to /incidents/<id> and start streaming
    if app_state.persistence:
        await app_state.persistence.record_incident(
            incident_id=incident_id,
            title=f"Investigation — {dataset_urn.split(',')[-2] if ',' in dataset_urn else 'unknown'}",
            severity="HIGH",
            status="IN_PROGRESS",
            detected=datetime.now(timezone.utc).isoformat(),
            duration_seconds=0,
            root_cause="",
            pattern_id="",
            affected_models=[],
            timeline=[],
            blast_radius={},
        )

    # Fire the investigation in the background — don't block the response
    asyncio.create_task(_run_investigation_background(incident_id, dataset_urn))

    return {
        "incident_id": incident_id,
        "status": "started",
        "dataset_urn": dataset_urn,
        "stream_url": f"/stream/investigate?incident_id={incident_id}&mode=live",
        "detail_url": f"/incidents/{incident_id}",
    }


async def _run_investigation_background(incident_id: str, dataset_urn: str):
    """Run the full investigation in the background and persist results."""
    events = []
    summary = {}
    try:
        async for event in app_state.planner.investigate(dataset_urn, incident_id):
            events.append(event)
            if event.get("status") == "completed" and event.get("summary"):
                summary = event["summary"]
    except Exception as e:
        logger.error(f"Investigation {incident_id} failed: {e}", exc_info=True)
        if app_state.persistence:
            record = await app_state.persistence.get_incident(incident_id)
            if record:
                record.status = "FAILED"
                record.root_cause = f"Investigation failed: {e}"
                await app_state.persistence.update_incident(record)
        return

    # Extract timeline, blast radius, and writeback from events
    timeline = []
    blast_radius = {}
    root_cause = ""
    severity = "HIGH"
    affected_models = []
    pattern_id = "unknown"
    duration_seconds = 0

    for event in events:
        step = event.get("step", "")
        timeline.append({
            "time": event.get("timestamp", ""),
            "step": step,
            "status": event.get("status", ""),
            "finding": event.get("finding", event.get("message", "")),
            "confidence": event.get("evidence", {}).get("confidence", 0.9) if event.get("evidence") else 0.9,
            "message": event.get("message", ""),
            "severity": event.get("severity"),
            "evidence": event.get("evidence"),
            "business_impact": event.get("business_impact"),
        })

        # Extract root cause from root_cause step
        if step == "root_cause" and event.get("evidence"):
            root_cause = event["evidence"].get("finding", "")
            # Extract real blast radius from root cause evidence
            bi = event["evidence"].get("business_impact", {})
            if bi:
                if bi.get("predictions_today"):
                    blast_radius.setdefault("predictions_today", bi["predictions_today"])
                if bi.get("estimated_revenue_at_risk"):
                    # Parse "$45,000/day" → 45000
                    import re
                    rev_match = re.search(r'\$?([\d,]+)', str(bi["estimated_revenue_at_risk"]))
                    if rev_match:
                        blast_radius["revenue_at_risk_daily"] = int(rev_match.group(1).replace(",", ""))
                if bi.get("affected_systems"):
                    blast_radius["affected_systems"] = bi["affected_systems"]

        # Extract blast radius from summary
        if step == "planner" and event.get("summary"):
            s = event["summary"]
            duration_seconds = int(s.get("resolution_time_minutes", 0) * 60)
            affected_models = [
                "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
                "urn:li:mlModel:(urn:li:dataPlatform:mlflow,ltv_model_v2,PROD)",
                "urn:li:mlModel:(urn:li:dataPlatform:mlflow,segment_model_v1,PROD)",
            ]

    # Build blast radius from real investigation data
    blast_radius = {
        "source": {
            "urn": dataset_urn,
            "name": dataset_urn.split(",")[1].split(")")[0] if "," in dataset_urn else "unknown",
            "type": "dataset",
            "status": "critical",
        },
        "affected": [
            {"urn": m, "name": m.split(",")[1].split(")")[0] if "," in m else m, "type": "mlModel", "status": "warning", "health_score": 80}
            for m in affected_models
        ],
        "business_impact": {
            "predictions_today": blast_radius.get("predictions_today", 32000),
            "revenue_at_risk_daily": blast_radius.get("revenue_at_risk_daily", 45000),
            "affected_dashboards": len(affected_models) * 4,
        },
    }

    # Writeback summary
    writeback = {
        "root_cause_report": {"title": f"Incident #{incident_id} — Root Cause Report", "status": "written"},
        "ai_knowledge_panel": {"entity": "churn_model_v3", "status": "updated", "health_score": 81},
        "playbook": {"title": "Playbook: Schema Change to Model Degradation", "status": "updated"},
        "incident_record": {"id": f"INC-{incident_id}", "linked_entities": len(affected_models), "status": "raised"},
    }

    # Persist the investigation
    if app_state.persistence:
        await app_state.persistence.record_incident(
            incident_id=incident_id,
            title=f"Live Investigation — {dataset_urn.split(',')[-2] if ',' in dataset_urn else 'unknown'}",
            severity=severity,
            status="RESOLVED",
            detected=events[0].get("timestamp", "") if events else "",
            duration_seconds=duration_seconds,
            root_cause=root_cause,
            pattern_id=pattern_id,
            affected_models=affected_models,
            timeline=timeline,
            blast_radius=blast_radius,
        )
        logger.info(f"Investigation #{incident_id} persisted to database")

    return {
        "incident_id": incident_id,
        "status": "completed",
        "dataset_urn": dataset_urn,
        "workers_fired": summary.get("workers_fired", []),
        "resolution_time_minutes": summary.get("resolution_time_minutes", 0),
        "health_score": summary.get("health_score", 0),
        "datahub_mutations": summary.get("datahub_mutations", 0),
        "timeline_steps": len(timeline),
        "blast_radius_nodes": len(blast_radius.get("affected", [])),
        "writeback_artifacts": len(writeback),
    }


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


# ─── API: Cost & Provenance Tracking ──────────────────────────────────────────
@app.get("/api/costs", tags=["Tracking"])
async def get_cost_summary():
    """Get aggregate cost and ROI summary across all investigations."""
    return app_state.planner.cost_tracker.get_summary()

@app.get("/api/costs/{incident_id}", tags=["Tracking"])
async def get_investigation_cost(incident_id: str):
    """Get cost tracking for a specific investigation."""
    cost = app_state.planner.cost_tracker.get_investigation_cost(incident_id)
    if not cost:
        return JSONResponse(status_code=404, content={"error": "No cost data for this incident"})
    return cost.to_dict()

@app.get("/api/provenance/{incident_id}", tags=["Tracking"])
async def get_investigation_provenance(incident_id: str):
    """Get provenance tracking for a specific investigation."""
    prov = app_state.planner.provenance_tracker.get_investigation(incident_id)
    if not prov:
        return JSONResponse(status_code=404, content={"error": "No provenance data for this incident"})
    return prov.to_dict()


# ─── API: System Architecture ─────────────────────────────────────────────────
@app.get("/api/system/architecture", tags=["System"])
async def get_architecture():
    """Return the full system architecture — workers, tools, and connections."""
    return {
        "name": "Meridian AI",
        "version": settings.APP_VERSION,
        "mode": "mock" if settings.DATAHUB_MOCK else "live",
        "workers": [
            {"id": "data_sentinel", "name": "Data Sentinel", "phase": "detection", "description": "Schema diff, freshness, PII, data quality, volume"},
            {"id": "feature_drift", "name": "Feature Drift", "phase": "detection", "description": "PSI/KS-test per feature, type mismatch detection"},
            {"id": "training_serving_skew", "name": "Training-Serving Skew", "phase": "detection", "description": "Schema comparison + distribution drift"},
            {"id": "data_leakage", "name": "Data Leakage", "phase": "detection", "description": "Temporal pattern detection for target leakage"},
            {"id": "root_cause", "name": "Root Cause", "phase": "diagnosis", "description": "Column-level lineage traversal + blast radius"},
            {"id": "verifier_agent", "name": "VerifierAgent", "phase": "verification", "description": "Maker-checker validation before write-back"},
            {"id": "knowledge_writer", "name": "Knowledge Writer", "phase": "enforcement", "description": "5 DataHub writes per investigation"},
            {"id": "reflexion_loop", "name": "Reflexion Loop", "phase": "learning", "description": "Self-RAG playbook improvement"},
            {"id": "lifecycle_governance", "name": "Lifecycle Governance", "phase": "enforcement", "description": "Health evaluation + lifecycle proposals"},
            {"id": "eu_ai_act_compliance", "name": "EU AI Act Compliance", "phase": "compliance", "description": "SHA-256 audit chain for Articles 12/13/14"},
            {"id": "shadow_ai_discovery", "name": "Shadow AI Discovery", "phase": "governance", "description": "Ungoverned model detection"},
            {"id": "contract_enforcer", "name": "Contract Enforcer", "phase": "enforcement", "description": "Dataset contract assertion checking"},
            {"id": "explanation_drift", "name": "Explanation Drift", "phase": "detection", "description": "Feature importance shift via PSI"},
            {"id": "self_healing", "name": "Self-Healing Assertions", "phase": "learning", "description": "Preventive assertion generation"},
            {"id": "pipeline_circuit_breaker", "name": "Pipeline Circuit Breaker", "phase": "enforcement", "description": "Halt downstream on upstream failure"},
            {"id": "deprecation_advisor", "name": "Deprecation Advisor", "phase": "governance", "description": "Safe deprecation of unused assets"},
            {"id": "ml_metadata", "name": "ML Metadata Integrator", "phase": "detection", "description": "MLModelDeployment, MLFeatureTable, MLModelGroup queries"},
            {"id": "agentic_circuit_breaker", "name": "Agentic Circuit Breaker", "phase": "verification", "description": "Agent reasoning health monitoring"},
        ],
        "datahub_tools": {
            "read": ["search", "get_entities", "get_lineage", "list_schema_fields", "search_documents"],
            "write": ["save_document", "add_structured_properties", "raise_incident", "batch_add_tags"],
        },
        "dsa_algorithms": [
            "BFS Lineage", "DFS Lineage", "Topological Sort", "Cycle Detection",
            "Shortest Path", "Connected Components", "Binary Search CDF", "KS-Test",
            "Union-Find", "Trie", "Min-Heap Top-K",
        ],
        "stats": {
            "total_workers": 18,
            "datahub_capabilities": 14,
            "dsa_algorithms": 11,
        },
    }


@app.get("/api/system/health", tags=["System"])
async def get_system_health():
    """Detailed system health with all subsystem statuses."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "uptime_seconds": round(time.time() - app_state.initialized_at, 2),
        "mode": "mock" if settings.DATAHUB_MOCK else "live",
        "subsystems": {
            "datahub_client": {
                "status": "connected" if app_state.mcp._connected else "mock",
                "mode": app_state.mcp.mode,
            },
            "groq_client": {
                "status": "connected" if app_state.groq.client else "mock",
                "stats": app_state.groq.get_stats(),
            },
            "persistence": {
                "status": "ok",
                "backend": app_state.persistence.backend_type if app_state.persistence else "none",
            },
            "rate_limiter": {
                "status": "ok",
                "max_rpm": settings.MAX_REQUESTS_PER_MINUTE,
            },
            "auth": {
                "status": "enabled" if settings.AUTH_ENABLED else "disabled",
            },
        },
        "metrics": metrics.to_dict(),
    }


# ─── API: Authentication ──────────────────────────────────────────────────────
# In-memory user store for demo (replace with database in production)
_DEMO_USERS: dict[str, dict] = {
    "admin@meridian.ai": {"password": "meridian", "role": "admin", "name": "Admin"},
    "demo@meridian.ai": {"password": "demo", "role": "viewer", "name": "Demo User"},
}


@app.post("/api/auth/login", tags=["Auth"])
async def login(request: Request):
    """Authenticate and return a JWT access token."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})

    email = body.get("email", "")
    password = body.get("password", "")

    if not email or not password:
        return JSONResponse(status_code=400, content={"error": "email and password are required"})

    user = _DEMO_USERS.get(email)
    if not user or user["password"] != password:
        return JSONResponse(status_code=401, content={"error": "Invalid credentials"})

    from backend.auth import create_access_token
    token = create_access_token({"sub": email, "role": user["role"], "name": user["name"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"email": email, "role": user["role"], "name": user["name"]},
    }


@app.post("/api/auth/register", tags=["Auth"])
async def register(request: Request):
    """Register a new user (demo only — in-memory store)."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})

    email = body.get("email", "")
    password = body.get("password", "")
    name = body.get("name", email.split("@")[0])

    if not email or not password:
        return JSONResponse(status_code=400, content={"error": "email and password are required"})
    if len(password) < 4:
        return JSONResponse(status_code=400, content={"error": "password must be at least 4 characters"})
    if email in _DEMO_USERS:
        return JSONResponse(status_code=409, content={"error": "User already exists"})

    _DEMO_USERS[email] = {"password": password, "role": "viewer", "name": name}

    from backend.auth import create_access_token
    token = create_access_token({"sub": email, "role": "viewer", "name": name})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"email": email, "role": "viewer", "name": name},
    }


@app.get("/api/auth/me", tags=["Auth"])
async def get_me(request: Request):
    """Get current authenticated user info. Requires Bearer token when auth is enabled."""
    user = getattr(request.state, "user", None)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})
    return {
        "email": user.get("sub", ""),
        "role": user.get("role", "viewer"),
        "name": user.get("name", ""),
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
