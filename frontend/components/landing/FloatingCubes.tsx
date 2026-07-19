'use client'

import { useEffect, useRef } from 'react'

interface Cube {
  x: number; y: number; z: number; size: number
  rx: number; ry: number; rz: number
  sx: number; sy: number; sz: number
  opacity: number; hue: number
}

export default function FloatingCubes() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animRef = useRef<number>(0)
  const cubesRef = useRef<Cube[]>([])
  const mouseRef = useRef({ x: 0, y: 0 })

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!
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

    const onMouse = (e: MouseEvent) => {
      const r = canvas.getBoundingClientRect()
      mouseRef.current = { x: e.clientX - r.left, y: e.clientY - r.top }
    }
    canvas.addEventListener('mousemove', onMouse)

    // 1 hero cube (huge), 4 medium, 4 small
    cubesRef.current = [
      { x: W()*0.55, y: H()*0.35, z: 0, size: 160, rx: 0.5, ry: 0.8, rz: 0.3, sx: 0.006, sy: 0.009, sz: 0.004, opacity: 0.7, hue: 270 },
      { x: W()*0.35, y: H()*0.15, z: 80, size: 100, rx: 1.2, ry: 0.4, rz: 0.7, sx: 0.008, sy: 0.007, sz: 0.005, opacity: 0.55, hue: 260 },
      { x: W()*0.75, y: H()*0.2, z: 60, size: 90, rx: 0.3, ry: 1.5, rz: 0.2, sx: 0.007, sy: 0.01, sz: 0.003, opacity: 0.5, hue: 280 },
      { x: W()*0.5, y: H()*0.7, z: 40, size: 110, rx: 0.8, ry: 0.6, rz: 1.1, sx: 0.005, sy: 0.008, sz: 0.006, opacity: 0.5, hue: 265 },
      { x: W()*0.8, y: H()*0.65, z: 100, size: 80, rx: 1.0, ry: 0.3, rz: 0.5, sx: 0.009, sy: 0.006, sz: 0.004, opacity: 0.45, hue: 275 },
      { x: W()*0.2, y: H()*0.4, z: 150, size: 50, rx: 0.7, ry: 1.2, rz: 0.9, sx: 0.012, sy: 0.01, sz: 0.007, opacity: 0.35, hue: 255 },
      { x: W()*0.9, y: H()*0.4, z: 120, size: 55, rx: 1.5, ry: 0.5, rz: 0.3, sx: 0.01, sy: 0.012, sz: 0.006, opacity: 0.3, hue: 285 },
      { x: W()*0.65, y: H()*0.85, z: 140, size: 45, rx: 0.4, ry: 0.9, rz: 1.3, sx: 0.011, sy: 0.008, sz: 0.009, opacity: 0.25, hue: 250 },
      { x: W()*0.3, y: H()*0.8, z: 160, size: 40, rx: 1.1, ry: 0.7, rz: 0.4, sx: 0.013, sy: 0.011, sz: 0.005, opacity: 0.2, hue: 290 },
    ]

    const proj = (x: number, y: number, z: number, w: number, h: number) => {
      const fov = 600, s = fov / (fov + z)
      return { x: w/2 + (x - w/2)*s, y: h/2 + (y - h/2)*s, s }
    }

    const drawCube = (ctx: CanvasRenderingContext2D, c: Cube, w: number, h: number, t: number) => {
      const half = c.size / 2
      const verts = [[-half,-half,-half],[half,-half,-half],[half,half,-half],[-half,half,-half],[-half,-half,half],[half,-half,half],[half,half,half],[-half,half,half]]

      const trX = c.rx + Math.sin(t*0.0005 + c.x*0.01)*0.1
      const trY = c.ry + Math.cos(t*0.0004 + c.y*0.01)*0.1
      const cosX = Math.cos(trX), sinX = Math.sin(trX), cosY = Math.cos(trY), sinY = Math.sin(trY), cosZ = Math.cos(c.rz), sinZ = Math.sin(c.rz)

      const rot = (v: number[]) => {
        let [vx,vy,vz] = v
        let ty=vy*cosX-vz*sinX, tz=vy*sinX+vz*cosX; vy=ty; vz=tz
        let tx=vx*cosY+vz*sinY; vz=-vx*sinY+vz*cosY; vx=tx
        tx=vx*cosZ-vy*sinZ; ty=vx*sinZ+vy*cosZ; vx=tx; vy=ty
        return [vx+c.x, vy+c.y, vz+c.z]
      }

      const rotated = verts.map(rot)
      const projected = rotated.map(v => proj(v[0], v[1], v[2], w, h))

      const faces = [[0,1,2,3],[4,5,6,7],[0,1,5,4],[2,3,7,6],[0,3,7,4],[1,2,6,5]]
      const sorted = faces.map(f => ({ f, z: f.reduce((s,i) => s+rotated[i][2],0)/4 })).sort((a,b) => a.z-b.z)

      for (const { f } of sorted) {
        const pts = f.map(i => projected[i])
        const [ax,ay] = [rotated[f[1]][0]-rotated[f[0]][0], rotated[f[1]][1]-rotated[f[0]][1]]
        const [bx,by] = [rotated[f[2]][0]-rotated[f[0]][0], rotated[f[2]][1]-rotated[f[0]][1]]
        const bright = Math.min(1, Math.abs(ax*by-ay*bx) / (c.size*c.size) * 2.5)

        ctx.beginPath(); ctx.moveTo(pts[0].x, pts[0].y)
        for (let i=1;i<pts.length;i++) ctx.lineTo(pts[i].x, pts[i].y)
        ctx.closePath()

        const g = ctx.createLinearGradient(pts[0].x, pts[0].y, pts[2].x, pts[2].y)
        g.addColorStop(0, `hsla(${c.hue}, 70%, 60%, ${c.opacity*bright*0.45})`)
        g.addColorStop(0.5, `hsla(${c.hue+20}, 60%, 50%, ${c.opacity*bright*0.3})`)
        g.addColorStop(1, `hsla(${c.hue+40}, 50%, 45%, ${c.opacity*bright*0.15})`)
        ctx.fillStyle = g; ctx.fill()
        ctx.strokeStyle = `hsla(${c.hue}, 70%, 70%, ${c.opacity*0.65})`
        ctx.lineWidth = c.size > 100 ? 2 : 1.5; ctx.stroke()
      }

      const pc = proj(c.x, c.y, c.z, w, h)
      const gr = c.size * pc.s * 2
      const glow = ctx.createRadialGradient(pc.x, pc.y, 0, pc.x, pc.y, gr)
      glow.addColorStop(0, `hsla(${c.hue}, 70%, 60%, ${c.opacity*0.18})`)
      glow.addColorStop(0.5, `hsla(${c.hue}, 60%, 50%, ${c.opacity*0.05})`)
      glow.addColorStop(1, `hsla(${c.hue}, 50%, 40%, 0)`)
      ctx.fillStyle = glow; ctx.fillRect(pc.x-gr, pc.y-gr, gr*2, gr*2)
    }

    const drawConnections = (ctx: CanvasRenderingContext2D, w: number, h: number) => {
      const cs = cubesRef.current
      for (let i=0;i<cs.length;i++) {
        for (let j=i+1;j<cs.length;j++) {
          const dx=cs[i].x-cs[j].x, dy=cs[i].y-cs[j].y, d=Math.sqrt(dx*dx+dy*dy)
          if (d < 350) {
            const a = (1-d/350)*0.12
            const pa=proj(cs[i].x,cs[i].y,cs[i].z,w,h), pb=proj(cs[j].x,cs[j].y,cs[j].z,w,h)
            ctx.beginPath(); ctx.moveTo(pa.x,pa.y); ctx.lineTo(pb.x,pb.y)
            ctx.strokeStyle=`rgba(139,92,246,${a})`; ctx.lineWidth=0.8; ctx.stroke()
          }
        }
      }
    }

    const animate = (t: number) => {
      const w=W(), h=H()
      ctx.clearRect(0,0,w,h)
      const m=mouseRef.current

      drawConnections(ctx,w,h)

      for (const c of cubesRef.current) {
        c.rx+=c.sx; c.ry+=c.sy; c.rz+=c.sz
        const dx=c.x-m.x, dy=c.y-m.y, d=Math.sqrt(dx*dx+dy*dy)
        if (d<250 && d>0) { const f=(250-d)/250*0.4; c.x+=(dx/d)*f; c.y+=(dy/d)*f }
        c.y+=Math.sin(t*0.0008+c.x*0.005)*0.15
        c.x+=Math.cos(t*0.0006+c.y*0.005)*0.08
        drawCube(ctx,c,w,h,t)
      }
      animRef.current = requestAnimationFrame(animate)
    }
    animRef.current = requestAnimationFrame(animate)
    return () => { cancelAnimationFrame(animRef.current); window.removeEventListener('resize', resize); canvas.removeEventListener('mousemove', onMouse) }
  }, [])

  return <canvas ref={canvasRef} style={{ position: 'absolute', top: '-5%', left: '-10%', width: '120%', height: '115%', zIndex: 1, pointerEvents: 'auto' }} />
}
