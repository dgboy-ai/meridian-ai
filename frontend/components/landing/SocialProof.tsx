'use client'

import { motion } from 'framer-motion'

const logos = [
  { name: 'DataHub', icon: '◆' },
  { name: 'MLflow', icon: '▲' },
  { name: 'Airflow', icon: '◎' },
  { name: 'Snowflake', icon: '⬡' },
  { name: 'Feast', icon: '◇' },
  { name: 'dbt', icon: '▢' },
]

export default function SocialProof() {
  return (
    <section style={{ position: 'relative', padding: '80px 32px' }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto', textAlign: 'center' }}>
        <motion.p initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.6 }}
          style={{ fontSize: '12px', fontWeight: 600, color: 'rgba(255,255,255,0.3)', textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: '36px' }}>
          Integrated with the modern data stack
        </motion.p>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '48px', flexWrap: 'wrap' }}>
          {logos.map((logo, i) => (
            <motion.div key={logo.name} initial={{ opacity: 0, y: 15 }} whileInView={{ opacity: 1, y: 0 }} whileHover={{ scale: 1.12, y: -3 }} viewport={{ once: true }} transition={{ delay: i * 0.1, duration: 0.5 }}
              style={{ display: 'flex', alignItems: 'center', gap: '10px', opacity: 0.4, cursor: 'default' }}>
              <span style={{ fontSize: '20px', color: '#8b5cf6' }}>{logo.icon}</span>
              <span style={{ fontSize: '15px', fontWeight: 600, color: 'rgba(255,255,255,0.8)', letterSpacing: '-0.01em' }}>{logo.name}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
