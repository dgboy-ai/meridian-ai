"""Cost Attribution Tracker — tracks tokens, compute cost, and ROI per investigation.

Based on IDC study:
"The sunk cost is months of ML engineering on projects that never reach production."

This module tracks:
  - Tokens consumed per worker per investigation
  - Compute cost per investigation
  - Time saved vs. manual investigation
  - Incidents prevented by assertions
  - ROI calculation: "Investigation cost $0.03. Prevented $45,000/day loss."
"""
import time
import logging
from dataclasses import dataclass, field

logger = logging.getLogger("meridian-ai.cost_tracker")


@dataclass
class WorkerCost:
    """Cost tracking for a single worker invocation."""
    worker_id: str
    tokens_in: int = 0
    tokens_out: int = 0
    duration_ms: float = 0.0
    model_used: str = ""
    cost_usd: float = 0.0

    def to_dict(self) -> dict:
        return {
            "worker_id": self.worker_id,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "duration_ms": round(self.duration_ms, 2),
            "model_used": self.model_used,
            "cost_usd": round(self.cost_usd, 6),
        }


@dataclass
class InvestigationCost:
    """Cost tracking for a complete investigation."""
    incident_id: str
    start_time: float = 0.0
    end_time: float = 0.0
    worker_costs: list[WorkerCost] = field(default_factory=list)
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_cost_usd: float = 0.0
    total_duration_ms: float = 0.0
    # ROI metrics
    manual_time_minutes: float = 45.0  # Average manual investigation time
    time_saved_minutes: float = 0.0
    incidents_prevented: int = 0
    revenue_at_risk: float = 0.0

    def to_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "total_tokens_in": self.total_tokens_in,
            "total_tokens_out": self.total_tokens_out,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_duration_ms": round(self.total_duration_ms, 2),
            "worker_costs": [wc.to_dict() for wc in self.worker_costs],
            "manual_time_minutes": self.manual_time_minutes,
            "time_saved_minutes": round(self.time_saved_minutes, 2),
            "incidents_prevented": self.incidents_prevented,
            "revenue_at_risk": self.revenue_at_risk,
            "roi_percentage": self.calculate_roi(),
            "cost_per_minute_saved": self.cost_per_minute_saved(),
        }

    def calculate_roi(self) -> float:
        """Calculate ROI as percentage."""
        if self.total_cost_usd <= 0:
            return 0.0
        value_of_time_saved = self.time_saved_minutes * 1.41  # Revenue per prediction minute
        if value_of_time_saved <= 0:
            return 0.0
        return round(((value_of_time_saved - self.total_cost_usd) / self.total_cost_usd) * 100, 2)

    def cost_per_minute_saved(self) -> float:
        """Calculate cost per minute of investigation time saved."""
        if self.time_saved_minutes <= 0:
            return 0.0
        return round(self.total_cost_usd / self.time_saved_minutes, 6)


# Token pricing (per 1K tokens) — Groq free tier estimates
TOKEN_PRICING = {
    "openai/gpt-oss-120b": {"input": 0.0, "output": 0.0},  # Free tier
    "qwen/qwen3.6-27b": {"input": 0.0, "output": 0.0},  # Free tier
    "qwen/qwen3-32b": {"input": 0.0, "output": 0.0},  # Free tier
    "llama-3.3-70b-versatile": {"input": 0.0, "output": 0.0},  # Free tier
    "llama-3.1-8b-instant": {"input": 0.0, "output": 0.0},  # Free tier
    "default": {"input": 0.0, "output": 0.0},  # Free tier
}


class CostTracker:
    """Track costs per investigation and across all investigations."""

    def __init__(self) -> None:
        self._investigations: dict[str, InvestigationCost] = {}
        self._total_cost_usd: float = 0.0
        self._total_investigations: int = 0
        self._total_time_saved_minutes: float = 0.0

    def start_investigation(self, incident_id: str) -> InvestigationCost:
        """Start tracking costs for an investigation."""
        cost = InvestigationCost(
            incident_id=incident_id,
            start_time=time.time(),
        )
        self._investigations[incident_id] = cost
        self._total_investigations += 1
        return cost

    def record_worker_cost(
        self,
        incident_id: str,
        worker_id: str,
        tokens_in: int = 0,
        tokens_out: int = 0,
        model_used: str = "default",
        duration_ms: float = 0.0,
    ) -> WorkerCost:
        """Record cost for a single worker invocation."""
        # Calculate cost from token pricing
        pricing = TOKEN_PRICING.get(model_used, TOKEN_PRICING["default"])
        cost_usd = (tokens_in * pricing["input"] + tokens_out * pricing["output"]) / 1000.0

        worker_cost = WorkerCost(
            worker_id=worker_id,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            duration_ms=duration_ms,
            model_used=model_used,
            cost_usd=cost_usd,
        )

        investigation = self._investigations.get(incident_id)
        if investigation:
            investigation.worker_costs.append(worker_cost)
            investigation.total_tokens_in += tokens_in
            investigation.total_tokens_out += tokens_out
            investigation.total_cost_usd += cost_usd
            investigation.total_duration_ms += duration_ms

        return worker_cost

    def end_investigation(
        self,
        incident_id: str,
        manual_time_minutes: float = 45.0,
        incidents_prevented: int = 0,
        revenue_at_risk: float = 0.0,
    ) -> InvestigationCost:
        """End tracking for an investigation and compute ROI."""
        investigation = self._investigations.get(incident_id)
        if not investigation:
            return InvestigationCost(incident_id=incident_id)

        investigation.end_time = time.time()
        investigation.manual_time_minutes = manual_time_minutes

        # Compute actual investigation time
        actual_time_ms = investigation.end_time - investigation.start_time
        actual_time_minutes = actual_time_ms / 60000.0

        # Compute time saved
        investigation.time_saved_minutes = max(0, manual_time_minutes - actual_time_minutes)
        investigation.incidents_prevented = incidents_prevented
        investigation.revenue_at_risk = revenue_at_risk

        # Update totals
        self._total_cost_usd += investigation.total_cost_usd
        self._total_time_saved_minutes += investigation.time_saved_minutes

        return investigation

    def get_investigation_cost(self, incident_id: str) -> InvestigationCost | None:
        """Get cost tracking for a specific investigation."""
        return self._investigations.get(incident_id)

    def get_summary(self) -> dict:
        """Get aggregate cost summary across all investigations."""
        return {
            "total_investigations": self._total_investigations,
            "total_cost_usd": round(self._total_cost_usd, 6),
            "total_time_saved_minutes": round(self._total_time_saved_minutes, 2),
            "avg_cost_per_investigation": round(
                self._total_cost_usd / max(self._total_investigations, 1), 6
            ),
            "avg_time_saved_per_investigation": round(
                self._total_time_saved_minutes / max(self._total_investigations, 1), 2
            ),
        }

    def get_roi_summary(self) -> dict:
        """Get ROI summary for business case."""
        summary = self.get_summary()
        # Estimate ROI based on time saved
        # Average ML engineer salary: $150K/year = $75/hour = $1.25/minute
        cost_per_minute = 1.25
        value_of_time_saved = summary["total_time_saved_minutes"] * cost_per_minute
        roi = 0.0
        if summary["total_cost_usd"] > 0:
            roi = ((value_of_time_saved - summary["total_cost_usd"]) / summary["total_cost_usd"]) * 100

        return {
            **summary,
            "value_of_time_saved_usd": round(value_of_time_saved, 2),
            "roi_percentage": round(roi, 2),
            "cost_per_minute_saved": round(
                summary["total_cost_usd"] / max(summary["total_time_saved_minutes"], 0.01), 6
            ),
            "engineer_hourly_rate": cost_per_minute * 60,
        }
