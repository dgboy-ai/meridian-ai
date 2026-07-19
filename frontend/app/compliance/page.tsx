'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

interface AuditRecord {
  record_id: string
  timestamp: string
  article: string
  system_name: string
  decision_type: string
  input_summary: string
  output_summary: string
  confidence: number
  human_override: boolean
  reasoning_chain: string[]
  hash_sha256: string
  previous_hash: string
}

interface AuditTrail {
  total_records: number
  chain_valid: boolean
  last_hash: string | null
}

interface PiiScanResult {
  status: string
  dataset_urn: string
  violations?: number
  affected_columns?: string[]
  severity?: string
  regulations?: string[]
}

export default function CompliancePage() {
  const [auditTrail, setAuditTrail] = useState<AuditTrail | null>(null)
  const [records, setRecords] = useState<AuditRecord[]>([])
  const [piiResult, setPiiResult] = useState<PiiScanResult | null>(null)
  const [scanning, setScanning] = useState(false)
  const [loading, setLoading] = useState(true)
  const [selectedRecord, setSelectedRecord] = useState<AuditRecord | null>(null)

  useEffect(() => {
    Promise.all([
      fetch('/api/compliance/audit-trail').then(r => r.json()),
      fetch('/api/compliance/eu-ai-act/42').then(r => r.json()),
    ]).then(([trail, file]) => {
      setAuditTrail(trail)
      setRecords(file.audit_records || [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const runPiiScan = async () => {
    setScanning(true)
    try {
      const res = await fetch('/api/compliance/scan-pii', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_urn: 'urn:li:dataset:(urn:li:dataPlatform:snowflake,meridian.raw_events,PROD)' }),
      })
      setPiiResult(await res.json())
    } catch {
      setPiiResult({ status: 'error', dataset_urn: '' })
    } finally {
      setScanning(false)
    }
  }

  if (loading) return (
    <main style={{ minHeight: '100vh', padding: '40px 0' }}>
      <div className="container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <div style={{ textAlign: 'center' }}>
          <div className="pulse" style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'var(--accent-blue)', opacity: 0.5, margin: '0 auto 16px' }} />
          <span style={{ color: 'var(--text-muted)' }}>Loading compliance data...</span>
        </div>
      </div>
    </main>
  )

  return (
    <main style={{ minHeight: '100vh', padding: '40px 0' }}>
      <div className="container">
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
          <a href="/" style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px', display: 'block', textDecoration: 'none' }}>
            ← Back to Dashboard
          </a>
          <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>
            <span style={{ color: 'var(--accent-blue)' }}>EU AI Act</span> Compliance
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '32px' }}>
            SHA-256 audit chain for Articles 12, 13, 14. Enforcement date: August 2, 2026.
          </p>
        </motion.div>

        {/* Audit Trail Summary */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '32px' }}>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="glass-card" style={{ padding: '24px' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>Audit Records</div>
            <div style={{ fontSize: '32px', fontWeight: 800, color: 'var(--accent-blue)' }}>{auditTrail?.total_records || 0}</div>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
            className="glass-card" style={{ padding: '24px' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>Chain Integrity</div>
            <div style={{ fontSize: '32px', fontWeight: 800, color: auditTrail?.chain_valid ? 'var(--accent-green)' : 'var(--accent-red)' }}>
              {auditTrail?.chain_valid ? 'VALID' : 'INVALID'}
            </div>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
            className="glass-card" style={{ padding: '24px' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>Articles Covered</div>
            <div style={{ fontSize: '32px', fontWeight: 800, color: 'var(--accent-purple)' }}>12, 13, 14</div>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}
            className="glass-card" style={{ padding: '24px', cursor: 'pointer' }} onClick={runPiiScan}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>PII Scanner</div>
            <div style={{ fontSize: '16px', fontWeight: 700, color: scanning ? 'var(--accent-amber)' : 'var(--accent-cyan)' }}>
              {scanning ? 'Scanning...' : 'Run PII Scan'}
            </div>
          </motion.div>
        </div>

        {/* PII Scan Result */}
        {piiResult && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            className="glass-card" style={{ padding: '24px', marginBottom: '32px', border: piiResult.status === 'violations_found' ? '1px solid rgba(244, 63, 94, 0.3)' : '1px solid rgba(16, 185, 129, 0.3)' }}>
            <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>
              PII Scan Results — {piiResult.dataset_urn.split(',')[1]?.split(')')[0] || 'Unknown'}
            </h3>
            {piiResult.status === 'violations_found' ? (
              <div>
                <div style={{ display: 'flex', gap: '16px', marginBottom: '12px' }}>
                  <span className="badge badge-red">{piiResult.violations} violations</span>
                  <span className="badge badge-amber">{piiResult.severity}</span>
                  {piiResult.regulations?.map(r => <span key={r} className="badge badge-blue">{r}</span>)}
                </div>
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                  Affected columns: {piiResult.affected_columns?.join(', ')}
                </div>
              </div>
            ) : (
              <div style={{ fontSize: '13px', color: 'var(--accent-green)' }}>No PII violations detected.</div>
            )}
          </motion.div>
        )}

        {/* Audit Records Table */}
        <div className="glass-card" style={{ padding: '24px', marginBottom: '32px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '16px', color: 'var(--text-secondary)' }}>
            SHA-256 Audit Chain
          </h3>
          {records.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No audit records yet. Run an investigation to generate compliance artifacts.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {records.map((record, i) => (
                <motion.div
                  key={record.record_id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  onClick={() => setSelectedRecord(selectedRecord?.record_id === record.record_id ? null : record)}
                  style={{
                    padding: '14px 18px', borderRadius: '10px',
                    background: selectedRecord?.record_id === record.record_id ? 'rgba(59, 130, 246, 0.08)' : 'rgba(255,255,255,0.02)',
                    border: selectedRecord?.record_id === record.record_id ? '1px solid rgba(59, 130, 246, 0.25)' : '1px solid var(--border-subtle)',
                    cursor: 'pointer', transition: 'all 0.15s',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="badge badge-blue">Article {record.article}</span>
                      <span style={{ fontSize: '13px', fontWeight: 600, color: '#fff' }}>{record.decision_type}</span>
                    </div>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                      {record.hash_sha256.slice(0, 12)}...
                    </span>
                  </div>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>{record.output_summary}</p>
                  <div style={{ display: 'flex', gap: '12px', fontSize: '11px', color: 'var(--text-muted)' }}>
                    <span>Confidence: {(record.confidence * 100).toFixed(0)}%</span>
                    <span>Human Override: {record.human_override ? 'Yes' : 'No'}</span>
                    <span>{new Date(record.timestamp).toLocaleString()}</span>
                  </div>

                  {/* Expanded detail */}
                  {selectedRecord?.record_id === record.record_id && (
                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
                      style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
                      <div style={{ fontSize: '12px', marginBottom: '8px' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Input: </span>
                        <span style={{ color: 'var(--text-secondary)' }}>{record.input_summary}</span>
                      </div>
                      <div style={{ fontSize: '12px', marginBottom: '8px' }}>
                        <span style={{ color: 'var(--text-muted)' }}>System: </span>
                        <span style={{ color: 'var(--text-secondary)' }}>{record.system_name}</span>
                      </div>
                      {record.reasoning_chain.length > 0 && (
                        <div style={{ fontSize: '12px', marginBottom: '8px' }}>
                          <span style={{ color: 'var(--text-muted)' }}>Reasoning Chain:</span>
                          <ul style={{ marginTop: '4px', paddingLeft: '16px' }}>
                            {record.reasoning_chain.map((step, j) => (
                              <li key={j} style={{ color: 'var(--text-secondary)', marginBottom: '2px' }}>{step}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      <div style={{ fontSize: '11px', fontFamily: 'monospace', color: 'var(--text-muted)', wordBreak: 'break-all' }}>
                        SHA-256: {record.hash_sha256}
                      </div>
                      {record.previous_hash && (
                        <div style={{ fontSize: '11px', fontFamily: 'monospace', color: 'var(--text-muted)', wordBreak: 'break-all', marginTop: '2px' }}>
                          Prev: {record.previous_hash}
                        </div>
                      )}
                    </motion.div>
                  )}
                </motion.div>
              ))}
            </div>
          )}
        </div>

        <footer style={{ marginTop: '40px', textAlign: 'center', fontSize: '12px', color: 'var(--text-muted)' }}>
          EU AI Act compliance audit chain — Articles 12 (Record-Keeping), 13 (Transparency), 14 (Human Oversight)
        </footer>
      </div>
    </main>
  )
}
