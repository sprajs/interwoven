import { LAYERS } from '../data/model.ts'
import { DIM_ORDER } from '../dims.ts'
import { useApp, useDimension, useDimensions, useFiltered, useModel } from '../store.ts'
import { calendar, log, type ScaleId } from '../time.ts'

const SCALES: { id: ScaleId; name: string; hint: string }[] = [
  { id: 'people', name: 'People alive', hint: 'Every stretch holds the same number of human lifetimes' },
  { id: 'calendar', name: calendar.name, hint: calendar.hint },
  { id: 'log', name: log.name, hint: log.hint },
]

/** One row of choices shared by every view: how time is spread, what colour means, and which links are drawn. */
export function Controls() {
  const view = useApp((s) => s.view)
  const scale = useApp((s) => s.scale)
  const dim = useApp((s) => s.dim)
  const layers = useApp((s) => s.layers)
  const lanes = useApp((s) => s.lanes)
  const majorOnly = useApp((s) => s.majorOnly)
  const dims = useDimensions()
  const app = useApp.getState()
  return (
    <div className="controls">
      <div className="controls-row">
      <div className="control">
        <span className="control-name">Time</span>
        <div className="choices">
          {SCALES.map((s) => (
            <button key={s.id} className="choice" aria-pressed={scale === s.id} title={s.hint} onClick={() => app.setScale(s.id)}>
              {s.name}
            </button>
          ))}
        </div>
      </div>
      <div className="control">
        <span className="control-name">Colour</span>
        <div className="choices">
          {DIM_ORDER.map((d) => (
            <button key={d} className="choice" aria-pressed={dim === d} onClick={() => app.setDim(d)}>
              {dims[d].name}
            </button>
          ))}
        </div>
      </div>
      {(view === 'timeline' || view === 'map') && (
        <div className="control">
          <span className="control-name">Links</span>
          <div className="choices">
            {LAYERS.map((l) => (
              <button key={l.id} className="choice" aria-pressed={layers.has(l.id)} title={l.hint} onClick={() => app.toggleLayer(l.id)}>
                {l.name}
              </button>
            ))}
          </div>
        </div>
      )}
      <div className="spacer" />
      <div className="control">
        {view === 'timeline' && (
          <button className="choice toggle" aria-pressed={lanes} title="Give each category a row of its own" onClick={() => app.setLanes(!lanes)}>
            Split rows
          </button>
        )}
        <button className="choice toggle" aria-pressed={majorOnly} title="Only discoveries that a field, or several fields, went on to depend on" onClick={() => app.setMajorOnly(!majorOnly)}>
          Major only
        </button>
      </div>
      </div>
      <Legend />
    </div>
  )
}

/** What each colour means, with how many discoveries are in view. Click to hide one; double-click to show it alone. */
function Legend() {
  const model = useModel()
  const dimension = useDimension()
  const hidden = useApp((s) => s.hidden)
  const span = useApp((s) => s.window)
  const filtered = useFiltered()
  const counts = new Map<string, number>()
  for (const e of filtered) {
    if (e.t === undefined || e.t < span[0] || e.t > span[1]) continue
    counts.set(dimension.of(e), (counts.get(dimension.of(e)) ?? 0) + 1)
  }
  const present = new Set(model.entries.map(dimension.of))
  return (
    <div className="legend" aria-label={`Colours: ${dimension.name}`}>
      {dimension.categories
        .filter((c) => present.has(c.id))
        .map((c) => {
          const off = hidden.has(`${dimension.id}:${c.id}`)
          return (
            <button
              key={c.id}
              className="legend-item"
              aria-pressed={!off}
              title={`${c.hint ? `${c.hint}\n` : ''}Click to ${off ? 'show' : 'hide'}. Double-click to show alone.`}
              onClick={() => useApp.getState().toggleCategory(dimension.id, c.id)}
              onDoubleClick={() => useApp.getState().toggleCategory(dimension.id, c.id, true)}
            >
              <i style={{ background: c.color }} />
              {c.name}
              <b>{off ? '' : (counts.get(c.id) ?? 0)}</b>
            </button>
          )
        })}
    </div>
  )
}
