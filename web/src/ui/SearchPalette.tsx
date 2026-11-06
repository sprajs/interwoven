import { AnimatePresence, motion } from 'motion/react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { parseYearQuery, type YearQuery } from '../data/derive.ts'
import type { Model } from '../data/model.ts'
import { isPlacedNode, type TimelineEntry } from '../data/types.ts'
import { formatYear } from '../engine/time.ts'
import { focusEntry, getEngine, useApp } from '../store.ts'
import { EvidenceBadge, Mark } from './icons.tsx'

const MAX_RESULTS = 50
/** Past this many matches, lighting them on the chart says nothing. */
const HIGHLIGHT_LIMIT = 800

function score(model: Model, q: string): { node: TimelineEntry; score: number }[] {
  const scored: { node: TimelineEntry; score: number }[] = []
  for (const node of [...model.nodes, ...model.unplaced]) {
    const title = node.title.toLowerCase()
    let s = -1
    if (title === q) s = 100
    else if (title.startsWith(q)) s = 80
    else if (title.includes(` ${q}`)) s = 65
    else if (title.includes(q)) s = 50
    else if (isPlacedNode(node) && String(Math.round(node.year)) === q) s = 45
    else if (node.id.toLowerCase().includes(q)) s = 40
    else if (node.labels.some((l) => l.includes(q))) s = 30
    else if (node.regions.some((r) => r.toLowerCase().includes(q))) s = 25
    else if (node.summary.toLowerCase().includes(q)) s = 20
    if (s >= 0) scored.push({ node, score: s + (3 - node.level) })
  }
  return scored.sort((a, b) => b.score - a.score || a.node.title.localeCompare(b.node.title))
}

export function searchEntries(model: Model, query: string): TimelineEntry[] {
  const q = query.trim().toLowerCase()
  if (!q) return model.keyEntries.map((index) => model.nodes[index]!)
  return score(model, q).slice(0, MAX_RESULTS).map((s) => s.node)
}

const describeDate = (date: YearQuery): string => (date.kind === 'year' ? `Go to ${formatYear(date.year)}` : `Open ${formatYear(date.start)} to ${formatYear(date.end)}`)

/**
 * Search lives on the chart rather than over it: what you type lights the matches where they
 * are, and a typed year or period takes you there or opens it.
 */
export function SearchPalette() {
  const open = useApp((s) => s.searchOpen)
  const setOpen = useApp((s) => s.setSearchOpen)
  const model = useApp((s) => s.model)
  const setSearchHits = useApp((s) => s.setSearchHits)
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const listRef = useRef<HTMLUListElement>(null)

  const results = useMemo(() => (model && open ? searchEntries(model, query) : []), [model, query, open])
  const date = useMemo(() => parseYearQuery(query), [query])
  const offset = date ? 1 : 0

  useEffect(() => setActive(0), [query])
  useEffect(() => {
    if (open) setQuery('')
    else setSearchHits(null)
  }, [open, setSearchHits])
  useEffect(() => {
    if (!model || !open) return
    const q = query.trim().toLowerCase()
    if (!q) return setSearchHits(null)
    if (date?.kind === 'period') {
      const hits = new Set<number>()
      for (let i = 0; i < model.n; i++) {
        const y = model.nodes[i]!.year
        if (y >= date.start && y <= date.end) hits.add(i)
      }
      return setSearchHits(hits)
    }
    const hits = score(model, q).flatMap((h) => {
      const index = model.indexById.get(h.node.id)
      return index === undefined ? [] : [index]
    })
    setSearchHits(hits.length && hits.length <= HIGHLIGHT_LIMIT ? new Set(hits) : null)
  }, [model, query, open, date, setSearchHits])
  useEffect(() => {
    listRef.current?.querySelector(`[data-index="${active}"]`)?.scrollIntoView({ block: 'nearest' })
  }, [active])

  const goToDate = () => {
    const engine = getEngine()
    if (!date || !engine) return
    if (date.kind === 'period') engine.openPeriod(date.start, date.end)
    else {
      // A year on its own: enough room around it to see what was going on.
      const span = Math.max(4, Math.abs(2030 - date.year) * 0.06)
      engine.flyToYears(date.year - span, date.year + span)
    }
    setOpen(false)
  }

  const choose = (position: number) => {
    if (date && position === 0) return goToDate()
    const node = results[position - offset]
    if (!node) return
    setOpen(false)
    focusEntry(node.id)
  }

  const count = results.length + offset

  return (
    <AnimatePresence>
      {open && model && (
        <motion.div
          className="pointer-events-none absolute inset-x-0 top-14 z-40 flex justify-end px-6 compact:top-18 compact:px-18"
          initial={{ opacity: 0, y: -3 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -3 }}
          transition={{ duration: 0.12 }}
        >
          <div role="dialog" aria-label="Find on the chart" className="sheet pointer-events-auto w-full max-w-sm border border-rule">
            <input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'ArrowDown') {
                  e.preventDefault()
                  setActive((a) => Math.min(count - 1, a + 1))
                } else if (e.key === 'ArrowUp') {
                  e.preventDefault()
                  setActive((a) => Math.max(0, a - 1))
                } else if (e.key === 'Enter') {
                  choose(active)
                }
                // The chart's own keys should not fire while typing.
                e.stopPropagation()
                if (e.key === 'Escape') setOpen(false)
              }}
              placeholder="An entry, a place, 1850, 1600 to 1700"
              aria-label="Find"
              role="combobox"
              aria-expanded="true"
              aria-controls="search-results"
              className="w-full border-b border-rule bg-transparent px-4 py-2 text-lead text-ink outline-none placeholder:text-ink-3"
            />
            <ul id="search-results" ref={listRef} role="listbox" className="thin-scroll max-h-[46vh] overflow-y-auto py-1">
              {date && (
                <li role="option" aria-selected={active === 0} data-index={0}>
                  <button onClick={goToDate} onPointerMove={() => setActive(0)} className={`flex w-full items-baseline gap-3 px-4 py-1 text-left text-body ${active === 0 ? 'bg-tint' : ''}`}>
                    <span className="min-w-0 flex-1">{describeDate(date)}</span>
                    <span className="note shrink-0">return</span>
                  </button>
                </li>
              )}
              {!query.trim() && <li className="note px-4 pb-1 pt-1">Landmarks</li>}
              {results.map((node, k) => {
                const position = k + offset
                return (
                  <li key={node.id} role="option" aria-selected={position === active} data-index={position}>
                    <button onClick={() => choose(position)} onPointerMove={() => setActive(position)} className={`flex w-full items-baseline gap-2 px-4 py-px text-left text-body ${position === active ? 'bg-tint' : ''}`}>
                      <span className="grid w-2 shrink-0 translate-y-px place-items-center self-center">
                        <Mark kind={node.kind} strength={node.evidence_strength} color={model.labelById.get(node.labels[0] ?? '')?.ink} />
                      </span>
                      <span className={`min-w-0 flex-1 ${node.kind === 'science' ? 'science' : ''}`}>{node.title} <EvidenceBadge strength={node.evidence_strength} /></span>
                      <span className="note shrink-0">{isPlacedNode(node) ? node.date_kind && node.date_kind !== 'point' ? node.date_label : formatYear(node.year) : 'awaiting a date'}</span>
                    </button>
                  </li>
                )
              })}
              {results.length === 0 && !date && <li className="note px-4 py-2">Nothing matches “{query}”.</li>}
            </ul>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
