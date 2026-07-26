'use client'

import { motion } from 'framer-motion'

const footerLinks = {
  Product: [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Models', href: '/models' },
    { label: 'Playbooks', href: '/playbooks' },
    { label: 'Compliance', href: '/compliance' },
    { label: 'API Docs', href: '/docs/api' },
  ],
  Resources: [
    { label: 'Documentation', href: '/docs' },
    { label: 'Getting Started', href: '/docs/getting-started' },
    { label: 'Architecture', href: '/docs/architecture' },
    { label: 'Security', href: '/docs/security' },
  ],
  Community: [
    { label: 'GitHub', href: 'https://github.com/dgboy-ai/meridian-ai' },
    { label: 'Issues', href: 'https://github.com/dgboy-ai/meridian-ai/issues' },
    { label: 'License (Apache 2.0)', href: 'https://github.com/dgboy-ai/meridian-ai/blob/main/LICENSE' },
  ],
}

const socialLinks = [
  {
    name: 'GitHub',
    href: 'https://github.com/dgboy-ai/meridian-ai',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
      </svg>
    ),
  },
]

export default function Footer() {
  return (
    <footer style={{
      position: 'relative',
      borderTop: '1px solid rgba(255, 255, 255, 0.04)',
      background: 'linear-gradient(180deg, transparent 0%, rgba(10, 6, 22, 0.5) 100%)',
    }}>
      {/* Top gradient line */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: '10%',
        right: '10%',
        height: '1px',
        background: 'linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.2) 30%, rgba(99, 102, 241, 0.3) 50%, rgba(139, 92, 246, 0.2) 70%, transparent)',
      }} />

      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '80px 32px 40px' }}>
        {/* Top section — Logo + Links */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1.5fr repeat(3, 1fr)',
          gap: '48px',
          marginBottom: '64px',
        }}>
          {/* Brand */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2L2 7l10 5 10-5-10-5z" />
                  <path d="M2 17l10 5 10-5" />
                  <path d="M2 12l10 5 10-5" />
                </svg>
              </div>
              <span style={{ fontSize: '16px', fontWeight: 700, color: '#fff' }}>Meridian AI</span>
            </div>
            <p style={{ fontSize: '13px', color: 'rgba(255, 255, 255, 0.4)', lineHeight: 1.7, maxWidth: '280px', marginBottom: '20px' }}>
              AI Reliability Engineer that makes DataHub smarter every time an ML incident occurs.
            </p>
            {/* Social links */}
            <div style={{ display: 'flex', gap: '8px' }}>
              {socialLinks.map(social => (
                <motion.a
                  key={social.name}
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  whileHover={{ scale: 1.1, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '8px',
                    background: 'rgba(255, 255, 255, 0.04)',
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'rgba(255, 255, 255, 0.5)',
                    textDecoration: 'none',
                    transition: 'color 0.2s, background 0.2s, border-color 0.2s',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.color = '#8b5cf6'
                    e.currentTarget.style.background = 'rgba(139, 92, 246, 0.1)'
                    e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.2)'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.color = 'rgba(255, 255, 255, 0.5)'
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)'
                    e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.06)'
                  }}
                >
                  {social.icon}
                </motion.a>
              ))}
            </div>
          </div>

          {/* Link columns */}
          {Object.entries(footerLinks).map(([title, items]) => (
            <div key={title}>
              <h4 style={{
                fontSize: '12px',
                fontWeight: 700,
                color: 'rgba(255, 255, 255, 0.5)',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                marginBottom: '20px',
              }}>
                {title}
              </h4>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {items.map(item => (
                  <li key={item.label}>
                    <motion.a
                      href={item.href}
                      whileHover={{ x: 4 }}
                      style={{
                        fontSize: '13px',
                        color: 'rgba(255, 255, 255, 0.45)',
                        textDecoration: 'none',
                        transition: 'color 0.2s',
                        display: 'inline-block',
                      }}
                      onMouseEnter={e => e.currentTarget.style.color = 'rgba(255, 255, 255, 0.85)'}
                      onMouseLeave={e => e.currentTarget.style.color = 'rgba(255, 255, 255, 0.45)'}
                    >
                      {item.label}
                    </motion.a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Divider */}
        <div style={{
          height: '1px',
          background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.06) 20%, rgba(255, 255, 255, 0.06) 80%, transparent)',
          marginBottom: '24px',
        }} />

        {/* Bottom section */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <a href="https://github.com/dgboy-ai/meridian-ai/blob/main/LICENSE" target="_blank" rel="noopener noreferrer" style={{ fontSize: '12px', color: 'rgba(255, 255, 255, 0.3)', textDecoration: 'none' }}>
              &copy; 2026 Meridian AI. Apache 2.0 License.
            </a>
            <span style={{ fontSize: '11px', color: 'rgba(255, 255, 255, 0.2)' }}>
              Built for the DataHub Agent Hackathon
            </span>
          </div>

          {/* Back to top */}
          <motion.button
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.95 }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              borderRadius: '8px',
              background: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(255, 255, 255, 0.06)',
              color: 'rgba(255, 255, 255, 0.4)',
              fontSize: '12px',
              cursor: 'pointer',
              transition: 'color 0.2s, background 0.2s',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.color = 'rgba(255, 255, 255, 0.8)'
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.06)'
            }}
            onMouseLeave={e => {
              e.currentTarget.style.color = 'rgba(255, 255, 255, 0.4)'
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)'
            }}
          >
            Back to top
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m18 15-6-6-6 6" />
            </svg>
          </motion.button>
        </div>
      </div>
    </footer>
  )
}
