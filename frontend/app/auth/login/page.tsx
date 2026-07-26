'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { apiUrl } from '../../../lib/config'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const res = await fetch(apiUrl('/api/auth/login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      const data = await res.json()

      if (!res.ok) {
        setError(data.error || 'Login failed')
        setLoading(false)
        return
      }

      // Store token in localStorage
      localStorage.setItem('meridian_token', data.access_token)
      localStorage.setItem('meridian_user', JSON.stringify(data.user))

      // Redirect to home
      router.push('/')
    } catch (err) {
      setError('Connection failed. Is the backend running?')
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg-primary)',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '400px',
        padding: '40px',
        background: 'var(--bg-secondary)',
        border: '1px solid rgba(255,255,255,0.06)',
        borderRadius: '12px',
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{
            fontSize: '24px',
            fontWeight: 700,
            color: 'var(--text-primary)',
            fontFamily: 'var(--font-mono)',
            marginBottom: '8px',
          }}>
            MERIDIAN AI
          </div>
          <div style={{
            fontSize: '12px',
            color: 'var(--text-muted)',
            fontFamily: 'monospace',
          }}>
            SECURE OPERATOR CONSOLE
          </div>
        </div>

        {/* Login Form */}
        <form onSubmit={handleLogin}>
          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--text-muted)',
              marginBottom: '6px',
              fontFamily: 'monospace',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}>
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="operator@meridian.ai"
              required
              style={{
                width: '100%',
                padding: '10px 12px',
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '6px',
                color: 'var(--text-primary)',
                fontSize: '14px',
                fontFamily: 'monospace',
                outline: 'none',
                transition: 'border-color 0.2s',
              }}
              onFocus={(e) => e.target.style.borderColor = 'var(--accent-cyan)'}
              onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.08)'}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label style={{
              display: 'block',
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--text-muted)',
              marginBottom: '6px',
              fontFamily: 'monospace',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              required
              style={{
                width: '100%',
                padding: '10px 12px',
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '6px',
                color: 'var(--text-primary)',
                fontSize: '14px',
                fontFamily: 'monospace',
                outline: 'none',
                transition: 'border-color 0.2s',
              }}
              onFocus={(e) => e.target.style.borderColor = 'var(--accent-cyan)'}
              onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.08)'}
            />
          </div>

          {error && (
            <div style={{
              padding: '10px 12px',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.2)',
              borderRadius: '6px',
              color: '#ef4444',
              fontSize: '12px',
              fontFamily: 'monospace',
              marginBottom: '20px',
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '12px',
              background: loading ? 'rgba(139, 92, 246, 0.3)' : 'rgba(139, 92, 246, 0.2)',
              border: '1px solid rgba(139, 92, 246, 0.3)',
              borderRadius: '6px',
              color: 'var(--accent-purple)',
              fontSize: '13px',
              fontWeight: 600,
              fontFamily: 'monospace',
              cursor: loading ? 'not-allowed' : 'pointer',
              textTransform: 'uppercase',
              letterSpacing: '1px',
              transition: 'all 0.2s',
            }}
          >
            {loading ? 'AUTHENTICATING...' : 'LOGIN'}
          </button>
        </form>

        {/* Footer */}
        <div style={{
          marginTop: '24px',
          textAlign: 'center',
          fontSize: '11px',
          color: 'var(--text-muted)',
        }}>
          <a href="/auth/register" style={{
            color: 'var(--accent-cyan)',
            textDecoration: 'none',
          }}>
            Create operator account →
          </a>
        </div>

        {/* Demo credentials */}
        <div style={{
          marginTop: '20px',
          padding: '12px',
          background: 'rgba(255,255,255,0.02)',
          borderRadius: '6px',
          border: '1px solid rgba(255,255,255,0.04)',
        }}>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'monospace', marginBottom: '6px' }}>
            DEMO CREDENTIALS:
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
            admin@meridian.ai / meridian123
          </div>
        </div>
      </div>
    </div>
  )
}
