'use client'

import { motion } from 'framer-motion'

const features = [
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    ),
    title: 'Autonomous Investigation',
    desc: '18 workers fire in parallel to detect, diagnose, and remediate ML incidents without human intervention.',
    color: '#8b5cf6',
    stat: '18',
    statLabel: 'Workers',
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <path d="M12 6v6l4 2" />
      </svg>
    ),
    title: '8-Minute Resolution',
    desc: 'From detection to remediation in minutes, not days. The reflexion loop makes each incident faster.',
    color: '#10b981',
    stat: '8min',
    statLabel: 'Avg Time',
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
        <polyline points="14 2 14 8 20 8" />
      </svg>
    ),
    title: 'DataHub Write-back',
    desc: 'Every investigation writes knowledge, playbooks, and compliance records back to DataHub permanently.',
    color: '#6366f1',
    stat: '4',
    statLabel: 'Artifacts',
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2L2 7l10 5 10-5-10-5z" />
        <path d="M2 17l10 5 10-5" />
        <path d="M2 12l10 5 10-5" />
      </svg>
    ),
    title: 'Column-Level Lineage',
    desc: 'Trace exact column dependencies through the lineage graph with BFS/DFS traversal algorithms.',
    color: '#a855f7',
    stat: '11',
    statLabel: 'Algorithms',
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
        <path d="M7 11V7a5 5 0 0 1 10 0v4" />
      </svg>
    ),
    title: 'EU AI Act Compliance',
    desc: 'SHA-256 audit chain for Articles 12, 13, 14. Technical files generated automatically.',
    color: '#06b6d4',
    stat: 'Art.12',
    statLabel: 'Compliant',
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
        <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
        <line x1="12" y1="22.08" x2="12" y2="12" />
      </svg>
    ),
    title: 'MCP Server',
    desc: 'Expose Meridian as an MCP tool so any AI agent can trigger investigations via Model Context Protocol.',
    color: '#ec4899',
    stat: '3',
    statLabel: 'Tools',
  },
]

const container = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.08 },
  },
}

const item = {
  hidden: { opacity: 0, y: 30, scale: 0.95 },
  show: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] } },
}

export default function Features() {
  return (
    <section id="features" style={{
      position: 'relative',
      padding: '120px 32px',
      background: 'linear-gradient(180deg, transparent 0%, rgba(15, 5, 35, 0.3) 30%, rgba(15, 5, 35, 0.5) 70%, transparent 100%)',
    }}>
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '80px', background: 'linear-gradient(to bottom, rgba(6,4,13,0.5), transparent)', pointerEvents: 'none' }} />
      <div style={{ maxWidth: '1200px', margin: '0 auto', position: 'relative', zIndex: 1 }}>
        {/* Section header */}
        <div style={{ textAlign: 'center', marginBottom: '80px' }}>
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
              Everything you need
            </span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            style={{
              fontSize: 'clamp(32px, 4vw, 48px)',
              fontWeight: 800,
              lineHeight: 1.15,
              letterSpacing: '-0.03em',
              color: '#fff',
              maxWidth: '640px',
              margin: '0 auto 20px',
            }}
          >
            Harness the power of AI, making{' '}
            <span style={{
              background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}>
              ML reliability
            </span>{' '}
            intuitive and effective
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            style={{ fontSize: '16px', color: 'rgba(255, 255, 255, 0.45)', maxWidth: '520px', margin: '0 auto', lineHeight: 1.6 }}
          >
            From schema drift detection to EU AI Act compliance, Meridian handles the full incident lifecycle.
          </motion.p>
        </div>

        {/* Dashboard Preview */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          style={{
            position: 'relative',
            borderRadius: '16px',
            overflow: 'hidden',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            background: 'rgba(8, 6, 18, 0.9)',
            marginBottom: '80px',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3), 0 0 40px rgba(139, 92, 246, 0.05)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '14px 18px', borderBottom: '1px solid rgba(255, 255, 255, 0.06)' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ef4444' }} />
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#f59e0b' }} />
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#10b981' }} />
            <span style={{ marginLeft: '12px', fontSize: '12px', color: 'rgba(255, 255, 255, 0.3)' }}>Meridian AI — Investigation Dashboard</span>
          </div>
          <div style={{ padding: '32px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '24px' }}>
              {[
                { label: 'System Health', value: '94%', change: '+2.1%', color: '#10b981' },
                { label: 'Avg Resolution', value: '8 min', change: '-83%', color: '#8b5cf6' },
                { label: 'Models Monitored', value: '42', change: '100%', color: '#6366f1' },
                { label: 'Incidents Today', value: '3', change: '-67%', color: '#f43f5e' },
              ].map((stat, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.3 + i * 0.08 }}
                  style={{ padding: '20px', borderRadius: '12px', background: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                  <div style={{ fontSize: '11px', color: 'rgba(255, 255, 255, 0.4)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>{stat.label}</div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                    <span style={{ fontSize: '24px', fontWeight: 800, color: '#fff' }}>{stat.value}</span>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: stat.color }}>{stat.change}</span>
                  </div>
                </motion.div>
              ))}
            </div>
            <div style={{ padding: '24px', borderRadius: '12px', background: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'rgba(255, 255, 255, 0.7)' }}>Live Investigation Feed</span>
                <span style={{ padding: '4px 10px', borderRadius: '6px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)', fontSize: '11px', fontWeight: 600, color: '#10b981' }}>HEALTHY</span>
              </div>
              <div style={{ fontFamily: 'monospace', fontSize: '12px', lineHeight: 2, color: 'rgba(255, 255, 255, 0.5)' }}>
                <div><span style={{ color: '#6366f1' }}>[SENTINEL]</span> Schema change detected in raw_events.user_age</div>
                <div><span style={{ color: '#f43f5e' }}>[DRIFT]</span> PSI = 0.31 on tenure feature (threshold: 0.1)</div>
                <div><span style={{ color: '#8b5cf6' }}>[ROOT CAUSE]</span> Column lineage traced: raw_events → feature_pipeline → churn_model</div>
                <div><span style={{ color: '#10b981' }}>[VERIFIER]</span> Confidence 0.95 — approved for write-back</div>
                <div><span style={{ color: '#10b981' }}>[WRITE]</span> 4 artifacts persisted to DataHub graph</div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Feature cards grid */}
        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: '-50px' }}
          style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}
        >
          {features.map((feature) => (
            <motion.div
              key={feature.title}
              variants={item}
              whileHover={{ y: -8, scale: 1.02 }}
              style={{
                padding: '28px',
                borderRadius: '16px',
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                cursor: 'default',
                position: 'relative',
                overflow: 'hidden',
                transition: 'border-color 0.3s, box-shadow 0.3s',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.borderColor = `${feature.color}40`
                e.currentTarget.style.boxShadow = `0 8px 32px ${feature.color}15, 0 0 0 1px ${feature.color}20`
              }}
              onMouseLeave={e => {
                e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.06)'
                e.currentTarget.style.boxShadow = 'none'
              }}
            >
              {/* Glow effect on hover */}
              <div style={{
                position: 'absolute',
                top: '-50%',
                right: '-50%',
                width: '200%',
                height: '200%',
                background: `radial-gradient(circle at center, ${feature.color}08 0%, transparent 50%)`,
                pointerEvents: 'none',
                opacity: 0,
                transition: 'opacity 0.3s',
              }} />

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px', position: 'relative' }}>
                <div style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '12px',
                  background: `${feature.color}12`,
                  border: `1px solid ${feature.color}25`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: feature.color,
                }}>
                  {feature.icon}
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: feature.color, lineHeight: 1 }}>{feature.stat}</div>
                  <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.35)', marginTop: '2px' }}>{feature.statLabel}</div>
                </div>
              </div>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#fff', marginBottom: '8px', position: 'relative' }}>{feature.title}</h3>
              <p style={{ fontSize: '14px', lineHeight: 1.6, color: 'rgba(255, 255, 255, 0.45)', position: 'relative' }}>{feature.desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
