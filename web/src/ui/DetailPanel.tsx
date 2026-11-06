import { AnimatePresence, motion } from 'motion/react'
import type { Model } from '../data/model.ts'
import { isPlacedNode, type RawLink, type TimelineEntry } from '../data/types.ts'
import { formatYear } from '../engine/time.ts'
import { EVENT_NAMES, lifeDateLabel, LATER_STAGES, type LaterStage } from '../data/lifecycle.ts'
import { shortDate } from '../engine/overlay.ts'
import { focusEntry, followEntry, useApp } from '../store.ts'
import { dateLimitNote, entryReasonLabel, evidenceLabel } from './entryText.ts'
import { CloseButton, EvidenceBadge, Mark } from './icons.tsx'
import { COMPACT_WIDTH, SHEET_WIDTH } from './layout.ts'

function LinkList({ title, links, side, model }: { title: string; links: RawLink[]; side: 'from' | 'to'; model: Model }) {
  if (links.length === 0) return null
  const yearOf = (id: string) => {
    const entry = model.entryById.get(id)
    return entry && isPlacedNode(entry) ? entry.year : Infinity
  }
  // In date order, with what has no date yet at the end.
  const sorted = [...links].sort((a, b) => yearOf(a[side]) - yearOf(b[side]) || (model.entryById.get(a[side])?.title ?? '').localeCompare(model.entryById.get(b[side])?.title ?? ''))
  const eventLabel = (id: string | undefined) => {
    const event = id ? model.events[id] : undefined
    return event ? `${event.event_type.replace(/_/g, ' ')} (${event.date_label})` : id ?? 'event not specified'
  }
  return (
    <section>
      <h3 className="section-head">{title}</h3>
      <ul>
        {sorted.map((link, n) => {
          const node = model.entryById.get(link[side])
          if (!node) return null
          return (
            <li key={link.id ?? `${link.from}-${link.to}-${n}`} className="border-b border-rule-soft py-2">
              <button onClick={() => focusEntry(node.id)} className="group flex w-full items-baseline gap-2 text-left text-body">
                <span className="grid w-2 shrink-0 translate-y-px place-items-center self-center">
                  <Mark kind={node.kind} strength={node.evidence_strength} color={model.labelById.get(node.labels[0] ?? '')?.ink} />
                </span>
                <span className={`link-hover min-w-0 flex-1 ${node.kind === 'science' ? 'science' : ''}`}>{node.title}</span>
                <span className="note shrink-0">{isPlacedNode(node) ? shortDate(node) : 'not yet placed'}</span>
              </button>
              {link.statement && (
                <p className="mt-1 pl-4 text-note text-ink-2">
                  {link.statement}
                  {link.tentative && <span className="text-ink-3"> Awaiting review.</span>}
                </p>
              )}
              {(link.from_event_id || link.to_event_id) && <p className="note mt-1 pl-4">Linked events: {eventLabel(link.from_event_id)} → {eventLabel(link.to_event_id)}.</p>}
              {link.temporal_note && <p className="note mt-1 pl-4">{link.temporal_note}</p>}
            </li>
          )
        })}
      </ul>
    </section>
  )
}

const STAGE_NAMES: Record<LaterStage, string> = {
  adoption: 'adoption',
  decline: 'decline',
  withdrawal: 'withdrawal',
  end_of_use: 'last use',
  abandonment: 'abandonment',
  revival: 'revival',
}

/** Two different things, kept apart: what the links imply, and what the evidence says. */
function LifeSection({ entry, index }: { entry: TimelineEntry; index: number | null }) {
  const model = useApp((s) => s.model)
  const life = model?.life.get(entry.id)
  const reach = model?.reach
  const year = isPlacedNode(entry) ? entry.year : null
  const latest = (index !== null ? reach?.any[index] : undefined) ?? year ?? 0
  const span = year === null ? 0 : Math.round(latest - year)
  const later = life?.events.filter((e) => e.role !== 'context') ?? []
  const unresearched = LATER_STAGES.filter((stage) => !life?.status[stage] || life.status[stage] === 'not_yet_researched')
  const stated = LATER_STAGES.filter((stage) => life?.status[stage] === 'unknown')
  return (
    <section>
      <h3 className="section-head">Evidence over time</h3>
      <p className="mt-2 text-note text-ink-2">
        {span > 0 ? (
          <>
            <span className="text-ink">Reach:</span> built on until {formatYear(latest)}, <span>{span.toLocaleString('en-US')}</span> {span === 1 ? 'year' : 'years'} on. This comes from the links in the research so far, and says nothing about how long it stayed in use.
          </>
        ) : year === null ? (
          <>
            <span className="text-ink">Reach:</span> not worked out, because the entry has no date to measure from yet.
          </>
        ) : (
          <>
            <span className="text-ink">Reach:</span> nothing dated in the research builds on it yet.
          </>
        )}
      </p>
      {later.length > 0 && (
        <>
          <p className="mt-2 text-note text-ink-2">
            <span className="text-ink">Recorded episodes:</span> each concerns its stated scope. Continuous use between separate dates remains unresearched.
          </p>
          <ul className="mt-1 space-y-1">
            {later.map((event) => (
              <li key={event.id} className="text-note text-ink-2">
                <span className="text-ink">{EVENT_NAMES[event.type] ?? event.type.replace(/_/g, ' ')}</span>, {lifeDateLabel(event)}. {event.statement}
                {event.role === 'awareness' && <p className="text-ink-3">This records disclosure or awareness; use or adoption requires separate evidence.</p>}
                {event.role === 'unclassified' && <p className="text-ink-3">Event role awaits classification.</p>}
                {event.review !== 'accepted' && <p className="text-ink-3">Historical claim awaiting review.</p>}
                {event.lifecycle_review !== 'accepted' && <p className="text-ink-3">Lifecycle classification awaiting review.</p>}
                {event.scope && <p className="text-ink-3">Scope: {event.scope.configuration}. Regions: {event.scope.regions.join('; ') || 'unspecified'}. Population: {event.scope.population.value ?? event.scope.population.status.replace(/_/g, ' ')}. Market: {event.scope.market.value ?? event.scope.market.status.replace(/_/g, ' ')}.</p>}
                {event.evidence?.map((item, i) => <p key={`${item.source_id}-${i}`} className="text-ink-3">{model?.sources[item.source_id]?.title ?? item.source_id}{item.locator ? ` · ${item.locator}` : ''}{item.supports ? `. ${item.supports}` : ''}</p>)}
                {event.uncertainty && <p className="text-ink-3">{event.uncertainty}</p>}
              </li>
            ))}
          </ul>
        </>
      )}
      <p className="note mt-2">
        {stated.length > 0 && `Researched and still unknown: ${stated.map((s) => STAGE_NAMES[s]).join(', ')}. `}
        {unresearched.length > 0 && `Not yet researched: ${unresearched.map((s) => STAGE_NAMES[s]).join(', ')}.`}
      </p>
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
  // A followed story reads its entries in its own sheet.
  const inStorySheet = useApp((s) => s.mode === 'story' && s.story !== null)
  const linked = model && selected !== null && model.parents[selected]!.length + model.children[selected]!.length > 0

  return (
    <AnimatePresence>
      {node && model && !(inStorySheet && selected !== null) && (
        <motion.aside
          key="detail"
          initial={{ x: SHEET_WIDTH }}
          animate={{ x: 0 }}
          exit={{ x: SHEET_WIDTH }}
          transition={{ duration: 0.26, ease: [0.2, 0.7, 0.2, 1] }}
          className="sheet thin-scroll absolute inset-x-0 bottom-0 z-30 max-h-[48vh] select-text overflow-y-auto border-t border-rule px-8 pb-8 pt-4 compact:inset-x-auto compact:right-0 compact:top-18 compact:max-h-none compact:border-l"
          style={{ width: window.innerWidth >= COMPACT_WIDTH ? SHEET_WIDTH : undefined }}
          aria-label={`About ${node.title}`}
        >
          <div className="flex items-baseline justify-between gap-3">
            <p className="note">{isPlacedNode(node) ? node.date_label : 'Awaiting a date'}</p>
            <CloseButton onClick={() => select(null)} label="Close" />
          </div>
          <h2 className={`text-head ${node.kind === 'science' ? 'science' : ''}`}>{node.title}</h2>
          <p className="note mt-1">
            {node.kind === 'science' ? 'Science' : 'Technology'}
            {node.regions.length > 0 && <> · {node.regions.join('; ')}</>}
          </p>
          <EvidenceBadge strength={node.evidence_strength} />

          <p className="mt-4 text-body">{node.summary}</p>
          {node.note && <p className="mt-2 text-body text-ink-2">{node.note}</p>}

          {node.labels.length > 0 && (
            <p className="mt-4 flex flex-wrap gap-x-4 text-note">
              {node.labels.map((id) => {
                const label = model.labelById.get(id)
                const on = activeLabels.has(id)
                return (
                  <button key={id} onClick={() => toggleLabel(id)} aria-pressed={on} className="flex items-center gap-1 text-ink-2 hover:text-ink">
                    <span className="size-2 shrink-0 rounded-full" style={{ background: label?.ink }} />
                    <span className={on ? 'link text-ink' : ''}>{label?.name ?? id}</span>
                  </button>
                )
              })}
            </p>
          )}

          {impactIsFull && selected !== null && model.impact[selected]! > 0 && (
            <p className="note mt-4">
              {model.impact[selected]!.toLocaleString('en-US')} placed {model.impact[selected] === 1 ? 'entry traces' : 'entries trace'} back to this one.
            </p>
          )}

          {linked && (
            <button onClick={() => followEntry(selected!)} className="group mt-4 flex items-baseline gap-2 text-body text-ink" title="Lay this thread out on its own (f, or click the entry twice)">
              <span className="link">Follow this thread</span>
              <span aria-hidden className="text-ink-3 transition-transform duration-200 group-hover:translate-x-1">→</span>
            </button>
          )}

          <LinkList title="Built on" links={model.links.filter((link) => link.to === node.id)} side="from" model={model} />
          <LinkList title="Led to" links={model.links.filter((link) => link.from === node.id)} side="to" model={model} />

          <LifeSection entry={node} index={selected} />

          <section>
            <h3 className="section-head">Why this date</h3>
            <div className="mt-2 space-y-1 text-note text-ink-2">
              <p>
                {isPlacedNode(node)
                  ? node.anchored ? `Earliest evidenced record of this entry. ${entryEvent?.event_type.replace(/_/g, ' ') ?? ''}.` : 'Synthetic date supplied by this dataset.'
                  : `Unplaced. ${node.placement_reason}`}
                {node.date_basis ? ` ${node.date_basis}` : ''}
              </p>
              {isPlacedNode(node) && dateLimitNote(node.date_kind) && <p>{dateLimitNote(node.date_kind)}</p>}
              {node.evidence_strength && <p>{evidenceLabel(node.evidence_strength)}.</p>}
              {node.anchor_rationale && <p>{node.anchor_rationale}</p>}
              {node.record_uncertainty && <p>{node.record_uncertainty}</p>}
              {node.community_date_label && <p>Community entry: {node.community_date_label}. {entryReasonLabel(node.entry_basis)}. Community: {node.entry_community}.</p>}
              {node.proxy_justification && <p>{node.proxy_justification}</p>}
              {node.entry_uncertainty && <p>{node.entry_uncertainty}</p>}
              {node.entry_scope && <p className="text-ink-3">
                Scope: {node.entry_scope.regions.length ? node.entry_scope.regions.join('; ') : 'regions unspecified'}.
                {' '}Applications: {node.entry_scope.applications.length ? node.entry_scope.applications.join('; ') : 'unspecified'}.
                {' '}Population: {node.entry_scope.population.value ?? node.entry_scope.population.status.replace(/_/g, ' ')}.
                {' '}Market: {node.entry_scope.market.value ?? node.entry_scope.market.status.replace(/_/g, ' ')}.
              </p>}
              {node.entry_scope && node.entry_scope.configuration !== node.summary && <p className="text-ink-3">Scoped configuration: {node.entry_scope.configuration}</p>}
              {node.commercial_date_status && <p>First commercial availability: {node.commercial_date_status.replace(/_/g, ' ')}{node.commercial_applicability ? `; applicability: ${node.commercial_applicability.replace(/_/g, ' ')}` : ''}.</p>}
              {node.lifecycle_review && <p className="text-ink-3">Historical claim: {node.review}. Lifecycle classification: {node.lifecycle_review.replace(/_/g, ' ')}.</p>}
              {node.review !== 'accepted' && <p className="text-ink-3">This claim is still awaiting review.</p>}
              {node.uncertainty && <p>{node.uncertainty}</p>}
            </div>
          </section>

          {node.entry_evidence && node.entry_evidence.length > 0 && <section>
            <h3 className="section-head">Entry evidence</h3>
            <ul className="mt-2 space-y-2">
              {node.entry_evidence.map((entry, index) => <li key={`${entry.source_id}-${index}`} className="text-note text-ink-2">
                <p>{model.sources[entry.source_id]?.title ?? entry.source_id} · {entry.locator}</p>
                <p>{entry.supports}</p>
              </li>)}
            </ul>
          </section>}

          {node.lifecycle && <details className="text-note text-ink-2">
            <summary className="section-head cursor-pointer">Lifecycle dates and unknowns</summary>
            <ul className="mt-2 space-y-2">
              {Object.entries(node.lifecycle).map(([stage, state]) => <li key={stage}>
                <p>{stage.replace(/_/g, ' ')}: {state.status.replace(/_/g, ' ')}{state.as_of ? ` (as of ${state.as_of})` : ''}.</p>
                {state.event_ids.map((id) => <p key={id} className="pl-2 text-ink-3">{model.events[id]?.date_label ?? id}</p>)}
                {state.rationale && <p className="text-ink-3">{state.rationale}</p>}
              </li>)}
            </ul>
          </details>}

          {Object.values(model.events).some((event) => event.node_id === node.id) && (
            <section>
              <h3 className="section-head">Recorded events</h3>
              <ul className="mt-2 space-y-2">
                {Object.values(model.events).filter((event) => event.node_id === node.id).map((event) => (
                  <li key={event.id} className="text-note text-ink-2">
                    <p className="text-ink">{event.event_type.replace(/_/g, ' ')}, {event.date_label}</p>
                    {event.statement && <p>{event.statement}</p>}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {node.sources.length > 0 && (
            <section>
              <h3 className="section-head">Sources</h3>
              <ul className="mt-2 space-y-1">
                {node.sources.map((id) => {
                  const source = model.sources[id]
                  if (!source) return null
                  return (
                    <li key={id} className="text-note text-ink-2">
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
