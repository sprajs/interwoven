import { useEffect, useRef, useState } from 'react'
import { LEVEL_NAMES } from '../data/types.ts'
import { onEngineFrame } from '../engine/frames.ts'
import { getEngine, useApp } from '../store.ts'
import { Mark } from './icons.tsx'
import { usePageMargins } from './layout.ts'

function RangeMark() {
  return (
    <svg width="20" height="8" viewBox="0 0 20 8" aria-hidden>
      <path d="M1 1v6M19 1v6M1 4h18" stroke="currentColor" strokeWidth="0.9" fill="none" />
    </svg>
  )
}

function ProvisionalMark() {
  return (
    <svg width="20" height="8" viewBox="0 0 20 8" aria-hidden>
      <path d="M2 4h16" stroke="currentColor" strokeWidth="0.7" fill="none" />
      <circle cx="10" cy="4" r="3" fill="currentColor" />
    </svg>
  )
}

function BrokenMark() {
  return (
    <svg width="22" height="6" viewBox="0 0 22 6" aria-hidden>
      <path d="M1 3h4.5M8 3h5M15.5 3h5.5" stroke="currentColor" strokeWidth="1" fill="none" strokeLinecap="round" />
    </svg>
  )
}

const ROUND_SPANS = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
const BAR_TARGET = 74

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
      const cam = engine.camera
      const cx = cam.centerX
      const span = Math.abs(engine.xToYear(cx + BAR_TARGET / 2) - engine.xToYear(cx - BAR_TARGET / 2))
      if (!(span > 0)) return
      const round = ROUND_SPANS.reduce((best, s) => (Math.abs(Math.log(s / span)) < Math.abs(Math.log(best / span)) ? s : best), ROUND_SPANS[0]!)
      const width = Math.max(14, Math.min(130, (round / span) * BAR_TARGET))
      bar.style.width = `${width}px`
      const label = round === 1 ? '1 year' : `${round.toLocaleString('en-US').replace(/,/g, ' ')} years`
      if (label !== last) {
        last = label
        text.textContent = label
      }
    })
  }, [])
  return (
    <div className="hidden items-center gap-2 whitespace-nowrap text-[14.5px] text-ink-3 min-[1000px]:flex" title="The length of this bar in years, at the middle of the view">
      <span ref={barRef} className="block h-[5px] border-x border-b border-ink-2" style={{ width: BAR_TARGET }} />
      <span ref={textRef} className="min-w-[4.2em]" />
    </div>
  )
}

/** Four marks for four depths of detail, from landmarks down. Choosing one zooms there. */
function DepthMarks() {
  const depth = useApp((s) => s.depth)
  const sizes = [9, 7, 5, 3.4]
  return (
    <div className="pointer-events-auto hidden items-center gap-[7px] min-[760px]:flex" role="group" aria-label="Depth of detail">
      {sizes.map((size, level) => (
        <button key={level} onClick={() => getEngine()?.zoomToDepth(level)} title={`${LEVEL_NAMES[level]}${level <= depth ? ', showing' : '. Zoom in to here.'}`} aria-pressed={level <= depth} className="group grid h-5 w-3 place-items-center" aria-label={LEVEL_NAMES[level]}>
          <span className={`block rounded-full transition-colors ${level <= depth ? 'bg-ink-2 group-hover:bg-ink' : 'border border-ink-3/70 group-hover:border-ink'}`} style={{ width: size, height: size }} />
        </button>
      ))}
    </div>
  )
}

/** The key to the marks and the view controls, under the chart. */
export function BottomBar() {
  const depth = useApp((s) => s.depth)
  const compressed = useApp((s) => s.compressed)
  const setCompressed = useApp((s) => s.setCompressed)
  const openPeriods = useApp((s) => s.openPeriods)
  const following = useApp((s) => s.mode === 'story' && s.story !== null)
  const mode = useApp((s) => s.mode)
  const margins = usePageMargins()
  const sheetOpen = useApp((s) => s.selected !== null || s.unplacedSelected !== null || s.mode !== 'threads' || s.labelsOpen || s.unplacedOpen)
  const crowded = useApp((s) => (s.selected !== null || (s.mode !== 'threads' && s.mode !== 'reach')) && s.labelsOpen)
  const [narrow, setNarrow] = useState(false)
  useEffect(() => {
    const onResize = () => setNarrow(window.innerWidth < 760)
    onResize()
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  return (
    <div className="pointer-events-none absolute bottom-[47px] z-10 flex items-center gap-4 text-ink-3 transition-[left,right] duration-300 min-[1000px]:gap-5" style={margins}>
      <ul className={`min-w-0 items-center gap-3.5 overflow-hidden whitespace-nowrap text-[14.5px] ${crowded || sheetOpen ? 'hidden' : 'hidden xl:flex'}`} aria-label="Key">
        <li className="flex items-center gap-1.5"><Mark kind="technology" size={8} />Technology</li>
        <li className="flex items-center gap-1.5 italic"><Mark kind="science" size={9} />Science</li>
        <li className="flex items-center gap-1.5"><RangeMark />Date range</li>
        <li className="flex items-center gap-1.5"><ProvisionalMark />Date provisional</li>
        <li className="flex items-center gap-1.5"><BrokenMark />Link awaiting review</li>
      </ul>

      <div className="flex-1" />

      {openPeriods > 0 && (
        <button onClick={() => getEngine()?.unfoldAll()} className="pointer-events-auto whitespace-nowrap text-[15px] italic text-ink underline decoration-[0.5px] underline-offset-[3px]" title="Flatten the sheet again (u)">
          Unfold {openPeriods > 1 ? `${openPeriods} periods` : 'the sheet'}
        </button>
      )}

      {!following && (
        <div className="pointer-events-auto flex items-center gap-2 text-[15px] leading-none" role="group" aria-label="Time scale">
          {[
            { on: true, label: narrow ? 'Compr.' : 'Compressed', hint: 'Recent centuries and busy periods get more room' },
            { on: false, label: 'Linear', hint: 'Every year is the same width' },
          ].map((option) => (
            <button
              key={option.label}
              title={option.hint}
              aria-pressed={compressed === option.on}
              onClick={() => setCompressed(option.on)}
              className={`whitespace-nowrap transition-colors ${compressed === option.on ? 'text-ink underline decoration-[0.5px] underline-offset-[3px]' : 'hover:text-ink'}`}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}

      <ScaleBar />

      <span className="sr-only" aria-live="polite">Showing down to {LEVEL_NAMES[depth]?.toLowerCase()}.</span>
      {!following && mode !== 'reach' && <DepthMarks />}
      {!following && (
        <button onClick={() => getEngine()?.redraw()} className="pointer-events-auto hidden whitespace-nowrap text-[15px] leading-none transition-colors hover:text-ink motion-reduce:hidden min-[1100px]:block" title="Draw the chart again from the beginning, slowly (r)">
          Redraw
        </button>
      )}

      <div className="pointer-events-auto flex items-center gap-3 text-[18px] leading-none">
        <button onClick={() => getEngine()?.zoomBy(1 / 1.6)} className="px-0.5 transition-colors hover:text-ink" aria-label="Zoom out">−</button>
        <button onClick={() => getEngine()?.fit()} className="text-[15px] leading-none transition-colors hover:text-ink" aria-label="Fit everything" title="Fit everything and unfold (0)">Fit</button>
        <button onClick={() => getEngine()?.zoomBy(1.6)} className="px-0.5 transition-colors hover:text-ink" aria-label="Zoom in">+</button>
      </div>
    </div>
  )
}

