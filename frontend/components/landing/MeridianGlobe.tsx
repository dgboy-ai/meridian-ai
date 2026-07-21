'use client'

import { useEffect, useRef } from 'react'

export default function MeridianGlobe() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animRef = useRef<number>(0)
  const mouseRef = useRef({ x: 0, y: 0 })

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const resize = () => {
      const dpr = window.devicePixelRatio || 1
      canvas.width = canvas.offsetWidth * dpr
      canvas.height = canvas.offsetHeight * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    }
    resize()
    window.addEventListener('resize', resize)

    const W = () => canvas.offsetWidth
    const H = () => canvas.offsetHeight

    const handleMouse = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect()
      mouseRef.current = { x: e.clientX - rect.left, y: e.clientY - rect.top }
    }
    canvas.addEventListener('mousemove', handleMouse)

    // Globe parameters
    const globeRadius = () => Math.min(W(), H()) * 0.32
    const meridianCount = 12
    const parallelCount = 7

    const project = (lat: number, lon: number, rotY: number, cx: number, cy: number, r: number) => {
      // Convert lat/lon to 3D
      const latRad = (lat * Math.PI) / 180
      const lonRad = ((lon + rotY) * Math.PI) / 180

      const x = r * Math.cos(latRad) * Math.sin(lonRad)
      const y = -r * Math.sin(latRad)
      const z = r * Math.cos(latRad) * Math.cos(lonRad)

      // Simple perspective
      const fov = 600
      const scale = fov / (fov + z)
      return {
        x: cx + x * scale,
        y: cy + y * scale,
        z,
        scale,
        visible: z > -r * 0.3,
      }
    }

    const drawMeridian = (ctx: CanvasRenderingContext2D, lon: number, rotY: number, cx: number, cy: number, r: number, time: number) => {
      const points: { x: number; y: number; z: number; visible: boolean }[] = []
      for (let lat = -90; lat <= 90; lat += 3) {
        points.push(project(lat, lon, rotY, cx, cy, r))
      }

      ctx.beginPath()
      let started = false
      for (const p of points) {
        if (p.visible) {
          if (!started) {
            ctx.moveTo(p.x, p.y)
            started = true
          } else {
            ctx.lineTo(p.x, p.y)
          }
        } else {
          started = false
        }
      }
      const alpha = 0.3 + Math.sin(time * 0.001 + lon * 0.1) * 0.1
      ctx.strokeStyle = `rgba(139, 92, 246, ${alpha})`
      ctx.lineWidth = 1.2
      ctx.stroke()
    }

    const drawParallel = (ctx: CanvasRenderingContext2D, lat: number, rotY: number, cx: number, cy: number, r: number) => {
      const points: { x: number; y: number; visible: boolean }[] = []
      for (let lon = 0; lon <= 360; lon += 3) {
        const p = project(lat, lon, rotY, cx, cy, r)
        points.push({ x: p.x, y: p.y, visible: p.visible })
      }

      ctx.beginPath()
      let started = false
      for (const p of points) {
        if (p.visible) {
          if (!started) {
            ctx.moveTo(p.x, p.y)
            started = true
          } else {
            ctx.lineTo(p.x, p.y)
          }
        } else {
          started = false
        }
      }
      ctx.strokeStyle = 'rgba(99, 102, 241, 0.2)'
      ctx.lineWidth = 1
      ctx.stroke()
    }

    const drawGlow = (ctx: CanvasRenderingContext2D, cx: number, cy: number, r: number, time: number) => {
      const pulse = 0.8 + Math.sin(time * 0.001) * 0.2
      const glow = ctx.createRadialGradient(cx, cy, r * 0.3, cx, cy, r * 2)
      glow.addColorStop(0, `rgba(139, 92, 246, ${0.15 * pulse})`)
      glow.addColorStop(0.3, `rgba(99, 102, 241, ${0.08 * pulse})`)
      glow.addColorStop(0.6, `rgba(139, 92, 246, ${0.03 * pulse})`)
      glow.addColorStop(1, 'rgba(139, 92, 246, 0)')
      ctx.fillStyle = glow
      ctx.fillRect(cx - r * 2.5, cy - r * 2.5, r * 5, r * 5)
    }

    const drawHighlights = (ctx: CanvasRenderingContext2D, rotY: number, cx: number, cy: number, r: number, time: number) => {
      // Highlight points that represent "incidents" on the globe
      const highlights = [
        { lat: 40, lon: -74 },   // New York
        { lat: 51, lon: 0 },     // London
        { lat: 35, lon: 139 },   // Tokyo
        { lat: -33, lon: 151 },  // Sydney
        { lat: 48, lon: 2 },     // Paris
      ]

      for (const hl of highlights) {
        const p = project(hl.lat, hl.lon, rotY, cx, cy, r)
        if (!p.visible) continue

        const pulse = 0.6 + Math.sin(time * 0.003 + hl.lon * 0.01) * 0.4

        // Outer ring
        ctx.beginPath()
        ctx.arc(p.x, p.y, 10 * p.scale, 0, Math.PI * 2)
        ctx.strokeStyle = `rgba(244, 63, 94, ${0.6 * pulse * p.scale})`
        ctx.lineWidth = 2
        ctx.stroke()

        // Inner dot
        ctx.beginPath()
        ctx.arc(p.x, p.y, 4 * p.scale, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(244, 63, 94, ${0.9 * pulse * p.scale})`
        ctx.fill()

        // Glow
        const glow = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, 20 * p.scale)
        glow.addColorStop(0, `rgba(244, 63, 94, ${0.4 * pulse * p.scale})`)
        glow.addColorStop(0.5, `rgba(244, 63, 94, ${0.1 * pulse * p.scale})`)
        glow.addColorStop(1, 'rgba(244, 63, 94, 0)')
        ctx.fillStyle = glow
        ctx.fillRect(p.x - 30, p.y - 30, 60, 60)
      }
    }

    const animate = (time: number) => {
      const w = W()
      const h = H()
      ctx.clearRect(0, 0, w, h)

      const cx = w * 0.5
      const cy = h * 0.5
      const r = globeRadius()
      const rotY = time * 0.008 // Slow rotation

      // Mouse influence on rotation
      const mouse = mouseRef.current
      const mouseOffset = (mouse.x - cx) * 0.0001

      // Glow
      drawGlow(ctx, cx, cy, r, time)

      // Draw parallels (latitude lines)
      for (let i = 1; i < parallelCount; i++) {
        const lat = -90 + (180 / parallelCount) * i
        drawParallel(ctx, lat, rotY + mouseOffset, cx, cy, r)
      }

      // Draw meridians (longitude lines)
      for (let i = 0; i < meridianCount; i++) {
        const lon = (360 / meridianCount) * i
        drawMeridian(ctx, lon, rotY + mouseOffset, cx, cy, r, time)
      }

      // Draw equator (brighter)
      ctx.beginPath()
      for (let lon = 0; lon <= 360; lon += 2) {
        const p = project(0, lon, rotY + mouseOffset, cx, cy, r)
        if (p.visible) {
          if (lon === 0) ctx.moveTo(p.x, p.y)
          else ctx.lineTo(p.x, p.y)
        }
      }
      ctx.strokeStyle = 'rgba(139, 92, 246, 0.4)'
      ctx.lineWidth = 1.8
      ctx.stroke()

      // Highlight points
      drawHighlights(ctx, rotY + mouseOffset, cx, cy, r, time)

      // Outer ring
      ctx.beginPath()
      ctx.arc(cx, cy, r, 0, Math.PI * 2)
      ctx.strokeStyle = 'rgba(139, 92, 246, 0.25)'
      ctx.lineWidth = 1.5
      ctx.stroke()

      animRef.current = requestAnimationFrame(animate)
    }
    animRef.current = requestAnimationFrame(animate)

    return () => {
      cancelAnimationFrame(animRef.current)
      window.removeEventListener('resize', resize)
      canvas.removeEventListener('mousemove', handleMouse)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '100%',
        height: '100%',
        zIndex: 0,
        pointerEvents: 'none',
      }}
    />
  )
}
