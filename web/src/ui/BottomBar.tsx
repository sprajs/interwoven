import { LEVEL_NAMES, NODE_TYPES } from '../data/types.ts'
import { getEngine, useApp } from '../store.ts'
import { Icon, ShapeIcon } from './icons.tsx'

/** Shape legend, semantic-depth readout and view controls, just above the overview. */
export function BottomBar() {
  const depth = useApp((s) => s.depth)
  const compressed = useApp((s) => s.compressed)
  const setCompressed = useApp((s) => s.setCompressed)

  return (
    <div className="pointer-events-none absolute inset-x-3 bottom-[4.65rem] z-20 flex items-center gap-3 sm:inset-x-4">
      <ul className="hidden items-center gap-3 lg:flex" aria-label="Node types">
        {NODE_TYPES.map((t) => (
          <li key={t.id} className="flex items-center gap-1.5 text-[11.5px] text-ink-2">
            <ShapeIcon type={t.id} color="#aab6cc" size={10} />
            {t.label}
          </li>
        ))}
      </ul>

      <div className="flex-1" />

      <div
        className="hidden items-center gap-2 text-[11.5px] text-ink-2 sm:flex"
        title="Zoom in to reveal deeper levels"
        aria-label={`Showing down to ${LEVEL_NAMES[depth]}`}
      >
        <span className="flex gap-1" aria-hidden>
          {LEVEL_NAMES.map((_, i) => (
            <span key={i} className={`h-1 w-3.5 rounded-full transition-colors duration-300 ${i <= depth ? 'bg-accent' : 'bg-white/14'}`} />
          ))}
        </span>
        <span className="w-[6.8rem]">{LEVEL_NAMES[depth]}</span>
      </div>

      <div className="glass pointer-events-auto flex rounded-full p-0.5 text-xs" role="group" aria-label="Time scale">
        {[
          { on: true, label: 'Compressed', hint: 'Recent centuries get more room' },
          { on: false, label: 'Linear', hint: 'Every year is the same width' },
        ].map((option) => (
          <button
            key={option.label}
            title={option.hint}
            aria-pressed={compressed === option.on}
            onClick={() => setCompressed(option.on)}
            className={`rounded-full px-2.5 py-1 transition-colors ${compressed === option.on ? 'bg-white/12 text-ink' : 'text-ink-2 hover:text-ink'}`}
          >
            {option.label}
          </button>
        ))}
      </div>

      <div className="glass pointer-events-auto flex rounded-full p-0.5 text-ink-2">
        <button onClick={() => getEngine()?.zoomBy(1 / 1.6)} className="rounded-full p-1.5 hover:bg-white/8 hover:text-ink" aria-label="Zoom out">
          <Icon name="minus" size={14} />
        </button>
        <button onClick={() => getEngine()?.fit()} className="rounded-full p-1.5 hover:bg-white/8 hover:text-ink" aria-label="Fit everything">
          <Icon name="fit" size={14} />
        </button>
        <button onClick={() => getEngine()?.zoomBy(1.6)} className="rounded-full p-1.5 hover:bg-white/8 hover:text-ink" aria-label="Zoom in">
          <Icon name="plus" size={14} />
        </button>
      </div>
    </div>
  )
}
