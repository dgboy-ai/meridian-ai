'use client'

import { useEffect, useRef, useState } from 'react'

interface Node3D {
  id: string
  label: string
  type: string
  baseX: number
  baseY: number
  baseZ: number
  x: number
  y: number
  z: number
  color: string
  size: number
}

interface Link3D {
  source: string
  target: string
}

interface Particle {
  sourceNode: Node3D
  targetNode: Node3D
  progress: number
  speed: number
  color: string
}

interface StarDust {
  x: number
  y: number
  z: number
  size: number
  speedY: number
}

interface BurstParticle {
  x: number
  y: number
  vx: number
  vy: number
  color: string
  life: number
  maxLife: number
  size: number
}

interface NodeData {
  name: string
  type: string
  status?: string
  health_score?: number
}

interface LineageGraph3DProps {
  activePhase: 'idle' | 'drift' | 'diagnose' | 'remediate'
  sourceNode?: NodeData | null
  affectedNodes?: NodeData[]
}

const NODE_COLORS: Record<string, string> = {
  dataset: '#6366f1',
  mlModel: '#a855f7',
  features: '#6366f1',
  deployment: '#a855f7',
  datahub: '#ec4899',
}

const STATUS_COLORS: Record<string, string> = {
  critical: '#f43f5e',
  warning: '#f59e0b',
  healthy: '#10b981',
}

export default function LineageGraph3D({ activePhase, sourceNode, affectedNodes }: LineageGraph3DProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const stateRef = useRef({ activePhase, rotation: 0, mouseX: 0, mouseY: 0 })
  const [dims, setDims] = useState({ width: 1200, height: 800 })

  // Synchronize window size using standard React state to prevent scaling distortion
  useEffect(() => {
    setDims({ width: window.innerWidth, height: window.innerHeight })
    const handleResize = () => {
      setDims({ width: window.innerWidth, height: window.innerHeight })
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  useEffect(() => {
    stateRef.current.activePhase = activePhase
  }, [activePhase])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationFrameId: number
    
    const handleMouseMove = (e: MouseEvent) => {
      stateRef.current.mouseX = e.clientX - window.innerWidth / 2
      stateRef.current.mouseY = e.clientY - window.innerHeight / 2
    }
    window.addEventListener('mousemove', handleMouseMove)

    // Setup Star Dust (ambient space particles)
    const starDust: StarDust[] = []
    for (let i = 0; i < 70; i++) {
      starDust.push({
        x: (Math.random() - 0.5) * 800,
        y: (Math.random() - 0.5) * 600,
        z: Math.random() * 400 - 200,
        size: 0.5 + Math.random() * 1.2,
        speedY: -(0.06 + Math.random() * 0.12)
      })
    }

    // Build nodes from props or fall back to defaults
    const hasRealData = sourceNode && affectedNodes && affectedNodes.length > 0
    const sourceName = hasRealData ? sourceNode!.name : 'raw_events'
    const sourceType = hasRealData ? sourceNode!.type : 'dataset'
    const sourceStatus = hasRealData ? (sourceNode!.status || 'critical') : 'critical'

    const nodePositions = [
      { baseX: -200, baseY: -40, baseZ: 30 },
      { baseX: -60, baseY: -10, baseZ: -30 },
      { baseX: 60, baseY: 30, baseZ: 25 },
      { baseX: 200, baseY: 60, baseZ: -35 },
      { baseX: 0, baseY: 110, baseZ: 40 },
    ]

    const nodes: Node3D[] = [
      { id: 'source', label: `${sourceName} (${sourceType})`, type: sourceType, ...nodePositions[0], x: 0, y: 0, z: 0, color: STATUS_COLORS[sourceStatus] || NODE_COLORS[sourceType] || '#6366f1', size: 6 },
    ]

    const affected = hasRealData ? affectedNodes! : [
      { name: 'feature_pipeline', type: 'dataset', status: 'warning' },
      { name: 'churn_model_v3', type: 'mlModel', status: 'critical' },
      { name: 'ltv_model_v2', type: 'mlModel', status: 'critical' },
    ]

    affected.forEach((a, i) => {
      const pos = nodePositions[Math.min(i + 1, nodePositions.length - 1)]
      const statusColor = STATUS_COLORS[a.status || 'healthy'] || NODE_COLORS[a.type] || '#a855f7'
      nodes.push({
        id: `affected-${i}`,
        label: `${a.name} (${a.type})`,
        type: a.type,
        ...pos,
        x: 0, y: 0, z: 0,
        color: statusColor,
        size: a.type === 'mlModel' ? 7 : 5,
      })
    })

    // Add DataHub node
    nodes.push({ id: 'datahub', label: 'DataHub GMS', type: 'datahub', ...nodePositions[4], x: 0, y: 0, z: 0, color: '#ec4899', size: 8 })

    const links: Link3D[] = nodes.slice(1, -1).map((n) => ({ source: 'source', target: n.id }))
    links.push({ source: 'datahub', target: 'source' })
    if (nodes.length > 2) links.push({ source: 'datahub', target: nodes[1].id })

    let particles: Particle[] = []
    let burstParticles: BurstParticle[] = []
    let lastPhase = activePhase

    // Extremely constrained projection scales to ensure it runs strictly in background
    const project = (x: number, y: number, z: number) => {
      const fov = 600
      const clampedZ = Math.max(-100, z)
      const scale = Math.min(1.1, fov / (fov + clampedZ))
      return {
        x: window.innerWidth / 2 + x * scale,
        y: window.innerHeight / 2 + y * scale,
        scale
      }
    }

    const triggerBurstAtNode = (nodeId: string, color: string, count = 20) => {
      const node = nodes.find(n => n.id === nodeId)
      if (!node) return
      const projected = project(node.x, node.y, node.z)
      for (let i = 0; i < count; i++) {
        const angle = Math.random() * Math.PI * 2
        const speed = 1 + Math.random() * 2
        burstParticles.push({
          x: projected.x,
          y: projected.y,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          color,
          life: 0,
          maxLife: 20 + Math.random() * 15,
          size: 1 + Math.random() * 1
        })
      }
    }

    const draw = () => {
      ctx.clearRect(0, 0, window.innerWidth, window.innerHeight)

      const phase = stateRef.current.activePhase

      if (phase !== lastPhase) {
        if (phase === 'drift') {
          triggerBurstAtNode('source', '#f43f5e', 18)
          nodes.filter(n => n.id.startsWith('affected')).forEach(n => triggerBurstAtNode(n.id, '#f43f5e', 12))
        } else if (phase === 'remediate') {
          triggerBurstAtNode('datahub', '#ec4899', 12)
          nodes.filter(n => n.id.startsWith('affected')).forEach(n => triggerBurstAtNode(n.id, '#10b981', 18))
        }
        lastPhase = phase
      }

      stateRef.current.rotation += 0.0012
      const cos = Math.cos(stateRef.current.rotation)
      const sin = Math.sin(stateRef.current.rotation)

      // 1. Draw Rotating Background Meridians Grid lines
      ctx.lineWidth = 1
      ctx.strokeStyle = 'rgba(168, 85, 247, 0.02)'
      for (let i = -3; i <= 3; i++) {
        const theta = (i * Math.PI) / 8
        ctx.beginPath()
        for (let angle = 0; angle <= Math.PI * 2; angle += 0.1) {
          const sx = 280 * Math.sin(angle) * Math.cos(theta)
          const sz = 280 * Math.cos(angle) * Math.cos(theta)
          const sy = 280 * Math.sin(theta)

          const rx = sx * cos - sz * sin
          const rz = sx * sin + sz * cos
          const proj = project(rx, sy, rz)
          
          if (angle === 0) ctx.moveTo(proj.x, proj.y)
          else ctx.lineTo(proj.x, proj.y)
        }
        ctx.stroke()
      }

      // 2. Draw Star Dust
      starDust.forEach(star => {
        star.y += star.speedY
        if (star.y < -300) {
          star.y = 300
          star.x = (Math.random() - 0.5) * 800
        }
        const proj = project(star.x, star.y, star.z)
        ctx.beginPath()
        ctx.arc(proj.x, proj.y, star.size * proj.scale, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(168, 85, 247, ${0.1 * proj.scale})`
        ctx.fill()
      })

      // 3. Update Node coordinates
      nodes.forEach((node) => {
        let rx = node.baseX * cos - node.baseZ * sin
        let rz = node.baseX * sin + node.baseZ * cos
        let ry = node.baseY

        const dx = rx - stateRef.current.mouseX * 0.3
        const dy = ry - stateRef.current.mouseY * 0.3
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < 180) {
          const force = (180 - dist) / 180
          rx += (dx / dist) * force * 15
          ry += (dy / dist) * force * 15
        }

        node.x = rx
        node.y = ry
        node.z = rz

        if (phase === 'drift') {
          node.color = (node.id === 'source' || node.id.startsWith('affected')) ? '#f43f5e' : '#f59e0b'
        } else if (phase === 'diagnose') {
          node.color = (node.id === 'source' || node.id.startsWith('affected')) ? '#f43f5e' : '#6366f1'
        } else if (phase === 'remediate') {
          node.color = '#10b981'
        } else {
          node.color = node.id === 'datahub' ? '#ec4899' : node.id === 'source' ? '#6366f1' : '#a855f7'
        }
      })

      // 4. Spawning energy particles
      if (Math.random() < 0.08) {
        const link = links[Math.floor(Math.random() * links.length)]
        const src = nodes.find((n) => n.id === link.source)
        const tgt = nodes.find((n) => n.id === link.target)
        if (src && tgt) {
          let pColor = '#a855f7'
          if (phase === 'drift') {
            pColor = (src.id === 'source' || src.id.startsWith('affected')) ? '#f43f5e' : '#f59e0b'
          } else if (phase === 'remediate') {
            pColor = '#10b981'
          } else {
            pColor = src.id === 'datahub' ? '#ec4899' : '#6366f1'
          }
          particles.push({
            sourceNode: src,
            targetNode: tgt,
            progress: 0,
            speed: 0.008 + Math.random() * 0.008,
            color: pColor
          })
        }
      }

      // 5. Draw Links
      ctx.lineWidth = 1
      links.forEach((link) => {
        const src = nodes.find((n) => n.id === link.source)
        const tgt = nodes.find((n) => n.id === link.target)
        if (src && tgt) {
          const pSrc = project(src.x, src.y, src.z)
          const pTgt = project(tgt.x, tgt.y, tgt.z)

          ctx.beginPath()
          ctx.moveTo(pSrc.x, pSrc.y)
          ctx.lineTo(pTgt.x, pTgt.y)

          let strokeGrad = ctx.createLinearGradient(pSrc.x, pSrc.y, pTgt.x, pTgt.y)
          strokeGrad.addColorStop(0, `${src.color}25`)
          strokeGrad.addColorStop(1, `${tgt.color}25`)
          ctx.strokeStyle = strokeGrad
          ctx.stroke()
        }
      })

      // 6. Draw Particles (iterate backwards to safely remove completed ones)
      for (let idx = particles.length - 1; idx >= 0; idx--) {
        const p = particles[idx]
        p.progress += p.speed
        if (p.progress >= 1) {
          particles.splice(idx, 1)
          continue
        }

        const x = p.sourceNode.x + (p.targetNode.x - p.sourceNode.x) * p.progress
        const y = p.sourceNode.y + (p.targetNode.y - p.sourceNode.y) * p.progress
        const z = p.sourceNode.z + (p.targetNode.z - p.sourceNode.z) * p.progress
        const projected = project(x, y, z)

        ctx.beginPath()
        ctx.arc(projected.x, projected.y, 2.5 * projected.scale, 0, Math.PI * 2)
        ctx.fillStyle = p.color
        ctx.shadowBlur = 6
        ctx.shadowColor = p.color
        ctx.fill()
        ctx.shadowBlur = 0
      }

      // 7. Draw Explosion Particles (iterate backwards to safely remove)
      for (let idx = burstParticles.length - 1; idx >= 0; idx--) {
        const p = burstParticles[idx]
        p.x += p.vx
        p.y += p.vy
        p.life++
        if (p.life >= p.maxLife) {
          burstParticles.splice(idx, 1)
          continue
        }

        const opacity = 1 - p.life / p.maxLife
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.size * opacity, 0, Math.PI * 2)
        ctx.fillStyle = p.color
        ctx.fill()
      }

      // 8. Draw Nodes
      nodes.forEach((node) => {
        const projected = project(node.x, node.y, node.z)

        // Diagnose sweep sonar on first affected node
        if (phase === 'diagnose' && node.id.startsWith('affected')) {
          const scanRadius = ((Date.now() % 1600) / 1600) * 80
          ctx.beginPath()
          ctx.arc(projected.x, projected.y, scanRadius * projected.scale, 0, Math.PI * 2)
          ctx.strokeStyle = `rgba(99, 102, 241, ${1 - (scanRadius / 80)})`
          ctx.lineWidth = 1
          ctx.stroke()
        }

        // Draw node body
        ctx.beginPath()
        ctx.arc(projected.x, projected.y, node.size * projected.scale, 0, Math.PI * 2)
        ctx.fillStyle = node.color
        ctx.shadowBlur = 10
        ctx.shadowColor = node.color
        ctx.fill()
        ctx.shadowBlur = 0

        ctx.beginPath()
        ctx.arc(projected.x, projected.y, (node.size + 4) * projected.scale, 0, Math.PI * 2)
        ctx.strokeStyle = `${node.color}15`
        ctx.lineWidth = 1
        ctx.stroke()

        // Tiny elegant text labels
        ctx.fillStyle = 'rgba(255, 255, 255, 0.75)'
        ctx.font = `600 ${Math.max(8, Math.round(9.5 * projected.scale))}px Inter`
        ctx.textAlign = 'center'
        ctx.fillText(node.label, projected.x, projected.y - (node.size + 8) * projected.scale)
      })

      animationFrameId = requestAnimationFrame(draw)
    }

    draw()

    return () => {
      cancelAnimationFrame(animationFrameId)
      window.removeEventListener('mousemove', handleMouseMove)
    }
  }, [dims]) // Redraw and reinitialize when dimensions change to apply coordinates correctly

  return (
    <div 
      className="canvas-container" 
      style={{ 
        position: 'fixed', 
        top: 0, 
        left: 0, 
        width: '100vw', 
        height: '100vh', 
        zIndex: -9999, // GUARANTEED ABSOLUTE BOTTOM LAYER RENDER
        pointerEvents: 'none' 
      }}
    >
      <canvas 
        ref={canvasRef} 
        width={dims.width} 
        height={dims.height} 
        className="canvas-element" 
        style={{ 
          position: 'absolute', 
          top: 0, 
          left: 0, 
          width: '100%', 
          height: '100%', 
          pointerEvents: 'none' 
        }} 
      />
    </div>
  )
}
