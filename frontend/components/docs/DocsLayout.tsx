'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { usePathname } from 'next/navigation'
import Navbar from '../landing/Navbar'

const sections = [
  {
    title: 'Getting Started',
    items: [
      { label: 'Overview', href: '/docs', icon: '◈' },
      { label: 'Quick Start', href: '/docs/getting-started', icon: '→' },
      { label: 'Architecture', href: '/docs/architecture', icon: '◆' },
    ],
  },
  {
    title: 'Core',
    items: [
      { label: 'Features', href: '/docs/features', icon: '◇' },
      { label: 'Security & Compliance', href: '/docs/security', icon: '◆' },
      { label: 'API Reference', href: '/docs/api', icon: '→' },
    ],
  },
  {
    title: 'Resources',
    items: [
      { label: 'For Judges', href: '/docs/judges', icon: '★' },
    ],
  },
]

export default function DocsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    setMobileOpen(false)
  }, [pathname])

  const isActive = (href: string) => {
    if (href === '/docs') return pathname === '/docs'
    return pathname.startsWith(href)
  }

  return (
    <>
    <Navbar />
    <div style={{ display: 'flex', minHeight: '100vh', paddingTop: '72px' }}>
      {/* Background particles */}
      <div style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        pointerEvents: 'none',
        overflow: 'hidden',
      }}>
        {/* Deep aurora gradients */}
        <div style={{
          position: 'absolute',
          top: '-20%',
          left: '-10%',
          width: '70vw',
          height: '70vw',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(139, 92, 246, 0.08) 0%, transparent 55%)',
          filter: 'blur(80px)',
        }} />
        <div style={{
          position: 'absolute',
          bottom: '-10%',
          right: '-5%',
          width: '60vw',
          height: '60vw',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(99, 102, 241, 0.06) 0%, transparent 55%)',
          filter: 'blur(80px)',
        }} />
        <div style={{
          position: 'absolute',
          top: '30%',
          left: '40%',
          width: '50vw',
          height: '50vw',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(6, 182, 212, 0.04) 0%, transparent 50%)',
          filter: 'blur(70px)',
        }} />
        {/* Grid overlay */}
        <div style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'linear-gradient(rgba(139,92,246,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(139,92,246,0.03) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
          maskImage: 'radial-gradient(ellipse at 50% 30%, black 10%, transparent 60%)',
          WebkitMaskImage: 'radial-gradient(ellipse at 50% 30%, black 10%, transparent 60%)',
        }} />
      </div>

      {/* Sidebar - Desktop */}
      <aside
        className="docs-sidebar"
        style={{
          position: 'fixed',
          top: '72px',
          left: 0,
          bottom: 0,
          width: '280px',
          background: 'rgba(6, 4, 15, 0.6)',
          backdropFilter: 'blur(24px)',
          borderRight: '1px solid rgba(255, 255, 255, 0.04)',
          padding: '32px 0',
          overflowY: 'auto',
          zIndex: 50,
        }}
      >
        {/* Logo area */}
        <div style={{ padding: '0 24px', marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <div style={{
              width: '28px',
              height: '28px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
            </div>
            <span style={{ fontSize: '15px', fontWeight: 700, color: '#fff' }}>Meridian AI</span>
          </div>
          <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.35)', letterSpacing: '0.05em' }}>Documentation</span>
        </div>

        {/* Nav sections */}
        {sections.map((section) => (
          <div key={section.title} style={{ marginBottom: '24px' }}>
            <div style={{
              padding: '0 24px',
              marginBottom: '8px',
              fontSize: '10px',
              fontWeight: 700,
              color: 'rgba(255,255,255,0.25)',
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
            }}>
              {section.title}
            </div>
            {section.items.map((item) => {
              const active = isActive(item.href)
              return (
                <a
                  key={item.href}
                  href={item.href}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '10px 24px',
                    fontSize: '13px',
                    fontWeight: active ? 600 : 500,
                    color: active ? '#fff' : 'rgba(255,255,255,0.5)',
                    textDecoration: 'none',
                    position: 'relative',
                    transition: 'all 0.2s',
                    background: active ? 'rgba(139, 92, 246, 0.08)' : 'transparent',
                    borderRight: active ? '2px solid #8b5cf6' : '2px solid transparent',
                  }}
                  onMouseEnter={e => {
                    if (!active) {
                      e.currentTarget.style.color = 'rgba(255,255,255,0.8)'
                      e.currentTarget.style.background = 'rgba(255,255,255,0.02)'
                    }
                  }}
                  onMouseLeave={e => {
                    if (!active) {
                      e.currentTarget.style.color = 'rgba(255,255,255,0.5)'
                      e.currentTarget.style.background = 'transparent'
                    }
                  }}
                >
                  <span style={{ fontSize: '8px', opacity: active ? 0.8 : 0.3 }}>{item.icon}</span>
                  {item.label}
                </a>
              )
            })}
          </div>
        ))}

        {/* Bottom glow accent */}
        <div style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: '120px',
          background: 'linear-gradient(to top, rgba(139, 92, 246, 0.03), transparent)',
          pointerEvents: 'none',
        }} />
      </aside>

      {/* Mobile sidebar toggle */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        style={{
          display: 'none',
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          zIndex: 200,
          width: '48px',
          height: '48px',
          borderRadius: '14px',
          background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
          border: 'none',
          color: '#fff',
          cursor: 'pointer',
          boxShadow: '0 8px 32px rgba(139, 92, 246, 0.4)',
          alignItems: 'center',
          justifyContent: 'center',
        }}
        className="docs-mobile-toggle"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          {mobileOpen ? (
            <>
              <path d="M18 6 6 18" />
              <path d="m6 6 12 12" />
            </>
          ) : (
            <>
              <path d="M4 8h16" />
              <path d="M4 16h16" />
            </>
          )}
        </svg>
      </button>

      {/* Mobile sidebar overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileOpen(false)}
              style={{
                position: 'fixed',
                inset: 0,
                background: 'rgba(6, 4, 15, 0.8)',
                backdropFilter: 'blur(8px)',
                zIndex: 150,
              }}
            />
            <motion.div
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              style={{
                position: 'fixed',
                top: 0,
                left: 0,
                bottom: 0,
                width: '280px',
                background: 'rgba(10, 6, 22, 0.98)',
                backdropFilter: 'blur(24px)',
                borderRight: '1px solid rgba(255,255,255,0.06)',
                padding: '80px 0 32px',
                zIndex: 160,
                overflowY: 'auto',
              }}
            >
              {sections.map((section) => (
                <div key={section.title} style={{ marginBottom: '24px' }}>
                  <div style={{
                    padding: '0 24px',
                    marginBottom: '8px',
                    fontSize: '10px',
                    fontWeight: 700,
                    color: 'rgba(255,255,255,0.25)',
                    letterSpacing: '0.12em',
                    textTransform: 'uppercase',
                  }}>
                    {section.title}
                  </div>
                  {section.items.map((item) => {
                    const active = isActive(item.href)
                    return (
                      <a
                        key={item.href}
                        href={item.href}
                        onClick={() => setMobileOpen(false)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '10px',
                          padding: '12px 24px',
                          fontSize: '14px',
                          fontWeight: active ? 600 : 500,
                          color: active ? '#fff' : 'rgba(255,255,255,0.6)',
                          textDecoration: 'none',
                          background: active ? 'rgba(139, 92, 246, 0.1)' : 'transparent',
                        }}
                      >
                        <span style={{ fontSize: '8px', opacity: 0.4 }}>{item.icon}</span>
                        {item.label}
                      </a>
                    )
                  })}
                </div>
              ))}
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Main content */}
      <main style={{
        flex: 1,
        marginLeft: '280px',
        padding: '48px 64px',
        maxWidth: '900px',
        position: 'relative',
        zIndex: 1,
      }}
        className="docs-main"
      >
        {children}
      </main>

      <style>{`
        @media (max-width: 900px) {
          .docs-sidebar { display: none !important; }
          .docs-main { margin-left: 0 !important; padding: 32px 24px !important; }
          .docs-mobile-toggle { display: flex !important; }
        }
      `}</style>
    </div>
    </>
  )
}
