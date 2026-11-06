import { create } from 'zustand'
import { layoutStory, lineageOf, threadOf, type RowOrder, type Story } from './data/derive.ts'
import type { LifeRecord } from './data/lifecycle.ts'
import type { Model } from './data/model.ts'
import type { RawNode } from './data/types.ts'
import type { Engine, Mode } from './engine/Engine.ts'

export interface Hover {
  index: number
  x: number
  y: number
}

interface AppState {
  model: Model | null
  error: string | null
  mode: Mode
  compressed: boolean
  hiddenKinds: ReadonlySet<string>
  activeLabels: ReadonlySet<string>
  selected: number | null
  /** The id of a selected entry that has no place on the chart yet. */
  unplacedSelected: string | null
  /** The order of the reach view's rows. */
  rowOrder: RowOrder
  /** The thread being followed, if any. */
  story: Story | null
  /** Documented later lives of the entries on the chart, from the lifecycle sidecar. */
  life: Map<number, LifeRecord>
  /** The same for every entry in the research, by id, placed or not. */
  lifeById: Record<string, LifeRecord>
  /** Entries matching the search box, while something is typed there. */
  searchHits: ReadonlySet<number> | null
  /** A label being pointed at. */
  previewLabel: string | null
  /** How many periods are open by hand. */
  openPeriods: number
  hover: Hover | null
  labelsOpen: boolean
  searchOpen: boolean
  unplacedOpen: boolean
  /** Deepest level currently showing, 0 to 3. */
  depth: number
  setModel(model: Model): void
  setError(message: string): void
  setMode(mode: Mode): void
  setCompressed(compressed: boolean): void
  toggleKind(id: string): void
  toggleLabel(id: string): void
  clearFilters(): void
  select(index: number | null): void
  selectUnplaced(id: string | null): void
  setHover(hover: Hover | null): void
  setLabelsOpen(open: boolean): void
  setSearchOpen(open: boolean): void
  setUnplacedOpen(open: boolean): void
  setDepth(depth: number): void
  setRowOrder(order: RowOrder): void
  setLife(life: Map<number, LifeRecord>, lifeById: Record<string, LifeRecord>): void
  setSearchHits(hits: ReadonlySet<number> | null): void
  setPreviewLabel(id: string | null): void
  setOpenPeriods(count: number): void
  setStory(story: Story | null): void
}

function toggled<T>(set: ReadonlySet<T>, value: T): Set<T> {
  const next = new Set(set)
  if (next.has(value)) next.delete(value)
  else next.add(value)
  return next
}

export const useApp = create<AppState>((set) => ({
  model: null,
  error: null,
  mode: 'threads',
  compressed: true,
  hiddenKinds: new Set(),
  activeLabels: new Set(),
  selected: null,
  unplacedSelected: null,
  rowOrder: 'thread',
  story: null,
  life: new Map(),
  lifeById: {},
  searchHits: null,
  previewLabel: null,
  openPeriods: 0,
  hover: null,
  labelsOpen: false,
  searchOpen: false,
  unplacedOpen: false,
  depth: 1,
  setModel: (model) => set({ model, error: null }),
  setError: (error) => set({ error }),
  setMode: (mode) => set({ mode }),
  setCompressed: (compressed) => set({ compressed }),
  toggleKind: (id) => set((s) => ({ hiddenKinds: toggled(s.hiddenKinds, id) })),
  toggleLabel: (id) => set((s) => ({ activeLabels: toggled(s.activeLabels, id) })),
  clearFilters: () => set({ hiddenKinds: new Set(), activeLabels: new Set() }),
  select: (selected) => set({ selected, unplacedSelected: null }),
  selectUnplaced: (unplacedSelected) => set({ unplacedSelected, selected: null }),
  setHover: (hover) => set({ hover }),
  setLabelsOpen: (labelsOpen) => set((s) => ({ labelsOpen, unplacedOpen: labelsOpen ? false : s.unplacedOpen })),
  setSearchOpen: (searchOpen) => set({ searchOpen }),
  setUnplacedOpen: (unplacedOpen) => set((s) => ({ unplacedOpen, labelsOpen: unplacedOpen ? false : s.labelsOpen })),
  setDepth: (depth) => set({ depth }),
  setRowOrder: (rowOrder) => set({ rowOrder }),
  setLife: (life, lifeById) => set({ life, lifeById }),
  setSearchHits: (searchHits) => set({ searchHits }),
  setPreviewLabel: (previewLabel) => set({ previewLabel }),
  setOpenPeriods: (openPeriods) => set({ openPeriods }),
  setStory: (story) => set({ story }),
}))

/** The engine is imperative and outside React; components reach it through this handle. */
let engine: Engine | null = null
export const setEngine = (e: Engine | null): void => {
  engine = e
}
export const getEngine = (): Engine | null => engine

/** Selects a node and flies to it. */
export function focusNode(index: number): void {
  useApp.getState().select(index)
  if (useApp.getState().mode !== 'story') engine?.flyToNode(index)
}

/** Lifts what led to an entry and what followed out of the chart, to read on its own. */
export function followEntry(index: number): boolean {
  const { model, setStory, setMode, select } = useApp.getState()
  if (!model) return false
  const { members, truncated } = lineageOf(index, model)
  if (members.length < 2) return false
  setStory(layoutStory(members, model, index, truncated))
  setMode('story')
  select(index)
  return true
}

/** Opens a whole connected thread as a story, starting from its first entry. */
export function openThread(start: number): void {
  const { model, setStory, setMode, select } = useApp.getState()
  if (!model) return
  const { members, truncated } = threadOf(start, model)
  const story = layoutStory(members, model, null, truncated)
  setStory(story)
  setMode('story')
  select(story.members[0] ?? null)
}

/** Moves through a followed thread in reading order. */
export function stepStory(delta: number): void {
  const { story, selected, select } = useApp.getState()
  if (!story) return
  const at = selected === null ? -1 : story.members.indexOf(selected)
  const next = Math.max(0, Math.min(story.members.length - 1, at + delta))
  select(story.members[next] ?? null)
}

export function focusEntry(id: string): void {
  const state = useApp.getState()
  const index = state.model?.indexById.get(id)
  if (index !== undefined) focusNode(index)
  else if (state.model?.entryById.has(id)) state.selectUnplaced(id)
}

type Filters = Pick<AppState, 'hiddenKinds' | 'activeLabels'>

export const passes = (node: Pick<RawNode, 'kind' | 'labels'>, f: Filters): boolean =>
  !f.hiddenKinds.has(node.kind) && (f.activeLabels.size === 0 || node.labels.some((l) => f.activeLabels.has(l)))
