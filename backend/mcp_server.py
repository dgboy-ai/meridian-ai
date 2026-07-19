"""Meridian AI MCP Server — official MCP SDK implementation.

Exposes Meridian AI as MCP tools so any AI agent (Claude, GPT, Cursor)
can trigger ML incident investigations via the Model Context Protocol.

Usage:
    python -m backend.mcp_server

Tools:
    - meridian_investigate: Run a full ML incident investigation (writes to DataHub)
    - meridian_health: Check ML model health score (read-only)
    - meridian_playbook: View reflexion playbook for a failure pattern (read-only)
"""
import asyncio
import json
import logging
import os
import sys

# Ensure backend package is importable when run as __main__
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server  # noqa: E402
from mcp.server.stdio import stdio_server  # noqa: E402
from mcp.types import Tool, TextContent  # noqa: E402

from backend.clients.datahub_client import DataHubMCPClient  # noqa: E402
from backend.clients.groq_client import GroqClient  # noqa: E402
from backend.workers.planner import PlannerAgent  # noqa: E402
from backend.health_score import HealthScoreCalculator  # noqa: E402

logger = logging.getLogger("meridian-ai.mcp")

# ─── Server Setup ──────────────────────────────────────────────────────────────

server = Server("meridian-ai")

# Shared state — initialized once
_datahub: DataHubMCPClient | None = None
_groq: GroqClient | None = None
_planner: PlannerAgent | None = None


def _get_planner() -> PlannerAgent:
    global _datahub, _groq, _planner
    if _planner is None:
        _datahub = DataHubMCPClient()
        _groq = GroqClient()
        _planner = PlannerAgent(mcp=_datahub, groq=_groq)
    return _planner


# ─── Tool Definitions ──────────────────────────────────────────────────────────

TOOLS = [
    Tool(
        name="meridian_investigate",
        description=(
            "Run a full ML incident investigation. Detects schema changes, "
            "traverses column-level lineage, computes blast radius, writes "
            "root cause reports and AI Knowledge panels to DataHub. "
            "This tool modifies DataHub state."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "model_urn": {
                    "type": "string",
                    "description": (
                        "DataHub URN of the model to investigate. "
                        "Example: urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"
                    ),
                },
                "incident_id": {
                    "type": "string",
                    "description": "Incident ID for tracking (optional, auto-generated if omitted)",
                },
            },
            "required": ["model_urn"],
        },
    ),
    Tool(
        name="meridian_health",
        description=(
            "Check ML health score for a model. Returns weighted health score "
            "(0-100), confidence level, assessment (RELIABLE/UNRELIABLE/INCOMPLETE), "
            "and per-metric breakdown. Read-only — no DataHub mutations."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "model_urn": {
                    "type": "string",
                    "description": "DataHub URN of the model to check",
                },
            },
            "required": ["model_urn"],
        },
    ),
    Tool(
        name="meridian_playbook",
        description=(
            "View the latest reflexion playbook for a failure pattern. "
            "Playbooks are self-improving documents that get updated after "
            "every investigation. Read-only."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "pattern_id": {
                    "type": "string",
                    "description": "Pattern identifier (e.g., schema-change-type-mismatch)",
                },
            },
            "required": ["pattern_id"],
        },
    ),
]


# ─── Tool Handlers ─────────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    planner = _get_planner()

    if name == "meridian_investigate":
        model_urn = arguments.get("model_urn", "")
        incident_id = arguments.get("incident_id", "MCP")
        if not model_urn:
            return [TextContent(type="text", text=json.dumps({"error": "model_urn is required"}))]

        results = []
        async for event in planner.investigate(model_urn, incident_id):
            results.append(event)

        summary = results[-1].get("summary", {}) if results else {}
        result = {
            "status": "completed",
            "incident_id": incident_id,
            "model_urn": model_urn,
            "workers_fired": summary.get("workers_fired", []),
            "health_score": summary.get("health_score"),
            "datahub_mutations": summary.get("datahub_mutations", 0),
            "resolution_time_minutes": summary.get("resolution_time_minutes", 0),
            "compliance": summary.get("compliance", {}),
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "meridian_health":
        model_urn = arguments.get("model_urn", "")
        if not model_urn:
            return [TextContent(type="text", text=json.dumps({"error": "model_urn is required"}))]

        calculator = HealthScoreCalculator()
        model_name = model_urn.split(",")[-2] if "," in model_urn else model_urn
        entities = await planner.mcp.get_entities([model_urn])
        entity = entities[0] if entities else {}

        health_val = entity.get("health_score", entity.get("ai_health_score", 80))
        confidence_val = entity.get("confidence", entity.get("ai_confidence", 0.85))
        resolved = entity.get("resolved_incidents", 0)

        data_quality = min(1.0, health_val / 100.0) if health_val else 0.7
        health_score = calculator.calculate_from_workers(
            model_urn=model_urn,
            model_name=model_name,
            data_quality=data_quality,
            drift_magnitude=confidence_val or 0.6,
            prediction_quality=confidence_val or 0.85,
            latency=0.94, cost=0.85, fairness=0.88,
            worker_confidences=[confidence_val] if confidence_val else None,
        )

        result = {
            "model_urn": model_urn,
            "model_name": model_name,
            "health_score": health_score.score,
            "assessment": health_score.assessment.value,
            "confidence": health_score.confidence,
            "resolved_incidents": resolved,
            "metrics": {m.name: round(m.normalized_value, 2) for m in health_score.metrics},
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "meridian_playbook":
        pattern_id = arguments.get("pattern_id", "")
        if not pattern_id:
            return [TextContent(type="text", text=json.dumps({"error": "pattern_id is required"}))]

        docs = await planner.mcp.search_documents(query=f"playbook {pattern_id}", tags=["playbook"])
        if docs:
            doc = docs[0]
            result = {
                "pattern_id": pattern_id,
                "title": doc.get("title", ""),
                "content": doc.get("content", ""),
                "tags": doc.get("tags", []),
            }
        else:
            result = {
                "pattern_id": pattern_id,
                "content": f"No playbook found for {pattern_id}. Will be created after first investigation.",
            }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    else:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


# ─── Entry Point ───────────────────────────────────────────────────────────────

async def main():
    logger.info("Starting Meridian AI MCP Server")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
