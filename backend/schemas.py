"""Pydantic schemas for API request/response validation."""
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InvestigationMode(str, Enum):
    LIVE = "live"
    REPLAY = "replay"


# ─── Request Schemas ───────────────────────────────────────────────────────────

class InvestigateRequest(BaseModel):
    """Request schema for investigation endpoint."""
    dataset_urn: str = Field(
        ...,
        description="DataHub URN of the dataset to investigate",
        examples=["urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)"],
        min_length=10,
        max_length=500,
    )
    incident_id: str = Field(
        default="42",
        description="Incident ID for tracking",
        examples=["42"],
        min_length=1,
        max_length=50,
    )
    mode: InvestigationMode = Field(
        default=InvestigationMode.REPLAY,
        description="Investigation mode: 'live' for real DataHub, 'replay' for pre-recorded",
    )

    @field_validator("dataset_urn")
    @classmethod
    def validate_urn(cls, v: str) -> str:
        if not v.startswith("urn:li:"):
            raise ValueError("Dataset URN must start with 'urn:li:'")
        return v


class ReplayRequest(BaseModel):
    """Request schema for replay endpoint."""
    incident_id: str = Field(
        default="42",
        description="Incident ID to replay",
        examples=["42"],
        min_length=1,
        max_length=50,
    )
    delay: float = Field(
        default=0.5,
        description="Delay between events in seconds",
        ge=0.1,
        le=5.0,
    )


# ─── Response Schemas ──────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., examples=["healthy"])
    service: str = Field(..., examples=["meridian-ai"])
    version: str = Field(..., examples=["1.0.0"])
    mode: str = Field(..., examples=["replay"])
    groq_connected: bool
    datahub_mock: bool


class ReadinessResponse(BaseModel):
    """Readiness probe response."""
    status: str = Field(..., examples=["ready"])
    checks: dict[str, bool]


class LivenessResponse(BaseModel):
    """Liveness probe response."""
    status: str = Field(..., examples=["alive"])


class MetricsResponse(BaseModel):
    """Metrics response."""
    uptime_seconds: float
    request_count: int
    error_count: int
    avg_latency_ms: float
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    error_rate: float
    app: str
    version: str
    mode: str


class IncidentSummary(BaseModel):
    """Incident summary for list endpoint."""
    id: str
    title: str
    severity: str
    status: str
    detected: str
    duration_seconds: int
    affected_models: list[str]
    pattern_id: str


class IncidentsResponse(BaseModel):
    """List incidents response."""
    incidents: list[IncidentSummary]


class ResolutionTimeEntry(BaseModel):
    """Resolution time entry."""
    id: str
    duration_minutes: int
    date: str
    pattern: str


class ResolutionTimesResponse(BaseModel):
    """Resolution times response."""
    incidents: list[ResolutionTimeEntry]
    trend: str
    predicted_next: int


class ModelResponse(BaseModel):
    """Model metadata response."""
    urn: str
    name: str
    type: str
    platform: str
    owner: str
    tags: list[str]
    health_score: int | None = None
    confidence: float | None = None


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: str | None = None
    path: str | None = None
    request_id: str | None = None


class SSEEvent(BaseModel):
    """SSE event schema."""
    step: str
    status: str
    timestamp: str
    finding: str | None = None
    confidence: float | None = None
    message: str | None = None
    evidence: dict | None = None
    severity: str | None = None
    business_impact: dict | None = None
