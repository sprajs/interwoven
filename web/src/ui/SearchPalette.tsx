import { AnimatePresence, motion } from 'motion/react'
import { useEffect, useMemo, useRef, useState } from 'react'
import type { Model } from '../data/model.ts'
import { formatYear } from '../engine/time.ts'
import { focusNode, useApp } from '../store.ts'
import { Icon, ShapeIcon } from './icons.tsx'

const MAX_RESULTS = 40

export function searchNodes(model: Model, query: string): number[] {
  const q = query.trim().toLowerCase()
  if (!q) return [...model.stepChanges]
  const scored: { i: number; score: number }[] = []
  for (let i = 0; i < model.n; i++) {
    const node = model.nodes[i]!
    const title = node.title.toLowerCase()
    let score = -1
    if (title === q) score = 100
    else if (title.startsWith(q)) score = 80
    else if (title.includes(` ${q}`)) score = 65
    else if (title.includes(q)) score = 50
    else if (String(node.year) === q) score = 45
    else if (node.labels.some((l) => l.includes(q))) score = 30
    else if (node.summary.toLowerCase().includes(q)) score = 20
    if (score >= 0) scored.push({ i, score: score + (3 - node.level) })
  }
  return scored
    .sort((a, b) => b.score - a.score || model.nodes[a.i]!.year - model.nodes[b.i]!.year)
    .slice(0, MAX_RESULTS)
    .map((s) => s.i)
}

export function SearchPalette() {
  const open = useApp((s) => s.searchOpen)
  const setOpen = useApp((s) => s.setSearchOpen)
  const model = useApp((s) => s.model)
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const listRef = useRef<HTMLUListElement>(null)

  const results = useMemo(() => (model && open ? searchNodes(model, query) : []), [model, query, open])

  useEffect(() => setActive(0), [query])
  useEffect(() => {
    if (open) setQuery('')
  }, [open])
  useEffect(() => {
    listRef.current?.querySelector(`[data-index="${active}"]`)?.scrollIntoView({ block: 'nearest' })
  }, [active])

  const choose = (i: number | undefined) => {
    if (i === undefined) return
    setOpen(false)
    focusNode(i)
  }

  return (
    <AnimatePresence>
      {open && model && (
        <motion.div
          className="absolute inset-0 z-50 flex items-start justify-center bg-black/40 px-4 pt-[14vh]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.12 }}
          onPointerDown={(e) => {
            if (e.target === e.currentTarget) setOpen(false)
          }}
        >
          <motion.div
            role="dialog"
            aria-label="Search the timeline"
            className="glass w-full max-w-xl overflow-hidden rounded-2xl"
            initial={{ y: -10, scale: 0.985 }}
            animate={{ y: 0, scale: 1 }}
            exit={{ y: -6, scale: 0.99 }}
            transition={{ type: 'spring', stiffness: 520, damping: 38 }}
          >
            <div className="flex items-center gap-3 border-b border-white/8 px-4 text-ink-2">
              <Icon name="search" />
              <input
                autoFocus
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'ArrowDown') {
                    e.preventDefault()
                    setActive((a) => Math.min(results.length - 1, a + 1))
                  } else if (e.key === 'ArrowUp') {
                    e.preventDefault()
                    setActive((a) => Math.max(0, a - 1))
                  } else if (e.key === 'Enter') {
                    choose(results[active])
                  }
                }}
                placeholder="Search technologies, science, labels or a year"
                aria-label="Search"
                role="combobox"
                aria-expanded="true"
                aria-controls="search-results"
                className="h-13 w-full bg-transparent text-[15px] text-ink outline-none placeholder:text-ink-3"
              />
            </div>
            <ul id="search-results" ref={listRef} role="listbox" className="thin-scroll max-h-[46vh] overflow-y-auto p-1.5">
              {!query.trim() && <li className="px-3 pb-1 pt-2 text-[11px] font-medium text-ink-3">Step changes</li>}
              {results.map((i, position) => {
                const node = model.nodes[i]!
                const lane = model.lanes[model.domainIndex[i]!]!
                return (
                  <li key={i} role="option" aria-selected={position === active} data-index={position}>
                    <button
                      onClick={() => choose(i)}
                      onPointerMove={() => setActive(position)}
                      className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left ${position === active ? 'bg-white/9' : ''}`}
                    >
                      <ShapeIcon type={node.type} color={lane.color} size={12} />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-[13.5px] text-ink">{node.title}</span>
                        <span className="block truncate text-xs text-ink-2">{lane.label}</span>
                      </span>
                      <span className="font-mono text-[11px] text-ink-2">{formatYear(node.year)}</span>
                    </button>
                  </li>
                )
              })}
              {results.length === 0 && <li className="px-3 py-6 text-center text-[13px] text-ink-2">No entries match “{query}”.</li>}
            </ul>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
