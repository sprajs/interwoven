import { AnimatePresence, motion } from 'motion/react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { parseYearQuery, type YearQuery } from '../data/derive.ts'
import type { Model } from '../data/model.ts'
import { formatYear } from '../engine/time.ts'
import { focusNode, getEngine, useApp } from '../store.ts'
import { Mark } from './icons.tsx'

const MAX_RESULTS = 50
/** Past this many matches, lighting them on the chart says nothing. */
const HIGHLIGHT_LIMIT = 800

function score(model: Model, q: string): { i: number; score: number }[] {
  const scored: { i: number; score: number }[] = []
  for (let i = 0; i < model.n; i++) {
    const node = model.nodes[i]!
    const title = node.title.toLowerCase()
    let s = -1
    if (title === q) s = 100
    else if (title.startsWith(q)) s = 80
    else if (title.includes(` ${q}`)) s = 65
    else if (title.includes(q)) s = 50
    else if (String(Math.round(node.year)) === q) s = 45
    else if (node.labels.some((l) => l.includes(q))) s = 30
    else if (node.regions.some((r) => r.toLowerCase().includes(q))) s = 25
    else if (node.summary.toLowerCase().includes(q)) s = 20
    if (s >= 0) scored.push({ i, score: s + (3 - node.level) })
  }
  return scored.sort((a, b) => b.score - a.score || model.nodes[a.i]!.year - model.nodes[b.i]!.year)
}

export function searchNodes(model: Model, query: string): number[] {
  const q = query.trim().toLowerCase()
  if (!q) return [...model.landmarks]
  return score(model, q).slice(0, MAX_RESULTS).map((s) => s.i)
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

  const results = useMemo(() => (model && open ? searchNodes(model, query) : []), [model, query, open])
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
    const hits = score(model, q)
    setSearchHits(hits.length && hits.length <= HIGHLIGHT_LIMIT ? new Set(hits.map((h) => h.i)) : null)
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
    const i = results[position - offset]
    if (i === undefined) return
    setOpen(false)
    focusNode(i)
  }

  const count = results.length + offset

  return (
    <AnimatePresence>
      {open && model && (
        <motion.div
          className="pointer-events-none absolute inset-x-0 top-[54px] z-40 flex justify-end px-[22px] min-[760px]:top-[52px] min-[760px]:px-14"
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.12 }}
        >
          <div role="dialog" aria-label="Find on the chart" className="sheet pointer-events-auto w-full max-w-[25rem] border border-rule">
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
              placeholder="An entry, a place, a label, 1850 or 1600 to 1700"
              aria-label="Find"
              role="combobox"
              aria-expanded="true"
              aria-controls="search-results"
              className="w-full border-b border-rule bg-transparent px-4 py-2.5 text-[18px] text-ink outline-none focus-visible:outline-none placeholder:italic placeholder:text-ink-3"
            />
            <ul id="search-results" ref={listRef} role="listbox" className="thin-scroll max-h-[46vh] overflow-y-auto py-1">
              {date && (
                <li role="option" aria-selected={active === 0} data-index={0}>
                  <button onClick={goToDate} onPointerMove={() => setActive(0)} className={`flex w-full items-baseline gap-3 px-4 py-1.5 text-left text-[16.5px] italic leading-tight ${active === 0 ? 'bg-ink/[0.06]' : ''}`}>
                    <span className="min-w-0 flex-1">{describeDate(date)}</span>
                    <span className="shrink-0 text-[14px] not-italic text-ink-3">return</span>
                  </button>
                </li>
              )}
              {!query.trim() && <li className="px-4 pb-1 pt-1.5 text-[14.5px] italic text-ink-3">Landmarks</li>}
              {results.map((i, k) => {
                const position = k + offset
                const node = model.nodes[i]!
                return (
                  <li key={i} role="option" aria-selected={position === active} data-index={position}>
                    <button onClick={() => choose(position)} onPointerMove={() => setActive(position)} className={`flex w-full items-baseline gap-3 px-4 py-1 text-left text-[16.5px] leading-tight ${position === active ? 'bg-ink/[0.06]' : ''}`}>
                      <span className="grid w-2.5 shrink-0 translate-y-[1px] place-items-center self-center">
                        <Mark kind={node.kind} size={9} color={`rgb(${model.ink[i * 3]! * 255} ${model.ink[i * 3 + 1]! * 255} ${model.ink[i * 3 + 2]! * 255})`} />
                      </span>
                      <span className={`min-w-0 flex-1 ${node.kind === 'science' ? 'italic' : ''}`}>{node.title}</span>
                      <span className="shrink-0 text-[14.5px] text-ink-3">{formatYear(node.year)}</span>
                    </button>
                  </li>
                )
              })}
              {results.length === 0 && !date && <li className="px-4 py-3 text-[15.5px] italic text-ink-3">Nothing matches “{query}”.</li>}
            </ul>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
