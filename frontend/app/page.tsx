'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { apiUrl } from '../lib/config'
import ParticleField from '../components/landing/ParticleField'
import Navbar from '../components/landing/Navbar'
import Hero from '../components/landing/Hero'
import SocialProof from '../components/landing/SocialProof'
import Features from '../components/landing/Features'
import HowItWorks from '../components/landing/HowItWorks'
import Workers from '../components/landing/Workers'
import Integrations from '../components/landing/Integrations'
import CTA from '../components/landing/CTA'
import Footer from '../components/landing/Footer'

interface Incident {
  id: string
  title: string
  severity: string
  status: string
  detected: string
  duration_seconds: number
  affected_models: string[]
  pattern_id: string
}

export default function Home() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(apiUrl('/api/incidents'))
      .then(r => r.json())
      .then(data => {
        setIncidents(data.incidents || [])
        setLoading(false)
      })
      .catch(() => {
        setIncidents([
          { id: '42', title: 'Schema Change in raw_events', severity: 'HIGH', status: 'RESOLVED', detected: '2026-07-16T08:00:00Z', duration_seconds: 180, affected_models: ['churn_model_v3'], pattern_id: 'SCHEMA_DRIFT' },
          { id: '28', title: 'Feature Pipeline Freshness Violation', severity: 'MEDIUM', status: 'RESOLVED', detected: '2026-07-15T12:00:00Z', duration_seconds: 480, affected_models: ['churn_model_v3'], pattern_id: 'FRESHNESS' },
          { id: '12', title: 'Schema Change in raw_events', severity: 'HIGH', status: 'RESOLVED', detected: '2026-07-14T09:00:00Z', duration_seconds: 1080, affected_models: ['churn_model_v3'], pattern_id: 'SCHEMA_CHANGE' },
        ])
        setLoading(false)
      })
  }, [])

  return (
    <main style={{ minHeight: '100vh', position: 'relative' }}>
      {/* Particle background */}
      <ParticleField />

      {/* Background gradient orbs — continuous across all sections */}
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 0,
        pointerEvents: 'none',
        overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute',
          top: '-20%',
          left: '-10%',
          width: '70vw',
          height: '70vw',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(139, 92, 246, 0.12) 0%, transparent 55%)',
          filter: 'blur(80px)',
        }} />
        <div style={{
          position: 'absolute',
          bottom: '-10%',
          right: '-5%',
          width: '60vw',
          height: '60vw',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, transparent 55%)',
          filter: 'blur(80px)',
        }} />
        <div style={{
          position: 'absolute',
          top: '30%',
          left: '40%',
          width: '50vw',
          height: '50vw',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(244, 63, 94, 0.06) 0%, transparent 50%)',
          filter: 'blur(70px)',
        }} />
        {/* Continuous aurora wave */}
        <div style={{
          position: 'absolute',
          top: '20%',
          left: '-20%',
          width: '140vw',
          height: '60vh',
          borderRadius: '50%',
          background: 'radial-gradient(ellipse, rgba(139, 92, 246, 0.08) 0%, transparent 60%)',
          filter: 'blur(60px)',
          transform: 'rotate(-5deg)',
        }} />
      </div>

      {/* Content */}
      <div style={{ position: 'relative', zIndex: 1 }}>
        <Navbar />
        <Hero />
        <SocialProof />
        <Features />
        <HowItWorks />
        <Workers />
        <Integrations />

        {/* Incident History Section */}
        <section id="history" style={{ position: 'relative', padding: '120px 32px' }}>
          <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
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
                  Investigation History
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
                Every incident makes us{' '}
                <span style={{
                  background: 'linear-gradient(135deg, #10b981, #06b6d4)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}>
                  faster
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
                The reflexion flywheel: 18min → 8min → 3min. Each resolution writes knowledge back to DataHub.
              </motion.p>
            </div>

            {/* Incident list */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {incidents.map((inc, i) => (
                <motion.a
                  key={inc.id}
                  href={`/incidents/${inc.id}`}
                  initial={{ opacity: 0, y: 15 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.08, duration: 0.4 }}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '60px 1fr auto auto',
                    alignItems: 'center',
                    gap: '16px',
                    padding: '18px 24px',
                    borderRadius: '12px',
                    background: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid rgba(255, 255, 255, 0.05)',
                    textDecoration: 'none',
                    color: '#fff',
                    transition: 'border-color 0.2s, background 0.2s',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.3)'
                    e.currentTarget.style.background = 'rgba(139, 92, 246, 0.04)'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.05)'
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)'
                  }}
                >
                  <span style={{
                    fontSize: '13px',
                    fontWeight: 700,
                    color: '#6366f1',
                  }}>
                    #{inc.id}
                  </span>
                  <span style={{
                    fontSize: '14px',
                    fontWeight: 600,
                    color: 'rgba(255, 255, 255, 0.8)',
                  }}>
                    {inc.title}
                  </span>
                  <span style={{
                    padding: '4px 10px',
                    borderRadius: '6px',
                    background: inc.severity === 'HIGH' ? 'rgba(244, 63, 94, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                    color: inc.severity === 'HIGH' ? '#f43f5e' : '#f59e0b',
                    fontSize: '11px',
                    fontWeight: 600,
                  }}>
                    {inc.severity}
                  </span>
                  <span style={{
                    fontSize: '13px',
                    color: 'rgba(255, 255, 255, 0.4)',
                    textAlign: 'right',
                  }}>
                    {Math.round(inc.duration_seconds / 60)}min
                  </span>
                </motion.a>
              ))}
            </div>
          </div>
        </section>

        <CTA />
        <Footer />
      </div>
    </main>
  )
}
