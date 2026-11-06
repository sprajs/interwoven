import { AnimatePresence, motion } from 'motion/react'
import { useEffect, useMemo, useRef, useState } from 'react'
import type { Model } from '../data/model.ts'
import { isPlacedNode, type TimelineEntry } from '../data/types.ts'
import { formatYear } from '../engine/time.ts'
import { focusEntry, useApp } from '../store.ts'
import { EvidenceBadge, Mark } from './icons.tsx'

const MAX_RESULTS = 50

export function searchEntries(model: Model, query: string): TimelineEntry[] {
  const q = query.trim().toLowerCase()
  if (!q) return model.landmarks.map((index) => model.nodes[index]!)
  const scored: { node: TimelineEntry; score: number }[] = []
  for (const node of [...model.nodes, ...model.unplaced]) {
    const title = node.title.toLowerCase()
    let score = -1
    if (title === q) score = 100
    else if (title.startsWith(q)) score = 80
    else if (title.includes(` ${q}`)) score = 65
    else if (title.includes(q)) score = 50
    else if (isPlacedNode(node) && String(Math.round(node.year)) === q) score = 45
    else if (node.id.toLowerCase().includes(q)) score = 40
    else if (node.labels.some((l) => l.includes(q))) score = 30
    else if (node.regions.some((r) => r.toLowerCase().includes(q))) score = 25
    else if (node.summary.toLowerCase().includes(q)) score = 20
    if (score >= 0) scored.push({ node, score: score + (3 - node.level) })
  }
  return scored
    .sort((a, b) => b.score - a.score || a.node.title.localeCompare(b.node.title))
    .slice(0, MAX_RESULTS)
    .map((result) => result.node)
}

export function SearchPalette() {
  const open = useApp((s) => s.searchOpen)
  const setOpen = useApp((s) => s.setSearchOpen)
  const model = useApp((s) => s.model)
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const listRef = useRef<HTMLUListElement>(null)

  const results = useMemo(() => (model && open ? searchEntries(model, query) : []), [model, query, open])

  useEffect(() => setActive(0), [query])
  useEffect(() => {
    if (open) setQuery('')
  }, [open])
  useEffect(() => {
    listRef.current?.querySelector(`[data-index="${active}"]`)?.scrollIntoView({ block: 'nearest' })
  }, [active])

  const choose = (node: TimelineEntry | undefined) => {
    if (!node) return
    setOpen(false)
    focusEntry(node.id)
  }

  return (
    <AnimatePresence>
      {open && model && (
        <motion.div
          className="absolute inset-0 z-50 flex items-start justify-center bg-[rgb(244_239_230/0.72)] px-4 pt-[13vh]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.12 }}
          onPointerDown={(e) => {
            if (e.target === e.currentTarget) setOpen(false)
          }}
        >
          <div role="dialog" aria-label="Search entries" className="sheet w-full max-w-[34rem] border border-rule">
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
              placeholder="Search for an entry, a place, a label or a year"
              aria-label="Search"
              role="combobox"
              aria-expanded="true"
              aria-controls="search-results"
              className="w-full border-b border-rule bg-transparent px-5 py-3.5 text-[21px] text-ink outline-none focus-visible:outline-none placeholder:italic placeholder:text-ink-3"
            />
            <ul id="search-results" ref={listRef} role="listbox" className="thin-scroll max-h-[48vh] overflow-y-auto py-1">
              {!query.trim() && <li className="px-5 pb-1 pt-2 text-[15px] italic text-ink-3">Landmarks</li>}
              {results.map((node, position) => {
                return (
                  <li key={node.id} role="option" aria-selected={position === active} data-index={position}>
                    <button
                      onClick={() => choose(node)}
                      onPointerMove={() => setActive(position)}
                      className={`flex w-full items-baseline gap-3 px-5 py-1.5 text-left text-[17px] leading-tight ${position === active ? 'bg-ink/[0.06]' : ''}`}
                    >
                      <span className="grid w-2.5 shrink-0 translate-y-[1px] place-items-center self-center">
                        <Mark kind={node.kind} strength={node.evidence_strength} size={9} color={model.labelById.get(node.labels[0] ?? '')?.ink} />
                      </span>
                      <span className={`min-w-0 flex-1 ${node.kind === 'science' ? 'italic' : ''}`}>{node.title} <EvidenceBadge strength={node.evidence_strength} /></span>
                      <span className="shrink-0 text-[15px] text-ink-3">{isPlacedNode(node) ? node.date_kind && node.date_kind !== 'point' ? node.date_label : formatYear(node.year) : 'Unplaced'}</span>
                    </button>
                  </li>
                )
              })}
              {results.length === 0 && <li className="px-5 py-5 text-[16px] italic text-ink-3">Nothing matches “{query}”.</li>}
            </ul>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
