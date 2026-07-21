'use client'

import DocsLayout from '../../../components/docs/DocsLayout'
import { DocH1, DocP, DocBadge, DocH2, DocH3, DocCode, DocInfo, DocTable, DocDivider, DocCard } from '../../../components/docs/DocElements'

export default function FeaturesPage() {
  return (
    <DocsLayout>
      <DocBadge color="#6366f1">Features</DocBadge>
      <DocH1>Features</DocH1>
      <DocP>
        16 production-ready capabilities across detection, diagnosis, enforcement,
        learning, compliance, and governance.
      </DocP>

      <DocH2>Core Investigation</DocH2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px', margin: '16px 0' }}>
        <DocCard title="Column-Level Lineage" icon="🔗" color="#8b5cf6">
          Traces exact column dependencies through the lineage graph. BFS/DFS
          traversal with O(V+E) complexity. Finds root cause across 5+ hops.
        </DocCard>
        <DocCard title="Pipeline Circuit Breaker" icon="⚡" color="#f43f5e">
          Halts downstream pipelines when upstream quality fails. Uses lineage-based
          impact analysis to determine blast radius.
        </DocCard>
        <DocCard title="Safe Deprecation Advisor" icon="📋" color="#f59e0b">
          Identifies unused datasets and proposes safe deprecation. Verifies no
          downstream consumers before recommending removal.
        </DocCard>
        <DocCard title="VerifierAgent" icon="🛡" color="#10b981">
          Maker-checker validation. Challenges RootCause conclusions before write-back.
          Ensures no incorrect knowledge enters DataHub.
        </DocCard>
      </div>

      <DocH2>Intelligence & Learning</DocH2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px', margin: '16px 0' }}>
        <DocCard title="Reflexion Loop" icon="🧠" color="#8b5cf6">
          Self-RAG playbook improvement after every incident. Playbook for
          "schema-change-type-mismatch" gets refined after each occurrence.
          Resolution time: 18min → 8min → 3min.
        </DocCard>
        <DocCard title="Semantic Search" icon="🔍" color="#6366f1">
          Vector-based playbook retrieval. Finds relevant past investigations
          even when patterns don&apos;t match exactly.
        </DocCard>
        <DocCard title="Adaptive Assertions" icon="📊" color="#06b6d4">
          Learns from historical patterns to generate preventive dataset contract
          assertions. Prevents future failures before they happen.
        </DocCard>
        <DocCard title="Self-Healing Assertions" icon="🔄" color="#10b981">
          Generates preventive assertions from incident patterns. Each investigation
          makes the system more resilient.
        </DocCard>
      </div>

      <DocH2>Compliance & Governance</DocH2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px', margin: '16px 0' }}>
        <DocCard title="EU AI Act Compliance" icon="📜" color="#f43f5e">
          SHA-256 audit chain for Articles 12 (Record-Keeping), 13 (Transparency),
          14 (Human Oversight). Technical File generated per investigation.
          Enforcement: August 2, 2026.
        </DocCard>
        <DocCard title="Bias Detection Lineage" icon="⚖️" color="#f59e0b">
          Checks for demographic skew and label imbalance in training data.
          Traces bias propagation through lineage.
        </DocCard>
        <DocCard title="PII Propagation" icon="🔒" color="#ec4899">
          Tracks PII flow through lineage to downstream columns. Identifies
          where sensitive data reaches unexpected consumers.
        </DocCard>
        <DocCard title="Shadow AI Discovery" icon="👤" color="#8b5cf6">
          Finds ungoverned ML models — models without owners, documentation,
          or quality checks. Surfaces governance gaps.
        </DocCard>
      </div>

      <DocH2>Agent Safety</DocH2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px', margin: '16px 0' }}>
        <DocCard title="Agentic Circuit Breaker" icon="🔌" color="#f43f5e">
          Monitors agent reasoning health. Detects infinite loops, semantic drift,
          and confidence degradation. Halts agent when safety thresholds are breached.
        </DocCard>
        <DocCard title="Provenance Validation" icon="✅" color="#10b981">
          Validates context before LLM calls. Ensures agents use verified,
          fresh data sources — not stale or hallucinated context.
        </DocCard>
        <DocCard title="Agent Provenance Tracking" icon="📋" color="#06b6d4">
          Tracks which context sources were used by each worker. Full audit trail
          for compliance and debugging.
        </DocCard>
        <DocCard title="Saga Pattern" icon="🔄" color="#8b5cf6">
          Compensating transactions for data integrity. If a write-back fails,
          the system rolls back previous mutations.
        </DocCard>
      </div>

      <DocH2>DataHub Integration (15 Capabilities)</DocH2>
      <DocH3>Read Operations (MCP Server)</DocH3>
      <DocTable
        headers={['Capability', 'Purpose', 'Used By']}
        rows={[
          ['search', 'Find production assets by query/tags', 'DataSentinel, RootCause'],
          ['get_entities', 'Batch metadata for any entity', 'All workers'],
          ['get_lineage', 'Upstream/downstream traversal', 'RootCause, PipelineCircuitBreaker'],
          ['get_lineage_paths_between', 'Exact path between two entities', 'Blast radius calculation'],
          ['list_schema_fields', 'Column-level metadata', 'DataSentinel, FeatureDrift'],
          ['get_dataset_queries', 'Real SQL referencing datasets', 'DataSentinel'],
          ['search_documents', 'Find past playbooks in Knowledge Base', 'ReflexionLoop'],
        ]}
      />

      <DocH3>Write Operations (MCP + GraphQL)</DocH3>
      <DocTable
        headers={['Capability', 'Purpose', 'Used By']}
        rows={[
          ['save_document', 'Persist root cause reports + playbooks', 'KnowledgeWriter, ReflexionLoop'],
          ['add_structured_properties', 'Update AI Knowledge panels', 'KnowledgeWriter, DataSentinel'],
          ['raise_incident', 'Create incidents programmatically', 'KnowledgeWriter'],
          ['batch_add_tags', 'Tag all affected assets in bulk', 'KnowledgeWriter, ContractEnforcer'],
          ['update_incident_status', 'Close/resolved incidents', 'KnowledgeWriter'],
        ]}
      />

      <DocH3>Governance & Proposals</DocH3>
      <DocTable
        headers={['Capability', 'Purpose', 'Used By']}
        rows={[
          ['propose_lifecycle_stage', 'Propose DEPRECATED for failing models', 'LifecycleGovernance'],
          ['list_pending_proposals', 'Check queued governance proposals', 'LifecycleGovernance'],
        ]}
      />

      <DocInfo type="tip">
        Meridian also exposes itself as MCP tools — any AI agent can trigger
        investigations via Model Context Protocol. See the API Reference for details.
      </DocInfo>
    </DocsLayout>
  )
}
