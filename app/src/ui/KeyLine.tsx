import { useApp, useDimension, useModel } from '../store.ts'

/**
 * A quiet line saying what the colours mean. It is left out where the page already says so, as
 * on a timeline with one headed row per category. Click a name to hide it; the Colour menu has the rest.
 */
export function KeyLine() {
  const model = useModel()
  const dimension = useDimension()
  const hidden = useApp((s) => s.hidden)
  const view = useApp((s) => s.view)
  const lanes = useApp((s) => s.lanes)
  if (view === 'timeline' && lanes) return null
  const present = new Set(model.entries.map(dimension.of))
  return (
    <div className="keyline" aria-label={`Colours: ${dimension.name}`}>
      {dimension.categories
        .filter((c) => present.has(c.id))
        .map((c) => {
          const off = hidden.has(`${dimension.id}:${c.id}`)
          return (
            <button key={c.id} className="key" aria-pressed={!off} title={`${c.hint ? `${c.hint}. ` : ''}Click to ${off ? 'show' : 'hide'}.`} onClick={() => useApp.getState().toggleCategory(dimension.id, c.id)}>
              <i style={{ background: c.color }} />
              {c.name}
            </button>
          )
        })}
      {view !== 'trends' && view !== 'index' && (
        <span className="key-note">
          <i className="strong" />
          <i className="pale" />
          paler marks are minor discoveries
        </span>
      )}
    </div>
  )
}
