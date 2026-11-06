import { useEffect, useMemo, useRef, useState } from 'react'
import type { RowOrder } from '../data/derive.ts'
import { hasLaterLife, tallyLifecycle } from '../data/lifecycle.ts'
import { onEngineFrame } from '../engine/frames.ts'
import { formatYear } from '../engine/time.ts'
import { focusNode, useApp } from '../store.ts'
import { CARTOUCHE_WIDTH, COMPACT_WIDTH, reachCornersFree, SHEET_WIDTH } from './layout.ts'

const ORDERS: { id: RowOrder; label: string; hint: string }[] = [
  { id: 'thread', label: 'by thread', hint: 'Connected work together, each entry near what it builds on' },
  { id: 'origin', label: 'by date', hint: 'A staircase of first appearances, as Priestley drew his chart' },
  { id: 'reach', label: 'by reach', hint: 'The longest influence first' },
]

/** A small drawing of each thing the rows can say, so the key and the chart read alike. */
function KeyMark({ kind }: { kind: 'direct' | 'fine' | 'broken' | 'life' | 'use' | 'withdrawn' | 'abandoned' | 'unknown' }) {
  const common = { stroke: 'currentColor', fill: 'none', strokeLinecap: 'round' as const }
  return (
    <svg width="30" height="11" viewBox="0 0 30 11" aria-hidden className="shrink-0 text-ink-2">
      {kind === 'direct' && <path d="M1 5.5h28" {...common} strokeWidth="1.25" />}
      {kind === 'fine' && <path d="M1 5.5h28" {...common} strokeWidth="0.7" />}
      {kind === 'broken' && <path d="M1 5.5h4M8 5.5h4M15 5.5h4M22 5.5h4" {...common} strokeWidth="0.7" />}
      {kind === 'life' && <path d="M1 5.5h28" {...common} strokeWidth="3" />}
      {kind === 'use' && <path d="M1 5.5h28M15 2v7" {...common} strokeWidth="0.9" />}
      {kind === 'withdrawn' && <path d="M1 5.5h24M22 .8h3.5v9.4H22" {...common} strokeWidth="1.2" />}
      {kind === 'abandoned' && <path d="M1 5.5h20M21 1.5l7 8M28 1.5l-7 8" {...common} strokeWidth="1.2" />}
      {kind === 'unknown' && (
        <>
          <circle cx="4" cy="5.5" r="0.8" fill="currentColor" />
          <circle cx="9" cy="5.5" r="0.8" fill="currentColor" />
          <circle cx="14" cy="5.5" r="0.8" fill="currentColor" />
          <text x="19" y="9" fontStyle="italic" fontSize="11" fill="currentColor">?</text>
        </>
      )}
    </svg>
  )
}

function Key({ mark, children }: { mark: Parameters<typeof KeyMark>[0]['kind']; children: React.ReactNode }) {
  return (
    <li className="flex items-center gap-2 text-[14.5px] leading-[1.25] text-ink-2">
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
  const life = useApp((s) => s.life)
  const rowOrder = useApp((s) => s.rowOrder)
  const setRowOrder = useApp((s) => s.setRowOrder)
  const width = useWidth()
  const [open, setOpen] = useState(width >= COMPACT_WIDTH)
  const tally = useMemo(() => tallyLifecycle(life, model?.n ?? 0), [life, model])
  const documented = useMemo(() => {
    if (!model) return []
    return [...life.entries()].filter(([, record]) => hasLaterLife(record)).sort((a, b) => model.nodes[a[0]]!.year - model.nodes[b[0]]!.year)
  }, [life, model])
  const cornerRef = useRef<HTMLDivElement>(null)
  const asideRef = useRef<HTMLElement>(null)
  // Zooming fills the corners with chart, so what sits in them steps aside until you return.
  useEffect(() => {
    return onEngineFrame((engine) => {
      const state = useApp.getState()
      if (window.innerWidth < CARTOUCHE_WIDTH || !reachCornersFree(state.model, state.rowOrder)) {
        // A sheet of its own never needs to step aside, and may have just stopped being a corner.
        for (const el of [cornerRef.current, asideRef.current]) {
          if (!el) continue
          el.style.opacity = ''
          el.style.pointerEvents = ''
        }
        return
      }
      const zoomed = engine.camera.logZoom > 0.12 || engine.camera.logY > 0.12 || engine.pleats.length > 0
      for (const el of [cornerRef.current, asideRef.current]) {
        if (!el) continue
        el.style.opacity = zoomed ? '0' : '1'
        el.style.pointerEvents = zoomed ? 'none' : ''
      }
    })
  }, [])
  if (!model) return null

  const compact = width < COMPACT_WIDTH
  const corner = width >= CARTOUCHE_WIDTH && reachCornersFree(model, rowOrder)
  const placement = compact
    ? 'absolute inset-x-0 bottom-0 z-20 max-h-[56vh] border-t border-rule'
    : corner
      ? 'absolute right-14 top-[108px] z-10 max-h-[calc(100vh-220px)]'
      : 'absolute bottom-0 right-0 top-[54px] z-20 border-l border-t border-rule'

  const keys = (
    <>
      <h3 className="border-b border-rule pb-0.5 text-[14.5px] italic text-ink-3">Reach, from the links</h3>
      <ul className="mt-1.5 space-y-[3px]">
        <Key mark="direct">Built on directly</Key>
        <Key mark="fine">Built on through later entries</Key>
        <Key mark="broken">Only through links awaiting review</Key>
      </ul>
      <h3 className="mt-3 border-b border-rule pb-0.5 text-[14.5px] italic text-ink-3">Life, from documented events</h3>
      <ul className="mt-1.5 space-y-[3px]">
        <Key mark="life">The stretch the evidence covers</Key>
        <Key mark="use">Evidence of use or sale</Key>
        <Key mark="withdrawn">Withdrawn from sale, not last use</Key>
        <Key mark="abandoned">Abandoned</Key>
        <Key mark="unknown">Not researched, whatever its length</Key>
      </ul>
    </>
  )

  return (
    <>
    {corner && (
      <div ref={cornerRef} className="absolute bottom-[116px] left-14 z-10 w-[252px] select-text transition-opacity duration-200" style={{ background: 'var(--color-paper)' }}>
        {keys}
      </div>
    )}
    <aside
      ref={asideRef}
      style={{ width: compact ? undefined : corner ? 306 : SHEET_WIDTH, background: corner ? 'var(--color-paper)' : undefined }}
      className={`sheet thin-scroll select-text overflow-y-auto pb-3 transition-opacity duration-200 ${corner ? '' : 'px-4 pt-3'} ${placement}`}
      aria-label="About the reach view"
    >
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-[21px] font-medium leading-none">Reach</h2>
        <div className="flex items-baseline gap-2.5 text-[14.5px]" role="group" aria-label="Order of rows">
          {ORDERS.map((option) => (
            <button
              key={option.id}
              title={option.hint}
              aria-pressed={rowOrder === option.id}
              onClick={() => setRowOrder(option.id)}
              className={rowOrder === option.id ? 'text-ink underline decoration-[0.5px] underline-offset-[3px]' : 'text-ink-3 hover:text-ink'}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <p className="mt-2 text-[15px] leading-snug text-ink-2">
        Of {tally.total.toLocaleString('en-US')} entries, <span className="text-ink">{tally.withLaterLife}</span> {tally.withLaterLife === 1 ? 'has' : 'have'} any recorded life beyond {tally.withLaterLife === 1 ? 'its' : 'their'} origin. For the rest, how long they lasted is not yet known.
      </p>

      {compact && (
        <button onClick={() => setOpen(!open)} aria-expanded={open} className="mt-1 text-[14.5px] italic text-ink-3 underline decoration-[0.5px] underline-offset-2">
          {open ? 'Hide the key' : 'Show the key'}
        </button>
      )}

      {open && (
        <>
          {!corner && <div className="mt-3">{keys}</div>}

          <table className="mt-3 w-full border-t border-rule text-[14.5px] text-ink-2">
            <caption className="sr-only">Documented later-life events</caption>
            <tbody>
              {[
                ['Decline', tally.counts.decline],
                ['Withdrawal', tally.counts.withdrawal],
                ['Last use', tally.counts.end_of_use],
                ['Abandonment', tally.counts.abandonment],
                ['Revival', tally.counts.revival],
              ].map(([name, count]) => (
                <tr key={name as string} className="border-b border-rule/50">
                  <td className="py-[2px]">{name}</td>
                  <td className={`py-[2px] text-right ${count === 0 ? 'italic text-ink-3' : 'text-ink'}`}>{count === 0 ? 'none documented' : count}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {documented.length > 0 && (
            <>
              <h3 className="mt-3 border-b border-rule pb-0.5 text-[14.5px] italic text-ink-3">The documented lives</h3>
              <ul>
                {documented.map(([i, record]) => {
                  const node = model.nodes[i]!
                  const last = record.events[record.events.length - 1]!
                  return (
                    <li key={i} className="border-b border-rule/50">
                      <button onClick={() => focusNode(i)} className="group flex w-full items-baseline gap-2 py-[3px] text-left text-[15px] leading-tight">
                        <span className="min-w-0 flex-1 group-hover:underline group-hover:decoration-[0.5px] group-hover:underline-offset-2">{node.title}</span>
                        <span className="shrink-0 text-[13.5px] text-ink-3">
                          {formatYear(record.events[0]!.start)} to {formatYear(last.end)}
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
    </>
  )
}
