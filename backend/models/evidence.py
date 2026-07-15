"""Evidence Object schema — every worker returns this structured object."""
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceItem(BaseModel):
    type: str
    description: Optional[str] = None
    before: Optional[dict] = None
    after: Optional[dict] = None
    entity_urn: Optional[str] = None
    downstream_count: Optional[int] = None
    affected_models: Optional[list[str]] = None
    affected_dashboards: Optional[int] = None


class BusinessImpact(BaseModel):
    predictions_today: Optional[int] = None
    estimated_revenue_at_risk: Optional[str] = None
    affected_systems: Optional[list[str]] = None


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
    business_impact: Optional[BusinessImpact] = None
    next_action: Optional[str] = None
    datahub_mutations: list[DataHubMutation] = []
