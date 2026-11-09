import { useMemo } from 'react'
import { create } from 'zustand'
import type { Entry, Model } from './data/model.ts'
import type { LinkLayer } from './data/types.ts'
import { DIM_ORDER, dimensions, type DimId, type Dimension } from './dims.ts'
import { calendar, log, peopleScale, PRESENT, type ScaleId, type TimeScale } from './time.ts'

export type ViewId = 'timeline' | 'map' | 'trends' | 'index'

export const VIEWS: { id: ViewId; name: string; hint: string }[] = [
  { id: 'timeline', name: 'Timeline', hint: 'Every discovery at its date' },
  { id: 'map', name: 'Map', hint: 'Where discoveries were made, through time' },
  { id: 'trends', name: 'Trends', hint: 'How many discoveries, per period and per person' },
  { id: 'index', name: 'Index', hint: 'Every record, and how much of it is researched' },
]

export interface Hover {
  id: string
  /** Where on the page to point at, in viewport pixels. */
  x: number
  y: number
}

interface State {
  model: Model | null
  error: string | null
  view: ViewId
  scale: ScaleId
  dim: DimId
  layers: ReadonlySet<LinkLayer>
  /** The stretch of time in view. */
  window: [number, number]
  /** Categories switched off, as `dimension:category`. */
  hidden: ReadonlySet<string>
  /** Show only tiers 0 and 1. */
  majorOnly: boolean
  /** Split the timeline into one row per category. */
  lanes: boolean
  query: string
  selected: string | null
  hover: Hover | null
  playing: boolean
  setModel(model: Model): void
  setError(message: string): void
  setView(view: ViewId): void
  setScale(scale: ScaleId): void
  setDim(dim: DimId): void
  toggleLayer(layer: LinkLayer): void
  setWindow(window: [number, number]): void
  toggleCategory(dim: DimId, category: string, solo?: boolean): void
  setMajorOnly(on: boolean): void
  setLanes(on: boolean): void
  setQuery(query: string): void
  select(id: string | null): void
  setHover(hover: Hover | null): void
  setPlaying(on: boolean): void
}

const VIEW_IDS = VIEWS.map((v) => v.id)
const SCALE_IDS: ScaleId[] = ['calendar', 'log', 'people']

/** The start of the default window: recorded history, where almost all of the data is. */
export const DEFAULT_START = -3999

function fromHash(): Partial<State> {
  const params = new URLSearchParams(location.hash.slice(1))
  const out: Partial<State> = {}
  const view = params.get('view') as ViewId | null
  if (view && VIEW_IDS.includes(view)) out.view = view
  const scale = params.get('scale') as ScaleId | null
  if (scale && SCALE_IDS.includes(scale)) out.scale = scale
  const dim = params.get('by') as DimId | null
  if (dim && DIM_ORDER.includes(dim)) out.dim = dim
  const links = params.get('links')
  if (links !== null) out.layers = new Set(links.split(',').filter(Boolean) as LinkLayer[])
  const span = params.get('t')?.split(',').map(Number)
  if (span?.length === 2 && span.every(Number.isFinite) && span[0]! < span[1]!) out.window = [span[0]!, span[1]!]
  const selected = params.get('id')
  if (selected) out.selected = selected
  if (params.get('lanes') === '0') out.lanes = false
  if (params.get('major') === '1') out.majorOnly = true
  return out
}

export const useApp = create<State>((set) => ({
  model: null,
  error: null,
  view: 'timeline',
  scale: 'people',
  dim: 'subject',
  layers: new Set(),
  window: [DEFAULT_START, PRESENT],
  hidden: new Set(),
  majorOnly: false,
  lanes: true,
  query: '',
  selected: null,
  hover: null,
  playing: false,
  ...fromHash(),
  setModel: (model) => set({ model }),
  setError: (error) => set({ error }),
  setView: (view) => set({ view, hover: null, playing: false }),
  setScale: (scale) => set({ scale }),
  setDim: (dim) => set({ dim }),
  toggleLayer: (layer) =>
    set((s) => {
      const layers = new Set(s.layers)
      if (layers.has(layer)) layers.delete(layer)
      else layers.add(layer)
      return { layers }
    }),
  setWindow: (window) => set({ window }),
  toggleCategory: (dim, category, solo) =>
    set((s) => {
      const key = `${dim}:${category}`
      const hidden = new Set(s.hidden)
      if (solo) {
        // Show this one alone, or everything again if it already stands alone.
        const all = dimensions(s.model!)[dim].categories.map((c) => `${dim}:${c.id}`)
        const alone = all.every((k) => (k === key ? !hidden.has(k) : hidden.has(k)))
        for (const k of all) {
          if (alone || k === key) hidden.delete(k)
          else hidden.add(k)
        }
      } else if (hidden.has(key)) hidden.delete(key)
      else hidden.add(key)
      return { hidden }
    }),
  setMajorOnly: (majorOnly) => set({ majorOnly }),
  setLanes: (lanes) => set({ lanes }),
  setQuery: (query) => set({ query }),
  select: (selected) => set({ selected }),
  setHover: (hover) => set({ hover }),
  setPlaying: (playing) => set({ playing }),
}))

// Keep the address in step with the view, so that any state can be linked to and reloaded.
useApp.subscribe((s) => {
  const params = new URLSearchParams()
  params.set('view', s.view)
  params.set('scale', s.scale)
  params.set('by', s.dim)
  if (s.layers.size) params.set('links', [...s.layers].join(','))
  params.set('t', s.window.map((t) => Math.round(t)).join(','))
  if (s.selected) params.set('id', s.selected)
  if (!s.lanes) params.set('lanes', '0')
  if (s.majorOnly) params.set('major', '1')
  const hash = `#${params.toString().replace(/%2C/g, ',')}`
  if (hash !== location.hash) history.replaceState(null, '', hash)
})

// Following a link that differs only after the # does not reload the page, so read it again.
window.addEventListener('hashchange', () => useApp.setState(fromHash()))

/** The model, once loaded. Views are only mounted after that. */
export function useModel(): Model {
  return useApp((s) => s.model)!
}

export function useDimensions(): Record<DimId, Dimension> {
  const model = useModel()
  return useMemo(() => dimensions(model), [model])
}

export function useDimension(): Dimension {
  const dim = useApp((s) => s.dim)
  return useDimensions()[dim]
}

export function useScale(): TimeScale {
  const model = useModel()
  const id = useApp((s) => s.scale)
  return useMemo(() => {
    if (id === 'log') return log
    const personYears = model.bundle.world_person_years
    if (id === 'people' && personYears) return peopleScale(personYears)
    return calendar
  }, [id, model])
}

/** The full stretch of time the data covers, a little wider than the data itself. */
export function useLimits(): [number, number] {
  const model = useModel()
  return useMemo(() => [Math.min(Math.floor((model.extent[0] - 2000) / 50000) * 50000, -200000) + 1, PRESENT], [model])
}

/** Discoveries that pass the category switches and the tier switch. Search and time are applied by each view. */
export function useFiltered(): Entry[] {
  const model = useModel()
  const dims = useDimensions()
  const hidden = useApp((s) => s.hidden)
  const majorOnly = useApp((s) => s.majorOnly)
  return useMemo(() => {
    const active = DIM_ORDER.filter((d) => [...hidden].some((k) => k.startsWith(`${d}:`)))
    return model.entries.filter((e) => {
      if (majorOnly && e.tier > 1) return false
      for (const d of active) if (hidden.has(`${d}:${dims[d].of(e)}`)) return false
      return true
    })
  }, [model, dims, hidden, majorOnly])
}

/** Ids that match the search box, or null when nothing is typed. */
export function useMatches(): ReadonlySet<string> | null {
  const model = useModel()
  const query = useApp((s) => s.query)
  return useMemo(() => {
    const words = query.toLowerCase().split(/\s+/).filter(Boolean)
    if (!words.length) return null
    return new Set(model.entries.filter((e) => words.every((w) => e.haystack.includes(w))).map((e) => e.id))
  }, [model, query])
}
