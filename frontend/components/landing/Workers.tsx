'use client'

import { motion } from 'framer-motion'

const workers = [
  { name: 'Data Sentinel', math: 'compute_schema_diff', category: 'Detection' },
  { name: 'Feature Drift', math: 'population_stability_index', category: 'Detection' },
  { name: 'Training-Serving Skew', math: 'ks_test', category: 'Detection' },
  { name: 'Data Leakage', math: 'check_temporal_leakage', category: 'Detection' },
  { name: 'Root Cause', math: 'traverse_column_lineage', category: 'Diagnosis' },
  { name: 'Knowledge Writer', math: 'DataHub mutations', category: 'Enforcement' },
  { name: 'Reflexion Loop', math: 'Self-RAG playbook', category: 'Learning' },
  { name: 'EU AI Act Compliance', math: 'SHA-256 audit chain', category: 'Compliance' },
  { name: 'Contract Enforcer', math: 'quarantine_assertions', category: 'Enforcement' },
  { name: 'Explanation Drift', math: 'PSI on importance', category: 'Detection' },
  { name: 'Self-Healing', math: 'preventative mapping', category: 'Learning' },
  { name: 'Pipeline Circuit Breaker', math: 'BFS dependency halt', category: 'Enforcement' },
]

const categoryColors: Record<string, string> = {
  Detection: '#f43f5e',
  Diagnosis: '#8b5cf6',
  Enforcement: '#6366f1',
  Learning: '#10b981',
  Compliance: '#06b6d4',
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
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'rgba(255, 255, 255, 0.6)' }}>
              21 Workers
            </span>
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
            <span style={{
              background: 'linear-gradient(135deg, #f43f5e, #ec4899)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}>
              real math
            </span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            style={{
              fontSize: '15px',
              color: 'rgba(255, 255, 255, 0.45)',
              maxWidth: '480px',
              margin: '0 auto',
              lineHeight: 1.6,
            }}
          >
            No LLM guessing. PSI, KS-test, BFS lineage traversal, SHA-256 audit chains — all deterministic.
          </motion.p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
          gap: '12px',
        }}>
          {workers.map((worker, i) => (
            <motion.div
              key={worker.name}
              initial={{ opacity: 0, y: 15 }}
              whileInView={{ opacity: 1, y: 0 }}
              whileHover={{ y: -4, scale: 1.03, borderColor: `${categoryColors[worker.category]}60` }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.04, duration: 0.4 }}
              style={{
                padding: '20px',
                borderRadius: '12px',
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                cursor: 'default',
              }}
            >
              <div style={{
                display: 'inline-block',
                padding: '2px 8px',
                borderRadius: '4px',
                background: `${categoryColors[worker.category]}15`,
                color: categoryColors[worker.category],
                fontSize: '10px',
                fontWeight: 600,
                marginBottom: '10px',
              }}>
                {worker.category}
              </div>
              <div style={{
                fontSize: '14px',
                fontWeight: 600,
                color: '#fff',
                marginBottom: '4px',
              }}>
                {worker.name}
              </div>
              <div style={{
                fontSize: '12px',
                fontFamily: 'monospace',
                color: 'rgba(255, 255, 255, 0.35)',
              }}>
                {worker.math}()
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
