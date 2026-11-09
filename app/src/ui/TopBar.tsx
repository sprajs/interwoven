import { useMemo, useState } from 'react'
import { LAYERS } from '../data/model.ts'
import { DIM_ORDER } from '../dims.ts'
import { shortDate } from '../lib/text.ts'
import { useApp, useDimension, useDimensions, useFiltered, useModel, VIEWS } from '../store.ts'
import type { ScaleId } from '../time.ts'
import { Menu, MenuHeading, Option } from './Menu.tsx'

const SCALES: { id: ScaleId; name: string; hint: string }[] = [
  { id: 'people', name: 'Population', hint: 'Every stretch of the axis holds the same number of human lifetimes' },
  { id: 'calendar', name: 'Calendar', hint: 'Every year is the same width' },
  { id: 'log', name: 'Logarithmic', hint: 'Each step back in time covers ten times as many years' },
]

/**
 * The one bar of the app: its name, the views, and four buttons that each state a choice and open
 * its alternatives. Nothing else is laid out, so the page belongs to the data.
 */
export function TopBar() {
  const view = useApp((s) => s.view)
  const scale = useApp((s) => s.scale)
  const layers = useApp((s) => s.layers)
  const lanes = useApp((s) => s.lanes)
  const majorOnly = useApp((s) => s.majorOnly)
  const dimension = useDimension()
  const app = useApp.getState()
  const linkNames = LAYERS.filter((l) => layers.has(l.id)).map((l) => l.name)
  return (
    <header className="topbar">
      <h1 className="brand">Interwoven</h1>
      <nav className="tabs" role="tablist" aria-label="Views">
        {VIEWS.map((v) => (
          <button key={v.id} role="tab" className="tab" aria-selected={view === v.id} title={v.hint} onClick={() => app.setView(v.id)}>
            {v.name}
          </button>
        ))}
      </nav>
      <div className="tools">
        <Menu label="Time" value={SCALES.find((s) => s.id === scale)!.name}>
          <MenuHeading>How time is spread across the page</MenuHeading>
          {SCALES.map((s) => (
            <Option key={s.id} single name={s.name} hint={s.hint} on={scale === s.id} onChoose={() => app.setScale(s.id)} />
          ))}
        </Menu>
        <ColourMenu />
        {(view === 'timeline' || view === 'map') && (
          <Menu label="Links" value={linkNames.length === 0 ? 'None' : linkNames.length === 1 ? linkNames[0]! : `${linkNames.length} kinds`}>
            <MenuHeading>Draw the stated links between discoveries</MenuHeading>
            {LAYERS.map((l) => (
              <Option key={l.id} name={l.name} hint={l.hint} on={layers.has(l.id)} onChoose={() => app.toggleLayer(l.id)} />
            ))}
          </Menu>
        )}
        <Menu label="Show" value={majorOnly ? 'Major only' : 'Everything'} align="right">
          <MenuHeading>Which discoveries</MenuHeading>
          <Option single name="Everything" hint="Every discovery recorded so far" on={!majorOnly} onChoose={() => app.setMajorOnly(false)} />
          <Option single name="Major only" hint="Only those that a field, or several fields, went on to depend on" on={majorOnly} onChoose={() => app.setMajorOnly(true)} />
          {view === 'timeline' && (
            <>
              <MenuHeading>Rows of the timeline</MenuHeading>
              <Option single name={`One row per ${dimension.name.toLowerCase()}`} on={lanes} onChoose={() => app.setLanes(true)} />
              <Option single name="All together" hint="One shape, to read the density of discovery" on={!lanes} onChoose={() => app.setLanes(false)} />
            </>
          )}
        </Menu>
        <Search />
      </div>
    </header>
  )
}

/** What colour means, and which of its categories are shown. */
function ColourMenu() {
  const model = useModel()
  const dims = useDimensions()
  const dimension = useDimension()
  const hidden = useApp((s) => s.hidden)
  const span = useApp((s) => s.window)
  const filtered = useFiltered()
  const app = useApp.getState()
  const counts = new Map<string, number>()
  for (const e of filtered) {
    if (e.t === undefined || e.t < span[0] || e.t > span[1]) continue
    counts.set(dimension.of(e), (counts.get(dimension.of(e)) ?? 0) + 1)
  }
  const present = useMemo(() => new Set(model.entries.map(dimension.of)), [model, dimension])
  return (
    <Menu label="Colour" value={dimension.name}>
      <MenuHeading>What colour means</MenuHeading>
      {DIM_ORDER.map((d) => (
        <Option key={d} single name={dims[d].name} hint={HINTS[d]} on={dimension.id === d} onChoose={() => app.setDim(d)} />
      ))}
      <MenuHeading>Shown, with how many are in view</MenuHeading>
      {dimension.categories
        .filter((c) => present.has(c.id))
        .map((c) => {
          const on = !hidden.has(`${dimension.id}:${c.id}`)
          return (
            <Option
              key={c.id}
              name={c.name}
              on={on}
              color={c.color}
              count={on ? (counts.get(c.id) ?? 0) : undefined}
              onChoose={() => app.toggleCategory(dimension.id, c.id)}
              onAlone={() => app.toggleCategory(dimension.id, c.id, true)}
            />
          )
        })}
    </Menu>
  )
}

const HINTS = {
  subject: 'Six broad families of fields',
  region: 'The part of the world it happened in',
  kind: 'Technology, science, mathematics or practice',
  origin: 'First known, reached independently, or derived',
}

/** Typing dims everything that does not match, in every view. The list underneath jumps to one record. */
function Search() {
  const model = useModel()
  const query = useApp((s) => s.query)
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const results = useMemo(() => {
    const terms = query.toLowerCase().split(/\s+/).filter(Boolean)
    if (!terms.length) return []
    return model.entries
      .filter((e) => terms.every((w) => e.haystack.includes(w)))
      .sort((a, b) => Number(b.name.toLowerCase().includes(terms[0]!)) - Number(a.name.toLowerCase().includes(terms[0]!)) || a.tier - b.tier)
  }, [model, query])
  const choose = (id: string) => {
    useApp.getState().select(id)
    setOpen(false)
  }
  return (
    <div className="search">
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">
        <circle cx="6" cy="6" r="4.5" />
        <path d="M9.5 9.5 13 13" strokeLinecap="round" />
      </svg>
      <input
        type="search"
        placeholder="Find"
        aria-label="Find a discovery, person or place"
        title="Find a discovery, person or place"
        value={query}
        onChange={(event) => {
          useApp.getState().setQuery(event.target.value)
          setOpen(true)
          setActive(0)
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        onKeyDown={(event) => {
          if (event.key === 'ArrowDown') setActive((i) => Math.min(i + 1, Math.min(results.length, 10) - 1))
          else if (event.key === 'ArrowUp') setActive((i) => Math.max(i - 1, 0))
          else if (event.key === 'Enter' && results[active]) choose(results[active].id)
          else if (event.key === 'Escape') {
            useApp.getState().setQuery('')
            event.currentTarget.blur()
          } else return
          event.preventDefault()
        }}
      />
      {open && query.trim() && (
        <div className="search-results" role="listbox">
          {results.slice(0, 10).map((e, i) => (
            <button key={e.id} role="option" aria-selected={i === active} data-active={i === active} className="search-result" onMouseDown={() => choose(e.id)}>
              <span>{e.name}</span>
              <span>{e.date ? shortDate(e.date.label) : 'undated'}</span>
            </button>
          ))}
          {results.length > 10 && <div className="search-empty">and {results.length - 10} more, picked out in the view</div>}
          {!results.length && <div className="search-empty">Nothing matches.</div>}
        </div>
      )}
    </div>
  )
}
