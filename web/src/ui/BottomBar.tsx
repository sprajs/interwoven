import { LEVEL_NAMES } from '../data/types.ts'
import { getEngine, useApp } from '../store.ts'
import { Mark } from './icons.tsx'

const SMALL = 'text-[15px] leading-none transition-colors'

function RangeMark() {
  return (
    <svg width="20" height="8" viewBox="0 0 20 8" aria-hidden>
      <path d="M1 1v6M19 1v6M1 4h18" stroke="currentColor" strokeWidth="0.9" fill="none" />
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

/** The key to the marks, the current depth and the view controls, under the chart. */
export function BottomBar() {
  const depth = useApp((s) => s.depth)
  const compressed = useApp((s) => s.compressed)
  const setCompressed = useApp((s) => s.setCompressed)

  return (
    <div className="pointer-events-none absolute inset-x-[22px] bottom-[50px] z-10 flex items-center gap-5 text-ink-3 min-[760px]:inset-x-14">
      <ul className="hidden items-center gap-4 text-[14.5px] lg:flex" aria-label="Key">
        <li className="flex items-center gap-1.5"><Mark kind="technology" size={8} />Technology</li>
        <li className="flex items-center gap-1.5 italic"><Mark kind="science" size={9} />Science</li>
        <li className="flex items-center gap-1.5"><RangeMark />Date range</li>
        <li className="flex items-center gap-1.5"><BrokenMark />Link awaiting review</li>
      </ul>

      <div className="flex-1" />

      <p className="hidden text-[14.5px] italic sm:block" aria-live="polite">
        Showing down to {LEVEL_NAMES[depth]?.toLowerCase()}
        {depth < 3 ? '. Zoom in for more.' : '.'}
      </p>

      <div className="pointer-events-auto flex items-center gap-2" role="group" aria-label="Time scale">
        {[
          { on: true, label: 'Compressed', hint: 'Recent centuries get more room' },
          { on: false, label: 'Linear', hint: 'Every year is the same width' },
        ].map((option) => (
          <button
            key={option.label}
            title={option.hint}
            aria-pressed={compressed === option.on}
            onClick={() => setCompressed(option.on)}
            className={`${SMALL} ${compressed === option.on ? 'text-ink underline decoration-[0.5px] underline-offset-[3px]' : 'hover:text-ink'}`}
          >
            {option.label}
          </button>
        ))}
      </div>

      <div className="pointer-events-auto flex items-center gap-3 text-[18px] leading-none">
        <button onClick={() => getEngine()?.zoomBy(1 / 1.6)} className="px-0.5 transition-colors hover:text-ink" aria-label="Zoom out">−</button>
        <button onClick={() => getEngine()?.fit()} className={`${SMALL} hover:text-ink`} aria-label="Fit everything">Fit</button>
        <button onClick={() => getEngine()?.zoomBy(1.6)} className="px-0.5 transition-colors hover:text-ink" aria-label="Zoom in">+</button>
      </div>
    </div>
  )
}
