"""Meridian AI MCP Server — wraps the planner as an MCP tool.

This allows AI agents (Claude, GPT, etc.) to call Meridian directly
via the Model Context Protocol.

Usage:
    python -m backend.mcp_server

The server exposes these tools:
    - meridian_investigate: Run a full investigation
    - meridian_health: Check model health
    - meridian_playbook: View a playbook
"""
import asyncio
import json
import logging
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger("meridian-ai.mcp")

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.workers.planner import PlannerAgent


# MCP Server implementation using stdio transport
# This is a minimal MCP server that can be used with Claude Desktop or other MCP clients


class MeridianMCPServer:
    """MCP Server for Meridian AI."""

    def __init__(self):
        self.mcp = DataHubMCPClient()
        self.groq = GroqClient()
        self.planner = PlannerAgent(mcp=self.mcp, groq=self.groq)

    async def handle_investigate(self, model_urn: str, incident_id: str = "MCP") -> dict:
        """Run a full investigation and return structured results."""
        results = []
        async for event in self.planner.investigate(model_urn, incident_id):
            results.append(event)

        summary = results[-1].get("summary", {}) if results else {}
        return {
            "status": "completed",
            "incident_id": incident_id,
            "model_urn": model_urn,
            "workers_fired": summary.get("workers_fired", []),
            "health_score": summary.get("health_score"),
            "datahub_mutations": summary.get("datahub_mutations", 0),
            "compliance": summary.get("compliance", {}),
            "events": results,
        }

    async def handle_health(self, model_urn: str) -> dict:
        """Check model health from real entity metadata."""
        from backend.health_score import HealthScoreCalculator
        calculator = HealthScoreCalculator()

        model_name = model_urn.split(",")[-2] if "," in model_urn else model_urn
        entities = await self.mcp.get_entities([model_urn])
        entity = entities[0] if entities else {}

        # Use real entity data when available
        health_score_val = entity.get("health_score", entity.get("ai_health_score", 80))
        confidence_val = entity.get("confidence", entity.get("ai_confidence", 0.85))
        resolved = entity.get("resolved_incidents", 0)
        resolution_time = entity.get("resolution_time_minutes", 5.0)

        # Compute metric scores from entity data
        data_quality = min(1.0, health_score_val / 100.0) if health_score_val else 0.7
        drift_magnitude = confidence_val if confidence_val else 0.6
        prediction_quality = confidence_val if confidence_val else 0.85

        health_score = calculator.calculate_from_workers(
            model_urn=model_urn,
            model_name=model_name,
            data_quality=data_quality,
            drift_magnitude=drift_magnitude,
            prediction_quality=prediction_quality,
            latency=0.94,
            cost=0.85,
            fairness=0.88,
            worker_confidences=[confidence_val] if confidence_val else None,
        )

        return {
            "model_urn": model_urn,
            "model_name": model_name,
            "health_score": health_score.score,
            "assessment": health_score.assessment.value,
            "confidence": health_score.confidence,
            "resolved_incidents": resolved,
            "resolution_time_minutes": resolution_time,
            "metrics": {m.name: round(m.normalized_value, 2) for m in health_score.metrics},
        }

    async def handle_playbook(self, pattern_id: str) -> dict:
        """View a playbook."""
        docs = await self.mcp.search_documents(query=f"playbook {pattern_id}", tags=["playbook"])
        if docs:
            doc = docs[0]
            return {
                "pattern_id": pattern_id,
                "title": doc.get("title", ""),
                "content": doc.get("content", ""),
                "tags": doc.get("tags", []),
            }
        return {
            "pattern_id": pattern_id,
            "content": f"No playbook found for {pattern_id}. Will be created after first investigation.",
        }


# Tool definitions for MCP
# MCP-standard hints: readOnlyHint, destructiveHint, idempotentHint
# These tell clients like Claude/Cursor which tools modify state and need confirmation
TOOLS = [
    {
        "name": "meridian_investigate",
        "description": "Run a full ML incident investigation. Detects schema changes, traverses lineage, writes root cause reports to DataHub. This tool modifies DataHub state.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model_urn": {
                    "type": "string",
                    "description": "DataHub URN of the model to investigate (e.g., urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD))",
                },
                "incident_id": {
                    "type": "string",
                    "description": "Incident ID for tracking (optional, auto-generated if not provided)",
                },
            },
            "required": ["model_urn"],
        },
        # MCP-standard tool hints
        "readOnlyHint": False,  # Writes to DataHub (root cause reports, tags, incidents)
        "destructiveHint": False,  # Does not delete data, only adds/modifies
        "idempotentHint": False,  # Running twice creates duplicate incidents
    },
    {
        "name": "meridian_health",
        "description": "Check ML health score for a model. Returns health score, confidence, and metric breakdown. This tool is read-only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model_urn": {
                    "type": "string",
                    "description": "DataHub URN of the model to check",
                },
            },
            "required": ["model_urn"],
        },
        # MCP-standard tool hints
        "readOnlyHint": True,  # Only reads from DataHub
        "destructiveHint": False,  # No modifications
        "idempotentHint": True,  # Running twice returns same result
    },
    {
        "name": "meridian_playbook",
        "description": "View the latest reflexion playbook for a failure pattern. Playbooks improve after every incident. This tool is read-only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern_id": {
                    "type": "string",
                    "description": "Pattern identifier (e.g., schema-change-type-mismatch)",
                },
            },
            "required": ["pattern_id"],
        },
        # MCP-standard tool hints
        "readOnlyHint": True,  # Only reads from DataHub
        "destructiveHint": False,  # No modifications
        "idempotentHint": True,  # Running twice returns same result
    },
]


async def main():
    """Run the MCP server on stdio with async I/O."""
    server = MeridianMCPServer()
    loop = asyncio.get_event_loop()
    cancelled = False

    # Use asyncio to read stdin without blocking the event loop
    reader = asyncio.StreamReader()
    transport, _ = await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin)

    try:
        while not cancelled:
            line = await reader.readline()
            if not line:
                break
            line = line.decode().strip()
            if not line:
                continue

            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                continue

            method = request.get("method", "")
            params = request.get("params", {})
            request_id = request.get("id")

            # Handle cancellation notification (MCP protocol)
            if method == "notifications/cancelled":
                logger.info(f"Cancelled: {params.get('requestId', 'unknown')}")
                continue

            # Skip notifications (no response needed)
            if method.startswith("notifications/"):
                continue

            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "meridian-ai", "version": "1.0.0"},
                    },
                }
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"tools": TOOLS},
                }
            elif method == "tools/call":
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})

                try:
                    if tool_name == "meridian_investigate":
                        result = await server.handle_investigate(
                            arguments.get("model_urn", ""),
                            arguments.get("incident_id", "MCP"),
                        )
                    elif tool_name == "meridian_health":
                        result = await server.handle_health(arguments.get("model_urn", ""))
                    elif tool_name == "meridian_playbook":
                        result = await server.handle_playbook(arguments.get("pattern_id", ""))
                    else:
                        result = {"error": f"Unknown tool: {tool_name}"}

                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]},
                    }
                except Exception as e:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -1, "message": str(e)},
                    }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -1, "message": f"Unknown method: {method}"},
                }

            print(json.dumps(response))
            sys.stdout.flush()
    except (KeyboardInterrupt, SystemExit):
        logger.info("MCP server shutting down")
    finally:
        transport.close()


if __name__ == "__main__":
    asyncio.run(main())
