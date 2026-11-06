import { AnimatePresence, motion } from 'motion/react'
import { useMemo, useState } from 'react'
import type { RawUnplacedNode } from '../data/types.ts'
import { LAYOUT } from '../design.ts'
import { focusEntry, useApp } from '../store.ts'
import { CloseButton, Mark, MARK_SIZE } from './icons.tsx'

interface Group {
  id: string
  name: string
  ink: string | undefined
  entries: RawUnplacedNode[]
}

/**
 * The research that has no date to stand on yet, set like the index at the back of a book.
 * It rises from the bottom of the sheet so the chart stays in view, and pointing at an entry
 * lights what it is already linked to on the chart.
 */
export function UnplacedPanel() {
  const open = useApp((s) => s.unplacedOpen)
  const model = useApp((s) => s.model)
  const setOpen = useApp((s) => s.setUnplacedOpen)
  const setSearchHits = useApp((s) => s.setSearchHits)
  const [query, setQuery] = useState('')
  const needle = query.trim().toLowerCase()

  const groups = useMemo(() => {
    if (!model) return []
    const byLabel = new Map<string, Group>()
    for (const entry of model.unplaced) {
      if (needle && !`${entry.title} ${entry.summary} ${entry.placement_reason} ${entry.labels.join(' ')}`.toLowerCase().includes(needle)) continue
      const id = entry.labels[0] ?? 'none'
      const label = model.labelById.get(id)
      let group = byLabel.get(id)
      if (!group) {
        group = { id, name: label?.name ?? 'No label yet', ink: label?.ink, entries: [] }
        byLabel.set(id, group)
      }
      group.entries.push(entry)
    }
    const out = [...byLabel.values()]
    for (const group of out) group.entries.sort((a, b) => a.title.localeCompare(b.title))
    return out.sort((a, b) => a.name.localeCompare(b.name))
  }, [model, needle])

  const reasons = useMemo(() => {
    const counts = { researching: 0, unknown: 0, open: 0 }
    for (const entry of model?.unplaced ?? []) {
      if (entry.anchor_status === 'unknown') counts.unknown++
      else if (entry.anchor_status === 'selected') counts.open++
      else counts.researching++
    }
    return counts
  }, [model])

  const shown = groups.reduce((sum, group) => sum + group.entries.length, 0)

  const linkedHits = (id: string) => {
    if (!model) return null
    const hits = new Set<number>()
    for (const link of model.links) {
      const other = link.from === id ? link.to : link.to === id ? link.from : null
      const index = other === null ? undefined : model.indexById.get(other)
      if (index !== undefined) hits.add(index)
    }
    return hits.size ? hits : null
  }

  return (
    <AnimatePresence>
      {open && model && (
        <motion.aside
          initial={{ y: '100%' }}
          animate={{ y: 0 }}
          exit={{ y: '100%' }}
          transition={{ duration: 0.3, ease: [0.2, 0.7, 0.2, 1] }}
          className="sheet thin-scroll absolute inset-x-0 bottom-0 z-30 h-[56vh] select-text overflow-y-auto border-t border-rule px-6 pb-8 pt-4 compact:px-18"
          aria-label="Entries awaiting a date"
        >
          <div className="flex flex-wrap items-baseline gap-x-8 gap-y-2">
            <h2 className="text-head">Awaiting a date</h2>
            <div className="order-1 ml-auto compact:order-3 compact:ml-0">
              <CloseButton onClick={() => setOpen(false)} label="Close" />
            </div>
            <p className="note order-2 min-w-0 basis-full compact:order-1 compact:flex-1 compact:basis-0">
              These {model.unplaced.length} entries are in the research, but none has a researched date to stand on yet, so the chart does not guess one: {reasons.researching} not yet researched, {reasons.unknown} researched and still unknown, {reasons.open} with a date open at one end. Each moves onto the chart when its date is settled.
            </p>
            <input value={query} onChange={(event) => setQuery(event.target.value)} aria-label="Filter entries awaiting a date" placeholder="Filter" className="order-3 w-full border-b border-rule bg-transparent text-body outline-none placeholder:text-ink-3 compact:order-2 compact:w-48" />
          </div>

          <div className="mt-6 gap-8" style={{ columnWidth: LAYOUT.column }}>
            {groups.map((group) => (
              <section key={group.id} className="mb-6 break-inside-avoid-column">
                <h3 className="flex items-baseline gap-2 border-b border-rule pb-1 text-note font-medium text-ink-2">
                  <span className="size-2 shrink-0 self-center rounded-full" style={{ background: group.ink }} />
                  {group.name}
                  <span className="figures ml-auto font-normal text-ink-3">{group.entries.length}</span>
                </h3>
                <ul className="mt-1">
                  {group.entries.map((entry) => (
                    <li key={entry.id}>
                      <button
                        onClick={() => focusEntry(entry.id)}
                        onPointerEnter={(e) => e.pointerType === 'mouse' && setSearchHits(linkedHits(entry.id))}
                        onPointerLeave={() => setSearchHits(null)}
                        title={entry.placement_reason}
                        className="group flex w-full items-baseline gap-2 text-left text-note text-ink transition-colors"
                      >
                        <span className="grid w-2 shrink-0 translate-y-px place-items-center self-center">
                          <Mark kind={entry.kind} size={MARK_SIZE.note} color={group.ink} />
                        </span>
                        <span className={`link-hover min-w-0 ${entry.kind === 'science' ? 'science' : ''}`}>{entry.title}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              </section>
            ))}
          </div>
          {shown === 0 && <p className="note mt-6">Nothing awaiting a date matches “{query}”.</p>}
        </motion.aside>
      )}
    </AnimatePresence>
  )
}
