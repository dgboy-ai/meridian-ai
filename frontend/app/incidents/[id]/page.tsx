'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { useParams } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import InvestigateButton from '../../../components/InvestigateButton'
import LineageGraph3D from '../../../components/LineageGraph3D'

// Use relative URLs - Next.js rewrites proxy to backend
const API = ''

interface TimelineEvent {
  time: string
  step: string
  status: string
  finding: string
  confidence: number
  message?: string
  severity?: string
  evidence?: any
  business_impact?: any
}

interface BlastNode {
  urn: string
  name: string
  type: string
  status: string
  health_score?: number
  confidence?: number
}

interface Incident {
  id: string
  title: string
  severity: string
  status: string
  detected: string
  resolved: string
  duration_seconds: number
  root_cause: string
  pattern_id: string
  timeline: TimelineEvent[]
  blast_radius: {
    source: BlastNode
    affected: BlastNode[]
    business_impact: {
      predictions_today: number
      revenue_at_risk_daily: number
      affected_dashboards: number
    }
  }
  writeback: Record<string, any>
}

const STEP_CONFIG: Record<string, { icon: string; color: string; label: string }> = {
  planner: { icon: '🧠', color: 'var(--accent-purple)', label: 'Planner' },
  data_sentinel: { icon: '🔍', color: 'var(--accent-red)', label: 'Data Sentinel' },
  feature_drift: { icon: '📉', color: 'var(--accent-amber)', label: 'Feature Drift' },
  training_serving_skew: { icon: '⚖️', color: 'var(--accent-amber)', label: 'Training-Serving Skew' },
  data_leakage: { icon: '🔒', color: 'var(--accent-red)', label: 'Data Leakage' },
  root_cause: { icon: '🎯', color: 'var(--accent-blue)', label: 'Root Cause' },
  verifier_agent: { icon: '🛡️', color: 'var(--accent-purple)', label: 'VerifierAgent' },
  validation: { icon: '✅', color: 'var(--accent-green)', label: 'Validation' },
  knowledge_writer: { icon: '📝', color: 'var(--accent-green)', label: 'Knowledge Writer' },
  reflexion: { icon: '🔄', color: 'var(--accent-purple)', label: 'Reflexion Loop' },
  lifecycle_governance: { icon: '🏛️', color: 'var(--accent-amber)', label: 'Lifecycle Governance' },
  eu_ai_act_compliance: { icon: '📋', color: 'var(--accent-blue)', label: 'EU AI Act Compliance' },
  shadow_ai_discovery: { icon: '🕵️', color: 'var(--accent-amber)', label: 'Shadow AI Discovery' },
  contract_enforcer: { icon: '📜', color: 'var(--accent-green)', label: 'Contract Enforcer' },
  explanation_drift: { icon: '💡', color: 'var(--accent-blue)', label: 'Explanation Drift' },
  self_healing_assertions: { icon: '🩹', color: 'var(--accent-green)', label: 'Self-Healing Assertions' },
  pipeline_circuit_breaker: { icon: '⚡', color: 'var(--accent-red)', label: 'Pipeline Circuit Breaker' },
  deprecation_advisor: { icon: '📦', color: 'var(--accent-amber)', label: 'Deprecation Advisor' },
  dbt_code_generator: { icon: '🗄️', color: 'var(--accent-cyan)', label: 'dbt Code Generator' },
  ml_metadata: { icon: '🤖', color: 'var(--accent-purple)', label: 'ML Metadata' },
  agentic_circuit_breaker: { icon: '🔌', color: 'var(--accent-red)', label: 'Agentic Circuit Breaker' },
  complete: { icon: '🏁', color: 'var(--accent-green)', label: 'Complete' },
}

export default function IncidentPage() {
  const params = useParams()
  const [incident, setIncident] = useState<Incident | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'timeline' | 'blast' | 'writeback'>('timeline')
  const [streamingEvents, setStreamingEvents] = useState<TimelineEvent[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamError, setStreamError] = useState('')
  const eventSourceRef = useRef<EventSource | null>(null)
  const retryCountRef = useRef(0)
  const MAX_RETRIES = 3

  useEffect(() => {
    fetch(`${API}/api/incidents/${params.id}`)
      .then(r => r.json())
      .then(data => {
        setIncident(data)
        setLoading(false)
        // Auto-start live SSE stream for in-progress investigations
        if (data.status === 'IN_PROGRESS') {
          startLiveStream()
        }
      })
      .catch(() => setLoading(false))
  }, [params.id])

  const startLiveStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    setStreamingEvents([])
    setIsStreaming(true)
    setStreamError('')
    retryCountRef.current = 0

    const connect = () => {
      const es = new EventSource(`${API}/stream/investigate?incident_id=${params.id}&mode=live`)
      eventSourceRef.current = es

      es.onmessage = (event) => {
        if (event.data === '[DONE]') {
          es.close()
          setIsStreaming(false)
          retryCountRef.current = 0
          // Refetch incident to get final state
          fetch(`${API}/api/incidents/${params.id}`)
            .then(r => r.json())
            .then(data => setIncident(data))
          return
        }
        try {
          const data = JSON.parse(event.data)
          if (data.step && data.step !== 'complete' && data.step !== 'error') {
            setStreamingEvents(prev => [...prev, data])
            retryCountRef.current = 0
          }
          if (data.step === 'error') {
            setStreamError(data.error || 'Stream error')
          }
        } catch {}
      }

      es.onerror = () => {
        es.close()
        if (retryCountRef.current < MAX_RETRIES) {
          retryCountRef.current++
          const delay = Math.min(1000 * Math.pow(2, retryCountRef.current), 8000)
          setStreamError(`Connection lost. Retrying in ${delay / 1000}s... (${retryCountRef.current}/${MAX_RETRIES})`)
          setTimeout(connect, delay)
        } else {
          setIsStreaming(false)
          setStreamError('Connection failed after retries.')
        }
      }
    }

    connect()
  }, [params.id])

  const startReplay = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    setStreamingEvents([])
    setIsStreaming(true)
    setStreamError('')
    retryCountRef.current = 0

    const connect = () => {
      const es = new EventSource(`${API}/stream/replay?incident_id=${params.id}&delay=0.6`)
      eventSourceRef.current = es

      es.onmessage = (event) => {
        // SSE heartbeat comments start with ':' and are ignored by EventSource
        // but [DONE] comes through as a message
        if (event.data === '[DONE]') {
          es.close()
          setIsStreaming(false)
          retryCountRef.current = 0
          return
        }
        try {
          const data = JSON.parse(event.data)
          // Skip heartbeat/error events with no step
          if (data.step && data.step !== 'complete' && data.step !== 'error') {
            setStreamingEvents(prev => [...prev, data])
            retryCountRef.current = 0 // Reset retry on successful event
          }
          if (data.step === 'error') {
            setStreamError(data.error || 'Stream error')
          }
        } catch {}
      }

      es.onerror = () => {
        es.close()
        // Auto-retry with exponential backoff
        if (retryCountRef.current < MAX_RETRIES) {
          retryCountRef.current++
          const delay = Math.min(1000 * Math.pow(2, retryCountRef.current), 8000)
          setStreamError(`Connection lost. Retrying in ${delay / 1000}s... (${retryCountRef.current}/${MAX_RETRIES})`)
          setTimeout(connect, delay)
        } else {
          setIsStreaming(false)
          setStreamError('Connection failed after retries. Check if the backend is running.')
        }
      }
    }

    connect()
  }, [params.id])

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  if (loading) return <Main><LoadingPulse /></Main>
  if (!incident) return (
    <Main>
      <div style={{ textAlign: 'center', padding: '80px 0' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '8px', color: 'var(--text-primary)' }}>Incident not found</h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>The investigation you&apos;re looking for doesn&apos;t exist.</p>
        <a href="/" className="btn-glass" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '10px 20px' }}>
          ← Back to all investigations
        </a>
      </div>
    </Main>
  )

  const displayTimeline = streamingEvents.length > 0 ? streamingEvents : incident.timeline

  const isLive = incident.status === 'IN_PROGRESS'

  return (
    <Main>
      <Header incident={incident} onReplay={isLive ? startLiveStream : startReplay} isStreaming={isStreaming} streamError={streamError} />
      <TabBar active={activeTab} onChange={setActiveTab} />
      {activeTab === 'timeline' && <Timeline events={displayTimeline} isStreaming={isStreaming} />}
      {activeTab === 'blast' && <BlastRadius radius={incident.blast_radius} />}
      {activeTab === 'writeback' && <WritebackLog writeback={incident.writeback} />}
    </Main>
  )
}

function Main({ children }: { children: React.ReactNode }) {
  return <main style={{ minHeight: '100vh', padding: '40px 0' }}><div className="container">{children}</div></main>
}

function LoadingPulse() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', gap: '16px' }}>
      <div className="pulse" style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'var(--accent-green)', opacity: 0.5 }} />
      <span style={{ color: 'var(--text-muted)' }}>Loading investigation...</span>
    </div>
  )
}

function Header({ incident, onReplay, isStreaming, streamError }: { incident: Incident; onReplay: () => void; isStreaming: boolean; streamError: string }) {
  const mins = Math.round(incident.duration_seconds / 60)
  const isLive = incident.status === 'IN_PROGRESS'
  return (
    <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <a href="/" style={{ fontSize: '13px', color: 'var(--text-muted)', textDecoration: 'none' }}>
          ← All Investigations
        </a>
        <InvestigateButton />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 700 }}>
          <span style={{ color: 'var(--accent-blue)' }}>#{incident.id}</span> {incident.title}
        </h1>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span className={`badge badge-${incident.severity === 'HIGH' ? 'red' : 'amber'}`}>{incident.severity}</span>
          {isLive && !isStreaming && (
            <span className="badge badge-green" style={{ animation: 'pulse-glow 2s ease-in-out infinite' }}>LIVE</span>
          )}
          <button
            onClick={onReplay}
            disabled={isStreaming}
            className="btn-glass"
            style={{ padding: '8px 16px', fontSize: '12px', cursor: isStreaming ? 'not-allowed' : 'pointer', opacity: isStreaming ? 0.5 : 1 }}
          >
            {isStreaming ? (isLive ? 'Investigating...' : 'Replaying...') : (isLive ? 'Watch Live' : 'Replay Investigation')}
          </button>
        </div>
      </div>
      <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '16px', maxWidth: '700px' }}>{incident.root_cause}</p>
      <div style={{ display: 'flex', gap: '24px', fontSize: '13px', color: 'var(--text-muted)' }}>
        <span>Detected: {new Date(incident.detected).toLocaleString()}</span>
        <span>Duration: {mins} minutes</span>
        {incident.pattern_id && <span>Pattern: {incident.pattern_id}</span>}
      </div>
      {streamError && (
        <div style={{
          marginTop: '12px', padding: '10px 14px', borderRadius: '8px',
          background: 'rgba(244, 63, 94, 0.08)', border: '1px solid rgba(244, 63, 94, 0.2)',
          fontSize: '13px', color: '#f43f5e',
        }}>
          {streamError}
        </div>
      )}
    </motion.div>
  )
}

function TabBar({ active, onChange }: { active: string; onChange: (t: any) => void }) {
  const tabs = ['timeline', 'blast', 'writeback'] as const
  const labels = { timeline: 'Investigation Timeline', blast: 'Blast Radius', writeback: 'Write-back Log' }
  return (
    <div style={{ display: 'flex', gap: '4px', margin: '32px 0 24px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1px' }}>
      {tabs.map(t => (
        <button key={t} onClick={() => onChange(t)} style={{
          padding: '10px 20px', borderRadius: '8px 8px 0 0', border: 'none', cursor: 'pointer',
          background: active === t ? 'var(--bg-card)' : 'transparent',
          color: active === t ? 'var(--text-primary)' : 'var(--text-muted)',
          fontWeight: active === t ? 600 : 400, fontSize: '14px',
          borderBottom: active === t ? '2px solid var(--accent-green)' : '2px solid transparent',
        }}>
          {labels[t]}
        </button>
      ))}
    </div>
  )
}

function Timeline({ events, isStreaming }: { events: TimelineEvent[]; isStreaming: boolean }) {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0', position: 'relative' }}>
        <div style={{
          position: 'absolute', left: '15px', top: '24px', bottom: '24px', width: '2px',
          background: 'linear-gradient(180deg, var(--accent-red), var(--accent-amber), var(--accent-green))',
          opacity: 0.3,
        }} />
        <AnimatePresence>
          {events.map((e, i) => {
            const config = STEP_CONFIG[e.step] || { icon: '❓', color: 'var(--text-muted)', label: e.step }
            return (
              <motion.div
                key={`${e.step}-${i}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: isStreaming ? 0 : 0.1 + i * 0.12 }}
                style={{ display: 'flex', gap: '16px', padding: '14px 0', position: 'relative' }}
              >
                <div style={{
                  width: '32px', height: '32px', borderRadius: '8px', flexShrink: 0,
                  background: `${config.color}20`,
                  border: `1px solid ${config.color}40`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '14px', zIndex: 1,
                }}>
                  {config.icon}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontSize: '13px', fontWeight: 600, color: config.color }}>
                      {config.label}
                    </span>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>{e.time}</span>
                  </div>
                  <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '6px', lineHeight: 1.5 }}>
                    {e.finding}
                  </p>
                  {e.message && (
                    <p style={{ fontSize: '12px', color: 'var(--text-muted)', fontStyle: 'italic', marginBottom: '6px' }}>
                      {e.message}
                    </p>
                  )}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '80px', height: '4px', borderRadius: '2px', background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${e.confidence * 100}%` }}
                        transition={{ delay: isStreaming ? 0 : 0.3 + i * 0.12, duration: 0.4 }}
                        style={{ height: '100%', background: config.color, borderRadius: '2px' }}
                      />
                    </div>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{(e.confidence * 100).toFixed(0)}% confidence</span>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </AnimatePresence>
        {isStreaming && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            style={{ display: 'flex', gap: '8px', alignItems: 'center', padding: '12px 0', paddingLeft: '48px' }}
          >
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-green)' }} />
            <span style={{ fontSize: '13px', color: 'var(--accent-green)' }}>Investigation in progress...</span>
          </motion.div>
        )}
      </div>
    </motion.div>
  )
}

function BlastRadius({ radius }: { radius: any }) {
  if (!radius) return <p style={{ color: 'var(--text-muted)' }}>No blast radius data</p>

  const source = radius.source
  const affected = radius.affected || []
  const impact = radius.business_impact || {}

  const STATUS_COLORS: Record<string, string> = {
    critical: '#EF4444',
    warning: '#F59E0B',
    healthy: '#10B981',
  }

  const TYPE_ICONS: Record<string, string> = {
    dataset: '📊',
    mlModel: '🤖',
    dashboard: '📈',
    deployment: '🚀',
    pipeline: '⚙️',
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
      {/* Business Impact Card */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Business Impact
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
          <div>
            <div style={{ fontSize: '28px', fontWeight: 700, color: 'var(--accent-amber)' }}>
              {(impact.predictions_today || 0).toLocaleString()}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Predictions/Day</div>
          </div>
          <div>
            <div style={{ fontSize: '28px', fontWeight: 700, color: 'var(--accent-red)' }}>
              ${(impact.revenue_at_risk_daily || 0).toLocaleString()}/day
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Revenue at Risk</div>
          </div>
          <div>
            <div style={{ fontSize: '28px', fontWeight: 700, color: 'var(--accent-blue)' }}>
              {impact.affected_dashboards || 0}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Dashboards Affected</div>
          </div>
        </div>
      </div>

      {/* Blast Radius Visualization */}
      <div className="card">
        <h3 style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Lineage Propagation — Blast Radius
        </h3>

        {/* Source Node */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          style={{
            padding: '16px 20px', borderRadius: '10px',
            background: 'rgba(239, 68, 68, 0.08)',
            border: '1px solid rgba(239, 68, 68, 0.25)',
            boxShadow: '0 0 30px rgba(239, 68, 68, 0.15)',
            marginBottom: '8px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: '10px', color: 'var(--accent-red)', fontWeight: 700, letterSpacing: '0.1em' }}>SOURCE</span>
              <div style={{ fontWeight: 700, fontSize: '16px', marginTop: '4px' }}>
                {TYPE_ICONS[source?.type] || '📦'} {source?.name}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>{source?.type}</div>
            </div>
            <span className="badge badge-red">Schema Change</span>
          </div>
        </motion.div>

        {/* Propagation Line */}
        <div style={{ display: 'flex', justifyContent: 'center', padding: '4px 0' }}>
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: '32px' }}
            transition={{ delay: 0.3, duration: 0.4 }}
            style={{
              width: '3px',
              background: 'linear-gradient(180deg, var(--accent-red), var(--accent-amber))',
              borderRadius: '2px',
            }}
          />
        </div>

        {/* Affected Nodes */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {affected.map((node: any, i: number) => {
            const color = STATUS_COLORS[node.status] || STATUS_COLORS.healthy
            return (
              <motion.div
                key={node.urn}
                initial={{ opacity: 0, x: -30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + i * 0.15, type: 'spring', stiffness: 100 }}
                style={{
                  padding: '14px 18px', borderRadius: '10px',
                  background: `${color}08`,
                  border: `1px solid ${color}25`,
                  boxShadow: node.status === 'critical' ? `0 0 20px ${color}15` : 'none',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '15px' }}>
                      {TYPE_ICONS[node.type] || '📦'} {node.name}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>{node.type}</div>
                  </div>
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                    {node.health_score && (
                      <span style={{ fontSize: '13px', color: color, fontWeight: 600 }}>
                        Health: {node.health_score}
                      </span>
                    )}
                    <span style={{
                      padding: '4px 10px', borderRadius: '6px', fontSize: '11px', fontWeight: 600,
                      background: `${color}15`, color: color,
                    }}>
                      {node.status}
                    </span>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>

        {/* Summary */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 + affected.length * 0.15 + 0.3 }}
          style={{
            marginTop: '16px', padding: '12px 16px', borderRadius: '8px',
            background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-subtle)',
            textAlign: 'center', fontSize: '13px', color: 'var(--text-secondary)',
          }}
        >
          Blast radius: {affected.length} affected assets · ${(impact.revenue_at_risk_daily || 0).toLocaleString()}/day revenue at risk
        </motion.div>
      </div>

      {/* 3D Lineage Graph */}
      <div className="card" style={{ marginTop: '24px', padding: '0', overflow: 'hidden', position: 'relative', height: '400px' }}>
        <div style={{ position: 'absolute', top: '16px', left: '16px', zIndex: 10 }}>
          <h3 style={{ fontSize: '14px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Lineage Graph — 3D View
          </h3>
          <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Interactive visualization of data flow and blast radius propagation
          </p>
        </div>
        <LineageGraph3D
          activePhase={affected.length > 0 ? 'drift' : 'idle'}
          sourceNode={source ? { name: source.name, type: source.type, status: source.status } : null}
          affectedNodes={affected.map((n: any) => ({ name: n.name, type: n.type, status: n.status, health_score: n.health_score }))}
        />
      </div>
    </motion.div>
  )
}

function WritebackLog({ writeback }: { writeback: Record<string, any> }) {
  if (!writeback) return <p style={{ color: 'var(--text-muted)' }}>No write-back data</p>

  const items = Object.entries(writeback).map(([key, val]: [string, any]) => ({
    label: key.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()),
    title: val.title || val.entity || val.id,
    status: val.status,
    extra: val.health_score ? `Health: ${val.health_score}` : val.linked_entities ? `${val.linked_entities} entities` : val.confidence ? `Confidence: ${(val.confidence * 100).toFixed(0)}%` : null,
  }))

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
      <div className="card" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-green)' }} />
          <h3 style={{ fontSize: '14px', color: 'var(--accent-green)' }}>
            {items.length} artifact{items.length !== 1 ? 's' : ''} written to DataHub
          </h3>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {items.map((item, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 + i * 0.1 }}
              style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '14px 18px', borderRadius: '8px',
                background: 'rgba(16, 185, 129, 0.04)',
                border: '1px solid rgba(16, 185, 129, 0.12)',
              }}
            >
              <div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '2px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{item.label}</div>
                <div style={{ fontSize: '14px', fontWeight: 600 }}>{item.title}</div>
                {item.extra && <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>{item.extra}</div>}
              </div>
              <span className="badge badge-green">{item.status}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  )
}
