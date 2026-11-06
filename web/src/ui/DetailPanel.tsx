import { AnimatePresence, motion } from 'motion/react'
import type { Model } from '../data/model.ts'
import { isPlacedNode, type RawLink } from '../data/types.ts'
import { formatYear } from '../engine/time.ts'
import { focusEntry, useApp } from '../store.ts'
import { CloseButton, EvidenceBadge, Mark } from './icons.tsx'
import { SHEET_WIDTH } from './layout.ts'
import { dateLimitNote, entryReasonLabel, evidenceLabel } from './entryText.ts'

function LinkList({ title, links, side, model }: { title: string; links: RawLink[]; side: 'from' | 'to'; model: Model }) {
  if (links.length === 0) return null
  const sorted = [...links].sort((a, b) => (model.entryById.get(a[side])?.title ?? '').localeCompare(model.entryById.get(b[side])?.title ?? ''))
  const eventLabel = (id: string | undefined) => {
    const event = id ? model.events[id] : undefined
    return event ? `${event.event_type.replace(/_/g, ' ')} (${event.date_label})` : id ?? 'event not specified'
  }
  return (
    <section className="mt-5">
      <h3 className="border-b border-rule pb-1 text-[15px] italic text-ink-3">{title}</h3>
      <ul>
        {sorted.map((link) => {
          const node = model.entryById.get(link[side])
          if (!node) return null
          return (
            <li key={link.id ?? `${link.from}-${link.to}`} className="border-b border-rule/50 py-2">
              <button onClick={() => focusEntry(node.id)} className="group flex w-full items-baseline gap-2 text-left text-[16px] leading-tight">
                <span className="grid w-2.5 shrink-0 translate-y-[1px] place-items-center self-center">
                  <Mark kind={node.kind} strength={node.evidence_strength} size={9} color={model.labelById.get(node.labels[0] ?? '')?.ink} />
                </span>
                <span className={`min-w-0 flex-1 group-hover:underline group-hover:decoration-[0.5px] group-hover:underline-offset-2 ${node.kind === 'science' ? 'italic' : ''}`}>{node.title}</span>
                <span className="shrink-0 text-[14px] text-ink-3">{isPlacedNode(node) ? node.date_kind && node.date_kind !== 'point' ? node.date_label : formatYear(node.year) : 'Unplaced'}</span>
              </button>
              {link.statement && (
                <p className="mt-1 pl-[18px] text-[14px] leading-snug text-ink-2">
                  {link.statement}
                  {link.tentative && <em className="text-ink-3"> Awaiting review.</em>}
                </p>
              )}
              {(link.from_event_id || link.to_event_id) && <p className="mt-1 pl-[18px] text-[13.5px] leading-snug text-ink-3">Linked events: {eventLabel(link.from_event_id)} → {eventLabel(link.to_event_id)}.</p>}
              {link.temporal_note && <p className="mt-1 pl-[18px] text-[13.5px] leading-snug text-ink-3">{link.temporal_note}</p>}
            </li>
          )
        })}
      </ul>
    </section>
  )
}

export function DetailPanel() {
  const model = useApp((s) => s.model)
  const selected = useApp((s) => s.selected)
  const unplacedSelected = useApp((s) => s.unplacedSelected)
  const select = useApp((s) => s.select)
  const activeLabels = useApp((s) => s.activeLabels)
  const toggleLabel = useApp((s) => s.toggleLabel)
  const node = model && selected !== null ? model.nodes[selected] : model?.entryById.get(unplacedSelected ?? '')
  const impactIsFull = model && node ? model.n <= 4000 || node.level === 0 : false
  const entryEvent = node?.anchor_event_id ? model?.events[node.anchor_event_id] : undefined

  return (
    <AnimatePresence>
      {node && model && (
        <motion.aside
          key="detail"
          initial={{ x: SHEET_WIDTH }}
          animate={{ x: 0 }}
          exit={{ x: SHEET_WIDTH }}
          transition={{ duration: 0.26, ease: [0.2, 0.7, 0.2, 1] }}
          className="sheet thin-scroll absolute inset-x-0 bottom-0 z-30 max-h-[48vh] select-text overflow-y-auto border-t border-rule px-5 pb-8 pt-4 min-[760px]:inset-x-auto min-[760px]:bottom-0 min-[760px]:right-0 min-[760px]:top-[46px] min-[760px]:border-t min-[760px]:max-h-none min-[760px]:border-l"
          style={{ width: window.innerWidth >= 760 ? SHEET_WIDTH : undefined }}
          aria-label={`About ${node.title}`}
        >
          <div className="flex items-baseline justify-between gap-3">
            <p className="text-[16px] text-ink-3">{node.date_label}</p>
            <CloseButton onClick={() => select(null)} label="Close" />
          </div>
          <h2 className={`mt-1 text-[27px] font-medium leading-[1.1] tracking-[-0.005em] ${node.kind === 'science' ? 'italic' : ''}`}>{node.title}</h2>
          <p className="mt-1 text-[15px] text-ink-3">
            {node.kind === 'science' ? 'Science' : 'Technology'}
            {node.regions.length > 0 && <> · {node.regions.join('; ')}</>}
          </p>
          <EvidenceBadge strength={node.evidence_strength} />

          <p className="mt-3 text-[17px] leading-[1.32]">{node.summary}</p>
          {node.note && <p className="mt-2 text-[16px] italic leading-snug text-ink-2">{node.note}</p>}

          {node.labels.length > 0 && (
            <p className="mt-3 flex flex-wrap gap-x-3 gap-y-0.5 text-[15px]">
              {node.labels.map((id) => {
                const label = model.labelById.get(id)
                const on = activeLabels.has(id)
                return (
                  <button key={id} onClick={() => toggleLabel(id)} aria-pressed={on} className="flex items-baseline gap-1.5 text-ink-2 hover:text-ink">
                    <span className="size-1.5 shrink-0 translate-y-[-2px] rounded-full" style={{ background: label?.ink }} />
                    <span className={on ? 'text-ink underline decoration-[0.5px] underline-offset-2' : ''}>{label?.name ?? id}</span>
                  </button>
                )
              })}
            </p>
          )}

          {impactIsFull && selected !== null && model.impact[selected]! > 0 && (
            <p className="mt-3 text-[15px] text-ink-2">
              {model.impact[selected]!.toLocaleString('en-US')} linked {model.impact[selected] === 1 ? 'entry traces' : 'entries trace'} back to this one.
            </p>
          )}

          <LinkList title="Built on" links={model.links.filter((link) => link.to === node.id)} side="from" model={model} />
          <LinkList title="Led to" links={model.links.filter((link) => link.from === node.id)} side="to" model={model} />

          <section className="mt-5">
            <h3 className="border-b border-rule pb-1 text-[15px] italic text-ink-3">Why this date</h3>
            <p className="mt-2 text-[14.5px] leading-snug text-ink-2">
              {isPlacedNode(node)
                ? node.anchored ? `${entryReasonLabel(node.entry_basis, entryEvent?.event_type, node.date_kind, node.date_label, node.evidence_strength)}. Community: ${node.entry_community ?? 'not yet specified'}.` : 'Synthetic date supplied by this dataset.'
                : `Unplaced. ${node.placement_reason}`}
              {node.date_basis ? ` ${node.date_basis}` : ''}
            </p>
            {isPlacedNode(node) && dateLimitNote(node.date_kind) && <p className="mt-1.5 text-[14.5px] leading-snug text-ink-2">{dateLimitNote(node.date_kind)}</p>}
            {node.evidence_strength && <p className="mt-1.5 text-[14.5px] leading-snug text-ink-2">{evidenceLabel(node.evidence_strength)}.</p>}
            {node.anchor_rationale && <p className="mt-1.5 text-[14.5px] leading-snug text-ink-2">{node.anchor_rationale}</p>}
            {node.proxy_justification && <p className="mt-1.5 text-[14.5px] italic leading-snug text-ink-2">{node.proxy_justification}</p>}
            {node.entry_uncertainty && <p className="mt-1.5 text-[14.5px] leading-snug text-ink-2">{node.entry_uncertainty}</p>}
            {node.entry_scope && <p className="mt-1.5 text-[13.5px] leading-snug text-ink-3">
              Scope: {node.entry_scope.regions.length ? node.entry_scope.regions.join('; ') : 'regions unspecified'}.
              {' '}Applications: {node.entry_scope.applications.length ? node.entry_scope.applications.join('; ') : 'unspecified'}.
              {' '}Population: {node.entry_scope.population.value ?? node.entry_scope.population.status.replace(/_/g, ' ')}.
              {' '}Market: {node.entry_scope.market.value ?? node.entry_scope.market.status.replace(/_/g, ' ')}.
            </p>}
            {node.entry_scope && node.entry_scope.configuration !== node.summary && <p className="mt-1.5 text-[13.5px] leading-snug text-ink-3">Scoped configuration: {node.entry_scope.configuration}</p>}
            {node.commercial_date_status && <p className="mt-1.5 text-[14.5px] leading-snug text-ink-2">First commercial availability: {node.commercial_date_status.replace(/_/g, ' ')}{node.commercial_applicability ? `; applicability: ${node.commercial_applicability.replace(/_/g, ' ')}` : ''}.</p>}
            {node.lifecycle_review && <p className="mt-1.5 text-[14.5px] leading-snug text-ink-3">Historical claim: {node.review}. Lifecycle classification: {node.lifecycle_review.replace(/_/g, ' ')}.</p>}
            {node.review !== 'accepted' && <p className="mt-1.5 text-[14.5px] italic leading-snug text-ink-3">This claim is still awaiting review.</p>}
            {node.uncertainty && <p className="mt-1.5 text-[14.5px] leading-snug text-ink-2">{node.uncertainty}</p>}
          </section>

          {node.entry_evidence && node.entry_evidence.length > 0 && <section className="mt-5">
            <h3 className="border-b border-rule pb-1 text-[15px] italic text-ink-3">Entry evidence</h3>
            <ul className="mt-1.5 space-y-2">
              {node.entry_evidence.map((entry, index) => <li key={`${entry.source_id}-${index}`} className="text-[14px] leading-snug text-ink-2">
                <p>{model.sources[entry.source_id]?.title ?? entry.source_id} · {entry.locator}</p>
                <p className="mt-0.5">{entry.supports}</p>
              </li>)}
            </ul>
          </section>}

          {node.lifecycle && <details className="mt-5 text-[14px] leading-snug text-ink-2">
            <summary className="cursor-pointer border-b border-rule pb-1 text-[15px] italic text-ink-3">Lifecycle dates and unknowns</summary>
            <ul className="mt-2 space-y-2">
              {Object.entries(node.lifecycle).map(([stage, state]) => <li key={stage}>
                <p>{stage.replace(/_/g, ' ')}: {state.status.replace(/_/g, ' ')}{state.as_of ? ` (as of ${state.as_of})` : ''}.</p>
                {state.event_ids.map((id) => <p key={id} className="pl-2 text-ink-3">{model.events[id]?.date_label ?? id}</p>)}
                {state.rationale && <p className="mt-0.5 text-ink-3">{state.rationale}</p>}
              </li>)}
            </ul>
          </details>}

          {Object.values(model.events).some((event) => event.node_id === node.id) && (
            <section className="mt-5">
              <h3 className="border-b border-rule pb-1 text-[15px] italic text-ink-3">Recorded events</h3>
              <ul className="mt-1.5 space-y-2">
                {Object.values(model.events).filter((event) => event.node_id === node.id).map((event) => (
                  <li key={event.id} className="text-[14.5px] leading-snug text-ink-2">
                    <p>{event.event_type.replace(/_/g, ' ')} · {event.date_label}</p>
                    {event.statement && <p className="mt-0.5">{event.statement}</p>}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {node.sources.length > 0 && (
            <section className="mt-5">
              <h3 className="border-b border-rule pb-1 text-[15px] italic text-ink-3">Sources</h3>
              <ul className="mt-1.5 space-y-1.5">
                {node.sources.map((id) => {
                  const source = model.sources[id]
                  if (!source) return null
                  return (
                    <li key={id} className="text-[14.5px] leading-snug text-ink-2">
                      {source.url ? (
                        <a href={source.url} target="_blank" rel="noreferrer">
                          {source.title}
                        </a>
                      ) : (
                        source.title
                      )}
                      {source.year ? ` (${source.year})` : ''}
                    </li>
                  )
                })}
              </ul>
            </section>
          )}
        </motion.aside>
      )}
    </AnimatePresence>
  )
}
