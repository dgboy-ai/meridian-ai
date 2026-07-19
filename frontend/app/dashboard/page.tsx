'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

interface CostSummary {
  total_investigations: number
  total_cost_usd: number
  total_tokens_in: number
  total_tokens_out: number
  avg_cost_per_investigation: number
  total_time_saved_minutes: number
}

interface ResolutionEntry {
  id: string
  duration_minutes: number
  date: string
  pattern: string
}

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

interface Architecture {
  name: string
  version: string
  mode: string
  workers: { id: string; name: string; phase: string; description: string }[]
  datahub_tools: { read: string[]; write: string[] }
  dsa_algorithms: string[]
  stats: { total_workers: number; datahub_capabilities: number; dsa_algorithms: number }
}

export default function DashboardPage() {
  const [costs, setCosts] = useState<CostSummary | null>(null)
  const [resolutionTimes, setResolutionTimes] = useState<ResolutionEntry[]>([])
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [architecture, setArchitecture] = useState<Architecture | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch('/api/costs').then(r => r.json()).catch(() => null),
      fetch('/api/resolution-times').then(r => r.json()).catch(() => null),
      fetch('/api/incidents').then(r => r.json()).catch(() => ({ incidents: [] })),
      fetch('/api/system/architecture').then(r => r.json()).catch(() => null),
    ]).then(([costData, resData, incData, archData]) => {
      setCosts(costData)
      setResolutionTimes(resData?.incidents || [])
      setIncidents(incData?.incidents || [])
      setArchitecture(archData)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  if (loading) return (
    <main style={{ minHeight: '100vh', padding: '40px 0' }}>
      <div className="container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <div style={{ textAlign: 'center' }}>
          <div className="pulse" style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'var(--accent-green)', opacity: 0.5, margin: '0 auto 16px' }} />
          <span style={{ color: 'var(--text-muted)' }}>Loading dashboard...</span>
        </div>
      </div>
    </main>
  )

  const maxDuration = Math.max(...resolutionTimes.map(r => r.duration_minutes), 1)

  return (
    <main style={{ minHeight: '100vh', padding: '40px 0' }}>
      <div className="container">
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
          <a href="/" style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px', display: 'block', textDecoration: 'none' }}>
            ← Back to Dashboard
          </a>
          <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>
            <span style={{ color: 'var(--accent-green)' }}>Analytics</span> Dashboard
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '32px' }}>
            Cost attribution, resolution flywheel, and system architecture overview.
          </p>
        </motion.div>

        {/* Key Metrics */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '32px' }}>
          {[
            { label: 'Total Investigations', value: costs?.total_investigations || incidents.length, color: 'var(--accent-blue)' },
            { label: 'Total Cost', value: `$${(costs?.total_cost_usd || 0).toFixed(4)}`, color: 'var(--accent-green)' },
            { label: 'Time Saved', value: `${Math.round(costs?.total_time_saved_minutes || 0)}min`, color: 'var(--accent-cyan)' },
            { label: 'Workers', value: architecture?.stats?.total_workers || 21, color: 'var(--accent-purple)' },
            { label: 'DataHub Tools', value: architecture?.stats?.datahub_capabilities || 12, color: 'var(--accent-amber)' },
            { label: 'DSA Algorithms', value: architecture?.stats?.dsa_algorithms || 11, color: 'var(--accent-red)' },
          ].map((metric, i) => (
            <motion.div key={metric.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 * i }} className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>{metric.label}</div>
              <div style={{ fontSize: '28px', fontWeight: 800, color: metric.color }}>{metric.value}</div>
            </motion.div>
          ))}
        </div>

        {/* Resolution Flywheel */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
          className="glass-card" style={{ padding: '24px', marginBottom: '32px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '20px', color: 'var(--text-secondary)' }}>
            Resolution Time Flywheel
          </h3>
          {resolutionTimes.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No resolution data yet. Run investigations to see the flywheel in action.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {resolutionTimes.map((entry, i) => {
                const width = (entry.duration_minutes / maxDuration) * 100
                const color = entry.duration_minutes <= 5 ? 'var(--accent-green)' :
                              entry.duration_minutes <= 10 ? 'var(--accent-amber)' : 'var(--accent-red)'
                return (
                  <div key={entry.id} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)', minWidth: '60px', textAlign: 'right' }}>#{entry.id}</span>
                    <div style={{ flex: 1, height: '24px', borderRadius: '6px', background: 'rgba(255,255,255,0.03)', overflow: 'hidden', position: 'relative' }}>
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${width}%` }}
                        transition={{ delay: 0.4 + i * 0.1, duration: 0.6 }}
                        style={{ height: '100%', background: color, borderRadius: '6px', display: 'flex', alignItems: 'center', paddingLeft: '10px' }}>
                        <span style={{ fontSize: '11px', fontWeight: 700, color: '#fff', whiteSpace: 'nowrap' }}>
                          {entry.duration_minutes}min
                        </span>
                      </motion.div>
                    </div>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', minWidth: '120px' }}>{entry.pattern}</span>
                  </div>
                )
              })}
              <div style={{ marginTop: '8px', padding: '12px 16px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.06)', border: '1px solid rgba(16, 185, 129, 0.15)', textAlign: 'center' }}>
                <span style={{ fontSize: '13px', color: 'var(--accent-green)', fontWeight: 600 }}>
                  Flywheel active: Each investigation makes the next one faster via reflexion playbooks
                </span>
              </div>
            </div>
          )}
        </motion.div>

        {/* Architecture Overview */}
        {architecture && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
            className="glass-card" style={{ padding: '24px', marginBottom: '32px' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '16px', color: 'var(--text-secondary)' }}>
              System Architecture — {architecture.workers.length} Workers
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '8px' }}>
              {architecture.workers.map((w, i) => {
                const phaseColors: Record<string, string> = {
                  detection: 'var(--accent-red)', diagnosis: 'var(--accent-blue)',
                  verification: 'var(--accent-cyan)', enforcement: 'var(--accent-green)',
                  learning: 'var(--accent-purple)', compliance: 'var(--accent-amber)',
                  governance: 'var(--text-muted)',
                }
                const color = phaseColors[w.phase] || 'var(--text-muted)'
                return (
                  <div key={w.id} style={{
                    display: 'flex', alignItems: 'center', gap: '10px',
                    padding: '10px 14px', borderRadius: '8px',
                    background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-subtle)',
                  }}>
                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: color, flexShrink: 0 }} />
                    <div>
                      <div style={{ fontSize: '13px', fontWeight: 600, color: '#fff' }}>{w.name}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{w.phase}</div>
                    </div>
                  </div>
                )
              })}
            </div>
          </motion.div>
        )}

        {/* Recent Incidents */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
          className="glass-card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '16px', color: 'var(--text-secondary)' }}>
            Recent Investigations
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {incidents.map((inc, i) => (
              <a key={inc.id} href={`/incidents/${inc.id}`} style={{
                display: 'grid', gridTemplateColumns: '60px 1fr auto auto',
                alignItems: 'center', gap: '12px', padding: '12px 16px',
                borderRadius: '8px', background: 'rgba(255,255,255,0.02)',
                border: '1px solid var(--border-subtle)', textDecoration: 'none', color: '#fff',
                transition: 'border-color 0.2s',
              }}
                onMouseEnter={e => e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.3)'}
                onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border-subtle)'}>
                <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--accent-blue)' }}>#{inc.id}</span>
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>{inc.title}</span>
                <span className={`badge badge-${inc.severity === 'HIGH' ? 'red' : 'amber'}`}>{inc.severity}</span>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{Math.round(inc.duration_seconds / 60)}min</span>
              </a>
            ))}
          </div>
        </motion.div>

        <footer style={{ marginTop: '40px', textAlign: 'center', fontSize: '12px', color: 'var(--text-muted)' }}>
          Data sourced from DataHub MCP · Cost computed from real worker token usage
        </footer>
      </div>
    </main>
  )
}
