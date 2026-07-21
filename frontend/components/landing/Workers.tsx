'use client'

import { motion } from 'framer-motion'

const workers = [
  { name: 'Data Sentinel', math: 'compute_schema_diff', category: 'Detection' },
  { name: 'Feature Drift', math: 'population_stability_index', category: 'Detection' },
  { name: 'Training-Serving Skew', math: 'ks_test', category: 'Detection' },
  { name: 'Data Leakage', math: 'check_temporal_leakage', category: 'Detection' },
  { name: 'Root Cause', math: 'traverse_column_lineage', category: 'Diagnosis' },
  { name: 'VerifierAgent', math: 'maker-checker validation', category: 'Verification' },
  { name: 'Knowledge Writer', math: 'DataHub mutations', category: 'Enforcement' },
  { name: 'Reflexion Loop', math: 'Self-RAG playbook', category: 'Learning' },
  { name: 'Lifecycle Governance', math: 'health_threshold decisions', category: 'Governance' },
  { name: 'EU AI Act Compliance', math: 'SHA-256 audit chain', category: 'Compliance' },
  { name: 'Shadow AI Discovery', math: 'governance gap detection', category: 'Governance' },
  { name: 'Contract Enforcer', math: 'quarantine_assertions', category: 'Enforcement' },
  { name: 'Explanation Drift', math: 'PSI on importance', category: 'Detection' },
  { name: 'Self-Healing', math: 'preventative mapping', category: 'Learning' },
  { name: 'Pipeline Circuit Breaker', math: 'BFS dependency halt', category: 'Enforcement' },
  { name: 'dbt Code Generator', math: 'metadata-aware SQL', category: 'Generation' },
  { name: 'Deprecation Advisor', math: 'lineage impact analysis', category: 'Governance' },
  { name: 'Agentic Circuit Breaker', math: 'reasoning health monitor', category: 'Verification' },
]

const categoryColors: Record<string, string> = {
  Detection: '#f43f5e',
  Diagnosis: '#8b5cf6',
  Verification: '#ec4899',
  Enforcement: '#6366f1',
  Learning: '#10b981',
  Compliance: '#06b6d4',
  Governance: '#f59e0b',
  Generation: '#a855f7',
}

const container = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.03 },
  },
}

const item = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  show: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } },
}

export default function Workers() {
  return (
    <section id="workers" style={{
      position: 'relative',
      padding: '120px 32px',
      background: 'linear-gradient(180deg, transparent 0%, rgba(15, 5, 35, 0.25) 50%, transparent 100%)',
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '64px' }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '100px',
              background: 'rgba(139, 92, 246, 0.08)',
              border: '1px solid rgba(139, 92, 246, 0.15)',
              marginBottom: '24px',
            }}
          >
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'rgba(255, 255, 255, 0.6)' }}>18 Workers</span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            style={{
              fontSize: 'clamp(28px, 3.5vw, 40px)',
              fontWeight: 800,
              lineHeight: 1.15,
              letterSpacing: '-0.03em',
              color: '#fff',
              maxWidth: '560px',
              margin: '0 auto 16px',
            }}
          >
            Every worker computes{' '}
            <span style={{ background: 'linear-gradient(135deg, #f43f5e, #ec4899)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              real math
            </span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            style={{ fontSize: '15px', color: 'rgba(255, 255, 255, 0.45)', maxWidth: '480px', margin: '0 auto', lineHeight: 1.6 }}
          >
            No LLM guessing. PSI, KS-test, BFS lineage traversal, SHA-256 audit chains — all deterministic.
          </motion.p>
        </div>

        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: '-50px' }}
          style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '10px' }}
        >
          {workers.map((worker) => {
            const color = categoryColors[worker.category] || '#8b5cf6'
            return (
              <motion.div
                key={worker.name}
                variants={item}
                whileHover={{ y: -4, scale: 1.03 }}
                style={{
                  padding: '18px',
                  borderRadius: '12px',
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid rgba(255, 255, 255, 0.05)',
                  cursor: 'default',
                  position: 'relative',
                  overflow: 'hidden',
                  transition: 'border-color 0.3s, box-shadow 0.3s',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = `${color}40`
                  e.currentTarget.style.boxShadow = `0 4px 20px ${color}10`
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.05)'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              >
                {/* Subtle corner glow */}
                <div style={{
                  position: 'absolute',
                  top: '-20px',
                  right: '-20px',
                  width: '60px',
                  height: '60px',
                  borderRadius: '50%',
                  background: `radial-gradient(circle, ${color}10 0%, transparent 70%)`,
                  pointerEvents: 'none',
                }} />

                <div style={{ display: 'inline-block', padding: '2px 8px', borderRadius: '4px', background: `${color}12`, color: color, fontSize: '10px', fontWeight: 600, marginBottom: '10px', position: 'relative' }}>
                  {worker.category}
                </div>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#fff', marginBottom: '4px', position: 'relative' }}>{worker.name}</div>
                <div style={{ fontSize: '12px', fontFamily: 'monospace', color: 'rgba(255, 255, 255, 0.35)', position: 'relative' }}>{worker.math}()</div>
              </motion.div>
            )
          })}
        </motion.div>
      </div>
    </section>
  )
}
