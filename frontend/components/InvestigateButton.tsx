'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const DATASETS = [
  {
    urn: 'urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)',
    name: 'raw_events',
    platform: 'Snowflake',
    description: 'Raw e-commerce event stream — most common incident source',
  },
  {
    urn: 'urn:li:dataset:(urn:li:dataPlatform:dbt,meridian.feature_pipeline,PROD)',
    name: 'feature_pipeline',
    platform: 'dbt',
    description: 'Feature engineering pipeline output',
  },
  {
    urn: 'urn:li:dataset:(urn:li:dataPlatform:feast,meridian.feature_store,PROD)',
    name: 'feature_store',
    platform: 'Feast',
    description: 'Online feature store serving production models',
  },
]

interface Props {
  onInvestigationStarted?: (incidentId: string) => void
}

export default function InvestigateButton({ onInvestigationStarted }: Props) {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedUrn, setSelectedUrn] = useState(DATASETS[0].urn)
  const [isStarting, setIsStarting] = useState(false)
  const [error, setError] = useState('')

  const handleStart = async () => {
    setIsStarting(true)
    setError('')
    try {
      const res = await fetch('/api/investigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_urn: selectedUrn }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: 'Failed to start' }))
        throw new Error(err.error)
      }
      const data = await res.json()
      setIsOpen(false)
      if (onInvestigationStarted) {
        onInvestigationStarted(data.incident_id)
      } else {
        window.location.href = `/incidents/${data.incident_id}`
      }
    } catch (e: any) {
      setError(e.message || 'Failed to start investigation')
    } finally {
      setIsStarting(false)
    }
  }

  return (
    <>
      {/* Trigger Button */}
      <motion.button
        onClick={() => setIsOpen(true)}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '10px',
          padding: '14px 28px',
          borderRadius: '12px',
          border: 'none',
          cursor: 'pointer',
          background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          color: '#fff',
          fontSize: '15px',
          fontWeight: 700,
          letterSpacing: '-0.01em',
          boxShadow: '0 4px 24px rgba(99, 102, 241, 0.3), 0 0 0 1px rgba(139, 92, 246, 0.2)',
          transition: 'box-shadow 0.2s',
        }}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        Run Investigation
      </motion.button>

      {/* Modal */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => !isStarting && setIsOpen(false)}
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 1000,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(6, 4, 13, 0.85)',
              backdropFilter: 'blur(8px)',
            }}
          >
            <motion.div
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 20, scale: 0.95 }}
              onClick={(e) => e.stopPropagation()}
              style={{
                width: '90%',
                maxWidth: '520px',
                background: 'rgba(12, 8, 28, 0.95)',
                border: '1px solid rgba(139, 92, 246, 0.2)',
                borderRadius: '20px',
                padding: '32px',
                boxShadow: '0 24px 80px rgba(0,0,0,0.5), 0 0 40px rgba(99, 102, 241, 0.1)',
              }}
            >
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <div>
                  <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#fff', marginBottom: '4px' }}>
                    New Investigation
                  </h2>
                  <p style={{ fontSize: '13px', color: 'rgba(255,255,255,0.4)' }}>
                    Select a dataset to investigate. 18 workers will fire.
                  </p>
                </div>
                <button
                  onClick={() => !isStarting && setIsOpen(false)}
                  style={{
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    color: 'rgba(255,255,255,0.5)',
                    width: '32px',
                    height: '32px',
                    cursor: isStarting ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '16px',
                  }}
                >
                  x
                </button>
              </div>

              {/* Dataset Selection */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '24px' }}>
                {DATASETS.map((ds) => (
                  <button
                    key={ds.urn}
                    onClick={() => setSelectedUrn(ds.urn)}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '12px',
                      padding: '14px 16px',
                      borderRadius: '12px',
                      border: selectedUrn === ds.urn
                        ? '2px solid rgba(99, 102, 241, 0.6)'
                        : '1px solid rgba(255,255,255,0.06)',
                      background: selectedUrn === ds.urn
                        ? 'rgba(99, 102, 241, 0.08)'
                        : 'rgba(255,255,255,0.02)',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.15s',
                    }}
                  >
                    <div style={{
                      width: '20px',
                      height: '20px',
                      borderRadius: '50%',
                      border: selectedUrn === ds.urn
                        ? '6px solid #6366f1'
                        : '2px solid rgba(255,255,255,0.2)',
                      flexShrink: 0,
                      marginTop: '2px',
                    }} />
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                        <span style={{ fontSize: '14px', fontWeight: 600, color: '#fff' }}>{ds.name}</span>
                        <span style={{
                          fontSize: '10px', fontWeight: 600, padding: '2px 6px', borderRadius: '4px',
                          background: 'rgba(139, 92, 246, 0.15)', color: '#a78bfa',
                        }}>
                          {ds.platform}
                        </span>
                      </div>
                      <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.35)' }}>
                        {ds.description}
                      </span>
                    </div>
                  </button>
                ))}
              </div>

              {/* Error */}
              {error && (
                <div style={{
                  padding: '10px 14px', borderRadius: '8px', marginBottom: '16px',
                  background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.2)',
                  fontSize: '13px', color: '#f43f5e',
                }}>
                  {error}
                </div>
              )}

              {/* Action */}
              <button
                onClick={handleStart}
                disabled={isStarting}
                style={{
                  width: '100%',
                  padding: '14px',
                  borderRadius: '12px',
                  border: 'none',
                  cursor: isStarting ? 'not-allowed' : 'pointer',
                  background: isStarting
                    ? 'rgba(99, 102, 241, 0.3)'
                    : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                  color: '#fff',
                  fontSize: '15px',
                  fontWeight: 700,
                  opacity: isStarting ? 0.7 : 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                }}
              >
                {isStarting ? (
                  <>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      style={{ width: '16px', height: '16px', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', borderRadius: '50%' }}
                    />
                    Starting Investigation...
                  </>
                ) : (
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <polygon points="5 3 19 12 5 21 5 3" />
                    </svg>
                    Start Investigation
                  </>
                )}
              </button>

              <p style={{ fontSize: '11px', color: 'rgba(255,255,255,0.25)', textAlign: 'center', marginTop: '12px' }}>
                18 workers will fire. Results written to DataHub. ~30 seconds in mock mode.
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
