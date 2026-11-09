import { useMemo, useState } from 'react'
import type { Entry } from '../data/model.ts'
import { plural, shortDate, words } from '../lib/text.ts'
import { useApp, useDimension, useFiltered, useMatches, useModel } from '../store.ts'

type SortKey = 'name' | 'date' | 'field' | 'place' | 'origin' | 'tier' | 'filled'

const COLUMNS: { key: SortKey; name: string; hint?: string }[] = [
  { key: 'name', name: 'Discovery' },
  { key: 'date', name: 'Earliest record' },
  { key: 'field', name: 'Field' },
  { key: 'place', name: 'Place' },
  { key: 'origin', name: 'Origin' },
  { key: 'tier', name: 'Tier', hint: '0: several fields or generations depended on it. 1: major in its field. 2: a bounded contribution. 3: fine detail.' },
  { key: 'filled', name: 'Researched', hint: 'How many of the facets have a value, and where the values come from' },
]

const FACET_LABELS: Record<string, string> = {
  summary: 'Summary',
  domain: 'Field',
  tier: 'Tier',
  advance: 'What was new',
  scale: 'Size of change',
  origin: 'Independence',
  concept: 'Shared concept',
  prompted_by: 'What prompted it',
  limit_removed: 'Bottleneck relieved',
  setting: 'Setting',
  funding: 'Who paid',
  places: 'Place',
  people: 'People',
  organizations: 'Organisations',
  societies: 'Society',
  known_from: 'How it is known',
  reception: 'Reception',
  fate: 'Standing today',
  market: 'Whether sold',
  measures: 'Performance figures',
  events: 'Dated events',
  links: 'Stated links',
}

/** How many rows to draw before asking. A table of thousands is slow and nobody reads it. */
const PAGE = 300

/**
 * Every record in view as a table, under a summary of how far each facet has been researched.
 * This is the working view: it shows what the dataset knows and where the gaps are.
 */
export function IndexView() {
  const model = useModel()
  const dimension = useDimension()
  const filtered = useFiltered()
  const matches = useMatches()
  const span = useApp((s) => s.window)
  const selected = useApp((s) => s.selected)
  const [sort, setSort] = useState<{ key: SortKey; down: boolean }>({ key: 'date', down: false })
  const [limit, setLimit] = useState(PAGE)

  const rows = useMemo(() => {
    // Undated records have no place in time, so the window cannot exclude them. They stay listed.
    const inView = filtered.filter((e) => (!matches || matches.has(e.id)) && (e.t === undefined || (e.t >= span[0] && e.t <= span[1])))
    const place = (e: Entry) => (e.at ? (model.bundle.places[e.at.place]?.name ?? '') : '')
    const value: Record<SortKey, (e: Entry) => string | number> = {
      name: (e) => e.name.toLowerCase(),
      date: (e) => e.t ?? Infinity,
      field: (e) => model.fieldNames.get(e.domain) ?? '',
      place,
      origin: (e) => e.origin ?? '~',
      tier: (e) => e.tier,
      filled: (e) => e.filled,
    }
    const pick = value[sort.key]
    return inView.sort((a, b) => {
      const x = pick(a)
      const y = pick(b)
      const order = x < y ? -1 : x > y ? 1 : a.name.localeCompare(b.name)
      return sort.down ? -order : order
    })
  }, [filtered, matches, span, sort, model])

  const coverage = useMemo(
    () =>
      model.bundle.facets.map((facet) => {
        const counts = { reviewed: 0, sourced: 0, recalled: 0 }
        for (const e of rows) {
          const basis = e.research.basis[facet]
          if (basis === 'reviewed' || basis === 'sourced' || basis === 'recalled') counts[basis] += 1
        }
        return { facet, ...counts, filled: counts.reviewed + counts.sourced + counts.recalled }
      }),
    [rows, model],
  )

  const total = Math.max(1, rows.length)
  const facets = model.bundle.facets.length
  return (
    <div className="index">
      <section className="index-summary" aria-label="How much is researched">
        <p className="index-intro">
          <strong>{plural(rows.length, 'discovery', 'discoveries')}</strong> in view. Each bar shows how many of them have a value for one facet:{' '}
          <Key name="reviewed" text="checked by a second reader" /> <Key name="sourced" text="from cited evidence" /> <Key name="recalled" text="from memory, to be checked" />. The
          empty part has not been researched.
        </p>
        {coverage.map((c) => (
          <div className="coverage-item" key={c.facet}>
            <header>
              <span>{FACET_LABELS[c.facet] ?? words(c.facet)}</span>
              <b>{Math.round((c.filled / total) * 100)}%</b>
            </header>
            <Bar reviewed={c.reviewed} sourced={c.sourced} recalled={c.recalled} total={total} />
          </div>
        ))}
      </section>
      <table className="records">
        <thead>
          <tr>
            {COLUMNS.map((column) => (
              <th
                key={column.key}
                title={column.hint}
                aria-sort={sort.key === column.key ? (sort.down ? 'descending' : 'ascending') : undefined}
                onClick={() => setSort((s) => ({ key: column.key, down: s.key === column.key ? !s.down : column.key === 'filled' }))}
              >
                {column.name}
                {sort.key === column.key ? (sort.down ? ' ↓' : ' ↑') : ''}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, limit).map((e) => {
            const category = dimension.categories.find((c) => c.id === dimension.of(e))
            const basis = Object.values(e.research.basis)
            const count = (b: string) => basis.filter((x) => x === b).length
            return (
              <tr key={e.id} data-selected={selected === e.id} onClick={() => useApp.getState().select(e.id)}>
                <td className="name" style={{ fontStyle: e.kind === 'science' ? 'italic' : undefined }}>
                  <i className="swatch" style={{ background: category?.color }} title={category?.name} />
                  {e.name}
                </td>
                <td className="num">{e.date ? shortDate(e.date.label) : <span className="muted">No date yet</span>}</td>
                <td>{model.fieldNames.get(e.domain)}</td>
                <td>{e.at ? model.bundle.places[e.at.place]?.name : <span className="muted">—</span>}</td>
                <td>{e.origin ? words(e.origin) : <span className="muted">—</span>}</td>
                <td className="num">{e.tier}</td>
                <td title={`${e.filled} of ${facets} facets have a value`}>
                  <Bar reviewed={count('reviewed')} sourced={count('sourced')} recalled={count('recalled')} total={facets} />
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
      {rows.length > limit && (
        <button className="more" onClick={() => setLimit(rows.length)}>
          Show all {plural(rows.length, 'discovery', 'discoveries')}
        </button>
      )}
    </div>
  )
}

function Bar({ reviewed, sourced, recalled, total }: { reviewed: number; sourced: number; recalled: number; total: number }) {
  const width = (n: number) => `${(n / total) * 100}%`
  return (
    <div className="bar">
      {reviewed > 0 && <i className="reviewed" style={{ width: width(reviewed) }} />}
      {sourced > 0 && <i className="sourced" style={{ width: width(sourced) }} />}
      {recalled > 0 && <i className="recalled" style={{ width: width(recalled) }} />}
    </div>
  )
}

function Key({ name, text }: { name: string; text: string }) {
  return (
    <span style={{ whiteSpace: 'nowrap' }}>
      <span className="bar" style={{ display: 'inline-flex', width: 14, verticalAlign: 1, marginRight: 5 }}>
        <i className={name} style={{ width: '100%' }} />
      </span>
      {text}
    </span>
  )
}
