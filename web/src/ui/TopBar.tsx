import { motion } from 'motion/react'
import type { Mode } from '../engine/Engine.ts'
import { useApp } from '../store.ts'
import { BrokenMark, LooseMark, Mark, MARK_SIZE, RangeMark } from './icons.tsx'
import { ViewGlyph } from './ViewGlyph.tsx'

const MODES: { id: Mode; label: string; hint: string }[] = [
  { id: 'threads', label: 'Threads', hint: 'Every placed entry and how each builds on the last (1)' },
  { id: 'story', label: 'Stories', hint: 'One thread at a time, as something to read (2)' },
  { id: 'reach', label: 'Reach', hint: 'How long each entry went on being built on, and what is documented about its end (3)' },
  { id: 'density', label: 'Density', hint: 'Where activity gathers in time (4)' },
  { id: 'landmarks', label: 'Landmarks', hint: 'The most prominent entries alone (5)' },
]

/** What the marks mean, set small under the name of the chart. */
function Key({ loose }: { loose: boolean }) {
  return (
    <ul className="note hidden items-center gap-3 whitespace-nowrap corner:flex" aria-label="Key">
      <li className="flex items-center gap-1"><Mark kind="technology" size={MARK_SIZE.note} />technology</li>
      <li className="science flex items-center gap-1"><Mark kind="science" size={MARK_SIZE.note} />science</li>
      <li className="flex items-center gap-1"><RangeMark />date range</li>
      <li className="flex items-center gap-1"><BrokenMark />awaiting review</li>
      <li className="flex items-center gap-1" title="An awareness proxy: a publication or similar stands in for when people could have known of it"><Mark kind="science" strength="awareness_proxy" size={MARK_SIZE.note} />proxy</li>
      <li className="flex items-center gap-1" title="A scoped inference: use or availability inferred from the stated context"><Mark kind="science" strength="scoped_inference" size={MARK_SIZE.note} />inferred</li>
      <li title="A date that limits one side only: known by this date, or not before it. The other end is unknown.">← by, not before →</li>
      {loose && <li className="flex items-center gap-1"><LooseMark />linked to an entry not yet placed</li>}
    </ul>
  )
}

export function TopBar() {
  const model = useApp((s) => s.model)
  const mode = useApp((s) => s.mode)
  const setMode = useApp((s) => s.setMode)
  const labelsOpen = useApp((s) => s.labelsOpen)
  const setLabelsOpen = useApp((s) => s.setLabelsOpen)
  const setSearchOpen = useApp((s) => s.setSearchOpen)
  const searchOpen = useApp((s) => s.searchOpen)
  const labelCount = useApp((s) => s.activeLabels.size + s.hiddenKinds.size)
  const plain = 'whitespace-nowrap pb-1 text-body transition-colors'

  return (
    <header className="pointer-events-none absolute inset-x-0 top-0 z-20 flex flex-wrap items-end gap-x-4 px-6 pt-2 compact:flex-nowrap compact:gap-x-8 compact:px-18">
      <div className="flex-1 compact:flex-none compact:self-start">
        <h1 className="text-title">{model?.title}</h1>
        <div className="-mt-1 pointer-events-auto"><Key loose={(model?.unplaced.length ?? 0) > 0} /></div>
      </div>
      <div className="hidden flex-1 compact:block" />
      <nav className="pointer-events-auto order-last flex basis-full items-end gap-4 compact:order-none compact:basis-auto wide:gap-6" aria-label="View">
        {MODES.map((m) => {
          const active = mode === m.id
          return (
            <button key={m.id} title={m.hint} aria-pressed={active} onClick={() => setMode(m.id)} className={`group relative flex flex-col items-start gap-1 pb-1 transition-colors ${active ? 'text-ink' : 'text-ink-3 hover:text-ink'}`}>
              <span className={`hidden transition-opacity wide:block ${active ? 'opacity-100' : 'opacity-50 group-hover:opacity-100'}`}>
                <ViewGlyph model={model} mode={m.id} />
              </span>
              <span className="whitespace-nowrap text-body">{m.label}</span>
              {active && <motion.span layoutId="mode-underline" className="absolute inset-x-0 bottom-0 h-px bg-ink" transition={{ type: 'spring', stiffness: 500, damping: 40 }} />}
            </button>
          )
        })}
      </nav>
      <span className="mb-1 hidden h-12 w-px bg-rule compact:block" aria-hidden />
      <div className="pointer-events-auto flex items-end gap-6">
        <button onClick={() => setLabelsOpen(!labelsOpen)} aria-expanded={labelsOpen} className={`${plain} ${labelsOpen || labelCount ? 'text-ink' : 'text-ink-3 hover:text-ink'}`} title="Follow labels through the chart (l)">
          Labels{labelCount > 0 ? ` (${labelCount})` : ''}
        </button>
        <button onClick={() => setSearchOpen(!searchOpen)} aria-expanded={searchOpen} className={`${plain} ${searchOpen ? 'text-ink' : 'text-ink-3 hover:text-ink'}`} title="Find an entry, a year or a period (/)">
          Find
        </button>
      </div>
    </header>
  )
}
