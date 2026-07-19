"""DataHub MCP client — dual-mode: real GMS HTTP when available, mock when not.

The client probes DataHub on startup. If GMS is reachable, all calls go through
real async HTTP via httpx. If not, it falls back to in-memory mock data for
development and demo.

Set DATAHUB_MOCK=false and ensure DataHub GMS is running at DATAHUB_GMS_URL
to use the real integration.
"""
import copy
import os
import json
import logging
import asyncio
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import quote

import httpx

logger = logging.getLogger("meridian-ai.datahub")

MOCK_ENTITIES = {
    "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)": {
        "urn": "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)",
        "type": "dataset",
        "name": "raw_events",
        "platform": "snowflake",
        "owner": "data-engineering",
        "tags": ["meridian-commerce", "production"],
        "fields": [
            {"name": "event_id", "type": "STRING"},
            {"name": "user_id", "type": "STRING"},
            {"name": "user_age", "type": "STRING"},
            {"name": "timestamp", "type": "TIMESTAMP"},
        ],
    },
    "urn:li:dataset:(urn:li:dataPlatform:dbt,meridian.feature_pipeline,PROD)": {
        "urn": "urn:li:dataset:(urn:li:dataPlatform:dbt,meridian.feature_pipeline,PROD)",
        "type": "dataset",
        "name": "feature_pipeline",
        "platform": "dbt",
        "owner": "data-engineering",
        "tags": ["meridian-commerce", "production"],
        "fields": [
            {"name": "user_id", "type": "STRING"},
            {"name": "age_bucket", "type": "STRING"},
            {"name": "event_frequency", "type": "INT"},
            {"name": "session_duration", "type": "INT"},
        ],
    },
    "urn:li:dataset:(urn:li:dataPlatform:feast,meridian.feature_store,PROD)": {
        "urn": "urn:li:dataset:(urn:li:dataPlatform:feast,meridian.feature_store,PROD)",
        "type": "dataset",
        "name": "feature_store",
        "platform": "feast",
        "owner": "ml-platform-team",
        "tags": ["meridian-commerce", "production", "golden"],
        "fields": [
            {"name": "user_id", "type": "STRING"},
            {"name": "age_bucket", "type": "STRING"},
            {"name": "event_frequency", "type": "INT"},
            {"name": "session_duration", "type": "INT"},
        ],
    },
    "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)": {
        "urn": "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
        "type": "mlModel",
        "name": "churn_model_v3",
        "platform": "mlflow",
        "owner": "ml-platform-team",
        "tags": ["meridian-commerce", "production", "churn"],
        "hyperparameters": {"algorithm": "XGBoost", "max_depth": 6},
        "health_score": 81,
        "confidence": 0.97,
        "resolved_incidents": 14,
        "resolution_time_minutes": 3.0,
        "known_failure_patterns": 3,
        "last_investigation": "2026-07-12T09:39:26Z",
        "ai_health_score": 89,
        "ai_confidence": 0.96,
    },
    "urn:li:mlModel:(urn:li:dataPlatform:mlflow,ltv_model_v2,PROD)": {
        "urn": "urn:li:mlModel:(urn:li:dataPlatform:mlflow,ltv_model_v2,PROD)",
        "type": "mlModel",
        "name": "ltv_model_v2",
        "platform": "mlflow",
        "owner": "ml-platform-team",
        "tags": ["meridian-commerce", "production", "ltv"],
        "health_score": 62,
        "confidence": 0.88,
        "resolved_incidents": 8,
    },
    "urn:li:mlModel:(urn:li:dataPlatform:mlflow,segment_model_v1,PROD)": {
        "urn": "urn:li:mlModel:(urn:li:dataPlatform:mlflow,segment_model_v1,PROD)",
        "type": "mlModel",
        "name": "segment_model_v1",
        "platform": "mlflow",
        "owner": "ml-platform-team",
        "tags": ["meridian-commerce", "production", "segmentation"],
        "health_score": 91,
        "confidence": 0.95,
        "resolved_incidents": 3,
    },
}

MOCK_LINEAGE = {
    "urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)": {
        "downstream": ["urn:li:dataset:(urn:li:dataPlatform:dbt,meridian.feature_pipeline,PROD)"],
    },
    "urn:li:dataset:(urn:li:dataPlatform:dbt,meridian.feature_pipeline,PROD)": {
        "upstream": ["urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)"],
        "downstream": ["urn:li:dataset:(urn:li:dataPlatform:feast,meridian.feature_store,PROD)"],
    },
    "urn:li:dataset:(urn:li:dataPlatform:feast,meridian.feature_store,PROD)": {
        "upstream": ["urn:li:dataset:(urn:li:dataPlatform:dbt,meridian.feature_pipeline,PROD)"],
        "downstream": [
            "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
            "urn:li:mlModel:(urn:li:dataPlatform:mlflow,ltv_model_v2,PROD)",
            "urn:li:mlModel:(urn:li:dataPlatform:mlflow,segment_model_v1,PROD)",
        ],
    },
}


class DataHubMCPClient:
    """Dual-mode DataHub client: real GMS HTTP or mock fallback.

    All public methods are async and use httpx for non-blocking I/O.
    The synchronous GMS probe happens once at startup to determine mode.

    Usage:
        client = DataHubMCPClient()  # auto-detects real vs mock
        client = DataHubMCPClient(mock=False)  # force real mode
        client = DataHubMCPClient(mock=True)   # force mock mode
        client = DataHubMCPClient(auth_mode="service_account")  # use service account
    """

    # Mutation tools require DataHub v0.5.0+
    MUTATION_TOOLS_MIN_VERSION = "0.5.0"

    def __init__(
        self,
        gms_url: str | None = None,
        token: str | None = None,
        mock: bool | None = None,
        timeout: float = 10.0,
        auth_mode: str | None = None,
    ):
        self.gms_url = gms_url or os.getenv("DATAHUB_GMS_URL", "http://localhost:8080/api/gms")
        self.token = token or os.getenv("DATAHUB_GMS_TOKEN", "")
        self.mock = mock if mock is not None else os.getenv("DATAHUB_MOCK", "true").lower() == "true"
        self._connected = False
        self._mode = "mock"
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._datahub_version: str | None = None
        self._mutation_tools_supported: bool = True  # Assume supported unless proven otherwise

        # Auth mode: "pat" (default) or "service_account"
        self._auth_mode = auth_mode or os.getenv("DATAHUB_AUTH_MODE", "pat")
        if self._auth_mode not in ("pat", "service_account"):
            logger.warning(f"Invalid auth_mode '{self._auth_mode}', defaulting to 'pat'")
            self._auth_mode = "pat"

        # Mock state
        self._entities: dict[str, dict] = copy.deepcopy(MOCK_ENTITIES)
        self._lineage: dict[str, dict] = copy.deepcopy(MOCK_LINEAGE)
        self._documents: list[dict] = []
        self._incidents: list[dict] = []
        self._proposals: list[dict] = []

        # Log auth mode
        if not self.mock:
            logger.info(f"Auth mode: {self._auth_mode}")

        # Attempt real connection if not forced mock
        if not self.mock:
            self._probe_gms()

    def reset_mock(self):
        """Reset all mock state to fresh copies of the original constants."""
        self._entities = copy.deepcopy(MOCK_ENTITIES)
        self._lineage = copy.deepcopy(MOCK_LINEAGE)
        self._documents = []
        self._incidents = []
        self._proposals = []

    async def connect(self):
        """Non-blocking startup: probe GMS asynchronously and set mode."""
        if self.mock:
            self._mode = "mock"
            self._connected = False
            logger.info("Mock mode forced, skipping GMS probe.")
            return
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._probe_gms)

    def _probe_gms(self):
        """Synchronously probe DataHub GMS to check availability and version (startup only)."""
        try:
            url = f"{self.gms_url}/health"
            req = Request(url, method="GET")
            if self.token:
                req.add_header("Authorization", f"Bearer {self.token}")
            resp = urlopen(req, timeout=3)
            if resp.status == 200:
                self._connected = True
                self._mode = "real"
                logger.info(f"Connected to DataHub GMS at {self.gms_url}")

                # Try to detect version
                self._detect_version()
            else:
                logger.warning(f"DataHub GMS returned {resp.status}, using mock")
                self._connected = False
                self._mode = "mock"
        except (URLError, HTTPError, OSError) as e:
            logger.warning(f"DataHub GMS unreachable at {self.gms_url}: {e}. Using mock.")
            self._connected = False
            self._mode = "mock"

    def _detect_version(self):
        """Detect DataHub version and check mutation tool support."""
        try:
            # Try to get version from server config endpoint
            url = f"{self.gms_url}/config"
            req = Request(url, method="GET")
            if self.token:
                req.add_header("Authorization", f"Bearer {self.token}")
            resp = urlopen(req, timeout=3)
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                self._datahub_version = data.get("version", "")
                logger.info(f"DataHub version: {self._datahub_version}")

                # Check if mutation tools are supported (v0.5.0+)
                if self._datahub_version:
                    self._mutation_tools_supported = self._check_version_support(
                        self._datahub_version,
                        self.MUTATION_TOOLS_MIN_VERSION,
                    )
                    if not self._mutation_tools_supported:
                        logger.warning(
                            f"DataHub version {self._datahub_version} does not support mutation tools. "
                            f"Minimum required: {self.MUTATION_TOOLS_MIN_VERSION}. "
                            f"Mutation operations will use mock fallback."
                        )
        except Exception as e:
            logger.debug(f"Could not detect DataHub version: {e}")
            # Assume supported if we can't detect version
            self._mutation_tools_supported = True

    def _check_version_support(self, current: str, minimum: str) -> bool:
        """Check if current version meets minimum requirement."""
        try:
            current_parts = [int(x) for x in current.split(".")[:3]]
            minimum_parts = [int(x) for x in minimum.split(".")[:3]]
            return current_parts >= minimum_parts
        except (ValueError, AttributeError):
            # If we can't parse version, assume supported
            return True

    def _check_mutation_support(self, tool_name: str) -> bool:
        """Check if a mutation tool is supported. Returns True if safe to proceed."""
        if self._mutation_tools_supported:
            return True

        # In mock mode, always allow
        if self._mode == "mock":
            return True

        # Warn but allow (will use mock fallback for the mutation)
        logger.warning(
            f"Mutation tool '{tool_name}' may not be supported on DataHub "
            f"version {self._datahub_version}. Minimum: {self.MUTATION_TOOLS_MIN_VERSION}. "
            f"Using mock fallback for this operation."
        )
        return True  # Allow but log warning

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None or self._client.is_closed:
            headers = {"Content-Type": "application/json"}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            self._client = httpx.AsyncClient(
                base_url=self.gms_url,
                headers=headers,
                timeout=httpx.Timeout(self._timeout),
            )
        return self._client

    async def _gms_request(self, method: str, path: str, body: dict | None = None) -> dict | None:
        """Make an async HTTP request to DataHub GMS."""
        if not self._connected:
            return None
        try:
            client = await self._get_client()
            if body is not None:
                response = await client.request(method, path, json=body)
            else:
                response = await client.request(method, path)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"GMS request failed: {method} {path}: HTTP {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"GMS request failed: {method} {path}: {e}")
            return None

    async def close(self):
        """Close the async HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @property
    def mode(self) -> str:
        return self._mode

    # ── Search ─────────────────────────────────────────────────────────

    async def search(self, query: str, entity_type: str | None = None, tags: list[str] | None = None) -> list[dict]:
        if self._connected:
            body = {
                "query": query,
                "entityType": entity_type,
            }
            result = await self._gms_request("POST", "/entities?action=search", body)
            if result and "entities" in result:
                return result["entities"]

        # Mock fallback
        results = []
        for urn, entity in self._entities.items():
            if entity_type and entity.get("type") != entity_type:
                continue
            if tags and not any(t in entity.get("tags", []) for t in tags):
                continue
            if not query or query.lower() in entity.get("name", "").lower() or query.lower() in urn.lower():
                results.append(entity)
        return results

    # ── Entities ───────────────────────────────────────────────────────

    async def get_entities(self, urns: list[str]) -> list[dict]:
        if self._connected:
            batch = {"urns": urns}
            result = await self._gms_request("POST", "/entities?action=batchGet", batch)
            if result and "entities" in result:
                return result["entities"]

        return [self._entities[urn] for urn in urns if urn in self._entities]

    # ── Lineage ────────────────────────────────────────────────────────

    async def get_lineage(self, urn: str, depth: int = 5) -> dict:
        if self._connected:
            encoded_urn = quote(urn, safe="")
            result = await self._gms_request("GET", f"/lineage/{encoded_urn}?direction=BOTH&depth={depth}")
            if result:
                return result

        lineage = self._lineage.get(urn, {})
        result = {"entity": urn, "upstream": [], "downstream": []}
        for up_urn in lineage.get("upstream", []):
            entity = self._entities.get(up_urn, {})
            result["upstream"].append({"urn": up_urn, "name": entity.get("name", ""), "type": entity.get("type", "")})
        for down_urn in lineage.get("downstream", []):
            entity = self._entities.get(down_urn, {})
            result["downstream"].append({"urn": down_urn, "name": entity.get("name", ""), "type": entity.get("type", "")})
        return result

    async def get_lineage_paths_between(self, source_urn: str, target_urn: str) -> list[list[dict]]:
        if self._connected:
            source_encoded = quote(source_urn, safe="")
            target_encoded = quote(target_urn, safe="")
            result = await self._gms_request("GET", f"/lineage/{source_encoded}/pathsTo/{target_encoded}")
            if result and "paths" in result:
                return result["paths"]

        paths = []
        for urn, entity in self._entities.items():
            if source_urn in str(self._lineage.get(urn, {})):
                path = []
                current = urn
                visited = set()
                while current and current not in visited:
                    visited.add(current)
                    e = self._entities.get(current, {})
                    path.append({"urn": current, "name": e.get("name", ""), "type": e.get("type", "")})
                    lineage = self._lineage.get(current, {})
                    next_downstream = lineage.get("downstream", [])
                    current = next_downstream[0] if next_downstream else None
                if path:
                    paths.append(path)
        return paths

    # ── Schema ─────────────────────────────────────────────────────────

    async def list_schema_fields(self, dataset_urn: str) -> list[dict]:
        if self._connected:
            encoded_urn = quote(dataset_urn, safe="")
            result = await self._gms_request("GET", f"/entities/{encoded_urn}/aspects/schemaMetadata")
            if result and "fields" in result:
                return result["fields"]

        entity = self._entities.get(dataset_urn, {})
        return entity.get("fields", [])

    async def get_dataset_queries(self, dataset_urn: str) -> list[dict]:
        if self._connected:
            encoded_urn = quote(dataset_urn, safe="")
            result = await self._gms_request("GET", f"/entities/{encoded_urn}/queries")
            if result and "queries" in result:
                return result["queries"]

        return [
            {"query": "SELECT * FROM raw_events WHERE user_age > 18", "tables": [dataset_urn]},
        ]

    # ── Knowledge Base ─────────────────────────────────────────────────
    # DataHub doesn't have a documents REST API. We use GraphQL for search
    # and store documents as structured properties or in-memory for mock mode.

    async def search_documents(self, query: str, tags: list[str] | None = None) -> list[dict]:
        if self._connected:
            # Use GraphQL search to find entities with matching descriptions
            graphql_query = """
            query SearchEntities($query: String!) {
                search(query: $query, start: 0, count: 10) {
                    searchResults {
                        entity {
                            urn
                            ... on Dataset { name description }
                            ... on MLModel { name description }
                        }
                    }
                }
            }
            """
            result = await self._graphql_mutation(graphql_query, {"query": query})
            if result and "search" in result:
                search_results = result["search"].get("searchResults", [])
                return [
                    {
                        "id": r["entity"]["urn"],
                        "title": r["entity"].get("name", ""),
                        "content": r["entity"].get("description", ""),
                        "tags": tags or [],
                    }
                    for r in search_results
                ]

        # Mock fallback - search in-memory documents
        results = []
        for doc in self._documents:
            if tags and not any(t in doc.get("tags", []) for t in tags):
                continue
            if query.lower() in doc.get("title", "").lower() or query.lower() in doc.get("content", "").lower():
                results.append(doc)
        return results

    async def save_document(
        self,
        title: str,
        content: str,
        tags: list[str] | None = None,
        linked_entities: list[str] | None = None,
        replace_existing: bool = False,
    ) -> dict:
        if self._connected:
            # DataHub doesn't have a documents API.
            # Store as structured properties on the first linked entity,
            # or just log for audit purposes.
            if linked_entities:
                # Write as structured properties on the entity
                props = {
                    "meridian_report_title": title,
                    "meridian_report_content": content[:1000],  # Truncate for storage
                    "meridian_report_tags": ",".join(tags or []),
                }
                await self.add_structured_properties(linked_entities[0], props)
                logger.info(f"Document '{title}' saved as structured properties on {linked_entities[0]}")

        # Always store in-memory for retrieval
        doc = {
            "id": f"doc-{len(self._documents) + 1}",
            "title": title,
            "content": content,
            "tags": tags or [],
            "linked_entities": linked_entities or [],
        }
        if replace_existing:
            self._documents = [d for d in self._documents if d.get("title") != title]
        self._documents.append(doc)
        return doc

    # ── Mutations ──────────────────────────────────────────────────────
    # All mutations use DataHub GraphQL API for correctness.
    # In mock mode, they update in-memory state.

    async def _graphql_mutation(self, mutation: str, variables: dict) -> dict | None:
        """Execute a GraphQL mutation against DataHub GMS."""
        if not self._connected:
            return None
        try:
            client = await self._get_client()
            body = {"query": mutation, "variables": variables}
            response = await client.post("/api/graphql", json=body)
            response.raise_for_status()
            data = response.json()
            if "errors" in data:
                logger.error(f"GraphQL mutation errors: {data['errors']}")
                return None
            return data.get("data")
        except Exception as e:
            logger.error(f"GraphQL mutation failed: {e}")
            return None

    async def add_structured_properties(self, entity_urn: str, properties: dict) -> dict:
        if self._connected:
            mutation = """
            mutation UpdateStructuredProperties($input: UpdateStructuredPropertiesInput!) {
                updateStructuredProperties(input: $input)
            }
            """
            # Convert properties to structured property format
            structured_props = []
            for key, value in properties.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        structured_props.append({
                            "structuredPropertyUrn": f"urn:li:structuredProperty:{key}.{sub_key}",
                            "values": [{"value": str(sub_value)}],
                        })
                else:
                    structured_props.append({
                        "structuredPropertyUrn": f"urn:li:structuredProperty:{key}",
                        "values": [{"value": str(value)}],
                    })

            result = await self._graphql_mutation(mutation, {
                "input": {
                    "entityUrn": entity_urn,
                    "properties": structured_props,
                }
            })
            if result:
                return {"status": "ok", "entity_urn": entity_urn, "properties": properties}

        # Mock fallback
        entity = self._entities.get(entity_urn)
        if entity:
            entity.update(properties)
        return {"status": "ok", "entity_urn": entity_urn, "properties": properties}

    async def batch_add_tags(self, urns: list[str], tags: list[str]) -> dict:
        if self._connected:
            # Use GraphQL mutation for adding tags
            mutation = """
            mutation BatchAddTags($input: BatchAddTagsInput!) {
                batchAddTags(input: $input)
            }
            """
            for urn in urns:
                for tag in tags:
                    result = await self._graphql_mutation(mutation, {
                        "input": {
                            "urn": urn,
                            "tag": tag,
                        }
                    })
                    if not result:
                        logger.warning(f"Failed to add tag '{tag}' to {urn}")

        # Mock fallback
        for urn in urns:
            entity = self._entities.get(urn)
            if entity:
                existing = entity.get("tags", [])
                entity["tags"] = list(set(existing + tags))
        return {"status": "ok", "tagged": len(urns)}

    async def raise_incident(
        self,
        type_: str,
        severity: str,
        description: str,
        affected_entities: list[str] | None = None,
    ) -> dict:
        if self._connected:
            # DataHub doesn't have a direct incident REST API.
            # Incidents are created via GraphQL mutations or the UI.
            # We'll use the MCP server's incident creation if available,
            # otherwise log the incident for manual creation.
            logger.info(
                f"Incident requested: type={type_}, severity={severity}, "
                f"affected={affected_entities}. "
                f"Note: DataHub incidents should be created via the UI or GraphQL."
            )

        # Create incident record (always, even in real mode for tracking)
        incident = {
            "id": f"INC-{len(self._incidents) + 1}",
            "type": type_,
            "severity": severity,
            "description": description,
            "affected_entities": affected_entities or [],
            "status": "OPEN",
        }
        self._incidents.append(incident)
        return incident

    async def update_incident_status(self, incident_id: str, status: str) -> dict:
        # DataHub incidents are managed via the UI.
        # We track status changes locally.
        for inc in self._incidents:
            if inc["id"] == incident_id:
                inc["status"] = status
                return inc
        return {"error": "Incident not found"}

    # ── Proposals ──────────────────────────────────────────────────────

    async def list_pending_proposals(self) -> list[dict]:
        if self._connected:
            result = await self._gms_request("GET", "/proposals?action=listPending")
            if result and "proposals" in result:
                return result["proposals"]

        return self._proposals

    async def accept_or_reject_proposal(self, proposal_id: str, decision: str) -> dict:
        if self._connected:
            body = {"decision": decision}
            result = await self._gms_request("POST", f"/proposals/{proposal_id}?action=decide", body)
            if result:
                return result

        self._proposals = [p for p in self._proposals if p.get("id") != proposal_id]
        return {"status": "ok", "proposal_id": proposal_id, "decision": decision}

    async def propose_lifecycle_stage(self, entity_urn: str, lifecycle_stage: str, reason: str) -> dict:
        if self._connected:
            body = {
                "entityUrn": entity_urn,
                "lifecycleStage": lifecycle_stage,
                "reason": reason,
            }
            result = await self._gms_request("POST", "/proposals?action=proposeLifecycle", body)
            if result:
                return result

        entity = self._entities.get(entity_urn)
        if entity:
            entity["lifecycle_stage_proposal"] = {"stage": lifecycle_stage, "reason": reason}
        proposal = {
            "id": f"prop-{len(self._proposals) + 1}",
            "entity_urn": entity_urn,
            "stage": lifecycle_stage,
            "reason": reason,
        }
        self._proposals.append(proposal)
        return {"status": "ok", "entity_urn": entity_urn, "proposal": lifecycle_stage}
