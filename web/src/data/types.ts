/** The on-disk dataset format. See web/README.md for how to add data. */
export type NodeType = 'discovery' | 'theory' | 'instrument' | 'invention' | 'system'

/** 0 = step change, 1 = major, 2 = technology, 3 = underlying science and detail. */
export type Level = 0 | 1 | 2 | 3

export interface RawNode {
  id: string
  title: string
  /** Decimal year. Negative is BCE. There is no year 0 in display, but values are not adjusted. */
  year: number
  level: Level
  type: NodeType
  domain: string
  labels: string[]
  /** Direct prerequisites. Drawn as solid links. */
  builds_on: string[]
  /** Softer intellectual influence. Drawn as dashed links. */
  informed_by?: string[]
  summary: string
  /** Why this reshaped what came after. Presence marks the node as a step change. */
  step_change?: string
}

export interface RawDomain {
  id: string
  label: string
  color: string
}

export interface RawEpoch {
  id: string
  label: string
  start: number
  end: number
}

export interface RawDataset {
  meta: { title: string; description?: string }
  domains: RawDomain[]
  epochs: RawEpoch[]
  nodes: RawNode[]
}

export const NODE_TYPES: { id: NodeType; label: string; shape: number }[] = [
  { id: 'discovery', label: 'Discovery', shape: 0 },
  { id: 'theory', label: 'Theory', shape: 1 },
  { id: 'instrument', label: 'Instrument', shape: 2 },
  { id: 'invention', label: 'Invention', shape: 3 },
  { id: 'system', label: 'System', shape: 4 },
]

export const LEVEL_NAMES = ['Step changes', 'Major advances', 'Technologies', 'Science & detail'] as const
