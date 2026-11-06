import { useEffect, useRef, useState } from 'react'
import { onEngineFrame } from '../engine/frames.ts'
import { formatYear } from '../engine/time.ts'
import { getEngine, passes, useApp } from '../store.ts'
import { LAYOUT } from '../design.ts'
import { usePageMargins } from './layout.ts'

const HEIGHT = LAYOUT.overview
const TICK_BY_LEVEL = [18, 12, 9, 6]

/** The whole of history along one ruled line: one fine tick per entry, with the current view bracketed. */
export function Overview() {
  const model = useApp((s) => s.model)
  const hiddenKinds = useApp((s) => s.hiddenKinds)
  const activeLabels = useApp((s) => s.activeLabels)
  const compressed = useApp((s) => s.compressed)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const windowRef = useRef<HTMLDivElement>(null)
  const boxRef = useRef<HTMLDivElement>(null)
  const [probe, setProbe] = useState<{ x: number; text: string } | null>(null)
  const dragging = useRef<{ id: number; kind: 'move' | 'start' | 'end'; grab: number; u0: number; u1: number } | null>(null)
  const [pleats, setPleats] = useState<{ a: number; b: number }[]>([])
  const margins = usePageMargins()

  useEffect(() => {
    const canvas = canvasRef.current
    const box = boxRef.current
    if (!canvas || !box || !model) return

    const draw = () => {
      const width = box.clientWidth
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      canvas.width = Math.round(width * dpr)
      canvas.height = Math.round(HEIGHT * dpr)
      canvas.style.width = `${width}px`
      canvas.style.height = `${HEIGHT}px`
      const ctx = canvas.getContext('2d')!
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.clearRect(0, 0, width, HEIGHT)

      const warp = compressed ? 1 : 0
      const baseline = HEIGHT - 3
      ctx.fillStyle = 'rgba(38,33,28,0.55)'
      ctx.fillRect(0, baseline, width, 0.75)

      const f = { hiddenKinds, activeLabels }
      const alpha = model.n > 4000 ? 0.12 : 0.85
      model.nodes.forEach((node, i) => {
        if (!passes(node, f)) return
        const x = model.time.u(node.year, warp) * width
        const h = TICK_BY_LEVEL[node.level] ?? 7
        ctx.fillStyle = `rgba(${model.ink[i * 3]! * 255},${model.ink[i * 3 + 1]! * 255},${model.ink[i * 3 + 2]! * 255},${alpha})`
        ctx.fillRect(x - 0.4, baseline - h, 0.8, h)
      })
    }

    draw()
    const observer = new ResizeObserver(draw)
    observer.observe(box)
    return () => observer.disconnect()
  }, [model, hiddenKinds, activeLabels, compressed])

  useEffect(() => {
    return onEngineFrame((engine) => {
      const box = boxRef.current
      const win = windowRef.current
      if (!box || !win) return
      const cam = engine.camera
      const width = box.clientWidth
      const x0 = Math.max(0, engine.uAtX(cam.insets.left) * width)
      const x1 = Math.min(width, engine.uAtX(cam.width - cam.insets.right) * width)
      win.style.transform = `translateX(${x0}px)`
      win.style.width = `${Math.max(5, x1 - x0)}px`
      // At full extent the bracket says nothing, so it stays out of the way.
      win.style.opacity = x1 - x0 > width * 0.985 ? '0' : '1'
      // The whole of history stays flat here, with the folded stretches toned.
      const next = engine.pleats
      setPleats((current) => {
        if (current.length === next.length && current.every((p, k) => p.a === next[k]!.u0 && p.b === next[k]!.u1)) return current
        return next.map((p) => ({ a: p.u0, b: p.u1 }))
      })
    })
  }, [])

  const localU = (clientX: number) => {
    const rect = boxRef.current!.getBoundingClientRect()
    return Math.min(1, Math.max(0, (clientX - rect.left) / rect.width))
  }

  if (!model) return null

  return (
    <div className="absolute bottom-4 z-10 transition-[left,right] duration-300" style={margins}>
      <div
        ref={boxRef}
        className="relative touch-none"
        style={{ height: HEIGHT, cursor: 'ew-resize' }}
        role="slider"
        aria-label="Position in time"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round((getEngine()?.camera.cu ?? 0.5) * 100)}
        tabIndex={0}
        onKeyDown={(e) => {
          const engine = getEngine()
          if (!engine) return
          const step = 0.1 / engine.camera.zoom
          const here = engine.uAtX(engine.camera.centerX)
          if (e.key === 'ArrowLeft') engine.panToU(here - step)
          if (e.key === 'ArrowRight') engine.panToU(here + step)
        }}
        onPointerDown={(e) => {
          const engine = getEngine()
          if (!engine) return
          e.currentTarget.setPointerCapture(e.pointerId)
          const u = localU(e.clientX)
          const cam = engine.camera
          const u0 = engine.uAtX(cam.insets.left)
          const u1 = engine.uAtX(cam.width - cam.insets.right)
          const width = boxRef.current!.clientWidth
          const reach = (e.pointerType === 'touch' ? 14 : 6) / width
          const zoomed = u1 - u0 < 0.985
          // The bracket's ends stretch it, which zooms time alone. Its middle carries it along.
          const kind = zoomed && Math.abs(u - u0) < reach ? 'start' : zoomed && Math.abs(u - u1) < reach ? 'end' : 'move'
          dragging.current = { id: e.pointerId, kind, grab: kind === 'move' && u >= u0 && u <= u1 ? u - (u0 + u1) / 2 : 0, u0, u1 }
          if (kind === 'move') engine.panToU(u - dragging.current.grab)
        }}
        onPointerMove={(e) => {
          const engine = getEngine()
          if (!engine) return
          const u = localU(e.clientX)
          const drag = dragging.current
          if (drag && drag.id === e.pointerId) {
            if (drag.kind === 'move') engine.panToU(u - drag.grab)
            else if (drag.kind === 'start') engine.showU(Math.min(u, drag.u1 - 0.002), drag.u1)
            else engine.showU(drag.u0, Math.max(u, drag.u0 + 0.002))
          }
          const rect = boxRef.current!.getBoundingClientRect()
          setProbe({ x: u * rect.width, text: formatYear(model.time.year(u, compressed ? 1 : 0)) })
        }}
        onWheel={(e) => {
          const engine = getEngine()
          if (!engine) return
          const cam = engine.camera
          cam.zoomAt(cam.toX(engine.toV(localU(e.clientX))), cam.centerY, -e.deltaY * 0.004, 'time', true)
          engine.invalidate()
        }}
        onDoubleClick={() => getEngine()?.fit()}
        onPointerUp={() => {
          dragging.current = null
        }}
        onPointerLeave={() => setProbe(null)}
      >
        <canvas ref={canvasRef} className="absolute inset-0" />
        {pleats.map((p) => (
          <div key={p.a} className="pointer-events-none absolute inset-y-0 bg-tint" style={{ left: `${p.a * 100}%`, width: `${(p.b - p.a) * 100}%` }} />
        ))}
        <div ref={windowRef} className="pointer-events-none absolute inset-y-0 left-0 border-x border-ink-2" />
        {probe && (
          <div className="note pointer-events-none absolute -top-7 -translate-x-1/2 whitespace-nowrap text-ink-2" style={{ left: probe.x }}>
            {probe.text}
          </div>
        )}
      </div>
    </div>
  )
}
