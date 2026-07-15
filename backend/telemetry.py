"""OpenTelemetry Spans — distributed tracing for each worker.

"Add OTEL spans for each worker" enables debugging in production.

This module provides:
  1. Span creation for each worker invocation
  2. Attribute recording for key metrics
  3. Error recording for failed operations
  4. Span context propagation across async boundaries

Based on OpenTelemetry Python SDK patterns.
"""
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from contextlib import contextmanager

logger = logging.getLogger("meridian-ai.telemetry")


@dataclass
class SpanAttributes:
    """Attributes for an OpenTelemetry span."""
    worker_id: str = ""
    incident_id: str = ""
    dataset_urn: str = ""
    model_urn: str = ""
    confidence: float = 0.0
    severity: str = ""
    duration_ms: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "worker_id": self.worker_id,
            "incident_id": self.incident_id,
            "dataset_urn": self.dataset_urn,
            "model_urn": self.model_urn,
            "confidence": self.confidence,
            "severity": self.severity,
            "duration_ms": round(self.duration_ms, 2),
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "cost_usd": round(self.cost_usd, 6),
            "error": self.error,
        }


@dataclass
class Span:
    """A single tracing span."""
    span_id: str
    name: str
    start_time: float
    end_time: float = 0.0
    attributes: SpanAttributes = field(default_factory=SpanAttributes)
    events: list[dict] = field(default_factory=list)
    status: str = "OK"
    parent_span_id: str = ""

    def end(self):
        """End the span."""
        self.end_time = time.time()

    def set_status(self, status: str):
        """Set span status."""
        self.status = status

    def add_event(self, name: str, attributes: dict | None = None):
        """Add an event to the span."""
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })

    def set_attribute(self, key: str, value):
        """Set a span attribute."""
        setattr(self.attributes, key, value)

    def record_exception(self, exception: Exception):
        """Record an exception on the span."""
        self.set_status("ERROR")
        self.attributes.error = str(exception)
        self.add_event("exception", {
            "exception.type": type(exception).__name__,
            "exception.message": str(exception),
        })

    def to_dict(self) -> dict:
        return {
            "span_id": self.span_id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": round((self.end_time - self.start_time) * 1000, 2) if self.end_time else 0,
            "attributes": self.attributes.to_dict(),
            "events": self.events,
            "status": self.status,
            "parent_span_id": self.parent_span_id,
        }


class TracingProvider:
    """OpenTelemetry-compatible tracing provider.

    In production, this would integrate with the OpenTelemetry SDK.
    For now, it provides a local tracing implementation.
    """

    def __init__(self, service_name: str = "meridian-ai"):
        self.service_name = service_name
        self._spans: list[Span] = []
        self._span_counter = 0

    def _generate_span_id(self) -> str:
        """Generate a unique span ID."""
        self._span_counter += 1
        return f"span-{self._span_counter:06d}"

    @contextmanager
    def start_span(
        self,
        name: str,
        parent_span_id: str = "",
        attributes: SpanAttributes | None = None,
    ):
        """Start a new span.

        Usage:
            with tracing.start_span("worker_name") as span:
                span.set_attribute("worker_id", "data_sentinel")
                # Do work
                span.add_event("completed", {"result": "success"})
        """
        span = Span(
            span_id=self._generate_span_id(),
            name=name,
            start_time=time.time(),
            parent_span_id=parent_span_id,
            attributes=attributes or SpanAttributes(),
        )
        self._spans.append(span)

        try:
            yield span
            span.set_status("OK")
        except Exception as e:
            span.record_exception(e)
            raise
        finally:
            span.end()

    def start_span_async(
        self,
        name: str,
        parent_span_id: str = "",
        attributes: SpanAttributes | None = None,
    ) -> Span:
        """Start a span without context manager (for async code)."""
        span = Span(
            span_id=self._generate_span_id(),
            name=name,
            start_time=time.time(),
            parent_span_id=parent_span_id,
            attributes=attributes or SpanAttributes(),
        )
        self._spans.append(span)
        return span

    def end_span(self, span: Span):
        """End a span started with start_span_async."""
        span.end()

    def get_spans(self) -> list[dict]:
        """Get all recorded spans."""
        return [s.to_dict() for s in self._spans]

    def get_span_by_id(self, span_id: str) -> Span | None:
        """Get a span by its ID."""
        for span in self._spans:
            if span.span_id == span_id:
                return span
        return None

    def get_trace_summary(self) -> dict:
        """Get a summary of the trace."""
        if not self._spans:
            return {"total_spans": 0}

        total_duration = max(s.end_time for s in self._spans if s.end_time) - min(s.start_time for s in self._spans)
        error_spans = [s for s in self._spans if s.status == "ERROR"]

        return {
            "total_spans": len(self._spans),
            "total_duration_ms": round(total_duration * 1000, 2),
            "error_spans": len(error_spans),
            "avg_span_duration_ms": round(
                sum((s.end_time - s.start_time) * 1000 for s in self._spans if s.end_time) / max(len(self._spans), 1),
                2,
            ),
            "spans": [s.to_dict() for s in self._spans],
        }

    def clear(self):
        """Clear all recorded spans."""
        self._spans.clear()
        self._span_counter = 0


# Global tracing provider instance
tracing = TracingProvider()
