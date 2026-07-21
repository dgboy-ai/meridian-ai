'use client'

import { useEffect, useState, useRef } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import FloatingCubes from './FloatingCubes'
import MeridianGlobe from './MeridianGlobe'
import CompassRose from './CompassRose'
import InvestigateButton from '../InvestigateButton'

const typewriterWords = [
  { text: 'Schema Drift', color: '#f43f5e' },
  { text: 'Data Leakage', color: '#ec4899' },
  { text: 'Feature Skew', color: '#a855f7' },
  { text: 'Model Decay', color: '#6366f1' },
  { text: 'Pipeline Failure', color: '#06b6d4' },
]

function useCountUp(target: number, duration: number = 2000, delay: number = 0) {
  const [count, setCount] = useState(0)
  useEffect(() => {
    const t = setTimeout(() => {
      const start = Date.now()
      const tick = () => {
        const p = Math.min((Date.now() - start) / duration, 1)
        setCount(Math.round((1 - Math.pow(1 - p, 3)) * target))
        if (p < 1) requestAnimationFrame(tick)
      }
      requestAnimationFrame(tick)
    }, delay)
    return () => clearTimeout(t)
  }, [target, duration, delay])
  return count
}

function TypewriterText() {
  const [index, setIndex] = useState(0)
  const [text, setText] = useState('')
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    const word = typewriterWords[index].text
    const t = setTimeout(() => {
      if (!deleting) {
        setText(word.slice(0, text.length + 1))
        if (text.length + 1 === word.length) setTimeout(() => setDeleting(true), 2800)
      } else {
        setText(word.slice(0, text.length - 1))
        if (text.length === 1) { setDeleting(false); setIndex(i => (i + 1) % typewriterWords.length) }
      }
    }, deleting ? 35 : 70)
    return () => clearTimeout(t)
  }, [text, deleting, index])

  const c = typewriterWords[index].color
  return (
    <span style={{ display: 'inline-flex', alignItems: 'baseline', minWidth: '220px' }}>
      <span style={{ color: c, fontWeight: 700, textShadow: `0 0 25px ${c}50` }}>
        {text || '\u00A0'}
      </span>
      <span style={{
        display: 'inline-block', width: '3px', height: '0.8em', marginLeft: '2px',
        background: c, verticalAlign: 'text-bottom',
        animation: 'pulse-glow 1s ease-in-out infinite',
      }} />
    </span>
  )
}

export default function Hero() {
  const ref = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end start'] })
  const y = useTransform(scrollYProgress, [0, 1], [0, 120])
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0])
  const scale = useTransform(scrollYProgress, [0, 0.5], [1, 0.96])
  const workers = useCountUp(18, 1500, 1200)
  const tools = useCountUp(15, 1500, 1400)

  return (
    <section ref={ref} id="hero" style={{ position: 'relative', minHeight: '100vh', display: 'flex', alignItems: 'center', padding: '100px 32px 60px' }}>

      {/* ── Aurora BG ── */}
      <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 25% 40%, rgba(60,20,120,0.95) 0%, rgba(15,5,35,0.9) 40%, rgba(6,4,13,1) 70%)' }} />
        <motion.div animate={{ x: ['-15%','15%','-8%','-15%'], y: ['-8%','8%','-5%','-8%'], scale: [1,1.25,1.1,1], opacity: [0.7,1,0.8,0.7] }} transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut' }} style={{ position: 'absolute', top: '-30%', left: '0%', width: '80vw', height: '90vh', borderRadius: '40% 60% 50% 50% / 50% 40% 60% 50%', background: 'radial-gradient(ellipse, rgba(139,92,246,0.5) 0%, rgba(109,40,217,0.25) 30%, transparent 60%)', filter: 'blur(40px)' }} />
        <motion.div animate={{ x: ['8%','-12%','18%','8%'], y: ['5%','-10%','6%','5%'], opacity: [0.5,0.75,0.5,0.5] }} transition={{ duration: 12, repeat: Infinity, ease: 'easeInOut' }} style={{ position: 'absolute', top: '-8%', right: '-5%', width: '60vw', height: '70vh', borderRadius: '50% 40% 60% 40% / 40% 60% 40% 60%', background: 'radial-gradient(ellipse, rgba(244,63,94,0.35) 0%, rgba(236,72,153,0.15) 30%, transparent 60%)', filter: 'blur(35px)' }} />
        <motion.div animate={{ x: ['-8%','12%','-5%','-8%'], y: ['6%','-5%','10%','6%'], opacity: [0.3,0.5,0.3,0.3] }} transition={{ duration: 14, repeat: Infinity, ease: 'easeInOut' }} style={{ position: 'absolute', bottom: '-8%', left: '10%', width: '50vw', height: '50vh', borderRadius: '50%', background: 'radial-gradient(ellipse, rgba(6,182,212,0.25) 0%, transparent 50%)', filter: 'blur(40px)' }} />
        <div style={{ position: 'absolute', inset: 0, backgroundImage: 'linear-gradient(rgba(139,92,246,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(139,92,246,0.05) 1px, transparent 1px)', backgroundSize: '50px 50px', maskImage: 'radial-gradient(ellipse at 55% 50%, black 15%, transparent 55%)', WebkitMaskImage: 'radial-gradient(ellipse at 55% 50%, black 15%, transparent 55%)' }} />
        {/* Bottom fade — blends hero into next section */}
        <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: '120px', background: 'linear-gradient(to bottom, transparent, rgba(6,4,13,1))', pointerEvents: 'none' }} />
      </div>

      {/* Scanning line */}
      <motion.div animate={{ y: ['-100vh','100vh'] }} transition={{ duration: 5, repeat: Infinity, ease: 'linear' }} style={{ position: 'absolute', left: 0, right: 0, height: '2px', background: 'linear-gradient(90deg, transparent, rgba(139,92,246,0.8) 50%, transparent)', boxShadow: '0 0 40px rgba(139,92,246,0.6), 0 0 80px rgba(139,92,246,0.3)', pointerEvents: 'none', zIndex: 4 }} />

      {/* Content */}
      <motion.div style={{ y, opacity, scale, width: '100%' }}>
        <div style={{ position: 'relative', zIndex: 6, width: '100%', maxWidth: '1200px', margin: '0 auto', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', alignItems: 'center' }} className="hero-grid">

          {/* Left */}
          <div>
            {/* Badge */}
            <motion.div initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.1 }}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '10px', padding: '7px 18px', borderRadius: '100px', background: 'linear-gradient(135deg, rgba(139,92,246,0.2), rgba(244,63,94,0.12))', border: '1px solid rgba(139,92,246,0.35)', marginBottom: '24px', boxShadow: '0 0 20px rgba(139,92,246,0.15)' }}>
              <motion.span animate={{ scale: [1,1.4,1], opacity: [1,0.4,1] }} transition={{ duration: 2, repeat: Infinity }} style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 10px #10b981' }} />
              <span style={{ fontSize: '12px', fontWeight: 600, color: 'rgba(255,255,255,0.9)', letterSpacing: '0.04em' }}>The Agent Hackathon Submission</span>
            </motion.div>

            {/* Headline — 2 lines max */}
            <div style={{ marginBottom: '16px' }}>
              <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.15 }}>
                <h1 style={{ fontSize: 'clamp(38px, 4.8vw, 68px)', fontWeight: 900, lineHeight: 1.05, letterSpacing: '-0.04em', color: '#fff', margin: 0, marginBottom: '4px' }}>
                  Catch failures at their peak
                </h1>
              </motion.div>
              <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.3 }}>
                <h1 style={{ fontSize: 'clamp(38px, 4.8vw, 68px)', fontWeight: 900, lineHeight: 1.05, letterSpacing: '-0.04em', margin: 0, color: '#fff' }}>
                  before they cost{' '}
                  <span style={{ background: 'linear-gradient(135deg, #f43f5e, #ec4899 25%, #a855f7 50%, #6366f1 75%, #06b6d4)', backgroundSize: '200% auto', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text', animation: 'gradient-flow 3s linear infinite' }}>
                    $45K/day
                  </span>
                </h1>
              </motion.div>
              {/* Typewriter */}
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.45 }} style={{ marginTop: '10px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ fontSize: 'clamp(16px, 1.8vw, 24px)', fontWeight: 700, color: 'rgba(255,255,255,0.35)' }}>Detecting:</span>
                <TypewriterText />
              </motion.div>
            </div>

            {/* Subtitle */}
            <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.55 }} style={{ fontSize: '15px', lineHeight: 1.7, color: 'rgba(255,255,255,0.45)', maxWidth: '440px', marginBottom: '24px' }}>
              18 specialized agents investigate ML incidents in parallel, trace root cause through DataHub lineage, and write knowledge back so every future incident resolves faster.
            </motion.p>

            {/* CTA */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.65 }} style={{ display: 'flex', gap: '14px', marginBottom: '36px' }} className="hero-cta-row">
              <InvestigateButton />
              <motion.a href="/dashboard" whileHover={{ scale: 1.03, y: -2, background: 'rgba(255,255,255,0.08)', borderColor: 'rgba(255,255,255,0.2)' }} whileTap={{ scale: 0.97 }}
                style={{ display: 'inline-flex', alignItems: 'center', padding: '16px 32px', borderRadius: '12px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.85)', fontSize: '15px', fontWeight: 600, textDecoration: 'none', backdropFilter: 'blur(10px)', transition: 'background 0.3s, border-color 0.3s' }}>
                Open Dashboard
              </motion.a>
            </motion.div>

            {/* Stats */}
            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.75 }} style={{ display: 'flex', gap: '36px' }}>
              {[{ v: workers, s: '', l: 'Workers', c: '#8b5cf6' }, { v: 8, s: 'min', l: 'Avg Resolution', c: '#10b981' }, { v: tools, s: '', l: 'DataHub Tools', c: '#6366f1' }].map((st, i) => (
                <motion.div key={i} initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.9 + i * 0.1, duration: 0.4 }} whileHover={{ scale: 1.05, y: -2 }}>
                  <div style={{ fontSize: '34px', fontWeight: 900, color: st.c, letterSpacing: '-0.03em', textShadow: `0 0 25px ${st.c}40`, fontVariantNumeric: 'tabular-nums' }}>{st.v}{st.s}</div>
                  <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.35)', marginTop: '2px', fontWeight: 500 }}>{st.l}</div>
                </motion.div>
              ))}
            </motion.div>
          </div>

          {/* Right: Globe + Cubes */}
          <motion.div initial={{ opacity: 0, scale: 0.7, x: 60 }} animate={{ opacity: 1, scale: 1, x: 0 }} transition={{ duration: 1, delay: 0.2, ease: [0.16,1,0.3,1] }} style={{ position: 'relative', height: '650px' }} className="hero-cubes">
            <div style={{ position: 'absolute', inset: 0, opacity: 0.85 }}><MeridianGlobe /></div>
            <FloatingCubes />
          </motion.div>
        </div>
      </motion.div>

      <CompassRose />

      {/* Scroll cue */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.8 }} style={{ position: 'absolute', bottom: '24px', left: '50%', transform: 'translateX(-50%)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', zIndex: 6 }}>
        <span style={{ fontSize: '9px', color: 'rgba(255,255,255,0.2)', letterSpacing: '0.15em', textTransform: 'uppercase', fontWeight: 600 }}>Scroll</span>
        <motion.div animate={{ y: [0,6,0] }} transition={{ duration: 1.5, repeat: Infinity }} style={{ width: '18px', height: '28px', borderRadius: '9px', border: '1.5px solid rgba(255,255,255,0.12)', display: 'flex', justifyContent: 'center', paddingTop: '5px' }}>
          <motion.div animate={{ opacity: [0.2,0.7,0.2], height: ['3px','8px','3px'] }} transition={{ duration: 1.5, repeat: Infinity }} style={{ width: '2px', borderRadius: '1px', background: 'rgba(139,92,246,0.5)' }} />
        </motion.div>
      </motion.div>
    </section>
  )
}
