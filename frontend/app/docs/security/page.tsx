'use client'

import DocsLayout from '../../../components/docs/DocsLayout'
import { DocH1, DocP, DocBadge, DocH2, DocH3, DocCode, DocInfo, DocTable, DocDivider, DocCard } from '../../../components/docs/DocElements'

export default function SecurityPage() {
  return (
    <DocsLayout>
      <DocBadge color="#f43f5e">Security & Compliance</DocBadge>
      <DocH1>Security & Compliance</DocH1>
      <DocP>
        Meridian AI implements production-grade security patterns and EU AI Act compliance
        with cryptographically verifiable audit trails.
      </DocP>

      <DocH2>EU AI Act Compliance</DocH2>
      <DocP>
        The EU AI Act enforcement date is <strong style={{ color: '#f43f5e' }}>August 2, 2026</strong> —
        22 days before the hackathon deadline. Meridian generates a Technical File for every
        investigation, covering Articles 12, 13, and 14.
      </DocP>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px', margin: '16px 0' }}>
        <DocCard title="Article 12: Record-Keeping" icon="📋" color="#f43f5e">
          Automatic logging of all AI decisions with timestamps, confidence scores,
          and reasoning chains. SHA-256 hash chain ensures tamper-proof records.
        </DocCard>
        <DocCard title="Article 13: Transparency" icon="👁" color="#f59e0b">
          Every investigation step is explainable. The Investigation Timeline shows
          what the AI found, why it concluded what it did, and what it did next.
        </DocCard>
        <DocCard title="Article 14: Human Oversight" icon="🛡" color="#10b981">
          Progressive Autonomy ensures humans approve irreversible actions.
          Maker-checker verification before any DataHub write-back.
        </DocCard>
      </div>

      <DocH2>SHA-256 Audit Chain</DocH2>
      <DocP>
        Every AI decision is logged with a SHA-256 hash. Each hash includes the previous
        hash, creating a blockchain-like chain that&apos;s cryptographically verifiable.
      </DocP>

      <DocCode>{`# Each audit record includes:
{
  "record_id": "audit-2026-07-12T14:32:00Z",
  "timestamp": "2026-07-12T14:32:00Z",
  "article": "12",
  "system_name": "Meridian AI",
  "decision_type": "ROOT_CAUSE_ANALYSIS",
  "confidence": 0.96,
  "reasoning_chain": [
    "Schema change detected in raw_events.age",
    "Lineage traversal: raw_events → feature_pipeline → churn_model_v3",
    "Blast radius: 3 models, 12 dashboards"
  ],
  "hash_sha256": "a1b2c3d4...",
  "previous_hash": "e5f6g7h8..."
}`}</DocCode>

      <DocH2>Deterministic Validation</DocH2>
      <DocP>
        Before any write-back to DataHub, Meridian runs 4 deterministic checks.
        LLMs reason. Code verifies. Then write back.
      </DocP>

      <DocTable
        headers={['Check', 'What It Does', 'On Failure']}
        rows={[
          ['Confidence Threshold', 'Worker confidence must be > 0.7', 'Reject, request more evidence'],
          ['Entity Exists', 'DataHub URN verified before mutation', 'Reject, log error'],
          ['Action Safety', 'Destructive actions need human approval', 'Queue for review'],
          ['Duplicate Check', 'Prevents raising duplicate incidents', 'Skip, update existing'],
        ]}
      />

      <DocH2>Maker-Checker Verification</DocH2>
      <DocP>
        The VerifierAgent challenges RootCause conclusions before write-back.
        This ensures no incorrect knowledge enters DataHub.
      </DocP>

      <DocInfo type="warning">
        If verification confidence falls below 0.5, the knowledge write-back is skipped entirely.
        The investigation still completes, but no artifacts are written to DataHub.
      </DocInfo>

      <DocH2>Security Measures</DocH2>
      <DocTable
        headers={['Measure', 'Implementation']}
        rows={[
          ['Authentication', 'JWT (opt-in via AUTH_ENABLED=true)'],
          ['Input Validation', 'Pydantic schemas validate all API inputs'],
          ['Rate Limiting', '60 req/min (configurable via MAX_RPM)'],
          ['Body Size Limits', '10MB max (configurable via MAX_BODY_SIZE)'],
          ['CORS', 'Configurable origins (default: * for dev)'],
          ['Secrets', 'Environment variables, never in code'],
          ['Audit Trail', 'SHA-256 hash chain for all AI decisions'],
          ['Docker', 'Non-root user, health checks, resource limits'],
        ]}
      />

      <DocH2>Agentic Circuit Breaker</DocH2>
      <DocP>
        Monitors agent reasoning health in real-time. Detects infinite loops,
        semantic drift, and confidence degradation. Halts the agent when safety
        thresholds are breached.
      </DocP>

      <DocCode>{`# Circuit breaker monitors:
- Loop detection (repeated identical reasoning)
- Semantic drift (conclusions diverging from evidence)
- Confidence degradation (declining worker confidence)
- Timeout enforcement (max investigation duration)`}</DocCode>

      <DocH2>Provenance Tracking</DocH2>
      <DocP>
        Every worker tracks which context sources were used. Full audit trail
        for compliance and debugging. Source trust and freshness scoring ensures
        agents use verified data.
      </DocP>
    </DocsLayout>
  )
}
