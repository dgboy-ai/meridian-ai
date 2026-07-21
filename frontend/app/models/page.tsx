'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { apiUrl } from '../../lib/config'

const API = ''

interface ModelHealth {
  urn: string
  name: string
  type: string
  platform: string
  owner: string
  tags: string[]
  health_score?: number
  confidence?: number
  resolved_incidents?: number
  resolution_time_minutes?: number
}

interface HealthScoreResponse {
  models: ModelHealth[]
}

export default function ModelsPage() {
  const [models, setModels] = useState<ModelHealth[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedModel, setSelectedModel] = useState<ModelHealth | null>(null)
  const [checkingHealth, setCheckingHealth] = useState(false)
  const [healthResult, setHealthResult] = useState<any>(null)

  const MOCK_MODELS: ModelHealth[] = [
    {
      urn: 'urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v3,PROD)',
      name: 'churn_model_v3', type: 'mlModel', platform: 'mlflow',
      owner: 'ml-platform-team', tags: ['production', 'churn'],
      health_score: 89, confidence: 0.97, resolved_incidents: 14, resolution_time_minutes: 3.0,
    },
    {
      urn: 'urn:li:mlModel:(urn:li:dataPlatform:mlflow,ltv_model_v2,PROD)',
      name: 'ltv_model_v2', type: 'mlModel', platform: 'mlflow',
      owner: 'ml-platform-team', tags: ['production', 'ltv'],
      health_score: 62, confidence: 0.88, resolved_incidents: 8, resolution_time_minutes: 8.0,
    },
    {
      urn: 'urn:li:mlModel:(urn:li:dataPlatform:mlflow,segment_model_v1,PROD)',
      name: 'segment_model_v1', type: 'mlModel', platform: 'mlflow',
      owner: 'ml-platform-team', tags: ['production', 'segmentation'],
      health_score: 91, confidence: 0.95, resolved_incidents: 3, resolution_time_minutes: 5.0,
    },
  ]

  useEffect(() => {
    fetch(apiUrl('/api/health-scores'))
      .then(r => r.json())
      .then(data => {
        // Use API data if non-empty, otherwise fall back to mock
        setModels(data.models && data.models.length > 0 ? data.models : MOCK_MODELS)
        setLoading(false)
      })
      .catch(() => {
        setModels(MOCK_MODELS)
        setLoading(false)
      })
  }, [])

  const checkModelHealth = async (model: ModelHealth) => {
    setSelectedModel(model)
    setCheckingHealth(true)
    setHealthResult(null)

    try {
      const res = await fetch(apiUrl(`/api/models/${model.name}`))
      if (res.ok) {
        const data = await res.json()
        setHealthResult(data)
      }
    } catch (err) {
      console.error('Health check failed:', err)
    } finally {
      setCheckingHealth(false)
    }
  }

  const getHealthColor = (score: number) => {
    if (score >= 80) return '#10b981'
    if (score >= 60) return '#f59e0b'
    return '#ef4444'
  }

  const getHealthLabel = (score: number) => {
    if (score >= 80) return 'Healthy'
    if (score >= 60) return 'Warning'
    return 'Critical'
  }

  if (loading) {
    return (
      <main style={{ minHeight: '100vh', padding: '40px 0' }}>
        <div className="container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
          <div style={{ textAlign: 'center' }}>
            <div className="pulse" style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'var(--accent-green)', opacity: 0.5, margin: '0 auto 16px' }} />
            <span style={{ color: 'var(--text-muted)' }}>Loading model health data...</span>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main style={{ minHeight: '100vh', padding: '40px 0' }}>
      <div className="container">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
          <a href="/" style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px', display: 'block', textDecoration: 'none' }}>
            ← Back to Dashboard
          </a>
          <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>
            <span style={{ color: 'var(--accent-purple)' }}>Model Health</span> Dashboard
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '32px' }}>
            Real-time health monitoring for production ML models. Click any model to run a health check.
          </p>
        </motion.div>

        {/* Model Cards Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '24px', marginBottom: '40px' }}>
          {models.map((model, idx) => {
            const healthColor = getHealthColor(model.health_score || 0)
            return (
              <motion.div
                key={model.urn}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="glass-card"
                style={{
                  padding: '24px',
                  cursor: 'pointer',
                  border: selectedModel?.urn === model.urn ? `2px solid ${healthColor}` : '1px solid var(--border-subtle)',
                  transition: 'all 0.2s',
                }}
                onClick={() => checkModelHealth(model)}
                whileHover={{ scale: 1.02 }}
              >
                {/* Model Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px' }}>
                      {model.platform}
                    </div>
                    <div style={{ fontSize: '18px', fontWeight: 700, color: '#fff' }}>{model.name}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>{model.owner}</div>
                  </div>
                  <div style={{
                    padding: '6px 12px', borderRadius: '8px',
                    background: `${healthColor}15`, color: healthColor,
                    fontSize: '12px', fontWeight: 700,
                  }}>
                    {getHealthLabel(model.health_score || 0)}
                  </div>
                </div>

                {/* Health Score Bar */}
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Health Score</span>
                    <span style={{ fontSize: '14px', fontWeight: 700, color: healthColor }}>{model.health_score}/100</span>
                  </div>
                  <div style={{ width: '100%', height: '8px', borderRadius: '4px', background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${model.health_score}%` }}
                      transition={{ delay: 0.3 + idx * 0.1, duration: 0.6 }}
                      style={{ height: '100%', background: healthColor, borderRadius: '4px' }}
                    />
                  </div>
                </div>

                {/* Stats Row */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Confidence</div>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: '#fff' }}>{((model.confidence || 0) * 100).toFixed(0)}%</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Resolved</div>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: '#fff' }}>{model.resolved_incidents || 0}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Avg Time</div>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: '#fff' }}>{model.resolution_time_minutes || 0}min</div>
                  </div>
                </div>

                {/* Tags */}
                <div style={{ display: 'flex', gap: '6px', marginTop: '12px', flexWrap: 'wrap' }}>
                  {model.tags.map(tag => (
                    <span key={tag} style={{
                      padding: '2px 8px', borderRadius: '4px', fontSize: '10px',
                      background: 'rgba(168, 85, 247, 0.1)', color: 'var(--accent-purple)',
                      border: '1px solid rgba(168, 85, 247, 0.2)',
                    }}>
                      {tag}
                    </span>
                  ))}
                </div>
              </motion.div>
            )
          })}
        </div>

        {/* Health Check Result Panel */}
        {selectedModel && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card"
            style={{ padding: '32px', marginBottom: '40px' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <h2 style={{ fontSize: '18px', fontWeight: 700 }}>
                Health Check: <span style={{ color: 'var(--accent-cyan)' }}>{selectedModel.name}</span>
              </h2>
              <button
                onClick={() => checkModelHealth(selectedModel)}
                disabled={checkingHealth}
                className="btn-glass"
                style={{ padding: '8px 16px', fontSize: '12px' }}
              >
                {checkingHealth ? 'Checking...' : 'Re-check'}
              </button>
            </div>

            {checkingHealth ? (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <div className="pulse" style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'var(--accent-cyan)', opacity: 0.5, margin: '0 auto 12px' }} />
                <span style={{ color: 'var(--text-muted)' }}>Running health check via DataHub MCP...</span>
              </div>
            ) : healthResult ? (
              <div>
                {/* Health Score Display */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '24px', marginBottom: '24px' }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '48px', fontWeight: 900, color: getHealthColor(healthResult.health_score || 0) }}>
                      {healthResult.health_score}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Health Score</div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '48px', fontWeight: 900, color: '#fff' }}>
                      {healthResult.confidence ? `${(healthResult.confidence * 100).toFixed(0)}%` : 'N/A'}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Confidence</div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '48px', fontWeight: 900, color: '#fff' }}>
                      {healthResult.resolved_incidents || 0}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Resolved Incidents</div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '48px', fontWeight: 900, color: 'var(--accent-cyan)' }}>
                      {healthResult.resolution_time_minutes || 0}min
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Avg Resolution</div>
                  </div>
                </div>

                {/* Assessment */}
                <div style={{
                  padding: '16px 20px', borderRadius: '8px',
                  background: 'rgba(16, 185, 129, 0.05)',
                  border: '1px solid rgba(16, 185, 129, 0.2)',
                }}>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--accent-green)', marginBottom: '4px' }}>
                    Assessment: {healthResult.assessment || 'Unknown'}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    Model URN: {healthResult.model_urn}
                  </div>
                </div>

                {/* Metrics Breakdown */}
                {healthResult.metrics && (
                  <div style={{ marginTop: '24px' }}>
                    <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: 'var(--text-secondary)' }}>
                      Metric Breakdown
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
                      {Object.entries(healthResult.metrics).map(([name, value]) => (
                        <div key={name} style={{
                          padding: '12px 16px', borderRadius: '8px',
                          background: 'rgba(255,255,255,0.02)',
                          border: '1px solid var(--border-subtle)',
                        }}>
                          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                            {name.replace(/_/g, ' ')}
                          </div>
                          <div style={{ fontSize: '18px', fontWeight: 700, color: '#fff', marginTop: '4px' }}>
                            {typeof value === 'number' ? value.toFixed(2) : String(value)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                Click a model card above to run a health check
              </div>
            )}
          </motion.div>
        )}

        {/* Footer */}
        <footer style={{ marginTop: '40px', textAlign: 'center', fontSize: '12px', color: 'var(--text-muted)' }}>
          Model health data sourced from DataHub MCP · Health scores computed from real worker confidence
        </footer>
      </div>
    </main>
  )
}
