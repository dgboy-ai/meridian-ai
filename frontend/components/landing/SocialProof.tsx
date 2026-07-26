'use client'

import { motion } from 'framer-motion'

const logos = [
  { name: 'DataHub', icon: '◆', real: true },
  { name: 'MLflow', icon: '▲', real: false },
  { name: 'Airflow', icon: '◎', real: false },
  { name: 'Snowflake', icon: '⬡', real: false },
  { name: 'Feast', icon: '◇', real: false },
  { name: 'dbt', icon: '▢', real: false },
]

export default function SocialProof() {
  return (
    <section style={{ position: 'relative', padding: '80px 32px' }}>
      {/* Top gradient — receives hero's aurora colors for seamless blend */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '100px', background: 'linear-gradient(to bottom, rgba(6,4,13,1), transparent)', pointerEvents: 'none' }} />
      {/* Subtle aurora glow continuation from hero */}
      <div style={{ position: 'absolute', top: '-40px', left: '20%', width: '60vw', height: '200px', borderRadius: '50%', background: 'radial-gradient(ellipse, rgba(139,92,246,0.08) 0%, transparent 60%)', filter: 'blur(40px)', pointerEvents: 'none' }} />
      <div style={{ maxWidth: '1000px', margin: '0 auto', textAlign: 'center', position: 'relative', zIndex: 1 }}>
        <motion.p initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.6 }}
          style={{ fontSize: '12px', fontWeight: 600, color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '36px' }}>
          Native DataHub integration with the modern data stack
        </motion.p>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '48px', flexWrap: 'wrap' }}>
          {logos.map((logo, i) => (
            <motion.div key={logo.name} initial={{ opacity: 0, y: 15 }} whileInView={{ opacity: 1, y: 0 }} whileHover={{ scale: 1.12, y: -3 }} viewport={{ once: true }} transition={{ delay: i * 0.1, duration: 0.5 }}
              style={{ display: 'flex', alignItems: 'center', gap: '10px', opacity: logo.real ? 0.9 : 0.35, cursor: 'default' }}>
              <span style={{ fontSize: '20px', color: logo.real ? '#8b5cf6' : 'rgba(255,255,255,0.4)' }}>{logo.icon}</span>
              <span style={{ fontSize: '15px', fontWeight: 600, color: logo.real ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.4)', letterSpacing: '-0.01em' }}>{logo.name}</span>
              {logo.real && (
                <span style={{ fontSize: '9px', fontWeight: 700, color: '#10b981', background: 'rgba(16,185,129,0.1)', padding: '2px 6px', borderRadius: '4px', border: '1px solid rgba(16,185,129,0.2)' }}>
                  NATIVE
                </span>
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
