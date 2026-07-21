'use client'

import { motion } from 'framer-motion'

const tools = [
  { name: 'MCP search', purpose: 'Find production assets', type: 'read' },
  { name: 'MCP get_entities', purpose: 'Fetch entity metadata', type: 'read' },
  { name: 'MCP get_lineage', purpose: 'Upstream/downstream traversal', type: 'read' },
  { name: 'MCP get_lineage_paths', purpose: 'Exact path between entities', type: 'read' },
  { name: 'MCP list_schema_fields', purpose: 'Column-level metadata', type: 'read' },
  { name: 'MCP get_dataset_queries', purpose: 'Real SQL referencing datasets', type: 'read' },
  { name: 'MCP search_documents', purpose: 'Find past playbooks', type: 'read' },
  { name: 'MCP save_document', purpose: 'Persist root cause reports + playbooks', type: 'write' },
  { name: 'GraphQL addStructuredProperties', purpose: 'AI Knowledge panel on entities', type: 'write' },
  { name: 'GraphQL raise_incident', purpose: 'Create incidents programmatically', type: 'write' },
  { name: 'GraphQL batch_add_tags', purpose: 'Tag all affected assets in bulk', type: 'write' },
  { name: 'GraphQL update_incident_status', purpose: 'Close/resolved incidents', type: 'write' },
  { name: 'Actions Framework YAML', purpose: 'Auto-trigger on schema changes', type: 'write' },
  { name: 'propose_lifecycle_stage', purpose: 'Propose DEPRECATED for failing models', type: 'write' },
  { name: 'list_pending_proposals', purpose: 'Check queued governance proposals', type: 'read' },
]

const container = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.04 },
  },
}

const item = {
  hidden: { opacity: 0, y: 15, scale: 0.97 },
  show: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } },
}

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
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'rgba(255, 255, 255, 0.6)' }}>DataHub Integration</span>
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
            15 DataHub capabilities{' '}
            <span style={{ background: 'linear-gradient(135deg, #8b5cf6, #6366f1)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              end-to-end
            </span>
          </motion.h2>
        </div>

        {/* Tools grid */}
        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: '-50px' }}
          style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '10px' }}
        >
          {tools.map((tool) => {
            const isWrite = tool.type === 'write'
            const color = isWrite ? '#10b981' : '#6366f1'
            return (
              <motion.div
                key={tool.name}
                variants={item}
                whileHover={{ y: -3, scale: 1.02 }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px',
                  padding: '16px 18px',
                  borderRadius: '12px',
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid rgba(255, 255, 255, 0.05)',
                  cursor: 'default',
                  transition: 'border-color 0.3s, box-shadow 0.3s',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = `${color}40`
                  e.currentTarget.style.boxShadow = `0 4px 16px ${color}10`
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.05)'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              >
                {/* Animated dot */}
                <motion.div
                  animate={{ scale: [1, 1.3, 1] }}
                  transition={{ duration: 2, repeat: Infinity, delay: Math.random() * 2 }}
                  style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: color,
                    boxShadow: `0 0 8px ${color}`,
                    flexShrink: 0,
                  }}
                />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: '13px', fontFamily: 'monospace', fontWeight: 600, color: '#fff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {tool.name}
                  </div>
                  <div style={{ fontSize: '12px', color: 'rgba(255, 255, 255, 0.4)', marginTop: '2px' }}>
                    {tool.purpose}
                  </div>
                </div>
                <div style={{
                  padding: '3px 10px',
                  borderRadius: '6px',
                  background: isWrite ? 'rgba(16, 185, 129, 0.1)' : 'rgba(99, 102, 241, 0.1)',
                  color: isWrite ? '#10b981' : '#6366f1',
                  fontSize: '10px',
                  fontWeight: 700,
                  letterSpacing: '0.05em',
                  flexShrink: 0,
                }}>
                  {isWrite ? 'WRITE' : 'READ'}
                </div>
              </motion.div>
            )
          })}
        </motion.div>
      </div>
    </section>
  )
}
