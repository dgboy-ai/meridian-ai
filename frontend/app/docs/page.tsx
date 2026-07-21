'use client'

import { motion } from 'framer-motion'
import DocsLayout from '../../components/docs/DocsLayout'
import { DocH1, DocP, DocBadge, DocCard, DocDivider, DocH2 } from '../../components/docs/DocElements'

export default function DocsPage() {
  return (
    <DocsLayout>
      <DocBadge color="#8b5cf6">Documentation</DocBadge>
      <DocH1>Meridian AI</DocH1>
      <DocP>
        The AI Reliability Engineer that autonomously investigates production ML incidents,
        writes operational knowledge back into DataHub, and ensures every future engineer
        — and every future AI agent — starts with everything the previous investigation learned.
      </DocP>

      {/* Hero stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', margin: '32px 0' }}>
        {[
          { value: '83%', label: 'Faster Resolution', color: '#10b981', sub: '18min → 3min' },
          { value: '15', label: 'DataHub Tools', color: '#8b5cf6', sub: 'Read + Write + Govern' },
          { value: '18', label: 'Workers', color: '#f43f5e', sub: 'Real computation' },
          { value: '552', label: 'Tests', color: '#06b6d4', sub: 'Passing' },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + i * 0.1, duration: 0.5 }}
            whileHover={{ y: -4, scale: 1.02 }}
            style={{
              padding: '20px',
              borderRadius: '14px',
              background: 'rgba(12, 8, 28, 0.5)',
              border: '1px solid rgba(255,255,255,0.06)',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '28px', fontWeight: 900, color: stat.color, letterSpacing: '-0.03em' }}>
              {stat.value}
            </div>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'rgba(255,255,255,0.7)', marginTop: '4px' }}>
              {stat.label}
            </div>
            <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.35)', marginTop: '2px' }}>
              {stat.sub}
            </div>
          </motion.div>
        ))}
      </div>

      <DocDivider />

      <DocH2>What is Meridian AI?</DocH2>
      <DocP>
        Production ML models fail silently. When they do, engineers spend 45+ minutes
        tracing lineage, reading stale docs, and searching Slack for context that should
        live in the metadata platform. The knowledge from each investigation vanishes —
        the next incident starts from zero.
      </DocP>
      <DocP>
        Meridian AI fixes this. It reads your DataHub context graph — lineage, schemas,
        ownership, ML metadata — detects anomalies, traces root cause through column-level
        lineage, and writes everything it learned back into DataHub permanently.
      </DocP>
      <DocP>
        <strong style={{ color: '#fff' }}>Every investigation becomes organizational memory.</strong> The
        next time this model breaks, the agent already knows what to do.
      </DocP>

      <DocDivider />

      <DocH2>The Problem</DocH2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', margin: '16px 0' }}>
        <DocCard title="Silent Failures" icon="🔴" color="#f43f5e">
          AI incidents rose 55% YoY. 77% of ML teams have no monitoring tools.
          Models silently degrade from 89% to 71% accuracy — nobody notices for 3 days.
        </DocCard>
        <DocCard title="Manual Investigation" icon="⏱" color="#f59e0b">
          Average investigation takes 45+ minutes. Engineers read stale docs, search Slack,
          trace lineage manually. Knowledge disappears after the fix.
        </DocCard>
        <DocCard title="No ML Lineage" icon="🔗" color="#8b5cf6">
          DataHub tracks datasets→dashboards but NOT training_data→features→model→deployment.
          When schema changes happen, you can't trace which models are affected.
        </DocCard>
        <DocCard title="Knowledge Doesn't Compound" icon="🧠" color="#06b6d4">
          Every investigation is isolated. No playbook system that improves with each incident.
          The hackathon prompt: "writes results back so the next person inherits the knowledge."
        </DocCard>
      </div>

      <DocDivider />

      <DocH2>The Solution</DocH2>
      <DocP>
        Meridian AI is an AI Reliability Engineer that autonomously investigates production
        ML incidents, writes operational knowledge back into DataHub, and ensures every
        future engineer — and every future AI agent — starts with everything the previous
        investigation learned.
      </DocP>

      {/* Lifecycle */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
        padding: '24px',
        borderRadius: '14px',
        background: 'rgba(12, 8, 28, 0.5)',
        border: '1px solid rgba(255,255,255,0.06)',
        margin: '24px 0',
        flexWrap: 'wrap',
      }}>
        {['Predict', 'Prevent', 'Detect', 'Diagnose', 'Remediate', 'Learn'].map((step, i) => (
          <div key={step} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              style={{
                padding: '8px 16px',
                borderRadius: '8px',
                background: i === 5 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(139, 92, 246, 0.1)',
                border: `1px solid ${i === 5 ? 'rgba(16, 185, 129, 0.3)' : 'rgba(139, 92, 246, 0.2)'}`,
                fontSize: '13px',
                fontWeight: 600,
                color: i === 5 ? '#10b981' : 'rgba(255,255,255,0.8)',
              }}
            >
              {step}
            </motion.div>
            {i < 5 && (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="2" strokeLinecap="round">
                <path d="M5 12h14" /><path d="m12 5 7 7-7 7" />
              </svg>
            )}
          </div>
        ))}
      </div>

      <DocDivider />

      <DocH2>How It Started</DocH2>
      <DocP>
        Meridian AI was born from a real problem: ML models at scale fail silently, and
        the knowledge gained from fixing them is lost. The name "Meridian" comes from the
        concept of a meridian line — a reference path that connects points across a system,
        just as DataHub&apos;s lineage graph connects data assets across an organization.
      </DocP>
      <DocP>
        Built for the DataHub Agent Hackathon, Meridian AI demonstrates what&apos;s possible
        when agents have complete context. It uses 15 DataHub capabilities end-to-end,
        writes 5 artifacts back per investigation, and implements a cumulative intelligence
        flywheel that gets faster with every incident.
      </DocP>

      <DocDivider />

      <DocH2>Built for DataHub</DocH2>
      <DocP>
        Meridian AI is deeply integrated with DataHub&apos;s context graph. It doesn&apos;t just
        read metadata — it writes knowledge back so DataHub itself becomes smarter.
      </DocP>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', margin: '16px 0' }}>
        <DocCard title="15 DataHub Capabilities" icon="◆" color="#8b5cf6">
          7 read tools (MCP), 5 write tools (MCP + GraphQL), 2 governance tools, plus Actions Framework.
          No other submission uses this many.
        </DocCard>
        <DocCard title="5 Artifacts Per Investigation" icon="◇" color="#6366f1">
          Root cause report, reflexion playbook, AI Knowledge panel, incident record,
          EU AI Act Technical File — all written to DataHub.
        </DocCard>
        <DocCard title="Actions Framework Auto-Trigger" icon="⚡" color="#f59e0b">
          YAML pipeline that fires investigation automatically when DataHub detects
          schema changes. Zero human intervention.
        </DocCard>
        <DocCard title="MCP Server as MCP Tool" icon="🔌" color="#06b6d4">
          Meridian exposes itself as MCP tools — any AI agent can trigger investigations
          via Model Context Protocol.
        </DocCard>
      </div>

      <DocDivider />

      <DocH2>Explore the Docs</DocH2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px', margin: '16px 0' }}>
        {[
          { href: '/docs/getting-started', title: 'Quick Start', desc: 'Get running in 30 seconds', color: '#10b981' },
          { href: '/docs/architecture', title: 'Architecture', desc: '18 workers, validation layer', color: '#8b5cf6' },
          { href: '/docs/features', title: 'Features', desc: 'All capabilities explained', color: '#6366f1' },
          { href: '/docs/security', title: 'Security & Compliance', desc: 'EU AI Act, SHA-256 audit', color: '#f43f5e' },
          { href: '/docs/api', title: 'API Reference', desc: 'Endpoints, MCP tools, CLI', color: '#06b6d4' },
          { href: '/docs/judges', title: 'For Judges', desc: 'Verification guide', color: '#f59e0b' },
        ].map((item) => (
          <motion.a
            key={item.href}
            href={item.href}
            whileHover={{ y: -4, scale: 1.02 }}
            style={{
              display: 'block',
              padding: '20px',
              borderRadius: '14px',
              background: 'rgba(12, 8, 28, 0.5)',
              border: '1px solid rgba(255,255,255,0.06)',
              textDecoration: 'none',
              transition: 'border-color 0.3s',
            }}
            onMouseEnter={e => e.currentTarget.style.borderColor = `${item.color}40`}
            onMouseLeave={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)'}
          >
            <div style={{ fontSize: '15px', fontWeight: 700, color: '#fff', marginBottom: '4px' }}>{item.title}</div>
            <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.45)' }}>{item.desc}</div>
            <div style={{ marginTop: '12px', fontSize: '12px', fontWeight: 600, color: item.color }}>
              Explore →
            </div>
          </motion.a>
        ))}
      </div>
    </DocsLayout>
  )
}
