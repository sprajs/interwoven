import { useEffect, useRef, useState } from 'react'
import { onEngineFrame } from '../engine/frames.ts'
import { formatYear } from '../engine/time.ts'
import { getEngine, passes, useApp } from '../store.ts'

const BINS = 150
const HEIGHT = 56

/** Whole-history strip: stacked activity per domain, with a draggable window on the current view. */
export function Overview() {
  const model = useApp((s) => s.model)
  const hiddenDomains = useApp((s) => s.hiddenDomains)
  const hiddenTypes = useApp((s) => s.hiddenTypes)
  const activeLabels = useApp((s) => s.activeLabels)
  const compressed = useApp((s) => s.compressed)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const windowRef = useRef<HTMLDivElement>(null)
  const boxRef = useRef<HTMLDivElement>(null)
  const [probe, setProbe] = useState<{ x: number; text: string } | null>(null)
  const dragging = useRef<number | null>(null)
  const binsRef = useRef<Int32Array>(new Int32Array(BINS))

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
      const laneCount = model.lanes.length
      const counts = new Int32Array(BINS * laneCount)
      const totals = new Int32Array(BINS)
      const f = { hiddenDomains, hiddenTypes, activeLabels }
      model.nodes.forEach((node, i) => {
        if (!passes(node, f)) return
        const b = Math.min(BINS - 1, Math.max(0, Math.floor(model.time.u(node.year, warp) * BINS)))
        counts[b * laneCount + model.domainIndex[i]!]!++
        totals[b]!++
      })
      binsRef.current = totals
      const max = Math.max(1, ...totals)

      // Bars carry a 1px gap so the strip reads as discrete counts at this width.
      const barWidth = width / BINS
      const chartHeight = HEIGHT - 6
      for (let b = 0; b < BINS; b++) {
        if (totals[b] === 0) continue
        const barHeight = Math.max(2, Math.sqrt(totals[b]! / max) * chartHeight)
        let y = HEIGHT - 3
        for (let l = 0; l < laneCount; l++) {
          const c = counts[b * laneCount + l]!
          if (c === 0) continue
          const h = (c / totals[b]!) * barHeight
          ctx.fillStyle = model.lanes[l]!.color
          ctx.globalAlpha = 0.85
          ctx.fillRect(b * barWidth + 0.5, y - h, Math.max(1, barWidth - 1), h)
          y -= h
        }
      }
      ctx.globalAlpha = 1
      ctx.fillStyle = 'rgba(170,190,230,0.14)'
      ctx.fillRect(0, HEIGHT - 2, width, 1)
    }

    draw()
    const observer = new ResizeObserver(draw)
    observer.observe(box)
    return () => observer.disconnect()
  }, [model, hiddenDomains, hiddenTypes, activeLabels, compressed])

  useEffect(() => {
    return onEngineFrame((engine) => {
      const box = boxRef.current
      const win = windowRef.current
      if (!box || !win) return
      const cam = engine.camera
      const width = box.clientWidth
      const left = cam.fromX(cam.insets.left) * width
      const right = cam.fromX(cam.width - cam.insets.right) * width
      const x0 = Math.max(0, left)
      const x1 = Math.min(width, right)
      win.style.transform = `translateX(${x0}px)`
      win.style.width = `${Math.max(6, x1 - x0)}px`
    })
  }, [])

  const localU = (clientX: number) => {
    const rect = boxRef.current!.getBoundingClientRect()
    return Math.min(1, Math.max(0, (clientX - rect.left) / rect.width))
  }

  if (!model) return null

  return (
    <div className="glass absolute inset-x-3 bottom-3 z-20 rounded-xl px-2 py-1 sm:inset-x-4">
      <div
        ref={boxRef}
        className="relative touch-none"
        style={{ height: HEIGHT, cursor: 'ew-resize' }}
        role="slider"
        aria-label="Timeline position"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round((getEngine()?.camera.cu ?? 0.5) * 100)}
        tabIndex={0}
        onKeyDown={(e) => {
          const engine = getEngine()
          if (!engine) return
          const step = 0.1 / engine.camera.zoom
          if (e.key === 'ArrowLeft') engine.panToU(engine.camera.cu - step)
          if (e.key === 'ArrowRight') engine.panToU(engine.camera.cu + step)
        }}
        onPointerDown={(e) => {
          e.currentTarget.setPointerCapture(e.pointerId)
          dragging.current = e.pointerId
          getEngine()?.panToU(localU(e.clientX))
        }}
        onPointerMove={(e) => {
          const engine = getEngine()
          if (!engine) return
          const u = localU(e.clientX)
          if (dragging.current === e.pointerId) engine.panToU(u)
          const warp = compressed ? 1 : 0
          const bin = Math.min(BINS - 1, Math.floor(u * BINS))
          const a = model.time.year(bin / BINS, warp)
          const b = model.time.year((bin + 1) / BINS, warp)
          const count = binsRef.current[bin] ?? 0
          const rect = boxRef.current!.getBoundingClientRect()
          setProbe({
            x: u * rect.width,
            text: `${formatYear(a)} to ${formatYear(b)}: ${count.toLocaleString('en-US')} ${count === 1 ? 'entry' : 'entries'}`,
          })
        }}
        onPointerUp={() => {
          dragging.current = null
        }}
        onPointerLeave={() => setProbe(null)}
      >
        <canvas ref={canvasRef} className="absolute inset-0" />
        <div
          ref={windowRef}
          className="pointer-events-none absolute inset-y-0 left-0 rounded-md border border-white/35 bg-white/7 shadow-[0_0_18px_rgb(141_180_255/0.2)]"
        />
        {probe && (
          <div
            className="glass pointer-events-none absolute -top-9 whitespace-nowrap rounded-lg px-2 py-1 font-mono text-[11px] text-ink"
            style={{ left: probe.x, transform: `translateX(${probe.x < 140 ? '0' : probe.x > (boxRef.current?.clientWidth ?? 0) - 140 ? '-100%' : '-50%'})` }}
          >
            {probe.text}
          </div>
        )}
      </div>
    </div>
  )
}
