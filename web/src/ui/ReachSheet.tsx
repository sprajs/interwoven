import { useEffect, useMemo, useState } from 'react'
import type { RowOrder } from '../data/derive.ts'
import { hasLifecycleEvidence, lifeDateLabel, plottedLifeEvents, reviewedLifeEvents, tallyLifecycle } from '../data/lifecycle.ts'
import { focusEntry, useApp } from '../store.ts'
import { COMPACT_WIDTH, SHEET_WIDTH } from './layout.ts'

const ORDERS: { id: RowOrder; label: string; hint: string }[] = [
  { id: 'thread', label: 'by thread', hint: 'Connected work together, each entry near what it builds on' },
  { id: 'origin', label: 'by date', hint: 'A staircase of first appearances, as Priestley drew his chart' },
  { id: 'reach', label: 'by reach', hint: 'The longest influence first' },
]

/** A small drawing of each thing the rows can say, so the key and the chart read alike. */
function KeyMark({ kind }: { kind: 'direct' | 'fine' | 'broken' | 'use' | 'withdrawn' | 'abandoned' | 'unknown' }) {
  const common = { stroke: 'currentColor', fill: 'none', strokeLinecap: 'round' as const }
  return (
    <svg width="30" height="12" viewBox="0 0 30 11" aria-hidden className="shrink-0 text-ink-2">
      {kind === 'direct' && <path d="M1 5.5h28" {...common} strokeWidth="1.25" />}
      {kind === 'fine' && <path d="M1 5.5h28" {...common} strokeWidth="0.7" />}
      {kind === 'broken' && <path d="M1 5.5h4M8 5.5h4M15 5.5h4M22 5.5h4" {...common} strokeWidth="0.7" />}
      {kind === 'use' && <path d="M1 5.5h28M15 2v7" {...common} strokeWidth="0.9" />}
      {kind === 'withdrawn' && <path d="M1 5.5h24M22 .8h3.5v9.4H22" {...common} strokeWidth="1.2" />}
      {kind === 'abandoned' && <path d="M1 5.5h20M21 1.5l7 8M28 1.5l-7 8" {...common} strokeWidth="1.2" />}
      {kind === 'unknown' && (
        <>
          <circle cx="4" cy="5.5" r="0.8" fill="currentColor" />
          <circle cx="9" cy="5.5" r="0.8" fill="currentColor" />
          <circle cx="14" cy="5.5" r="0.8" fill="currentColor" />
          <text x="19" y="9" fontSize="11" fill="currentColor">?</text>
        </>
      )}
    </svg>
  )
}

function Key({ mark, children }: { mark: Parameters<typeof KeyMark>[0]['kind']; children: React.ReactNode }) {
  return (
    <li className="flex items-center gap-2 text-note text-ink-2">
      <KeyMark kind={mark} />
      <span>{children}</span>
    </li>
  )
}

function useWidth(): number {
  const [width, setWidth] = useState(window.innerWidth)
  useEffect(() => {
    const onResize = () => setWidth(window.innerWidth)
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])
  return width
}

/** Tells the reader what the rows mean and what is actually known about how things ended. */
export function ReachSheet() {
  const model = useApp((s) => s.model)
  const rowOrder = useApp((s) => s.rowOrder)
  const setRowOrder = useApp((s) => s.setRowOrder)
  const width = useWidth()
  const [open, setOpen] = useState(width >= COMPACT_WIDTH)
  const total = model ? model.n + model.unplaced.length : 0
  const tally = useMemo(() => tallyLifecycle(model?.life.values() ?? [], total), [model, total])
  // Separate scoped episodes; their first and last dates never imply a continuous lifespan.
  const documented = useMemo(() => {
    if (!model) return []
    return [...model.life].filter(([, record]) => hasLifecycleEvidence(record)).sort((a, b) => (plottedLifeEvents(a[1])[0]?.year ?? Infinity) - (plottedLifeEvents(b[1])[0]?.year ?? Infinity))
  }, [model])
  if (!model) return null

  const compact = width < COMPACT_WIDTH
  const placement = compact ? 'absolute inset-x-0 bottom-0 z-20 max-h-[56vh] border-t border-rule px-6 pt-3' : 'absolute bottom-0 right-0 top-18 z-20 border-l border-t border-rule px-8 pt-4'

  const keys = (
    <>
      <h3 className="section-head mt-0">Reach, from the links</h3>
      <ul className="mt-1">
        <Key mark="direct">Built on directly</Key>
        <Key mark="fine">Built on through later entries</Key>
        <Key mark="broken">Only through links awaiting review</Key>
      </ul>
      <h3 className="section-head mt-4">Scoped recorded episodes</h3>
      <ul className="mt-1">
        <Key mark="use">A reviewed scoped episode</Key>
        <Key mark="withdrawn">Withdrawn from sale, not last use</Key>
        <Key mark="abandoned">Abandonment within its stated scope</Key>
        <Key mark="unknown">No further evidence shown</Key>
      </ul>
    </>
  )

  return (
      <aside style={{ width: compact ? undefined : SHEET_WIDTH }} className={`sheet thin-scroll select-text overflow-y-auto pb-3 ${placement}`} aria-label="About the reach view">
        <div className="flex items-baseline justify-between gap-3">
          <h2 className="text-head">Reach</h2>
          <div className="flex items-baseline gap-3 text-note" role="group" aria-label="Order of rows">
            {ORDERS.map((option) => (
              <button
                key={option.id}
                title={option.hint}
                aria-pressed={rowOrder === option.id}
                onClick={() => setRowOrder(option.id)}
                className={rowOrder === option.id ? 'link text-ink' : 'text-ink-3 hover:text-ink'}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <p className="mt-2 text-body text-ink-2">
          Of <span className="figures">{tally.total.toLocaleString('en-US')}</span> entries, <span className="text-ink">{tally.withLifecycleEvidence}</span> have reviewed scoped use, availability or later-stage episodes. Separate episodes do not establish continuous life or a global ending.
        </p>

        {compact && (
          <button onClick={() => setOpen(!open)} aria-expanded={open} className="note link mt-1">
            {open ? 'Hide the key' : 'Show the key'}
          </button>
        )}

        {open && (
          <>
            <div className="mt-4">{keys}</div>

            <table className="figures mt-4 w-full border-t border-rule text-note text-ink-2">
              <caption className="pb-1 text-left">Reviewed scoped episodes</caption>
              <tbody>
                {[
                  ['Adoption', tally.counts.adoption],
                  ['Decline', tally.counts.decline],
                  ['Withdrawal', tally.counts.withdrawal],
                  ['End of use within scope', tally.counts.end_of_use],
                  ['Abandonment', tally.counts.abandonment],
                  ['Revival', tally.counts.revival],
                ].map(([name, count]) => (
                  <tr key={name as string} className="border-b border-rule-soft">
                    <td className="py-px">{name}</td>
                    <td className={`py-px text-right ${count === 0 ? 'text-ink-3' : 'text-ink'}`}>{count === 0 ? 'none documented' : count}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {documented.length > 0 && (
              <>
                <h3 className="section-head mt-4">Entries with reviewed episodes</h3>
                <ul>
                  {documented.map(([id, record]) => {
                    const entry = model.entryById.get(id)
                    if (!entry) return null
                    const episodes = reviewedLifeEvents(record)
                    const last = episodes[episodes.length - 1]!
                    return (
                      <li key={id} className="border-b border-rule-soft">
                        <button onClick={() => focusEntry(id)} className="group flex w-full items-baseline gap-2 py-px text-left text-note text-ink">
                          <span className={`link-hover min-w-0 flex-1 ${entry.kind === 'science' ? 'science' : ''}`}>{entry.title}</span>
                          <span className="figures shrink-0 text-ink-3">
                            {episodes.length} {episodes.length === 1 ? 'episode' : 'episodes'} · {lifeDateLabel(last)}
                          </span>
                        </button>
                      </li>
                    )
                  })}
                </ul>
              </>
            )}
          </>
        )}
      </aside>
  )
}
