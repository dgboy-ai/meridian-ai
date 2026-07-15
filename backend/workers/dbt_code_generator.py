"""dbt Code Generator — metadata-aware dbt model generation from DataHub schemas.

Reads actual DataHub entity metadata (schema, lineage, descriptions) and generates
production-ready dbt models. Targets Challenge 2 (Code Generation) of the hackathon.
"""
import json
from datetime import datetime, timezone

from backend.clients.datahub_client import DataHubMCPClient
from backend.clients.groq_client import GroqClient
from backend.models import EvidenceObject, Severity, DataHubMutation


class DbtCodeGenerator:
    def __init__(self, mcp: DataHubMCPClient, groq: GroqClient):
        self.mcp = mcp
        self.groq = groq

    async def generate(
        self,
        source_dataset_urn: str,
        target_model_name: str,
    ) -> EvidenceObject:
        """Generate a dbt model from DataHub metadata.

        Args:
            source_dataset_urn: URN of the source dataset to model
            target_model_name: Name for the generated dbt model
        """
        now = datetime.now(timezone.utc).isoformat()

        # Read source schema from DataHub
        source_fields = await self.mcp.list_schema_fields(source_dataset_urn)
        source_entity = (await self.mcp.get_entities([source_dataset_urn])) or [{}]
        source_name = source_entity[0].get("name", "unknown") if source_entity else "unknown"

        # Read lineage for downstream dependencies
        lineage = await self.mcp.get_lineage(source_dataset_urn, depth=3)

        # Read descriptions and tags for context
        tags = source_entity[0].get("tags", []) if source_entity else []
        owner = source_entity[0].get("owner", "unknown") if source_entity else "unknown"

        messages = [
            {
                "role": "system",
                "content": (
                    "You are the dbt Code Generator for Meridian AI. "
                    "Generate production-ready dbt models from DataHub metadata."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Source Dataset: {source_name} ({source_dataset_urn})\n"
                    f"Platform: {source_entity[0].get('platform', 'unknown') if source_entity else 'unknown'}\n"
                    f"Owner: {owner}\n"
                    f"Tags: {', '.join(tags)}\n"
                    f"Fields: {json.dumps(source_fields, indent=2)}\n"
                    f"Downstream: {json.dumps(lineage.get('downstream', []), indent=2)}\n\n"
                    f"Generate a dbt model named '{target_model_name}' that:\n"
                    "1. References the source with correct dbt source syntax\n"
                    "2. Includes proper column aliases and types\n"
                    "3. Adds data quality assertions\n"
                    "4. Includes documentation blocks\n"
                    "5. Follows dbt best practices (CTEs, naming conventions)\n\n"
                    "Return the dbt SQL code and a schema YAML."
                ),
            },
        ]

        response = self.groq.complete_json(messages, model="reasoning")
        dbt_sql = response.get("dbt_sql", self._default_sql(source_name, target_model_name, source_fields))
        schema_yaml = response.get("schema_yaml", self._default_yaml(target_model_name, source_fields))

        # Save the generated code as a DataHub document
        full_content = f"""# dbt Model: {target_model_name}
Generated: {now}
Source: {source_name} ({source_dataset_urn})
Owner: {owner}

## SQL Model
```sql
{dbt_sql}
```

## Schema YAML
```yaml
{schema_yaml}
```
"""
        await self.mcp.save_document(
            title=f"dbt Model: {target_model_name}",
            content=full_content,
            tags=["dbt", "code-generation", "auto-generated"],
            linked_entities=[source_dataset_urn],
        )

        return EvidenceObject(
            worker_id="dbt_code_generator",
            timestamp=now,
            finding=(
                f"Generated dbt model '{target_model_name}' from {source_name}: "
                f"{len(source_fields)} columns, schema YAML included"
            ),
            confidence=0.90,
            severity=Severity.LOW,
            datahub_mutations=[
                DataHubMutation(
                    tool="save_document",
                    params={"title": f"dbt Model: {target_model_name}"},
                    safe=True,
                ),
                DataHubMutation(
                    tool="batchAddTags",
                    params={"tags": ["dbt", "code-generated"]},
                    safe=True,
                ),
            ],
        )

    def _default_sql(self, source_name: str, model_name: str, fields: list[dict]) -> str:
        """Generate default dbt SQL when LLM is unavailable."""
        columns = ",\n    ".join(f'"{f["name"]}"' for f in fields)
        return f"""{{{{ config(
    materialized='table',
    schema='ml_features',
    tags=['{model_name}', 'auto-generated']
) }}}}

-- Model: {model_name}
-- Source: {source_name}
-- Generated by: Meridian AI dbt Code Generator

with source as (
    select * from {{{{ source('raw', '{source_name}') }}}}
),

transformed as (
    select
        {columns}
    from source
    where _deleted = false
)

select * from transformed"""

    def _default_yaml(self, model_name: str, fields: list[dict]) -> str:
        """Generate default dbt schema YAML when LLM is unavailable."""
        columns_yaml = "\n".join(
            f'      - name: "{f["name"]}"\n        description: "{f.get("name", "")} column"'
            for f in fields
        )
        return f"""version: 2

models:
  - name: {model_name}
    description: "Auto-generated by Meridian AI dbt Code Generator"
    columns:
{columns_yaml}

sources:
  - name: raw
    description: "Raw data sources from DataHub"
    database: meridian
    schema: raw
"""
