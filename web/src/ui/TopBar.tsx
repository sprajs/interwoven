import { motion } from 'motion/react'
import type { Mode } from '../engine/Engine.ts'
import { useApp } from '../store.ts'

const MODES: { id: Mode; label: string; hint: string }[] = [
  { id: 'threads', label: 'Threads', hint: 'Placed entries and their recorded connections' },
  { id: 'density', label: 'Density', hint: 'Where activity gathers in time' },
  { id: 'landmarks', label: 'Landmarks', hint: 'The most prominent entries alone' },
]

const TEXT_BUTTON = 'relative whitespace-nowrap pb-0.5 text-[15.5px] min-[760px]:text-[17px] leading-none transition-colors'

export function TopBar() {
  const title = useApp((s) => s.model?.title ?? '')
  const description = useApp((s) => s.model?.description ?? '')
  const mode = useApp((s) => s.mode)
  const setMode = useApp((s) => s.setMode)
  const labelsOpen = useApp((s) => s.labelsOpen)
  const setLabelsOpen = useApp((s) => s.setLabelsOpen)
  const setSearchOpen = useApp((s) => s.setSearchOpen)
  const labelCount = useApp((s) => s.activeLabels.size + s.hiddenKinds.size)
  const unplacedCount = useApp((s) => s.model?.unplaced.length ?? 0)
  const unplacedOpen = useApp((s) => s.unplacedOpen)
  const setUnplacedOpen = useApp((s) => s.setUnplacedOpen)

  return (
    <header className="pointer-events-none absolute inset-x-0 top-0 z-20 flex flex-wrap items-baseline gap-x-3 gap-y-2 px-[22px] pt-3.5 min-[760px]:gap-x-8 min-[760px]:px-14">
      <div className="flex basis-full items-baseline gap-3 min-[760px]:basis-auto">
        <h1 className="text-[27px] font-medium leading-none tracking-[-0.01em]">{title}</h1>
        <p className="caption hidden text-[15px] xl:block">{description}</p>
      </div>
      <div className="hidden flex-1 min-[760px]:block" />
      <nav className="pointer-events-auto flex items-baseline gap-3 min-[760px]:gap-5" aria-label="View">
        {MODES.map((m) => (
          <button
            key={m.id}
            title={m.hint}
            aria-pressed={mode === m.id}
            onClick={() => setMode(m.id)}
            className={`${TEXT_BUTTON} ${mode === m.id ? 'text-ink' : 'text-ink-3 hover:text-ink'}`}
          >
            {m.label}
            {mode === m.id && (
              <motion.span layoutId="mode-underline" className="absolute inset-x-0 -bottom-[3px] h-px bg-ink" transition={{ type: 'spring', stiffness: 500, damping: 40 }} />
            )}
          </button>
        ))}
      </nav>
      <span className="hidden h-3.5 w-px self-center bg-rule min-[760px]:block" aria-hidden />
      <button
        onClick={() => setLabelsOpen(!labelsOpen)}
        aria-expanded={labelsOpen}
        className={`${TEXT_BUTTON} pointer-events-auto ${labelsOpen || labelCount ? 'text-ink' : 'text-ink-3 hover:text-ink'}`}
      >
        Labels{labelCount > 0 ? ` (${labelCount})` : ''}
      </button>
      <button onClick={() => setSearchOpen(true)} className={`${TEXT_BUTTON} pointer-events-auto text-ink-3 hover:text-ink`} title="Search (⌘K)">
        Search
      </button>
      {unplacedCount > 0 && (
        <button onClick={() => setUnplacedOpen(!unplacedOpen)} aria-expanded={unplacedOpen}
          className={`${TEXT_BUTTON} pointer-events-auto ${unplacedOpen ? 'text-ink' : 'text-ink-3 hover:text-ink'}`}>
          Unplaced ({unplacedCount})
        </button>
      )}
    </header>
  )
}
