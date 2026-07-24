"""Evidence Object schema — every worker returns this structured object."""
from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceItem(BaseModel):
    type: str
    description: str | None = None
    before: dict | None = None
    after: dict | None = None
    entity_urn: str | None = None
    downstream_count: int | None = None
    affected_models: list[str] | None = None
    affected_dashboards: int | None = None


class BusinessImpact(BaseModel):
    predictions_today: int | None = None
    estimated_revenue_at_risk: str | None = None
    affected_systems: list[str] | None = None


class DataHubMutation(BaseModel):
    tool: str
    params: dict
    safe: bool = True


class EvidenceObject(BaseModel):
    worker_id: str
    timestamp: str
    finding: str
    confidence: float = Field(ge=0.0, le=1.0)
    severity: Severity
    evidence: list[EvidenceItem] = []
    business_impact: BusinessImpact | None = None
    next_action: str | None = None
    datahub_mutations: list[DataHubMutation] = []
