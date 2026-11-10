import { useMemo, useState, type ReactNode } from 'react'
import { create } from 'zustand'
import { sharedWith, type Entry } from '../data/model.ts'
import type { Basis, DetailData, Discovery, Link } from '../data/types.ts'
import { dateLabel, tierName, words } from '../lib/text.ts'
import { useApp, useModel } from '../store.ts'
import { yearLabel } from '../time.ts'

/** Facets a record can have that are shown in the fact list, in reading order. */
const FACET_NAMES: Record<string, string> = {
  summary: 'a summary',
  advance: 'what was new',
  scale: 'how big a change it was',
  origin: 'whether it was independent',
  prompted_by: 'what prompted it',
  limit_removed: 'the bottleneck it relieved',
  setting: 'its setting',
  funding: 'who paid for it',
  places: 'where it happened',
  people: 'who did it',
  organizations: 'organisations involved',
  societies: 'the society it belongs to',
  known_from: 'how it is known',
  reception: 'how it was received',
  fate: 'where it stands today',
  market: 'whether it was sold',
  measures: 'performance figures',
  links: 'what it built on',
}

/** Which sections of the sheet are open. Kept between records, so a reader's choice of depth sticks. */
const useSections = create<{ open: ReadonlySet<string>; toggle(id: string): void }>((set) => ({
  open: new Set(),
  toggle: (id) =>
    set((s) => {
      const open = new Set(s.open)
      if (open.has(id)) open.delete(id)
      else open.add(id)
      return { open }
    }),
}))

/** A part of the sheet that opens when asked for. Its heading says how much is inside. */
function Section({ id, title, count, children }: { id: string; title: string; count?: number | string; children: ReactNode }) {
  const open = useSections((s) => s.open.has(id))
  return (
    <section className="section" data-open={open}>
      <button className="section-head" aria-expanded={open} onClick={() => useSections.getState().toggle(id)}>
        <svg width="9" height="6" viewBox="0 0 9 6" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M1 1l3.5 3.5L8 1" />
        </svg>
        <span>{title}</span>
        {count !== undefined && <b>{count}</b>}
      </button>
      {open && <div className="section-body">{children}</div>}
    </section>
  )
}

function EntryLink({ id, plain }: { id: string; plain?: boolean }) {
  const model = useModel()
  const entry = model.byId.get(id)
  if (!entry) return <>{id}</>
  return (
    <button
      className={plain ? 'entry-link plain' : 'entry-link'}
      onClick={() => useApp.getState().select(id)}
    >
      {entry.name}
    </button>
  )
}

function Dot({ basis }: { basis?: Basis }) {
  if (!basis || basis === 'not_applicable') return null
  const title = { sourced: 'From evidence cited on this record', reviewed: 'Checked against the evidence by a second reader', recalled: 'Entered from general knowledge. Not yet checked against a source', unknown: 'Investigated and not settled' }[basis]
  return <i className="basis" data-basis={basis === 'reviewed' ? 'sourced' : basis} title={title} />
}

export function Detail({ entry, data }: { entry: Entry; data: DetailData }) {
  return <DetailBody entry={{...data.entry, index: entry.index, domainId: entry.domainId, group: entry.group, haystack: entry.haystack}} data={data} />
}

function DetailBody({ entry, data }: { entry: Discovery & Pick<Entry, 'index' | 'domainId' | 'group' | 'haystack'>; data: DetailData }) {
  const model = useModel()
  const bundle = { ...model.bundle, ...data }
  const basis = entry.research.basis
  const list = (ids: string[] | undefined) => (ids?.length ? ids.map(words).join(', ') : null)
  const links = data.links
  const stated = links.filter((l) => l.status === 'established')
  const open = links.filter((l) => l.status !== 'established')
  const shared = useMemo(() => sharedWith(model, entry), [model, entry])
  const sources = Object.entries(data.sources).map(([id, source]) => ({id, ...source}))
  // A link is held by the later discovery, so an earlier one can have links and no basis for them.
  const missing = bundle.facets.filter((f) => FACET_NAMES[f] && !basis[f] && !(f === 'links' && stated.length > 0))
  const place = entry.at ? bundle.places[entry.at.place] : undefined
  const country = place?.within ? bundle.places[place.within] : undefined

  const facts: [string, ReactNode, Basis | undefined][] = [
    ['Field', [entry.domain, ...(entry.fields ?? [])].map((f) => model.fieldNames.get(f) ?? f).join(', '), basis.domain],
    ['What was new', list(entry.advance), basis.advance],
    ['Change', entry.scale ? words(entry.scale) : null, basis.scale],
    [
      'Origin',
      entry.origin || entry.concept ? (
        <>
          {entry.origin ? words(entry.origin) : ''}
          {entry.concept && (
            <span className="relation">
              {entry.origin ? ' · ' : ''}one of the places that reached “{bundle.concepts[entry.concept]?.name ?? entry.concept}”
            </span>
          )}
        </>
      ) : null,
      basis.origin ?? basis.concept,
    ],
    ['Prompted by', list(entry.prompted_by), basis.prompted_by],
    ['Why there', entry.why ?? null, basis.prompted_by],
    ['Relieved', list(entry.limit_removed), basis.limit_removed],
    ['Setting', list(entry.setting), basis.setting],
    ['Paid for by', list(entry.funding), basis.funding],
    [
      'Where',
      entry.places?.length
        ? entry.places.map((p, i) => (
            <span key={p.place}>
              {i > 0 && '; '}
              {bundle.places[p.place]?.name ?? p.place}
              {p.note && <span className="relation"> ({p.note})</span>}
            </span>
          ))
        : null,
      basis.places,
    ],
    [
      'Who',
      entry.people?.length
        ? entry.people.map((p, i) => {
            const person = bundle.people[p.person]
            return (
              <span key={p.person}>
                {i > 0 && ', '}
                {person?.name ?? p.person}
                {person?.born !== undefined && person?.died !== undefined && <span className="relation"> ({person.born}–{person.died})</span>}
              </span>
            )
          })
        : null,
      basis.people,
    ],
    ['Organisations', entry.organizations?.map((o) => bundle.organizations[o.organization]?.name ?? o.organization).join(', ') ?? null, basis.organizations],
    ['Society', entry.societies?.map((s) => bundle.societies[s]?.name ?? s).join(', ') ?? null, basis.societies],
    ['Known from', list(entry.known_from), basis.known_from],
    ['Reception', entry.reception ? words(entry.reception) : null, basis.reception],
    ['Today', entry.fate ? `${words(entry.fate)}${entry.end_reason?.length ? ` (${entry.end_reason.map(words).join(', ').toLowerCase()})` : ''}` : null, basis.fate],
    ['Sold', entry.market ? words(entry.market.status) : null, basis.market],
  ]

  const shownFacts = facts.filter(([, value]) => value)
  return (
    <aside className="detail" aria-label={entry.name}>
      <div className="detail-head">
        <h2>{entry.name}</h2>
        <button className="close" aria-label="Close" onClick={() => useApp.getState().select(null)}>
          <svg width="12" height="12" viewBox="0 0 12 12" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" aria-hidden="true">
            <path d="M1.5 1.5l9 9M10.5 1.5l-9 9" />
          </svg>
        </button>
      </div>
      <p className="dateline">
        <strong title={entry.date?.label}>{entry.date ? yearLabel(entry.date) : 'No date established'}</strong>
        {place && ` · ${place.name}${country && country.id !== place.id && ['site', 'settlement'].includes(place.kind) ? `, ${country.name}` : ''}`}
      </p>
      <p className="summary">{entry.summary ?? entry.description}</p>
      <p className="glance">
        {tierName(entry.tier)} · {words(entry.kind)} · {model.fieldNames.get(entry.domain)}
      </p>
      <Lineage entry={entry} links={stated} />

      <Section id="facts" title="What is recorded" count={shownFacts.length}>
        {entry.summary && <p className="small scope">{entry.description}</p>}
        <dl className="facts">
          {entry.impact && (
            <Fact name="Importance" basis={basis.impact}>
              Reach {entry.impact.reach}, depth {entry.impact.depth}, generativity {entry.impact.generativity}, each out of 3
              {entry.impact.note && <span className="relation"> · {entry.impact.note}</span>}
            </Fact>
          )}
          {shownFacts.map(([name, value, b]) => (
            <Fact key={name} name={name} basis={b}>
              {value}
            </Fact>
          ))}
        </dl>
        <p className="key">
          <span>
            <i className="basis" data-basis="sourced" />
            from cited evidence
          </span>
          <span>
            <i className="basis" data-basis="recalled" />
            from memory, to be checked
          </span>
        </p>
        {missing.length > 0 && <p className="small">Not yet researched: {missing.map((f) => FACET_NAMES[f]).join(', ')}.</p>}
      </Section>

      <Section id="events" title="Dated events" count={entry.events.length}>
        <ol className="events">
          {entry.events.map((event) => (
            <li key={event.id}>
              <time>
                {dateLabel(event.label)}
                <span className="type">{words(event.type)}</span>
                {event.id === entry.earliest_record.event && <em className="flag">Earliest record</em>}
                {event.id === entry.community_entry?.event && <em className="flag">In use or known</em>}
              </time>
              <p>{event.statement}</p>
            </li>
          ))}
        </ol>
        {!entry.earliest_record.event && <p className="small">{entry.earliest_record.rationale}</p>}
      </Section>

      {(stated.length > 0 || open.length > 0 || shared.length > 0) && (
        <Section id="links" title="Connections" count={stated.length + shared.length}>
          <ul className="linklist">
            {stated.map((link, i) => (
              <LinkRow key={i} link={link} self={entry.id} />
            ))}
            {shared.map((s) => (
              <SharedRow key={`${s.what}-${s.id}`} label={`Same ${s.what}: ${s.name}`} ids={s.entries.map((e) => e.id)} />
            ))}
            {open.map((link, i) => (
              <li key={`open-${i}`} className="muted">
                <span className="relation">Open question · </span>
                <EntryLink id={link.from === entry.id ? link.to : link.from} plain />
                <div>{link.statement}</div>
              </li>
            ))}
          </ul>
        </Section>
      )}

      {(entry.caveats || entry.research.unresolved?.length) && (
        <Section id="doubts" title="What is not established" count={(entry.caveats ? 1 : 0) + (entry.research.unresolved?.length ?? 0)}>
          {entry.caveats && <p className="small">{entry.caveats}</p>}
          {entry.research.unresolved?.map((u, i) => (
            <p className="small" key={i}>
              <strong>{words(u.about)}:</strong> {u.note}
            </p>
          ))}
        </Section>
      )}

      {sources.length > 0 && (
        <Section id="sources" title="Sources" count={sources.length}>
          <ol className="sources">
            {sources.map((s) => (
              <li key={s.id}>
                {s.authors.slice(0, 2).join(', ')}
                {s.authors.length > 2 ? ' and others' : ''}
                {s.year ? ` (${s.year})` : ''}. {s.url ? <a href={s.url} target="_blank" rel="noreferrer">{s.title}</a> : s.title}
              </li>
            ))}
          </ol>
        </Section>
      )}
    </aside>
  )
}

/** How many rows of the rail to show on each side before pointing at the full list. */
const RAIL = 4

/**
 * What this discovery came from and what followed from it, as a short rail through time. It also
 * lists the other places that reached the same thing, since that is a connection too.
 */
function Lineage({ entry, links }: { entry: Entry; links: Link[] }) {
  const model = useModel()
  const causal = links.filter((l) => l.layer === 'dependence' || l.layer === 'transmission')
  const byDate = (a: Entry, b: Entry) => (a.t ?? 0) - (b.t ?? 0)
  const pick = (ids: string[]) => [...new Set(ids)].map((id) => model.byId.get(id)).filter((e): e is Entry => !!e).sort(byDate)
  const before = pick(causal.filter((l) => l.to === entry.id).map((l) => l.from))
  const after = pick(causal.filter((l) => l.from === entry.id).map((l) => l.to))
  const elsewhere = entry.concept ? (model.shared.get(`concept:${entry.concept}`) ?? []).filter(e => e.id !== entry.id) : []
  // A record that is another place's version of the same thing is listed once, under that heading.
  const parallel = new Set(elsewhere.map((e) => e.id))
  const earlier = before.filter((e) => !parallel.has(e.id))
  const later = after.filter((e) => !parallel.has(e.id))
  if (!earlier.length && !later.length && !elsewhere.length) return null
  const row = (e: Entry, self = false) =>
    self ? (
      <div className="lineage-row" data-self="true" key={e.id}>
        <i />
        <time>{e.date ? yearLabel(e.date) : ''}</time>
        <span>{e.name}</span>
      </div>
    ) : (
      <button className="lineage-row" key={e.id} onClick={() => useApp.getState().select(e.id)}>
        <i />
        <time>{e.date ? yearLabel(e.date) : ''}</time>
        <span>{e.name}</span>
      </button>
    )
  const hidden = Math.max(0, earlier.length - RAIL) + Math.max(0, later.length - RAIL)
  return (
    <>
      {(earlier.length > 0 || later.length > 0) && (
        <div className="lineage">
          <h3>{earlier.length ? (later.length ? 'What it built on, and what followed' : 'What it built on') : 'What followed from it'}</h3>
          {earlier.slice(-RAIL).map((e) => row(e))}
          {row(entry, true)}
          {later.slice(0, RAIL).map((e) => row(e))}
          {hidden > 0 && <p className="lineage-more">and {hidden} more under Connections</p>}
          {!earlier.length && <p className="lineage-more">Nothing it built on has been recorded yet.</p>}
        </div>
      )}
      {elsewhere.length > 0 && (
        <div className="lineage">
          <h3>Also reached elsewhere: {model.bundle.concepts[entry.concept!]?.name ?? entry.concept}</h3>
          {elsewhere.slice(0, 6).map((e) => (
            <button className="lineage-row" key={e.id} onClick={() => useApp.getState().select(e.id)}>
              <i />
              <time>{e.date ? yearLabel(e.date) : ''}</time>
              <span>
                {e.name}
                {e.at && <span className="relation"> · {model.bundle.places[e.at.place]?.name}</span>}
              </span>
            </button>
          ))}
          {elsewhere.length > 6 && <p className="lineage-more">and {elsewhere.length - 6} more under Connections</p>}
        </div>
      )}
    </>
  )
}

function Fact({ name, basis, children }: { name: string; basis?: Basis; children: ReactNode }) {
  return (
    <>
      <dt>{name}</dt>
      <dd>
        {children}
        <Dot basis={basis} />
      </dd>
    </>
  )
}

const RELATION: Record<string, [string, string]> = {
  builds_on: ['Built on', 'Led to'],
  adapts: ['Adapted', 'Adapted by'],
  requires: ['Needed', 'Needed by'],
  uses_instrument: ['Observed with', 'Made possible the observation of'],
  uses_process: ['Produced with', 'Made possible the production of'],
  uses_theory: ['Designed from', 'Informed the design of'],
  transmitted_from: ['Received from', 'Passed on to'],
  supersedes: ['Replaced', 'Replaced by'],
  part_of: ['Part of', 'Includes'],
  independent_of: ['Reached independently of', 'Reached independently of'],
  companion_of: ['Worked together with', 'Worked together with'],
  same_principle: ['Same principle as', 'Same principle as'],
  same_family: ['Same family as', 'Same family as'],
}

function LinkRow({ link, self }: { link: Link; self: string }) {
  const incoming = link.to === self
  const relation = RELATION[link.type]?.[incoming ? 0 : 1] ?? words(link.type)
  return (
    <li>
      <span className="relation">{relation} · </span>
      <EntryLink id={incoming ? link.from : link.to} />
      <div>{link.statement}</div>
    </li>
  )
}

function SharedRow({ label, ids }: { label: string; ids: string[] }) {
  const [all, setAll] = useState(false)
  const shown = all ? ids : ids.slice(0, 4)
  return (
    <li>
      <span className="relation">{label}</span>
      <div>
        {shown.map((id, i) => (
          <span key={id}>
            {i > 0 && ' · '}
            <EntryLink id={id} plain />
          </span>
        ))}
        {ids.length > shown.length && (
          <>
            {' · '}
            <button className="more" onClick={() => setAll(true)}>
              {ids.length - shown.length} more
            </button>
          </>
        )}
      </div>
    </li>
  )
}
