'use client'

import { motion } from 'framer-motion'

const steps = [
  {
    num: '01',
    title: 'Detect',
    desc: 'Data Sentinel monitors schema changes, freshness, and data quality in real-time via DataHub MCP.',
    color: '#f43f5e',
  },
  {
    num: '02',
    title: 'Diagnose',
    desc: 'Root Cause worker traverses column-level lineage with BFS to find the exact source of failure.',
    color: '#8b5cf6',
  },
  {
    num: '03',
    title: 'Remediate',
    desc: 'Knowledge Writer persists findings to DataHub. Pipeline Circuit Breaker halts affected downstream jobs.',
    color: '#6366f1',
  },
  {
    num: '04',
    title: 'Learn',
    desc: 'Reflexion Loop updates playbooks. Next time the same pattern occurs, resolution is 3x faster.',
    color: '#10b981',
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
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'rgba(255, 255, 255, 0.6)' }}>
              How it works
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
              maxWidth: '600px',
              margin: '0 auto 20px',
            }}
          >
            From incident to{' '}
            <span style={{
              background: 'linear-gradient(135deg, #10b981, #06b6d4)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}>
              resolution
            </span>{' '}
            in four steps
          </motion.h2>
        </div>

        {/* Steps */}
        <div style={{ position: 'relative' }}>
          {/* Vertical line */}
          <div style={{
            position: 'absolute',
            left: '24px',
            top: '40px',
            bottom: '40px',
            width: '2px',
            background: 'linear-gradient(180deg, #f43f5e, #8b5cf6, #6366f1, #10b981)',
            opacity: 0.3,
          }} />

          <div style={{ display: 'flex', flexDirection: 'column', gap: '48px' }}>
            {steps.map((step, i) => (
              <motion.div
                key={step.num}
                initial={{ opacity: 0, x: -30 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                style={{
                  display: 'flex',
                  gap: '32px',
                  alignItems: 'flex-start',
                  paddingLeft: '0',
                }}
              >
                {/* Step number */}
                <div style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '12px',
                  background: `${step.color}15`,
                  border: `1px solid ${step.color}30`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '14px',
                  fontWeight: 800,
                  color: step.color,
                  flexShrink: 0,
                  position: 'relative',
                  zIndex: 1,
                }}>
                  {step.num}
                </div>

                {/* Content */}
                <div>
                  <h3 style={{
                    fontSize: '22px',
                    fontWeight: 700,
                    color: '#fff',
                    marginBottom: '8px',
                  }}>
                    {step.title}
                  </h3>
                  <p style={{
                    fontSize: '15px',
                    lineHeight: 1.7,
                    color: 'rgba(255, 255, 255, 0.5)',
                    maxWidth: '500px',
                  }}>
                    {step.desc}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
