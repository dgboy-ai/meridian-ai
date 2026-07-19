'use client'

import { motion } from 'framer-motion'

const tools = [
  { name: 'MCP search', purpose: 'Find production assets', type: 'read' },
  { name: 'MCP get_lineage', purpose: 'Upstream/downstream traversal', type: 'read' },
  { name: 'MCP list_schema_fields', purpose: 'Column-level metadata', type: 'read' },
  { name: 'MCP search_documents', purpose: 'Find past playbooks', type: 'read' },
  { name: 'MCP save_document', purpose: 'Persist root cause reports', type: 'write' },
  { name: 'GraphQL addStructuredProperties', purpose: 'AI Knowledge panel', type: 'write' },
  { name: 'GraphQL raise_incident', purpose: 'Create incidents', type: 'write' },
  { name: 'GraphQL batch_add_tags', purpose: 'Tag affected assets', type: 'write' },
]

export default function Integrations() {
  return (
    <section id="integrations" style={{
      position: 'relative',
      padding: '120px 32px',
      background: 'linear-gradient(180deg, transparent 0%, rgba(20, 8, 45, 0.2) 50%, transparent 100%)',
    }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '64px' }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '100px',
              background: 'rgba(139, 92, 246, 0.08)',
              border: '1px solid rgba(139, 92, 246, 0.15)',
              marginBottom: '24px',
            }}
          >
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'rgba(255, 255, 255, 0.6)' }}>
              DataHub Integration
            </span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            style={{
              fontSize: 'clamp(28px, 3.5vw, 40px)',
              fontWeight: 800,
              lineHeight: 1.15,
              letterSpacing: '-0.03em',
              color: '#fff',
              maxWidth: '560px',
              margin: '0 auto 16px',
            }}
          >
            12 DataHub capabilities{' '}
            <span style={{
              background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}>
              end-to-end
            </span>
          </motion.h2>
        </div>

        {/* Tools grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '12px',
        }}>
          {tools.map((tool, i) => (
            <motion.div
              key={tool.name}
              initial={{ opacity: 0, y: 15 }}
              whileInView={{ opacity: 1, y: 0 }}
              whileHover={{ y: -3, scale: 1.02, borderColor: 'rgba(139, 92, 246, 0.35)' }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.06, duration: 0.4 }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '14px',
                padding: '18px 20px',
                borderRadius: '12px',
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid rgba(255, 255, 255, 0.05)',
              }}
            >
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: tool.type === 'write' ? '#10b981' : '#6366f1',
                boxShadow: `0 0 8px ${tool.type === 'write' ? '#10b981' : '#6366f1'}`,
                flexShrink: 0,
              }} />
              <div>
                <div style={{
                  fontSize: '13px',
                  fontFamily: 'monospace',
                  fontWeight: 600,
                  color: '#fff',
                }}>
                  {tool.name}
                </div>
                <div style={{
                  fontSize: '12px',
                  color: 'rgba(255, 255, 255, 0.4)',
                  marginTop: '2px',
                }}>
                  {tool.purpose}
                </div>
              </div>
              <div style={{
                marginLeft: 'auto',
                padding: '2px 8px',
                borderRadius: '4px',
                background: tool.type === 'write' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(99, 102, 241, 0.1)',
                color: tool.type === 'write' ? '#10b981' : '#6366f1',
                fontSize: '10px',
                fontWeight: 600,
                flexShrink: 0,
              }}>
                {tool.type === 'write' ? 'WRITE' : 'READ'}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
