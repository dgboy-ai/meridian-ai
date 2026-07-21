'use client'

import DocsLayout from '../../../components/docs/DocsLayout'
import { DocH1, DocP, DocBadge, DocH2, DocH3, DocCode, DocInfo, DocTable, DocDivider } from '../../../components/docs/DocElements'

export default function ApiPage() {
  return (
    <DocsLayout>
      <DocBadge color="#06b6d4">API Reference</DocBadge>
      <DocH1>API Reference</DocH1>
      <DocP>
        Meridian AI exposes a REST API, MCP Server tools, and a CLI.
      </DocP>

      <DocH2>REST API Endpoints</DocH2>
      <DocTable
        headers={['Method', 'Endpoint', 'Description']}
        rows={[
          ['GET', '/health', 'Basic health check'],
          ['GET', '/health/ready', 'Readiness probe'],
          ['GET', '/health/live', 'Liveness probe'],
          ['GET', '/metrics', 'Prometheus-compatible metrics'],
          ['GET', '/api/incidents', 'List all incidents'],
          ['GET', '/api/incidents/:id', 'Get incident details'],
          ['GET', '/api/models/:name', 'Get model metadata'],
          ['GET', '/api/health-scores', 'Get health scores for all models'],
          ['GET', '/api/resolution-times', 'Get resolution time trends'],
          ['POST', '/api/investigate', 'Start a live investigation'],
          ['GET', '/api/costs', 'Get cost/ROI summary'],
          ['GET', '/api/system/architecture', 'System architecture info'],
          ['GET', '/api/system/health', 'Detailed system health'],
          ['GET', '/api/compliance/audit-trail', 'Full audit trail'],
          ['GET', '/api/compliance/eu-ai-act/:id', 'EU AI Act Technical File'],
        ]}
      />

      <DocH2>SSE Streaming Endpoints</DocH2>
      <DocTable
        headers={['Endpoint', 'Description']}
        rows={[
          ['/stream/replay?incident_id=42', 'Stream pre-recorded investigation events'],
          ['/stream/investigate?dataset_urn=...&mode=live', 'Stream live investigation events'],
        ]}
      />

      <DocH2>MCP Server Tools</DocH2>
      <DocP>
        Meridian exposes itself as MCP tools so any AI agent can trigger investigations.
      </DocP>

      <DocH3>meridian_investigate</DocH3>
      <DocP>Run a full ML incident investigation. Writes to DataHub.</DocP>
      <DocCode>{`{
  "model_urn": "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)",
  "incident_id": "optional-custom-id"
}`}</DocCode>

      <DocH3>meridian_health</DocH3>
      <DocP>Check ML health score for a model. Read-only.</DocP>
      <DocCode>{`{
  "model_urn": "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)"
}`}</DocCode>

      <DocH3>meridian_playbook</DocH3>
      <DocP>View the latest reflexion playbook for a failure pattern. Read-only.</DocP>
      <DocCode>{`{
  "pattern_id": "schema-change-type-mismatch"
}`}</DocCode>

      <DocH2>CLI Commands</DocH2>
      <DocTable
        headers={['Command', 'Description']}
        rows={[
          ['meridian investigate <model_urn>', 'Run full investigation'],
          ['meridian health <model_urn>', 'Check model health'],
          ['meridian playbook <pattern_id>', 'View a playbook'],
          ['meridian seed', 'Seed demo data'],
          ['meridian serve --port 8000', 'Start the API server'],
        ]}
      />

      <DocH2>DataHub Integration</DocH2>
      <DocP>
        Meridian uses 15 DataHub capabilities. Here&apos;s the complete mapping:
      </DocP>

      <DocH3>Read via MCP Server</DocH3>
      <DocCode>{`search, get_entities, get_lineage, get_lineage_paths_between,
list_schema_fields, get_dataset_queries, search_documents`}</DocCode>

      <DocH3>Write via MCP + GraphQL</DocH3>
      <DocCode>{`save_document, add_structured_properties, raise_incident,
batch_add_tags, update_incident_status`}</DocCode>

      <DocH3>Governance</DocH3>
      <DocCode>{`propose_lifecycle_stage, list_pending_proposals`}</DocCode>

      <DocH3>Orchestration</DocH3>
      <DocCode>{`Actions Framework YAML (config/actions/meridian_auto_trigger.yaml)`}</DocCode>

      <DocInfo type="tip">
        Switch between mock and real mode with:
        export DATAHUB_MOCK=false
        export DATAHUB_GMS_URL=http://localhost:8080/api/gms
      </DocInfo>
    </DocsLayout>
  )
}
