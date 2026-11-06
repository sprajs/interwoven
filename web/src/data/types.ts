/** The dataset format the app reads. `npm run import` builds it from the research graph. */
export type NodeKind = 'science' | 'technology'

/** 0 is most prominent. Deeper levels appear as you zoom in. */
export type Level = 0 | 1 | 2 | 3

export interface RawNode {
  id: string
  title: string
  kind: NodeKind
  level: Level
  /** Where the mark sits: the midpoint of `start` and `end`. Negative is BCE. */
  year: number
  start: number
  end: number
  date_label: string
  date_basis?: string
  /** The kind of event that dates this node, such as "demonstration". */
  placed_by: string
  /** True if the source data selected this date as the node's anchor, not just its earliest record. */
  anchored: boolean
  /** One or more overlapping labels. The first sets the ink colour. */
  labels: string[]
  summary: string
  regions: string[]
  uncertainty?: string
  review: 'accepted' | 'candidate' | 'withheld'
  /** Why this entry changed what followed, where that has been written. */
  note?: string
  sources: string[]
}

export interface RawLink {
  from: string
  to: string
  relation: string
  statement?: string
  /** Softer or still unreviewed links are drawn broken, as a pen lifting off the page. */
  tentative: boolean
}

export interface RawLabel {
  id: string
  name: string
  ink: string
}

export interface RawSource {
  title: string
  url?: string
  year?: string | number
}

export interface RawDataset {
  meta: { title: string; description?: string; provenance?: string }
  labels: RawLabel[]
  nodes: RawNode[]
  links: RawLink[]
  sources?: Record<string, RawSource>
}

export const KINDS: { id: NodeKind; name: string; plural: string; shape: number }[] = [
  { id: 'technology', name: 'Technology', plural: 'Technologies', shape: 0 },
  { id: 'science', name: 'Science', plural: 'Science', shape: 1 },
]

export const LEVEL_NAMES = ['Landmarks', 'Major advances', 'Supporting work', 'Fine detail'] as const
