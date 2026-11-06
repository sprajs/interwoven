import { useEffect, useRef, useState } from 'react'
import { onEngineFrame } from '../engine/frames.ts'
import { formatYear } from '../engine/time.ts'
import { getEngine, passes, useApp } from '../store.ts'

const HEIGHT = 30
const TICK_BY_LEVEL = [20, 15, 10, 7]

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
  const dragging = useRef<number | null>(null)

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
      const baseline = HEIGHT - 3.5
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
      const x0 = Math.max(0, cam.fromX(cam.insets.left) * width)
      const x1 = Math.min(width, cam.fromX(cam.width - cam.insets.right) * width)
      win.style.transform = `translateX(${x0}px)`
      win.style.width = `${Math.max(5, x1 - x0)}px`
      // At full extent the bracket says nothing, so it stays out of the way.
      win.style.opacity = x1 - x0 > width * 0.985 ? '0' : '1'
    })
  }, [])

  const localU = (clientX: number) => {
    const rect = boxRef.current!.getBoundingClientRect()
    return Math.min(1, Math.max(0, (clientX - rect.left) / rect.width))
  }

  if (!model) return null

  return (
    <div className="absolute inset-x-[22px] bottom-3 z-10 min-[760px]:inset-x-14">
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
          const rect = boxRef.current!.getBoundingClientRect()
          setProbe({ x: u * rect.width, text: formatYear(model.time.year(u, compressed ? 1 : 0)) })
        }}
        onPointerUp={() => {
          dragging.current = null
        }}
        onPointerLeave={() => setProbe(null)}
      >
        <canvas ref={canvasRef} className="absolute inset-0" />
        <div ref={windowRef} className="pointer-events-none absolute inset-y-0 left-0 border-x border-ink/60 bg-ink/[0.045]" />
        {probe && (
          <div className="pointer-events-none absolute -top-[22px] -translate-x-1/2 whitespace-nowrap text-[14px] text-ink-2" style={{ left: probe.x }}>
            {probe.text}
          </div>
        )}
      </div>
    </div>
  )
}
