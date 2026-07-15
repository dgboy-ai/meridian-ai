"""Prometheus-compatible metrics for DataHub backend."""

from __future__ import annotations

import time

from prometheus_client import Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# ---------------------------------------------------------------------------
# Metric definitions
# ---------------------------------------------------------------------------

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

investigation_total = Counter(
    "investigation_total",
    "Total investigations triggered",
    ["status"],
)

worker_execution_seconds = Histogram(
    "worker_execution_seconds",
    "Worker execution duration in seconds",
    ["worker_type"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

groq_calls_total = Counter(
    "groq_calls_total",
    "Total Groq API calls",
    ["model", "status"],
)

# ---------------------------------------------------------------------------
# FastAPI middleware
# ---------------------------------------------------------------------------


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Records request count and duration for every HTTP call."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        method = request.method
        path = request.url.path

        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start

        http_requests_total.labels(
            method=method, endpoint=path, status_code=response.status_code
        ).inc()
        http_request_duration_seconds.labels(
            method=method, endpoint=path
        ).observe(elapsed)

        return response


# ---------------------------------------------------------------------------
# /metrics endpoint handler (mount in your FastAPI app)
# ---------------------------------------------------------------------------


async def metrics_endpoint(request: Request) -> Response:
    """Return all collected Prometheus metrics as plain text."""
    return Response(
        content=generate_latest(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


# ---------------------------------------------------------------------------
# Convenience helpers for non-HTTP metrics
# ---------------------------------------------------------------------------


def record_investigation(status: str = "success") -> None:
    investigation_total.labels(status=status).inc()


def record_worker_execution(worker_type: str, duration: float) -> None:
    worker_execution_seconds.labels(worker_type=worker_type).observe(duration)


def record_groq_call(model: str, status: str = "success") -> None:
    groq_calls_total.labels(model=model, status=status).inc()
