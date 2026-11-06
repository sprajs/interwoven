import { create } from 'zustand'
import type { Model } from './data/model.ts'
import type { Engine, Mode } from './engine/Engine.ts'

export interface Hover {
  index: number
  x: number
  y: number
}

interface AppState {
  model: Model | null
  error: string | null
  warnings: string[]
  mode: Mode
  compressed: boolean
  hiddenDomains: ReadonlySet<string>
  hiddenTypes: ReadonlySet<string>
  activeLabels: ReadonlySet<string>
  selected: number | null
  hover: Hover | null
  filtersOpen: boolean
  searchOpen: boolean
  /** Deepest level currently appearing as you zoom, 0 to 3. */
  depth: number
  setModel(model: Model, warnings: string[]): void
  setError(message: string): void
  setMode(mode: Mode): void
  setCompressed(compressed: boolean): void
  toggleDomain(id: string): void
  toggleType(id: string): void
  toggleLabel(id: string): void
  clearFilters(): void
  select(index: number | null): void
  setHover(hover: Hover | null): void
  setFiltersOpen(open: boolean): void
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
  warnings: [],
  mode: 'network',
  compressed: true,
  hiddenDomains: new Set(),
  hiddenTypes: new Set(),
  activeLabels: new Set(),
  selected: null,
  hover: null,
  filtersOpen: false,
  searchOpen: false,
  depth: 1,
  setModel: (model, warnings) => set({ model, warnings, error: null }),
  setError: (error) => set({ error }),
  setMode: (mode) => set({ mode }),
  setCompressed: (compressed) => set({ compressed }),
  toggleDomain: (id) => set((s) => ({ hiddenDomains: toggled(s.hiddenDomains, id) })),
  toggleType: (id) => set((s) => ({ hiddenTypes: toggled(s.hiddenTypes, id) })),
  toggleLabel: (id) => set((s) => ({ activeLabels: toggled(s.activeLabels, id) })),
  clearFilters: () => set({ hiddenDomains: new Set(), hiddenTypes: new Set(), activeLabels: new Set() }),
  select: (selected) => set({ selected }),
  setHover: (hover) => set({ hover }),
  setFiltersOpen: (filtersOpen) => set({ filtersOpen }),
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

export const isFilterActive = (s: Pick<AppState, 'hiddenDomains' | 'hiddenTypes' | 'activeLabels'>): boolean =>
  s.hiddenDomains.size + s.hiddenTypes.size + s.activeLabels.size > 0

export const passes = (
  node: { domain: string; type: string; labels: string[] },
  s: Pick<AppState, 'hiddenDomains' | 'hiddenTypes' | 'activeLabels'>,
): boolean =>
  !s.hiddenDomains.has(node.domain) &&
  !s.hiddenTypes.has(node.type) &&
  (s.activeLabels.size === 0 || node.labels.some((l) => s.activeLabels.has(l)))
