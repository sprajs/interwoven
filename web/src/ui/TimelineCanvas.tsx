import { useEffect, useRef } from 'react'
import { Engine } from '../engine/Engine.ts'
import { emitFrame } from '../engine/frames.ts'
import { clearTextCache } from '../engine/overlay.ts'
import { followEntry, openThread, setEngine, stepStory, useApp } from '../store.ts'
import { COMPACT_WIDTH, LABELS_WIDTH, rightSheetOpen, SHEET_WIDTH } from './layout.ts'


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
        onFollow: (index) => {
          // An entry with no links has nothing to follow, so the second tap just keeps it selected.
          if (!followEntry(index)) useApp.getState().select(index)
        },
        onFolds: (count) => useApp.getState().setOpenPeriods(count),
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
    if (import.meta.env.DEV) Object.assign(window, { engine, useApp, followEntry, openThread, stepStory })

    const sync = () => {
      const s = useApp.getState()
      const compact = window.innerWidth < COMPACT_WIDTH
      const panel = !compact && rightSheetOpen(s)
      const story = s.mode === 'story'
      const labels = !compact && s.labelsOpen
      // On narrow screens details open as a bottom sheet, so the view makes room above it.
      const sheet = compact && (s.selected !== null || story)
      engine.setInsets({
        top: compact ? 118 : 104,
        bottom: sheet ? window.innerHeight * 0.5 : compact ? 104 : 96,
        left: labels ? LABELS_WIDTH + 36 : compact ? 22 : 56,
        right: panel ? SHEET_WIDTH + 36 : compact ? 22 : 56,
      })
      engine.setView({
        mode: s.mode,
        compressed: s.compressed,
        hiddenKinds: s.hiddenKinds,
        activeLabels: s.activeLabels,
        selected: s.selected,
        rowOrder: s.rowOrder,
        story: s.story,
        searchHits: s.searchHits,
        previewLabel: s.previewLabel,
      })
    }

    let lastModel = useApp.getState().model
    if (lastModel) engine.setModel(lastModel)
    engine.setLife(useApp.getState().life)
    sync()
    const unsubscribe = useApp.subscribe((s, prev) => {
      if (s.model !== lastModel && s.model) {
        lastModel = s.model
        engine.setModel(s.model)
      }
      if (s.life !== prev.life) engine.setLife(s.life)
      if (
        s.mode !== prev.mode ||
        s.compressed !== prev.compressed ||
        s.hiddenKinds !== prev.hiddenKinds ||
        s.activeLabels !== prev.activeLabels ||
        s.selected !== prev.selected ||
        s.labelsOpen !== prev.labelsOpen ||
        s.rowOrder !== prev.rowOrder ||
        s.story !== prev.story ||
        s.searchHits !== prev.searchHits ||
        s.previewLabel !== prev.previewLabel
      ) {
        sync()
      }
    })
    window.addEventListener('resize', sync)

    // Text measured before the web fonts arrive has the wrong width.
    const fonts = ['400 14px "EB Garamond Variable"', 'italic 400 14px "EB Garamond Variable"', '500 17px "EB Garamond Variable"']
    void Promise.all(fonts.map((font) => document.fonts.load(font))).then(() => {
      clearTextCache()
      engine.invalidate()
    })

    return () => {
      unsubscribe()
      window.removeEventListener('resize', sync)
      setEngine(null)
      engine.dispose()
    }
  }, [])

  return (
    <div className="absolute inset-0" role="img" aria-label="A chart of how science and technology build on one another. Use search to browse the entries as a list.">
      <canvas ref={glRef} className="absolute inset-0" />
      <canvas ref={overlayRef} className="absolute inset-0 touch-none" style={{ cursor: 'grab' }} />
    </div>
  )
}
