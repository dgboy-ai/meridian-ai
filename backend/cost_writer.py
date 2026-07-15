"""Cost Attribution Writer — writes investigation costs to DataHub.

"Nobody can trace inference cost to upstream data assets. This is the #1
unsolved FinOps problem in 2026."

This module writes cost attribution data to DataHub as structured properties:
  - investigation_cost_usd: Total cost of the investigation
  - tokens_consumed: Total tokens used across all LLM calls
  - time_saved_minutes: Time saved vs. manual investigation
  - cost_per_minute_saved: Efficiency metric
  - roi_percentage: Return on investment

Based on IDC study:
"Investigation cost $0.03. Prevented $45,000/day loss. ROI: 1,500,000%"
"""
import logging
from datetime import datetime, timezone

from backend.clients.datahub_client import DataHubMCPClient
from backend.cost_tracker import CostTracker, InvestigationCost

logger = logging.getLogger("meridian-ai.cost_writer")


class CostWriter:
    """Write cost attribution data to DataHub."""

    def __init__(self, mcp: DataHubMCPClient):
        self.mcp = mcp

    async def write_investigation_cost(
        self,
        incident_id: str,
        investigation_cost: InvestigationCost,
        model_urns: list[str],
        health_score: int = 0,
    ) -> dict:
        """Write cost attribution to DataHub as structured properties.

        Args:
            incident_id: Incident ID for tracking
            investigation_cost: Cost tracking data from CostTracker
            model_urns: Model URNs to write cost data to
            health_score: Health score at time of investigation

        Returns:
            Write result with cost summary
        """
        now = datetime.now(timezone.utc).isoformat()

        # Build cost properties
        cost_properties = {
            "investigation_id": incident_id,
            "investigation_cost_usd": investigation_cost.total_cost_usd,
            "tokens_consumed": investigation_cost.total_tokens_in + investigation_cost.total_tokens_out,
            "tokens_input": investigation_cost.total_tokens_in,
            "tokens_output": investigation_cost.total_tokens_out,
            "time_saved_minutes": investigation_cost.time_saved_minutes,
            "cost_per_minute_saved": investigation_cost.cost_per_minute_saved(),
            "manual_time_minutes": investigation_cost.manual_time_minutes,
            "actual_time_minutes": round(investigation_cost.total_duration_ms / 60000, 2),
            "health_score": health_score,
            "timestamp": now,
        }

        # Calculate ROI
        if investigation_cost.total_cost_usd > 0 and investigation_cost.time_saved_minutes > 0:
            # Average ML engineer salary: $150K/year = $75/hour = $1.25/minute
            value_of_time_saved = investigation_cost.time_saved_minutes * 1.25
            roi = ((value_of_time_saved - investigation_cost.total_cost_usd) / investigation_cost.total_cost_usd) * 100
            cost_properties["roi_percentage"] = round(roi, 2)
            cost_properties["value_of_time_saved_usd"] = round(value_of_time_saved, 2)
        else:
            cost_properties["roi_percentage"] = 0.0
            cost_properties["value_of_time_saved_usd"] = 0.0

        # Write to each model entity
        results = []
        for model_urn in model_urns:
            try:
                result = await self.mcp.add_structured_properties(
                    entity_urn=model_urn,
                    properties=cost_properties,
                )
                results.append({
                    "model_urn": model_urn,
                    "status": "written",
                    "cost_usd": investigation_cost.total_cost_usd,
                    "roi_percentage": cost_properties.get("roi_percentage", 0),
                })
                logger.info(f"Cost attribution written to {model_urn}: ${investigation_cost.total_cost_usd:.6f}")
            except Exception as e:
                logger.error(f"Failed to write cost attribution to {model_urn}: {e}")
                results.append({
                    "model_urn": model_urn,
                    "status": "failed",
                    "error": str(e),
                })

        return {
            "incident_id": incident_id,
            "cost_properties": cost_properties,
            "write_results": results,
            "summary": {
                "total_cost_usd": investigation_cost.total_cost_usd,
                "tokens_consumed": investigation_cost.total_tokens_in + investigation_cost.total_tokens_out,
                "time_saved_minutes": investigation_cost.time_saved_minutes,
                "roi_percentage": cost_properties.get("roi_percentage", 0),
            },
        }

    async def write_aggregate_costs(
        self,
        model_urns: list[str],
        cost_tracker: CostTracker,
    ) -> dict:
        """Write aggregate cost summary to DataHub.

        Args:
            model_urns: Model URNs to write aggregate data to
            cost_tracker: CostTracker instance with all investigation costs

        Returns:
            Write result with aggregate summary
        """
        now = datetime.now(timezone.utc).isoformat()
        summary = cost_tracker.get_roi_summary()

        aggregate_properties = {
            "aggregate_cost_usd": summary["total_cost_usd"],
            "total_investigations": summary["total_investigations"],
            "total_time_saved_minutes": summary["total_time_saved_minutes"],
            "avg_cost_per_investigation": summary["avg_cost_per_investigation"],
            "avg_time_saved_per_investigation": summary["avg_time_saved_per_investigation"],
            "value_of_time_saved_usd": summary["value_of_time_saved_usd"],
            "roi_percentage": summary["roi_percentage"],
            "cost_per_minute_saved": summary["cost_per_minute_saved"],
            "engineer_hourly_rate": summary["engineer_hourly_rate"],
            "last_updated": now,
        }

        # Write to each model entity
        results = []
        for model_urn in model_urns:
            try:
                result = await self.mcp.add_structured_properties(
                    entity_urn=model_urn,
                    properties=aggregate_properties,
                )
                results.append({
                    "model_urn": model_urn,
                    "status": "written",
                })
                logger.info(f"Aggregate cost summary written to {model_urn}")
            except Exception as e:
                logger.error(f"Failed to write aggregate costs to {model_urn}: {e}")
                results.append({
                    "model_urn": model_urn,
                    "status": "failed",
                    "error": str(e),
                })

        return {
            "aggregate_properties": aggregate_properties,
            "write_results": results,
            "summary": summary,
        }
