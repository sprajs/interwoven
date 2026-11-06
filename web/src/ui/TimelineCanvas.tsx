import { useEffect, useRef } from 'react'
import { Engine } from '../engine/Engine.ts'
import { emitFrame } from '../engine/frames.ts'
import { setEngine, useApp } from '../store.ts'

const COMPACT_WIDTH = 760

/** Mounts the engine and mirrors app state into it. */
export function TimelineCanvas() {
  const glRef = useRef<HTMLCanvasElement>(null)
  const overlayRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const glCanvas = glRef.current!
    const overlay = overlayRef.current!
    let engine: Engine
    try {
      engine = new Engine(glCanvas, overlay, {
        onHover: (index, x, y) => useApp.getState().setHover(index === null ? null : { index, x, y }),
        onSelect: (index) => useApp.getState().select(index),
        onFrame: (e) => {
          // The depth readout is the only per-frame value React needs, and it changes rarely.
          let depth = 1
          for (let level = 2; level <= 3; level++) if ((e.reveal[level] ?? 0) > 0.5) depth = level
          if (depth !== useApp.getState().depth) useApp.getState().setDepth(depth)
          emitFrame(e)
        },
        onFatal: (message) => useApp.getState().setError(message),
      })
    } catch (e) {
      useApp.getState().setError(e instanceof Error ? e.message : String(e))
      return
    }
    setEngine(engine)

    const sync = () => {
      const s = useApp.getState()
      const compact = window.innerWidth < COMPACT_WIDTH
      const panel = !compact && (s.selected !== null || s.mode !== 'network')
      // On narrow screens details open as a bottom sheet, so the view makes room above it.
      const sheet = compact && s.selected !== null
      engine.setInsets({
        top: compact ? 104 : 112,
        bottom: sheet ? window.innerHeight * 0.5 : compact ? 92 : 108,
        left: compact ? 36 : 172,
        right: panel ? 344 : compact ? 20 : 44,
      })
      engine.setView({
        mode: s.mode,
        compressed: s.compressed,
        hiddenDomains: s.hiddenDomains,
        hiddenTypes: s.hiddenTypes,
        activeLabels: s.activeLabels,
        selected: s.selected,
      })
    }

    let lastModel = useApp.getState().model
    if (lastModel) engine.setModel(lastModel)
    sync()
    const unsubscribe = useApp.subscribe((s, prev) => {
      if (s.model !== lastModel && s.model) {
        lastModel = s.model
        engine.setModel(s.model)
      }
      if (
        s.mode !== prev.mode ||
        s.compressed !== prev.compressed ||
        s.hiddenDomains !== prev.hiddenDomains ||
        s.hiddenTypes !== prev.hiddenTypes ||
        s.activeLabels !== prev.activeLabels ||
        s.selected !== prev.selected
      ) {
        sync()
      }
    })
    window.addEventListener('resize', sync)

    // Text measured before the web fonts load has the wrong width.
    void document.fonts.ready.then(() => engine.invalidate())

    return () => {
      unsubscribe()
      window.removeEventListener('resize', sync)
      setEngine(null)
      engine.dispose()
    }
  }, [])

  return (
    <div className="absolute inset-0" role="img" aria-label="Interactive timeline of science and technology. Use search to browse the entries as a list.">
      <canvas ref={glRef} className="absolute inset-0" />
      <canvas ref={overlayRef} className="absolute inset-0 touch-none" style={{ cursor: 'grab' }} />
    </div>
  )
}
