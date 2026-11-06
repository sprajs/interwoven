import { useEffect, useRef } from 'react'
import { Engine } from '../engine/Engine.ts'
import { emitFrame } from '../engine/frames.ts'
import { clearTextCache } from '../engine/overlay.ts'
import { followEntry, openThread, setEngine, stepStory, useApp } from '../store.ts'
import { FONT_FACES, LAYOUT, UNIT } from '../design.ts'
import { COMPACT_WIDTH, LABELS_WIDTH, rightSheetOpen, SHEET_CLEARANCE, SHEET_WIDTH } from './layout.ts'


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
        onFrame: emitFrame,
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
      const sheet = compact && (s.selected !== null || s.unplacedSelected !== null || story)
      const bottom = s.unplacedOpen ? window.innerHeight * 0.56 : sheet ? window.innerHeight * 0.5 : compact && s.mode === 'reach' ? 26 * UNIT : LAYOUT.frameBottom
      engine.setInsets({
        top: (compact ? LAYOUT.frameTopCompact : LAYOUT.frameTop) + LAYOUT.framePad,
        bottom: bottom + LAYOUT.framePad,
        left: labels ? LABELS_WIDTH + SHEET_CLEARANCE : compact ? LAYOUT.marginCompact : LAYOUT.margin,
        right: panel ? SHEET_WIDTH + SHEET_CLEARANCE : compact ? LAYOUT.marginCompact : LAYOUT.margin,
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
    sync()
    const unsubscribe = useApp.subscribe((s, prev) => {
      if (s.model !== lastModel && s.model) {
        lastModel = s.model
        engine.setModel(s.model)
      }
      if (
        s.mode !== prev.mode ||
        s.compressed !== prev.compressed ||
        s.hiddenKinds !== prev.hiddenKinds ||
        s.activeLabels !== prev.activeLabels ||
        s.selected !== prev.selected ||
        s.unplacedSelected !== prev.unplacedSelected ||
        s.unplacedOpen !== prev.unplacedOpen ||
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
    void Promise.all(FONT_FACES.map((face) => document.fonts.load(face))).then(() => {
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
