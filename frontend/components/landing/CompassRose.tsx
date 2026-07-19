'use client'

import { motion } from 'framer-motion'

export default function CompassRose() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 1, delay: 1.5 }}
      style={{
        position: 'absolute',
        bottom: '80px',
        right: '40px',
        width: '60px',
        height: '60px',
        zIndex: 6,
      }}
    >
      <svg viewBox="0 0 60 60" width="60" height="60">
        {/* Outer ring */}
        <circle cx="30" cy="30" r="28" fill="none" stroke="rgba(139, 92, 246, 0.35)" strokeWidth="1" />
        <circle cx="30" cy="30" r="24" fill="none" stroke="rgba(139, 92, 246, 0.2)" strokeWidth="0.7" />

        {/* Cardinal directions */}
        {/* N */}
        <line x1="30" y1="6" x2="30" y2="14" stroke="rgba(139, 92, 246, 0.7)" strokeWidth="2" />
        <text x="30" y="5" textAnchor="middle" fill="rgba(139, 92, 246, 0.8)" fontSize="7" fontWeight="700">N</text>

        {/* S */}
        <line x1="30" y1="46" x2="30" y2="54" stroke="rgba(139, 92, 246, 0.4)" strokeWidth="1.2" />
        <text x="30" y="58" textAnchor="middle" fill="rgba(139, 92, 246, 0.5)" fontSize="7" fontWeight="700">S</text>

        {/* E */}
        <line x1="46" y1="30" x2="54" y2="30" stroke="rgba(139, 92, 246, 0.4)" strokeWidth="1.2" />
        <text x="58" y="32" textAnchor="middle" fill="rgba(139, 92, 246, 0.5)" fontSize="7" fontWeight="700">E</text>

        {/* W */}
        <line x1="6" y1="30" x2="14" y2="30" stroke="rgba(139, 92, 246, 0.4)" strokeWidth="1.2" />
        <text x="2" y="32" textAnchor="middle" fill="rgba(139, 92, 246, 0.4)" fontSize="6" fontWeight="700">W</text>

        {/* Needle */}
        <motion.g
          animate={{ rotate: [0, 5, -3, 0] }}
          transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
          style={{ transformOrigin: '30px 30px' }}
        >
          {/* North needle (bright) */}
          <polygon points="30,10 27,30 33,30" fill="rgba(139, 92, 246, 0.8)" />
          {/* South needle (dim) */}
          <polygon points="30,50 27,30 33,30" fill="rgba(139, 92, 246, 0.3)" />
        </motion.g>

        {/* Center dot */}
        <circle cx="30" cy="30" r="3" fill="rgba(139, 92, 246, 1)" />
        <circle cx="30" cy="30" r="5" fill="none" stroke="rgba(139, 92, 246, 0.4)" strokeWidth="0.8" />

        {/* Tick marks */}
        {Array.from({ length: 36 }).map((_, i) => {
          const angle = (i * 10 * Math.PI) / 180
          const isMajor = i % 9 === 0
          const innerR = isMajor ? 21 : 24
          const outerR = 27
          return (
            <line
              key={i}
              x1={30 + Math.sin(angle) * innerR}
              y1={30 - Math.cos(angle) * innerR}
              x2={30 + Math.sin(angle) * outerR}
              y2={30 - Math.cos(angle) * outerR}
              stroke={`rgba(139, 92, 246, ${isMajor ? 0.6 : 0.25})`}
              strokeWidth={isMajor ? 1.2 : 0.7}
            />
          )
        })}
      </svg>
    </motion.div>
  )
}
