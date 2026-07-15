"""Structured JSON logging configuration for FastAPI."""

from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Request-scoped correlation ID
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

# ---------------------------------------------------------------------------
# JSON formatter (falls back to stdlib Formatter when python-json-logger is
# absent so the rest of the codebase never needs a try/except).
# ---------------------------------------------------------------------------

try:
    from pythonjsonlogger import json as _json  # python-json-logger >=3.x

    class _JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_entry = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "request_id": request_id_var.get("-"),
            }
            if record.exc_info and record.exc_info[0] is not None:
                log_entry["exception"] = self.formatException(record.exc_info)
            return _json.dumps(log_entry, default=str)

except ImportError:
    # python-json-logger not installed — fall back to plain text with request_id.
    class _JsonFormatter(logging.Formatter):  # type: ignore[no-redef]
        def format(self, record: logging.LogRecord) -> str:
            base = super().format(record)
            rid = request_id_var.get("-")
            return f"[{rid}] {base}"


# ---------------------------------------------------------------------------
# Public setup helpers
# ---------------------------------------------------------------------------


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with JSON output to stderr."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


# ---------------------------------------------------------------------------
# FastAPI middleware — injects a unique request_id into every log line
# ---------------------------------------------------------------------------


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Attaches a ``request_id`` context variable for each incoming request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        rid = request.headers.get("X-Request-ID", uuid.uuid4().hex)
        token = request_id_var.set(rid)

        logger = get_logger("http")
        logger.info("%s %s", request.method, request.url.path)

        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Unhandled exception")
            raise
        finally:
            logger.info(
                "%s %s -> %s", request.method, request.url.path, response.status_code
            )
            request_id_var.reset(token)

        response.headers["X-Request-ID"] = rid
        return response
