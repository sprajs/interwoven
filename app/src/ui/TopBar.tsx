import { useMemo, useState } from 'react'
import { shortDate } from '../lib/text.ts'
import { useApp, useModel, VIEWS } from '../store.ts'

export function TopBar() {
  const view = useApp((s) => s.view)
  return (
    <header className="topbar">
      <h1 className="brand">Interwoven</h1>
      <nav className="tabs" role="tablist" aria-label="Views">
        {VIEWS.map((v) => (
          <button key={v.id} role="tab" className="tab" aria-selected={view === v.id} title={v.hint} onClick={() => useApp.getState().setView(v.id)}>
            {v.name}
          </button>
        ))}
      </nav>
      <Search />
    </header>
  )
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
        placeholder="Find a discovery, person or place"
        aria-label="Find a discovery, person or place"
        value={query}
        onChange={(event) => {
          useApp.getState().setQuery(event.target.value)
          setOpen(true)
          setActive(0)
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        onKeyDown={(event) => {
          if (event.key === 'ArrowDown') setActive((i) => Math.min(i + 1, Math.min(results.length, 12) - 1))
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
          {results.slice(0, 12).map((e, i) => (
            <button key={e.id} role="option" aria-selected={i === active} data-active={i === active} className="search-result" onMouseDown={() => choose(e.id)}>
              <span>{e.name}</span>
              <span>{e.date ? shortDate(e.date.label) : 'undated'}</span>
            </button>
          ))}
          {results.length > 12 && <div className="search-empty">and {results.length - 12} more, highlighted in the view</div>}
          {!results.length && <div className="search-empty">Nothing matches.</div>}
        </div>
      )}
    </div>
  )
}
