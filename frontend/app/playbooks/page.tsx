'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

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

const PATTERN_INFO: Record<string, { name: string; description: string; color: string }> = {
  'schema-change-type-mismatch': {
    name: 'Schema Change — Type Mismatch',
    description: 'Column type changed between upstream and downstream, causing silent failures in ML pipelines.',
    color: 'var(--accent-red)',
  },
  'freshness-violation': {
    name: 'Freshness Violation',
    description: 'Data pipeline failed to deliver on schedule, causing stale features in production models.',
    color: 'var(--accent-amber)',
  },
  'SCHEMA_DRIFT': {
    name: 'Schema Drift',
    description: 'Gradual schema evolution detected through DataHub schema diff analysis.',
    color: 'var(--accent-red)',
  },
  'FRESHNESS': {
    name: 'Freshness Violation',
    description: 'Feature pipeline freshness SLA violated.',
    color: 'var(--accent-amber)',
  },
  'SCHEMA_CHANGE': {
    name: 'Schema Change',
    description: 'Abrupt schema change in upstream dataset.',
    color: 'var(--accent-red)',
  },
}

export default function PlaybooksPage() {
  const [resolutionTimes, setResolutionTimes] = useState<ResolutionEntry[]>([])
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedPattern, setSelectedPattern] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      fetch('/api/resolution-times').then(r => r.json()).catch(() => null),
      fetch('/api/incidents').then(r => r.json()).catch(() => ({ incidents: [] })),
    ]).then(([resData, incData]) => {
      setResolutionTimes(resData?.incidents || [])
      setIncidents(incData?.incidents || [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  if (loading) return (
    <main style={{ minHeight: '100vh', padding: '40px 0' }}>
      <div className="container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <div style={{ textAlign: 'center' }}>
          <div className="pulse" style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'var(--accent-purple)', opacity: 0.5, margin: '0 auto 16px' }} />
          <span style={{ color: 'var(--text-muted)' }}>Loading playbooks...</span>
        </div>
      </div>
    </main>
  )

  // Group incidents by pattern
  const patternGroups: Record<string, Incident[]> = {}
  incidents.forEach(inc => {
    const pid = inc.pattern_id || 'unknown'
    if (!patternGroups[pid]) patternGroups[pid] = []
    patternGroups[pid].push(inc)
  })

  // Compute improvement per pattern
  const patternImprovements = Object.entries(patternGroups).map(([pattern, incs]) => {
    const sorted = [...incs].sort((a, b) => new Date(a.detected).getTime() - new Date(b.detected).getTime())
    const first = sorted[0]
    const last = sorted[sorted.length - 1]
    const firstTime = first ? first.duration_seconds / 60 : 0
    const lastTime = last ? last.duration_seconds / 60 : 0
    const improvement = firstTime > 0 ? Math.round(((firstTime - lastTime) / firstTime) * 100) : 0
    return { pattern, incidents: sorted, firstTime, lastTime, improvement, count: incs.length }
  })

  return (
    <main style={{ minHeight: '100vh', padding: '40px 0' }}>
      <div className="container">
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
          <a href="/" style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px', display: 'block', textDecoration: 'none' }}>
            ← Back to Dashboard
          </a>
          <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>
            <span style={{ color: 'var(--accent-purple)' }}>Reflexion</span> Playbooks
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '12px' }}>
            Self-improving playbooks that get faster after every incident. The reflexion flywheel in action.
          </p>
        </motion.div>

        {/* Flywheel Summary */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
          className="glass-card" style={{ padding: '24px', marginBottom: '32px', border: '1px solid rgba(139, 92, 246, 0.2)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'var(--accent-purple)', boxShadow: '0 0 12px var(--accent-purple)' }} />
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--accent-purple)' }}>The Reflexion Flywheel</h3>
          </div>
          <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
            {resolutionTimes.length >= 2 ? (
              <>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--accent-red)' }}>{resolutionTimes[0].duration_minutes}min</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>First Occurrence</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', color: 'var(--text-muted)', fontSize: '20px' }}>→</div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--accent-amber)' }}>
                    {resolutionTimes[Math.floor(resolutionTimes.length / 2)].duration_minutes}min
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Mid Point</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', color: 'var(--text-muted)', fontSize: '20px' }}>→</div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--accent-green)' }}>
                    {resolutionTimes[resolutionTimes.length - 1].duration_minutes}min
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Latest</div>
                </div>
              </>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>Need more investigations to show the flywheel.</p>
            )}
          </div>
        </motion.div>

        {/* Pattern Playbooks */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {patternImprovements.map((pi, i) => {
            const info = PATTERN_INFO[pi.pattern] || { name: pi.pattern, description: 'Failure pattern detected by Meridian AI workers.', color: 'var(--text-muted)' }
            const isExpanded = selectedPattern === pi.pattern
            return (
              <motion.div key={pi.pattern} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 + i * 0.08 }}
                className="glass-card" style={{ padding: '24px', cursor: 'pointer', border: isExpanded ? `1px solid ${info.color}40` : '1px solid var(--border-subtle)' }}
                onClick={() => setSelectedPattern(isExpanded ? null : pi.pattern)}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div>
                    <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#fff', marginBottom: '4px' }}>{info.name}</h3>
                    <p style={{ fontSize: '13px', color: 'var(--text-muted)', maxWidth: '600px' }}>{info.description}</p>
                  </div>
                  <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '22px', fontWeight: 800, color: pi.improvement > 0 ? 'var(--accent-green)' : 'var(--text-muted)' }}>
                        {pi.improvement > 0 ? `-${pi.improvement}%` : 'N/A'}
                      </div>
                      <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>improvement</div>
                    </div>
                    <span className="badge badge-purple">{pi.count} incidents</span>
                  </div>
                </div>

                {/* Timeline */}
                <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end', height: '40px', marginBottom: '8px' }}>
                  {pi.incidents.map((inc, j) => {
                    const time = inc.duration_seconds / 60
                    const maxTime = Math.max(...pi.incidents.map(x => x.duration_seconds / 60), 1)
                    const height = (time / maxTime) * 100
                    const color = time <= 5 ? 'var(--accent-green)' : time <= 10 ? 'var(--accent-amber)' : 'var(--accent-red)'
                    return (
                      <motion.div key={inc.id}
                        initial={{ height: 0 }}
                        animate={{ height: `${height}%` }}
                        transition={{ delay: 0.3 + j * 0.08, duration: 0.4 }}
                        style={{ flex: 1, background: color, borderRadius: '4px 4px 0 0', minWidth: '20px', position: 'relative' }}
                        title={`#${inc.id}: ${Math.round(time)}min`}>
                        <span style={{ position: 'absolute', bottom: '-16px', left: '50%', transform: 'translateX(-50%)', fontSize: '9px', color: 'var(--text-muted)' }}>
                          #{inc.id}
                        </span>
                      </motion.div>
                    )
                  })}
                </div>

                {/* Expanded Playbook Detail */}
                {isExpanded && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
                    style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--border-subtle)' }}>
                    <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--accent-purple)', marginBottom: '8px' }}>Playbook Evolution</h4>
                    {pi.incidents.map((inc, j) => (
                      <div key={inc.id} style={{
                        padding: '12px 16px', borderRadius: '8px', marginBottom: '8px',
                        background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-subtle)',
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                          <span style={{ fontSize: '13px', fontWeight: 600, color: '#fff' }}>Incident #{inc.id}</span>
                          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{new Date(inc.detected).toLocaleDateString()}</span>
                        </div>
                        <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: 'var(--text-muted)' }}>
                          <span>Duration: <strong style={{ color: '#fff' }}>{Math.round(inc.duration_seconds / 60)}min</strong></span>
                          <span>Severity: {inc.severity}</span>
                          {inc.affected_models.length > 0 && <span>Models: {inc.affected_models.length}</span>}
                        </div>
                        {j === pi.incidents.length - 1 && pi.incidents.length > 1 && (
                          <div style={{ marginTop: '8px', padding: '8px 12px', borderRadius: '6px', background: 'rgba(16, 185, 129, 0.06)', fontSize: '12px', color: 'var(--accent-green)' }}>
                            Playbook updated after this resolution — next occurrence will be faster.
                          </div>
                        )}
                      </div>
                    ))}
                  </motion.div>
                )}
              </motion.div>
            )
          })}
        </div>

        {patternImprovements.length === 0 && (
          <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
            <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>No failure patterns detected yet. Run investigations to build playbooks.</p>
          </div>
        )}

        <footer style={{ marginTop: '40px', textAlign: 'center', fontSize: '12px', color: 'var(--text-muted)' }}>
          Reflexion playbooks improve after every investigation via Self-RAG retrieval from DataHub Knowledge Base
        </footer>
      </div>
    </main>
  )
}
