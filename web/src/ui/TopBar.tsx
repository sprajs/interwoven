import { motion } from 'motion/react'
import type { Mode } from '../engine/Engine.ts'
import { useApp } from '../store.ts'
import { ViewGlyph } from './ViewGlyph.tsx'

const MODES: { id: Mode; label: string; hint: string }[] = [
  { id: 'threads', label: 'Threads', hint: 'Every entry and how each builds on the last (1)' },
  { id: 'story', label: 'Stories', hint: 'One thread at a time, as something to read (2)' },
  { id: 'reach', label: 'Reach', hint: 'How long each entry went on being built on, and what is documented about its end (3)' },
  { id: 'density', label: 'Density', hint: 'Where activity gathers in time (4)' },
  { id: 'landmarks', label: 'Landmarks', hint: 'The most prominent entries alone (5)' },
]

const TEXT_BUTTON = 'relative whitespace-nowrap pb-0.5 text-[15.5px] min-[760px]:text-[17px] leading-none transition-colors'

export function TopBar() {
  const model = useApp((s) => s.model)
  const title = model?.title ?? ''
  const description = model?.description ?? ''
  const mode = useApp((s) => s.mode)
  const setMode = useApp((s) => s.setMode)
  const labelsOpen = useApp((s) => s.labelsOpen)
  const setLabelsOpen = useApp((s) => s.setLabelsOpen)
  const setSearchOpen = useApp((s) => s.setSearchOpen)
  const searchOpen = useApp((s) => s.searchOpen)
  const labelCount = useApp((s) => s.activeLabels.size + s.hiddenKinds.size)

  return (
    <header className="pointer-events-none absolute inset-x-0 top-0 z-20 flex flex-wrap items-end gap-x-3 gap-y-1 px-[22px] pt-2.5 min-[760px]:flex-nowrap min-[760px]:gap-x-7 min-[760px]:px-14">
      <div className="flex basis-full items-baseline gap-3 min-[760px]:basis-auto min-[760px]:self-center">
        <h1 className="text-[27px] font-medium leading-none tracking-[-0.01em]">{title}</h1>
        <p className="caption hidden text-[15px] 2xl:block">{description}</p>
      </div>
      <div className="hidden flex-1 min-[760px]:block" />
      <nav className="pointer-events-auto flex items-end gap-[14px] min-[900px]:gap-5" aria-label="View">
        {MODES.map((m) => {
          const active = mode === m.id
          return (
            <button key={m.id} title={m.hint} aria-pressed={active} onClick={() => setMode(m.id)} className={`group relative flex flex-col items-start gap-[3px] pb-[3px] transition-colors ${active ? 'text-ink' : 'text-ink-3 hover:text-ink'}`}>
              <span className={`hidden transition-opacity min-[900px]:block ${active ? 'opacity-100' : 'opacity-55 group-hover:opacity-100'}`}>
                <ViewGlyph model={model} mode={m.id} />
              </span>
              <span className="whitespace-nowrap text-[15.5px] leading-none min-[760px]:text-[16.5px]">{m.label}</span>
              {active && <motion.span layoutId="mode-underline" className="absolute inset-x-0 bottom-0 h-px bg-ink" transition={{ type: 'spring', stiffness: 500, damping: 40 }} />}
            </button>
          )
        })}
      </nav>
      <span className="mb-[3px] hidden h-8 w-px bg-rule min-[760px]:block" aria-hidden />
      <div className="pointer-events-auto ml-auto flex items-end gap-4 min-[760px]:ml-0 min-[760px]:gap-5">
        <button onClick={() => setLabelsOpen(!labelsOpen)} aria-expanded={labelsOpen} className={`${TEXT_BUTTON} pb-[3px] ${labelsOpen || labelCount ? 'text-ink' : 'text-ink-3 hover:text-ink'}`} title="Follow labels through the chart (l)">
          Labels{labelCount > 0 ? ` (${labelCount})` : ''}
        </button>
        <button onClick={() => setSearchOpen(!searchOpen)} aria-expanded={searchOpen} className={`${TEXT_BUTTON} pb-[3px] ${searchOpen ? 'text-ink' : 'text-ink-3 hover:text-ink'}`} title="Find an entry, a year or a period (/)">
          Find
        </button>
      </div>
    </header>
  )
}
