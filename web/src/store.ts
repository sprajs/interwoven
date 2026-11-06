import { create } from 'zustand'
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
  hover: Hover | null
  labelsOpen: boolean
  searchOpen: boolean
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
  setHover(hover: Hover | null): void
  setLabelsOpen(open: boolean): void
  setSearchOpen(open: boolean): void
  setDepth(depth: number): void
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
  hover: null,
  labelsOpen: false,
  searchOpen: false,
  depth: 1,
  setModel: (model) => set({ model, error: null }),
  setError: (error) => set({ error }),
  setMode: (mode) => set({ mode }),
  setCompressed: (compressed) => set({ compressed }),
  toggleKind: (id) => set((s) => ({ hiddenKinds: toggled(s.hiddenKinds, id) })),
  toggleLabel: (id) => set((s) => ({ activeLabels: toggled(s.activeLabels, id) })),
  clearFilters: () => set({ hiddenKinds: new Set(), activeLabels: new Set() }),
  select: (selected) => set({ selected }),
  setHover: (hover) => set({ hover }),
  setLabelsOpen: (labelsOpen) => set({ labelsOpen }),
  setSearchOpen: (searchOpen) => set({ searchOpen }),
  setDepth: (depth) => set({ depth }),
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
  engine?.flyToNode(index)
}

type Filters = Pick<AppState, 'hiddenKinds' | 'activeLabels'>

export const passes = (node: Pick<RawNode, 'kind' | 'labels'>, f: Filters): boolean =>
  !f.hiddenKinds.has(node.kind) && (f.activeLabels.size === 0 || node.labels.some((l) => f.activeLabels.has(l)))
