'use client'

import { motion } from 'framer-motion'

export function DocH1({ children }: { children: React.ReactNode }) {
  return (
    <motion.h1
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      style={{
        fontSize: 'clamp(32px, 4vw, 44px)',
        fontWeight: 900,
        lineHeight: 1.1,
        letterSpacing: '-0.04em',
        color: '#fff',
        marginBottom: '16px',
      }}
    >
      {children}
    </motion.h1>
  )
}

export function DocH2({ children }: { children: React.ReactNode }) {
  return (
    <motion.h2
      initial={{ opacity: 0, y: 15 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
      style={{
        fontSize: '24px',
        fontWeight: 800,
        lineHeight: 1.2,
        letterSpacing: '-0.03em',
        color: '#fff',
        marginTop: '56px',
        marginBottom: '16px',
        paddingBottom: '12px',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      {children}
    </motion.h2>
  )
}

export function DocH3({ children }: { children: React.ReactNode }) {
  return (
    <h3 style={{
      fontSize: '18px',
      fontWeight: 700,
      color: '#fff',
      marginTop: '32px',
      marginBottom: '12px',
    }}>
      {children}
    </h3>
  )
}

export function DocP({ children }: { children: React.ReactNode }) {
  return (
    <p style={{
      fontSize: '15px',
      lineHeight: 1.75,
      color: 'rgba(255,255,255,0.6)',
      marginBottom: '16px',
    }}>
      {children}
    </p>
  )
}

export function DocBadge({ color = '#8b5cf6', children }: { color?: string; children: React.ReactNode }) {
  return (
    <span style={{
      display: 'inline-block',
      padding: '4px 12px',
      borderRadius: '6px',
      background: `${color}15`,
      color: color,
      fontSize: '12px',
      fontWeight: 700,
      letterSpacing: '0.02em',
      marginBottom: '16px',
    }}>
      {children}
    </span>
  )
}

export function DocCode({ children, inline }: { children: React.ReactNode; inline?: boolean }) {
  if (inline) {
    return (
      <code style={{
        padding: '2px 8px',
        borderRadius: '6px',
        background: 'rgba(139, 92, 246, 0.1)',
        color: '#c4b5fd',
        fontSize: '13px',
        fontFamily: "'SF Mono', 'Cascadia Code', Consolas, monospace",
      }}>
        {children}
      </code>
    )
  }
  return (
    <pre style={{
      padding: '20px 24px',
      borderRadius: '12px',
      background: 'rgba(12, 8, 28, 0.8)',
      border: '1px solid rgba(255,255,255,0.06)',
      overflow: 'auto',
      marginBottom: '20px',
      fontSize: '13px',
      lineHeight: 1.7,
      fontFamily: "'SF Mono', 'Cascadia Code', Consolas, monospace",
      color: 'rgba(255,255,255,0.8)',
    }}>
      <code>{children}</code>
    </pre>
  )
}

export function DocCard({ title, icon, color = '#8b5cf6', children }: {
  title: string
  icon: string
  color?: string
  children: React.ReactNode
}) {
  return (
    <motion.div
      whileHover={{ y: -4, scale: 1.01 }}
      style={{
        padding: '24px',
        borderRadius: '16px',
        background: 'rgba(12, 8, 28, 0.5)',
        border: '1px solid rgba(255,255,255,0.06)',
        marginBottom: '16px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '10px',
          background: `${color}15`,
          border: `1px solid ${color}25`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '16px',
        }}>
          {icon}
        </div>
        <span style={{ fontSize: '15px', fontWeight: 700, color: '#fff' }}>{title}</span>
      </div>
      <div style={{ fontSize: '14px', lineHeight: 1.7, color: 'rgba(255,255,255,0.55)' }}>
        {children}
      </div>
    </motion.div>
  )
}

export function DocInfo({ type = 'info', children }: { type?: 'info' | 'warning' | 'tip'; children: React.ReactNode }) {
  const colors = {
    info: { bg: 'rgba(99, 102, 241, 0.08)', border: 'rgba(99, 102, 241, 0.2)', icon: '◈', label: 'Info' },
    warning: { bg: 'rgba(245, 158, 11, 0.08)', border: 'rgba(245, 158, 11, 0.2)', icon: '⚠', label: 'Warning' },
    tip: { bg: 'rgba(16, 185, 129, 0.08)', border: 'rgba(16, 185, 129, 0.2)', icon: '◆', label: 'Tip' },
  }
  const c = colors[type]
  return (
    <div style={{
      padding: '16px 20px',
      borderRadius: '12px',
      background: c.bg,
      border: `1px solid ${c.border}`,
      marginBottom: '20px',
      fontSize: '14px',
      lineHeight: 1.7,
      color: 'rgba(255,255,255,0.7)',
    }}>
      <span style={{ fontWeight: 700, marginRight: '8px' }}>{c.icon} {c.label}:</span>
      {children}
    </div>
  )
}

export function DocTable({ headers, rows }: { headers: string[]; rows: string[][] }) {
  return (
    <div style={{
      borderRadius: '12px',
      border: '1px solid rgba(255,255,255,0.06)',
      overflow: 'hidden',
      marginBottom: '24px',
    }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr style={{ background: 'rgba(139, 92, 246, 0.06)' }}>
            {headers.map((h, i) => (
              <th key={i} style={{
                padding: '12px 16px',
                textAlign: 'left',
                fontWeight: 700,
                color: 'rgba(255,255,255,0.7)',
                borderBottom: '1px solid rgba(255,255,255,0.06)',
                fontSize: '11px',
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
              }}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} style={{ background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)' }}>
              {row.map((cell, j) => (
                <td key={j} style={{
                  padding: '12px 16px',
                  color: 'rgba(255,255,255,0.6)',
                  borderBottom: '1px solid rgba(255,255,255,0.04)',
                }}>
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function DocDivider() {
  return (
    <div style={{
      height: '1px',
      background: 'linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.2) 50%, transparent)',
      margin: '40px 0',
    }} />
  )
}
