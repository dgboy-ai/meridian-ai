'use client'

import { motion } from 'framer-motion'
import DocsLayout from '../../../components/docs/DocsLayout'
import { DocH1, DocP, DocBadge, DocH2, DocH3, DocCode, DocInfo, DocTable, DocDivider, DocCard } from '../../../components/docs/DocElements'

export default function ArchitecturePage() {
  return (
    <DocsLayout>
      <DocBadge color="#8b5cf6">Architecture</DocBadge>
      <DocH1>How Meridian AI Works</DocH1>
      <DocP>
        18 workers fire in parallel, each computing real things — PSI, KS-test,
        schema diff, lineage traversal — not LLM guessing.
      </DocP>

      <DocH2>Architecture Overview</DocH2>

      {/* Architecture diagram */}
      <div style={{
        padding: '32px',
        borderRadius: '16px',
        background: 'rgba(12, 8, 28, 0.6)',
        border: '1px solid rgba(255,255,255,0.06)',
        margin: '24px 0',
        fontFamily: "'SF Mono', Consolas, monospace",
        fontSize: '12px',
        lineHeight: 1.8,
        color: 'rgba(255,255,255,0.6)',
        overflow: 'auto',
      }}>
        <pre style={{ margin: 0 }}>{`
┌─────────────────────────────────────────────────────────┐
│                    TRIGGER                               │
│  Scheduled scan · Actions Framework · User request       │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│              PLANNER AGENT (18 workers)                  │
│  Llama 3 70B via Groq                                    │
│  Detects → Diagnoses → Remediates → Learns              │
│  AutonomyManager gates each worker                      │
│  HealthScore computed from real worker confidence        │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│              DETERMINISTIC VALIDATION                     │
│  Confidence > 0.7 · Entity exists · Safe ops             │
│  Maker-checker: VerifierAgent challenges RootCause       │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│              WRITE-BACK TO DATAHUB                       │
│  Root cause report · AI Knowledge panel · Playbook       │
│  Incident record · EU AI Act Technical File              │
│  5 artifacts per investigation                           │
└─────────────────────────────────────────────────────────┘`}</pre>
      </div>

      <DocH2>The Workers</DocH2>
      <DocP>
        Every worker uses real computation. PSI is real math. KS-test is real math.
        Lineage traversal is real graph algorithms. No LLM guessing.
      </DocP>

      <DocTable
        headers={['Worker', 'Phase', 'What It Computes']}
        rows={[
          ['Planner Agent', 'Orchestration', 'Decomposes goal, assigns workers, tracks progress'],
          ['Data Sentinel', 'Detection', 'Schema diff + freshness + PII + data quality + volume'],
          ['Feature Drift', 'Detection', 'PSI/KS-test per feature + type mismatch'],
          ['Training-Serving Skew', 'Detection', 'Schema comparison + distribution drift'],
          ['Data Leakage', 'Detection', 'Temporal pattern detection'],
          ['Root Cause', 'Diagnosis', 'Column-level lineage traversal + blast radius'],
          ['VerifierAgent', 'Verification', 'Challenges RootCause before write-back'],
          ['Knowledge Writer', 'Enforcement', '5 DataHub writes per investigation'],
          ['Reflexion Loop', 'Learning', 'Self-RAG playbook improvement'],
          ['Lifecycle Governance', 'Governance', 'Health evaluation + proposals'],
          ['EU AI Act Compliance', 'Compliance', 'SHA-256 audit chain + Technical File'],
          ['Shadow AI Discovery', 'Governance', 'Ungoverned model detection'],
          ['Contract Enforcer', 'Enforcement', 'Assertion checking + quarantine'],
          ['Explanation Drift', 'Detection', 'Feature importance shift via PSI'],
          ['Self-Healing Assertions', 'Learning', 'Preventive assertion generation'],
          ['Pipeline Circuit Breaker', 'Enforcement', 'Halts downstream on upstream failure'],
          ['Deprecation Advisor', 'Governance', 'Safe deprecation of unused assets'],
          ['ML Metadata Integrator', 'Detection', 'MLModelDeployment, MLFeatureTable queries'],
        ]}
      />

      <DocH2>Deterministic Validation Layer</DocH2>
      <DocP>
        LLMs reason. Code verifies. Then write back. This is how Meridian ensures
        every write to DataHub is safe and justified.
      </DocP>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px', margin: '16px 0' }}>
        {[
          { title: 'Confidence Threshold', desc: 'Worker confidence must be > 0.7', color: '#8b5cf6', icon: '✓' },
          { title: 'Entity Exists', desc: 'DataHub URN verified before mutation', color: '#6366f1', icon: '✓' },
          { title: 'Action Safety', desc: 'Destructive ops queued for human approval', color: '#f59e0b', icon: '⚠' },
          { title: 'Duplicate Check', desc: 'Prevents raising duplicate incidents', color: '#10b981', icon: '✓' },
        ].map((check) => (
          <div key={check.title} style={{
            padding: '16px',
            borderRadius: '12px',
            background: 'rgba(12, 8, 28, 0.5)',
            border: '1px solid rgba(255,255,255,0.06)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ color: check.color, fontSize: '14px' }}>{check.icon}</span>
              <span style={{ fontSize: '13px', fontWeight: 700, color: '#fff' }}>{check.title}</span>
            </div>
            <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>{check.desc}</div>
          </div>
        ))}
      </div>

      <DocH2>Progressive Autonomy</DocH2>
      <DocP>
        Meridian implements 5 levels of agent autonomy — from advisory to self-improving.
        Agents ask permission for irreversible actions.
      </DocP>
      <DocTable
        headers={['Level', 'Name', 'Behavior']}
        rows={[
          ['0', 'Advisory', 'Suggests only; human executes'],
          ['1', 'Supervised', 'Executes with pre-approval'],
          ['2', 'Monitored', 'Executes; human reviews post-hoc'],
          ['3', 'Autonomous', 'Executes without human involvement'],
          ['4', 'Self-improving', 'Refines its own procedures via reflexion'],
        ]}
      />

      <DocH2>DSA Algorithms (11 Implemented)</DocH2>
      <DocP>
        Real graph algorithms for lineage traversal and drift detection.
      </DocP>
      <DocTable
        headers={['Algorithm', 'Complexity', 'Purpose']}
        rows={[
          ['BFS Lineage', 'O(V+E)', 'Multi-hop lineage traversal'],
          ['DFS Lineage', 'O(V+E)', 'Deep graph exploration'],
          ['Topological Sort', 'O(V+E)', 'Pipeline dependency ordering'],
          ['Cycle Detection', 'O(V+E)', 'Graph validation'],
          ['Shortest Path', 'O(V+E)', 'Fastest propagation path'],
          ['Connected Components', 'O(V+E)', 'Lineage grouping'],
          ['Binary Search CDF', 'O(log n)', 'Fast CDF lookup'],
          ['KS-Test Binary', 'O((n+m)log(n+m))', 'Drift detection'],
          ['Union-Find', 'O(α(n))', 'Connectivity queries'],
          ['Trie', 'O(m)', 'Entity prefix search'],
          ['Min-Heap Top-K', 'O(n log k)', 'Fast top-k selection'],
        ]}
      />

      <DocH2>Tech Stack</DocH2>
      <DocTable
        headers={['Layer', 'Technology']}
        rows={[
          ['Backend', 'Python 3.11+ FastAPI (async)'],
          ['LLM Inference', 'Groq (Llama 3 70B) — $0 via free tier'],
          ['DataHub Integration', 'MCP Server + GraphQL (dual-mode: real + mock)'],
          ['Statistical Computation', 'PSI, KS-test, schema diff (pure Python)'],
          ['Compliance', 'EU AI Act SHA-256 audit chain'],
          ['Frontend', 'Next.js 14 + Framer Motion'],
          ['Deployment', 'Docker Compose (DataHub + MySQL + Kafka + ES)'],
          ['Testing', '552 tests (pytest + pytest-asyncio)'],
        ]}
      />
    </DocsLayout>
  )
}
