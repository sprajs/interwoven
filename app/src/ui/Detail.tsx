import { useMemo, useState, type ReactNode } from 'react'
import { sharedWith, type Entry } from '../data/model.ts'
import type { Basis, Evidence, Link } from '../data/types.ts'
import { dateLabel, plural, words } from '../lib/text.ts'
import { useApp, useModel } from '../store.ts'

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

export function Detail({ entry }: { entry: Entry }) {
  const model = useModel()
  const { bundle } = model
  const basis = entry.research.basis
  const list = (ids: string[] | undefined) => (ids?.length ? ids.map(words).join(', ') : null)
  const links = model.linksOf.get(entry.id) ?? []
  const stated = links.filter((l) => l.status === 'established')
  const open = links.filter((l) => l.status !== 'established')
  const shared = useMemo(() => sharedWith(model, entry), [model, entry])
  const sources = useMemo(() => {
    const ids = new Set<string>()
    const add = (items?: Evidence[]) => items?.forEach((e) => ids.add(e.source))
    entry.events.forEach((e) => add(e.evidence))
    links.forEach((l) => add(l.evidence))
    entry.research.unresolved?.forEach((u) => add(u.evidence))
    return [...ids].map((id) => ({ id, ...bundle.sources[id]! })).filter((s) => s.title)
  }, [entry, links, bundle])
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
          {entry.origin ? words(entry.origin) : 'Not yet assessed'}
          {entry.concept && <span className="relation"> · one of several reaching “{bundle.concepts[entry.concept]?.name ?? entry.concept}”</span>}
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

  return (
    <aside className="detail" aria-label={entry.name}>
      <div className="detail-head">
        <h2 style={{ fontStyle: entry.kind === 'science' ? 'italic' : undefined }}>{entry.name}</h2>
        <button className="close" aria-label="Close" onClick={() => useApp.getState().select(null)}>
          <svg width="12" height="12" viewBox="0 0 12 12" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" aria-hidden="true">
            <path d="M1.5 1.5l9 9M10.5 1.5l-9 9" />
          </svg>
        </button>
      </div>
      <p className="dateline">
        <strong>{entry.date ? dateLabel(entry.date.label) : 'No date established'}</strong>
        {place && ` · ${place.name}${country && country.id !== place.id ? `, ${country.name}` : ''}`}
        {` · ${words(entry.kind)}`}
      </p>
      {entry.summary && <p className="summary">{entry.summary}</p>}
      <p className="description">{entry.description}</p>

      <h3>What is recorded</h3>
      <dl className="facts">
        {facts
          .filter(([, value]) => value)
          .map(([name, value, b]) => (
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

      <h3>
        Dated events <span>{entry.events.length}</span>
      </h3>
      <ol className="events">
        {entry.events.map((event) => (
          <li key={event.id}>
            <time>
              {dateLabel(event.label)}
              <span className="type">{words(event.type)}</span>
            </time>
            <p>
              {event.statement}
              {event.id === entry.earliest_record.event && <em className="flag"> · Earliest record</em>}
              {event.id === entry.community_entry?.event && <em className="flag"> · In use or known</em>}
            </p>
          </li>
        ))}
      </ol>
      {!entry.earliest_record.event && <p className="small">{entry.earliest_record.rationale}</p>}

      {(stated.length > 0 || open.length > 0) && (
        <>
          <h3>
            Stated links <span>{stated.length}</span>
          </h3>
          <ul className="linklist">
            {stated.map((link, i) => (
              <LinkRow key={i} link={link} self={entry.id} />
            ))}
            {open.map((link, i) => (
              <li key={`open-${i}`} style={{ color: 'var(--ink-3)' }}>
                <span className="relation">Open question · </span>
                <EntryLink id={link.from === entry.id ? link.to : link.from} plain />
                <div>{link.statement}</div>
              </li>
            ))}
          </ul>
        </>
      )}

      {shared.length > 0 && (
        <>
          <h3>Shares something with</h3>
          <ul className="linklist">
            {shared.map((s) => (
              <SharedRow key={`${s.what}-${s.id}`} label={`Same ${s.what}: ${s.name}`} ids={s.entries.map((e) => e.id)} />
            ))}
          </ul>
        </>
      )}

      {(entry.caveats || entry.research.unresolved?.length) && (
        <>
          <h3>What is not established</h3>
          {entry.caveats && <p className="small">{entry.caveats}</p>}
          {entry.research.unresolved?.map((u, i) => (
            <p className="small" key={i}>
              <strong>{words(u.about)}:</strong> {u.note}
            </p>
          ))}
        </>
      )}

      {sources.length > 0 && <Sources sources={sources} />}
    </aside>
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

function Sources({ sources }: { sources: { id: string; title: string; authors: string[]; year?: number; url?: string }[] }) {
  const [all, setAll] = useState(false)
  const shown = all ? sources : sources.slice(0, 4)
  return (
    <>
      <h3>
        Sources <span>{sources.length}</span>
      </h3>
      <ol className="sources">
        {shown.map((s) => (
          <li key={s.id}>
            {s.authors.slice(0, 2).join(', ')}
            {s.authors.length > 2 ? ' and others' : ''}
            {s.year ? ` (${s.year})` : ''}. {s.url ? <a href={s.url} target="_blank" rel="noreferrer">{s.title}</a> : s.title}
          </li>
        ))}
      </ol>
      {sources.length > shown.length && (
        <button className="more" onClick={() => setAll(true)}>
          Show all {plural(sources.length, 'source')}
        </button>
      )}
    </>
  )
}
