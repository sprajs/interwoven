import { useEffect, useMemo, useRef } from 'react'
import type { RowOrder } from '../data/derive.ts'
import type { Model } from '../data/model.ts'
import { onEngineFrame } from '../engine/frames.ts'
import type { PileForm } from '../engine/piles.ts'
import { getEngine, useApp } from '../store.ts'
import { rightSheetOpen, usePageMargins } from './layout.ts'

const ROUND_SPANS = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
const BAR_TARGET = 72

/**
 * A map's scale bar for time. The axis is not uniform, so it is measured at the middle of
 * the view and changes as you move, which is itself worth seeing.
 */
function ScaleBar() {
  const barRef = useRef<HTMLSpanElement>(null)
  const textRef = useRef<HTMLSpanElement>(null)
  useEffect(() => {
    let last = ''
    return onEngineFrame((engine) => {
      const bar = barRef.current
      const text = textRef.current
      if (!bar || !text) return
      const cx = engine.camera.centerX
      const span = Math.abs(engine.xToYear(cx + BAR_TARGET / 2) - engine.xToYear(cx - BAR_TARGET / 2))
      if (!(span > 0)) return
      const round = ROUND_SPANS.reduce((best, s) => (Math.abs(Math.log(s / span)) < Math.abs(Math.log(best / span)) ? s : best), ROUND_SPANS[0]!)
      bar.style.width = `${Math.max(12, Math.min(BAR_TARGET * 1.8, (round / span) * BAR_TARGET))}px`
      const label = round === 1 ? '1 year' : `${round.toLocaleString('en-US').replace(/,/g, ' ')} years`
      if (label !== last) {
        last = label
        text.textContent = label
      }
    })
  }, [])
  return (
    <div className="note hidden items-center gap-2 whitespace-nowrap wide:flex" title="The length of this bar in years, at the middle of the view">
      <span ref={barRef} className="block h-1 border-x border-b border-ink-2" style={{ width: BAR_TARGET }} />
      <span ref={textRef} />
    </div>
  )
}

const STRIP_ROWS = 2
const STRIP_PITCH = 6
/** Past this many, a mark each stops being readable, and the count says it better. */
const STRIP_LIMIT = 260

/**
 * Every entry still waiting for a date, as a word-sized row of its marks. They have no place
 * along the axis, so they sit in the margin in no time order, ready to move onto the chart.
 */
function UnplacedStrip({ model }: { model: Model }) {
  const open = useApp((s) => s.unplacedOpen)
  const setOpen = useApp((s) => s.setUnplacedOpen)
  const marks = useMemo(() => {
    if (model.unplaced.length > STRIP_LIMIT) return []
    return [...model.unplaced]
      .sort((a, b) => (a.labels[0] ?? '').localeCompare(b.labels[0] ?? '') || a.title.localeCompare(b.title))
      .map((entry, k) => ({
        id: entry.id,
        kind: entry.kind,
        ink: model.labelById.get(entry.labels[0] ?? '')?.ink ?? 'currentColor',
        x: Math.floor(k / STRIP_ROWS) * STRIP_PITCH + STRIP_PITCH / 2,
        y: (k % STRIP_ROWS) * STRIP_PITCH + STRIP_PITCH / 2,
      }))
  }, [model])
  const count = model.unplaced.length
  const width = Math.ceil(count / STRIP_ROWS) * STRIP_PITCH
  if (count === 0) return null
  return (
    <button onClick={() => setOpen(!open)} aria-expanded={open} className={`group pointer-events-auto flex min-w-0 items-center gap-3 text-left transition-colors ${open ? 'text-ink' : 'text-ink-2 hover:text-ink'}`} title="The entries in the research that have no researched date yet (w)">
      <span className="note link-hover whitespace-nowrap text-inherit"><span className="figures">{count}</span> awaiting a date</span>
      <svg width={width} height={STRIP_ROWS * STRIP_PITCH} viewBox={`0 0 ${width} ${STRIP_ROWS * STRIP_PITCH}`} aria-hidden className="hidden shrink wide:block">
        {marks.map((mark) =>
          mark.kind === 'technology' ? <circle key={mark.id} cx={mark.x} cy={mark.y} r="2" fill={mark.ink} /> : <circle key={mark.id} cx={mark.x} cy={mark.y} r="1.6" fill="none" stroke={mark.ink} strokeWidth="0.8" />,
        )}
      </svg>
    </button>
  )
}

const REACH_ORDERS: { id: RowOrder; label: string; hint: string }[] = [
  { id: 'thread', label: 'By thread', hint: 'Connected work together, each entry near what it builds on' },
  { id: 'origin', label: 'By date', hint: 'A staircase of first appearances, as Priestley drew his chart' },
  { id: 'reach', label: 'By reach', hint: 'The longest influence first' },
]

const PILE_FORMS: { id: PileForm; label: string; hint: string }[] = [
  { id: 'subject', label: 'By subject', hint: 'A pile for each family of subjects, to see where each one gathers' },
  { id: 'together', label: 'Together', hint: 'One pile, layered by family, to see where everything gathers' },
]

/** What the current view offers, kept to one quiet line so the chart keeps the page. */
function ViewLine() {
  const mode = useApp((s) => s.mode)
  const following = useApp((s) => s.story !== null)
  const aboutOpen = useApp((s) => s.aboutOpen)
  const setAboutOpen = useApp((s) => s.setAboutOpen)
  const rowOrder = useApp((s) => s.rowOrder)
  const setRowOrder = useApp((s) => s.setRowOrder)
  const pile = useApp((s) => s.pile)
  const setPile = useApp((s) => s.setPile)
  const sheetOpen = useApp((s) => rightSheetOpen(s))

  if (mode === 'story' && !following) {
    return (
      <p className="pointer-events-auto whitespace-nowrap">
        <span className="hidden wide:inline">Click an entry to read what led to it and what followed, or </span>
        <button onClick={() => setAboutOpen(!aboutOpen)} aria-expanded={aboutOpen} className="link hover:text-ink">browse the stories</button>
      </p>
    )
  }
  if (mode === 'reach') {
    return (
      <div className="pointer-events-auto flex items-center gap-4 whitespace-nowrap">
        <div className="flex items-center gap-2" role="group" aria-label="Order of rows">
          {REACH_ORDERS.map((option) => (
            <button key={option.id} title={option.hint} aria-pressed={rowOrder === option.id} onClick={() => setRowOrder(option.id)} className={`transition-colors ${rowOrder === option.id ? 'link text-ink' : 'hover:text-ink'}`}>
              {option.label}
            </button>
          ))}
        </div>
        <button onClick={() => setAboutOpen(!aboutOpen)} aria-expanded={aboutOpen} className="link hover:text-ink">Key</button>
      </div>
    )
  }
  if (mode === 'density') {
    return (
      <div className="flex min-w-0 items-center gap-4 whitespace-nowrap">
        <div className="pointer-events-auto flex items-center gap-2" role="group" aria-label="Arrangement of the piles">
          {PILE_FORMS.map((option) => (
            <button key={option.id} title={option.hint} aria-pressed={pile === option.id} onClick={() => setPile(option.id)} className={`transition-colors ${pile === option.id ? 'link text-ink' : 'hover:text-ink'}`}>
              {option.label}
            </button>
          ))}
        </div>
        {!sheetOpen && <p className="hidden corner:block">One mark per dated entry. This shows research so far, not all that happened.</p>}
      </div>
    )
  }
  return null
}

/** The way back to the whole of the unplaced research, and the view controls, under the chart. */
export function BottomBar() {
  const model = useApp((s) => s.model)
  const compressed = useApp((s) => s.compressed)
  const setCompressed = useApp((s) => s.setCompressed)
  const openPeriods = useApp((s) => s.openPeriods)
  const following = useApp((s) => s.mode === 'story' && s.story !== null)
  const margins = usePageMargins()

  return (
    <div className="note pointer-events-none absolute bottom-14 z-10 flex h-8 items-center gap-4 transition-[left,right] duration-300 wide:gap-6" style={margins}>
      <ViewLine />
      {model && <UnplacedStrip model={model} />}
      <div className="flex-1" />

      {openPeriods > 0 && (
        <button onClick={() => getEngine()?.unfoldAll()} className="link pointer-events-auto whitespace-nowrap text-ink" title="Flatten the sheet again (u)">
          Unfold {openPeriods > 1 ? `${openPeriods} periods` : 'the sheet'}
        </button>
      )}

      {!following && (
        <div className="pointer-events-auto hidden items-center gap-2 compact:flex" role="group" aria-label="Time scale">
          {[
            { on: true, label: 'Compressed', hint: 'Recent centuries and busy periods get more room' },
            { on: false, label: 'Linear', hint: 'Every year is the same width' },
          ].map((option) => (
            <button key={option.label} title={option.hint} aria-pressed={compressed === option.on} onClick={() => setCompressed(option.on)} className={`whitespace-nowrap transition-colors ${compressed === option.on ? 'link text-ink' : 'hover:text-ink'}`}>
              {option.label}
            </button>
          ))}
        </div>
      )}

      <ScaleBar />

      <div className="pointer-events-auto flex items-center gap-3">
        <button onClick={() => getEngine()?.zoomBy(1 / 1.6)} className="px-1 text-body transition-colors hover:text-ink" aria-label="Zoom out">−</button>
        <button onClick={() => getEngine()?.fit()} className="transition-colors hover:text-ink" aria-label="Fit everything" title="Fit everything and unfold (0)">Fit</button>
        <button onClick={() => getEngine()?.zoomBy(1.6)} className="px-1 text-body transition-colors hover:text-ink" aria-label="Zoom in">+</button>
      </div>
    </div>
  )
}
