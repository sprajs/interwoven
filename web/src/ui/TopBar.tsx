import { motion } from 'motion/react'
import type { Mode } from '../engine/Engine.ts'
import { isFilterActive, useApp } from '../store.ts'
import { Icon } from './icons.tsx'

const MODES: { id: Mode; label: string; hint: string }[] = [
  { id: 'network', label: 'Network', hint: 'Nodes and how they connect' },
  { id: 'density', label: 'Density', hint: 'Where activity concentrates in time' },
  { id: 'steps', label: 'Step changes', hint: 'The advances that reshaped what followed' },
]

export function TopBar() {
  const title = useApp((s) => s.model?.title ?? '')
  const mode = useApp((s) => s.mode)
  const setMode = useApp((s) => s.setMode)
  const filtersOpen = useApp((s) => s.filtersOpen)
  const setFiltersOpen = useApp((s) => s.setFiltersOpen)
  const setSearchOpen = useApp((s) => s.setSearchOpen)
  const filterCount = useApp((s) => (isFilterActive(s) ? s.hiddenDomains.size + s.hiddenTypes.size + s.activeLabels.size : 0))

  return (
    <header className="pointer-events-none absolute inset-x-0 top-0 z-20 flex items-center gap-2 px-3 pt-3 sm:gap-3 sm:px-4">
      <div className="hidden min-w-0 items-center gap-2 pl-1 pr-2 md:flex">
        <svg width="20" height="20" viewBox="0 0 32 32" fill="none" aria-hidden>
          <path d="M3 23C12 23 12 9 20 9h9M3 9c9 0 9 14 17 14h9" stroke="#8db4ff" strokeWidth="2.6" strokeLinecap="round" />
        </svg>
        <span className="truncate text-[15px] font-semibold tracking-tight">{title}</span>
      </div>

      <nav className="glass pointer-events-auto flex rounded-full p-1" aria-label="View mode">
        {MODES.map((m) => (
          <button
            key={m.id}
            title={m.hint}
            aria-pressed={mode === m.id}
            onClick={() => setMode(m.id)}
            className={`relative whitespace-nowrap rounded-full px-2.5 py-1.5 text-[13px] font-medium transition-colors sm:px-3.5 ${mode === m.id ? 'text-ink' : 'text-ink-2 hover:text-ink'}`}
          >
            {mode === m.id && (
              <motion.span
                layoutId="mode-pill"
                className="absolute inset-0 rounded-full bg-white/12 shadow-[inset_0_1px_0_rgb(255_255_255/0.12)]"
                transition={{ type: 'spring', stiffness: 480, damping: 38 }}
              />
            )}
            <span className="relative">{m.label}</span>
          </button>
        ))}
      </nav>

      <div className="flex-1" />

      <button
        onClick={() => setFiltersOpen(!filtersOpen)}
        aria-expanded={filtersOpen}
        className={`glass pointer-events-auto flex h-10 items-center gap-2 rounded-full px-3 text-[13px] font-medium transition-colors hover:text-ink sm:px-3.5 ${filtersOpen || filterCount ? 'text-ink' : 'text-ink-2'}`}
      >
        <Icon name="filter" />
        <span className="hidden sm:inline">Filters</span>
        {filterCount > 0 && <span className="rounded-full bg-accent/25 px-1.5 font-mono text-[11px] text-ink">{filterCount}</span>}
      </button>

      <button
        onClick={() => setSearchOpen(true)}
        className="glass pointer-events-auto flex h-10 items-center gap-2 rounded-full px-3 text-[13px] text-ink-2 transition-colors hover:text-ink sm:w-52 sm:px-3.5"
        aria-label="Search"
      >
        <Icon name="search" />
        <span className="hidden flex-1 text-left sm:inline">Search</span>
        <kbd className="hidden rounded bg-white/8 px-1.5 py-0.5 font-mono text-[10.5px] text-ink-2 sm:inline">⌘K</kbd>
      </button>
    </header>
  )
}
