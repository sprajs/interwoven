import { AnimatePresence, motion } from 'motion/react'
import type { Model } from '../data/model.ts'
import { isPlacedNode, type RawLink, type TimelineEntry } from '../data/types.ts'
import { formatYear } from '../engine/time.ts'
import { documentedSpan, EVENT_NAMES, hasLaterLife, LATER_STAGES, type LaterStage } from '../data/lifecycle.ts'
import { focusEntry, followEntry, getEngine, useApp } from '../store.ts'
import { CloseButton, Mark } from './icons.tsx'
import { COMPACT_WIDTH, SHEET_WIDTH } from './layout.ts'

const withArticle = (phrase: string) => `${/^[aeiou]/i.test(phrase) ? 'an' : 'a'} ${phrase}`

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
                  <Mark kind={node.kind} color={model.labelById.get(node.labels[0] ?? '')?.ink} />
                </span>
                <span className={`link-hover min-w-0 flex-1 ${node.kind === 'science' ? 'science' : ''}`}>{node.title}</span>
                <span className="note shrink-0">{isPlacedNode(node) ? formatYear(node.year) : 'not yet placed'}</span>
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
  const life = useApp((s) => s.lifeById[entry.id])
  const reach = getEngine()?.reach
  const year = isPlacedNode(entry) ? entry.year : null
  const latest = (index !== null ? reach?.any[index] : undefined) ?? year ?? 0
  const span = year === null ? 0 : Math.round(latest - year)
  const later = life && hasLaterLife(life) ? life.events.filter((e) => e.role !== 'origin') : []
  const documented = documentedSpan(life)
  const unresearched = LATER_STAGES.filter((stage) => !life?.status[stage] && !later.some((e) => e.type === stage))
  const stated = LATER_STAGES.filter((stage) => life?.status[stage] === 'unknown')
  return (
    <section>
      <h3 className="section-head">How long it lasted</h3>
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
            <span className="text-ink">Documented life:</span> {documented ? `${formatYear(documented.start)} to ${formatYear(documented.end)}` : 'only these dated events'}.
          </p>
          <ul className="mt-1 space-y-1">
            {later.map((event) => (
              <li key={event.id} className="text-note text-ink-2">
                <span className="text-ink">{EVENT_NAMES[event.type] ?? event.type}</span>, {event.label}. {event.statement}
                {event.review !== 'accepted' && <span className="text-ink-3"> Awaiting review.</span>}
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
  const mode = useApp((s) => s.mode)
  const linked = model && selected !== null && model.parents[selected]!.length + model.children[selected]!.length > 0

  return (
    <AnimatePresence>
      {node && model && !(mode === 'story' && selected !== null) && (
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
            <h3 className="section-head">How this is dated</h3>
            <div className="mt-2 space-y-1 text-note text-ink-2">
              <p>
                {isPlacedNode(node) ? (node.anchored ? `Placed by its selected anchor, ${withArticle(node.placed_by)}.` : 'Illustrative date supplied by this dataset.') : node.placement_reason}
                {node.date_basis ? ` ${node.date_basis}` : ''}
              </p>
              {node.anchor_status && <p>Anchor: {node.anchor_status.replace(/_/g, ' ')}{node.anchor_policy ? `; policy: ${node.anchor_policy.replace(/_/g, ' ')}` : ''}.</p>}
              {node.anchor_rationale && <p>{node.anchor_rationale}</p>}
              {node.commercial_date_status && <p>First commercial availability: {node.commercial_date_status.replace(/_/g, ' ')}{node.commercial_applicability ? `; applicability: ${node.commercial_applicability.replace(/_/g, ' ')}` : ''}.</p>}
              {node.lifecycle_review && <p className="text-ink-3">Historical claim: {node.review}. Lifecycle classification: {node.lifecycle_review.replace(/_/g, ' ')}.</p>}
              {node.review !== 'accepted' && <p className="text-ink-3">This claim is still awaiting review.</p>}
              {node.uncertainty && <p>{node.uncertainty}</p>}
            </div>
          </section>

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
