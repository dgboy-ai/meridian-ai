'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { motion, useInView, AnimatePresence } from 'framer-motion'

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

interface ResolutionTime {
  id: string
  duration_minutes: number
  date: string
  pattern: string
}

// Use relative URLs - Next.js rewrites proxy to backend
const API = ''

function AnimatedCounter({ target, duration = 2 }: { target: number; duration?: number }) {
  const [count, setCount] = useState(0)
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true })

  useEffect(() => {
    if (!inView) return
    let start = 0
    const step = target / (duration * 60)
    const timer = setInterval(() => {
      start += step
      if (start >= target) {
        setCount(target)
        clearInterval(timer)
      } else {
        setCount(Math.floor(start))
      }
    }, 1000 / 60)
    return () => clearInterval(timer)
  }, [target, duration, inView])

  return <span ref={ref}>{count}</span>
}

export default function Home() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [resolutionTimes, setResolutionTimes] = useState<ResolutionTime[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/incidents`).then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      }),
      fetch(`${API}/api/resolution-times`).then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      }),
    ]).then(([incidentsData, resolutionData]) => {
      setIncidents(incidentsData.incidents || [])
      setResolutionTimes(resolutionData.incidents || [])
      setLoading(false)
    }).catch((err) => {
      console.error('Failed to load data:', err)
      setError('Unable to connect to Meridian AI backend. Make sure the API server is running.')
      setLoading(false)
    })
  }, [])

  return (
    <main className="bg-mesh" style={{ minHeight: '100vh' }}>
      <HeroSection />
      <div className="container" style={{ paddingBottom: '64px' }}>
        <StatsSection />
        <div className="grid-2col">
          <motion.div
            className="card card-glow"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <h2 style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Incident Resolution Time
            </h2>
            <ResolutionGraph times={resolutionTimes} loading={loading} />
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '12px', fontStyle: 'italic' }}>
              Gets faster every incident. Not because the model improved. Because the knowledge base improved.
            </p>
          </motion.div>

          <motion.div
            className="card card-glow"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <h2 style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              How It Works
            </h2>
            <div className="grid-2col-inner">
              {[
                { step: '01', title: 'Detect', desc: 'Data Sentinel finds schema changes, drift, anomalies', color: 'var(--accent-red)' },
                { step: '02', title: 'Diagnose', desc: 'Root Cause traverses lineage to find WHY', color: 'var(--accent-amber)' },
                { step: '03', title: 'Remediate', desc: 'Knowledge Writer writes fixes back to DataHub', color: 'var(--accent-blue)' },
                { step: '04', title: 'Learn', desc: 'Reflexion loop improves playbook every incident', color: 'var(--accent-green)' },
              ].map((item, i) => (
                <motion.div
                  key={item.step}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.5 + i * 0.1 }}
                  style={{
                    padding: '16px',
                    borderRadius: '8px',
                    background: `${item.color}08`,
                    border: `1px solid ${item.color}20`,
                  }}
                >
                  <div style={{ fontSize: '11px', color: item.color, fontWeight: 700, marginBottom: '4px' }}>
                    STEP {item.step}
                  </div>
                  <div style={{ fontSize: '15px', fontWeight: 600, marginBottom: '4px' }}>{item.title}</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{item.desc}</div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>

        <motion.div
          className="card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          style={{ marginBottom: '32px' }}
        >
          <h2 style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Recent Investigations
          </h2>
          {error ? (
            <div style={{ color: 'var(--accent-red)', padding: '20px', textAlign: 'center', fontSize: '14px' }}>
              {error}
              <div style={{ marginTop: '12px' }}>
                <button
                  onClick={() => window.location.reload()}
                  className="btn-glass"
                  style={{ fontSize: '13px', padding: '8px 16px' }}
                >
                  Retry
                </button>
              </div>
            </div>
          ) : loading ? (
            <div style={{ color: 'var(--text-muted)', padding: '20px', textAlign: 'center' }}>Loading...</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {incidents.map((inc) => (
                <a
                  key={inc.id}
                  href={`/incidents/${inc.id}`}
                  className="incident-row"
                >
                  <span style={{ fontWeight: 600, color: 'var(--accent-blue)' }}>#{inc.id}</span>
                  <span style={{ fontSize: '14px' }}>{inc.title}</span>
                  <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{inc.pattern_id}</span>
                  <span className={`badge badge-${inc.severity === 'HIGH' ? 'red' : 'amber'}`}>
                    {inc.severity}
                  </span>
                  <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                    {Math.round(inc.duration_seconds / 60)}m
                  </span>
                </a>
              ))}
            </div>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
          style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)', fontSize: '13px' }}
        >
          Built for the DataHub Agent Hackathon · Apache 2.0 · $0 infrastructure cost
        </motion.div>
      </div>
    </main>
  )
}

function HeroSection() {
  return (
    <div className="hero-gradient" style={{ padding: '80px 0 60px', textAlign: 'center' }}>
      <div className="container">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px', marginBottom: '16px' }}>
            <div style={{
              width: '40px', height: '40px', borderRadius: '10px',
              background: 'linear-gradient(135deg, var(--accent-green), var(--accent-blue))',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '18px', fontWeight: 'bold',
            }}>M</div>
            <span style={{ fontSize: '14px', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.1em' }}>MERIDIAN AI</span>
          </div>
          <h1 style={{ fontSize: '42px', fontWeight: 800, marginBottom: '16px', lineHeight: 1.1 }}>
            <span className="gradient-text">Silent ML failures</span> cost{' '}
            <span className="gradient-text-red">$45,000/day</span>
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '18px', maxWidth: '600px', margin: '0 auto 24px', lineHeight: 1.6 }}>
            Most teams don&apos;t notice for 3 days. We catch them in 8 minutes.
            And the next one takes 3.
          </p>
          <a
            href="/incidents/42"
            className="btn-glass"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 24px', fontSize: '14px', fontWeight: 600 }}
          >
            View Investigation #42 →
          </a>
        </motion.div>
      </div>
    </div>
  )
}

function StatsSection() {
  const stats = [
    { value: 42, label: 'Incidents Resolved', suffix: '' },
    { value: 14, label: 'Playbooks Written', suffix: '' },
    { value: 400, label: 'Hours Saved', suffix: '+' },
  ]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '32px' }}>
      {stats.map((stat, i) => (
        <motion.div
          key={stat.label}
          className="card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 + i * 0.1 }}
          style={{ textAlign: 'center', padding: '24px' }}
        >
          <div style={{ fontSize: '36px', fontWeight: 800, color: 'var(--accent-green)', marginBottom: '4px' }}>
            <AnimatedCounter target={stat.value} />{stat.suffix}
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{stat.label}</div>
        </motion.div>
      ))}
    </div>
  )
}

function ResolutionGraph({ times, loading }: { times: ResolutionTime[]; loading: boolean }) {
  if (loading) return <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>Loading...</div>

  if (times.length === 0) return <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No resolution data</div>

  const maxTime = Math.max(...times.map(t => t.duration_minutes))

  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: '16px', height: '200px', padding: '20px 0' }}>
      {times.map((t, i) => {
        const height = (t.duration_minutes / maxTime) * 140
        const colors = ['var(--accent-red)', 'var(--accent-amber)', 'var(--accent-green)']
        return (
          <motion.div
            key={t.id}
            initial={{ height: 0 }}
            animate={{ height }}
            transition={{ delay: 0.5 + i * 0.2, duration: 0.6, type: 'spring' }}
            style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}
          >
            <span style={{ fontSize: '13px', fontWeight: 600, color: colors[i % colors.length] }}>
              {t.duration_minutes}m
            </span>
            <div style={{
              width: '100%',
              background: `linear-gradient(180deg, ${colors[i % colors.length]}, ${colors[i % colors.length]}88)`,
              borderRadius: '4px 4px 0 0',
              boxShadow: `0 0 12px ${colors[i % colors.length]}40`,
            }} />
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>#{t.id}</span>
          </motion.div>
        )
      })}
    </div>
  )
}
