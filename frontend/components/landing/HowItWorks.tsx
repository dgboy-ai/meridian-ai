'use client'

import { motion } from 'framer-motion'

const steps = [
  {
    num: '01',
    title: 'Detect',
    desc: 'Data Sentinel monitors schema changes, freshness, and data quality in real-time via DataHub MCP.',
    color: '#f43f5e',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.3-4.3" />
      </svg>
    ),
  },
  {
    num: '02',
    title: 'Diagnose',
    desc: 'Root Cause worker traverses column-level lineage with BFS to find the exact source of failure.',
    color: '#8b5cf6',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="16" x2="12" y2="12" />
        <line x1="12" y1="8" x2="12.01" y2="8" />
      </svg>
    ),
  },
  {
    num: '03',
    title: 'Remediate',
    desc: 'Knowledge Writer persists findings to DataHub. Pipeline Circuit Breaker halts affected downstream jobs.',
    color: '#6366f1',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    ),
  },
  {
    num: '04',
    title: 'Learn',
    desc: 'Reflexion Loop updates playbooks. Next time the same pattern occurs, resolution is 3x faster.',
    color: '#10b981',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 12a9 9 0 0 1-9 9m9-9a9 9 0 0 0-9-9m9 9H3m9 9a9 9 0 0 1-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 0 1 9-9" />
      </svg>
    ),
  },
]

export default function HowItWorks() {
  return (
    <section id="how-it-works" style={{
      position: 'relative',
      padding: '120px 32px',
      background: 'linear-gradient(180deg, transparent 0%, rgba(20, 8, 45, 0.2) 50%, transparent 100%)',
    }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
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
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'rgba(255, 255, 255, 0.6)' }}>How it works</span>
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
              maxWidth: '600px',
              margin: '0 auto 20px',
            }}
          >
            From incident to{' '}
            <span style={{ background: 'linear-gradient(135deg, #10b981, #06b6d4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              resolution
            </span>{' '}
            in four steps
          </motion.h2>
        </div>

        {/* Steps */}
        <div style={{ position: 'relative' }}>
          {/* Animated vertical line */}
          <motion.div
            initial={{ scaleY: 0 }}
            whileInView={{ scaleY: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
            style={{
              position: 'absolute',
              left: '24px',
              top: '40px',
              bottom: '40px',
              width: '2px',
              background: 'linear-gradient(180deg, #f43f5e, #8b5cf6, #6366f1, #10b981)',
              opacity: 0.4,
              transformOrigin: 'top',
            }}
          />

          <div style={{ display: 'flex', flexDirection: 'column', gap: '48px' }}>
            {steps.map((step, i) => (
              <motion.div
                key={step.num}
                initial={{ opacity: 0, x: -40 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ delay: i * 0.15, duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
                style={{ display: 'flex', gap: '32px', alignItems: 'flex-start' }}
              >
                {/* Step number with pulse */}
                <div style={{ position: 'relative', flexShrink: 0 }}>
                  <motion.div
                    whileInView={{ scale: [0.8, 1.1, 1] }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.15 + 0.2, duration: 0.5 }}
                    style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '14px',
                      background: `${step.color}15`,
                      border: `1px solid ${step.color}30`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: step.color,
                      position: 'relative',
                      zIndex: 1,
                    }}
                  >
                    {step.icon}
                  </motion.div>
                  {/* Glow ring */}
                  <motion.div
                    animate={{ scale: [1, 1.5, 1], opacity: [0.3, 0, 0.3] }}
                    transition={{ duration: 3, repeat: Infinity, delay: i * 0.5 }}
                    style={{
                      position: 'absolute',
                      inset: '-4px',
                      borderRadius: '16px',
                      border: `1px solid ${step.color}20`,
                      pointerEvents: 'none',
                    }}
                  />
                </div>

                {/* Content */}
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                    <span style={{ fontSize: '11px', fontWeight: 700, color: step.color, letterSpacing: '0.1em', textTransform: 'uppercase' }}>
                      Step {step.num}
                    </span>
                    <div style={{ width: '24px', height: '1px', background: `${step.color}40` }} />
                  </div>
                  <h3 style={{ fontSize: '24px', fontWeight: 700, color: '#fff', marginBottom: '10px' }}>{step.title}</h3>
                  <p style={{ fontSize: '15px', lineHeight: 1.7, color: 'rgba(255, 255, 255, 0.5)', maxWidth: '500px' }}>{step.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
