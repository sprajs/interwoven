/** The dataset format the app reads. `npm run import` builds it from the research graph. */
export type NodeKind = 'science' | 'technology'

/** 0 is most prominent. Deeper levels appear as you zoom in. */
export type Level = 0 | 1 | 2 | 3
export type EntryBasis = 'first_commercial_availability' | 'commercial_availability' | 'practical_use' | 'adoption' | 'public_availability' | 'recognition' | 'public_awareness'
export type EvidenceStrength = 'direct' | 'scoped_inference' | 'awareness_proxy'
export type DateInterpretation = 'event_date' | 'known_by' | 'known_from'
export type DateKind = 'point' | 'interval' | 'known_by' | 'known_from'

export interface HistoricalBound { year: number; month?: number; day?: number }
export interface HistoricalDate {
  status: string
  precision?: string
  calendar?: string
  label?: string
  basis?: string
  earliest?: HistoricalBound
  latest?: HistoricalBound
  earliest_status?: string
  latest_status?: string
}
export interface EntryEvidence { source_id: string; locator: string; supports: string }
export interface EntryScope {
  regions: string[]
  configuration: string
  applications: string[]
  market: { status: string; value?: string }
  population: { status: string; value?: string }
}
export interface LifecycleState {
  status: string
  event_ids: string[]
  rationale?: string
  evidence?: { source_id: string; locator?: string; supports?: string }[]
  as_of?: string
}

export interface RawEntry {
  id: string
  title: string
  kind: NodeKind
  level: Level
  date_label: string
  date_basis?: string
  anchor_status?: string
  anchor_policy?: string
  anchor_rationale?: string
  anchor_event_id?: string
  entry_basis?: EntryBasis
  evidence_strength?: EvidenceStrength
  date_interpretation?: DateInterpretation
  entry_community?: string
  entry_scope?: EntryScope
  entry_evidence?: EntryEvidence[]
  entry_uncertainty?: string
  proxy_justification?: string
  commercial_date_status?: string
  commercial_applicability?: string
  lifecycle_review?: string
  lifecycle?: Record<string, LifecycleState>
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

export interface RawNode extends RawEntry {
  /** Display coordinate: an interval midpoint or the supplied limit of a bound. */
  year: number
  start?: number
  end?: number
  date_kind?: DateKind
  entry_date?: HistoricalDate
  placed_by: string
  anchored: boolean
}

export interface RawUnplacedNode extends RawEntry {
  anchor_status: string
  placement_reason: string
}

export type TimelineEntry = RawNode | RawUnplacedNode
export const isPlacedNode = (entry: TimelineEntry): entry is RawNode => 'year' in entry

export interface RawEvent {
  id: string
  node_id: string
  event_type: string
  date_label: string
  date_status: string
  date_basis?: string
  date?: HistoricalDate
  statement?: string
  scope?: EntryScope
  uncertainty?: string
}

export interface RawLink {
  id?: string
  from: string
  to: string
  from_event_id?: string
  to_event_id?: string
  relation: string
  statement?: string
  temporal_note?: string
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
  /** Records awaiting a defensible selected community-entry choice stay accessible. */
  unplaced?: RawUnplacedNode[]
  links: RawLink[]
  events?: Record<string, RawEvent>
  sources?: Record<string, RawSource>
}

export const KINDS: { id: NodeKind; name: string; plural: string; shape: number }[] = [
  { id: 'technology', name: 'Technology', plural: 'Technologies', shape: 0 },
  { id: 'science', name: 'Science', plural: 'Science', shape: 1 },
]

export const LEVEL_NAMES = ['Landmarks', 'Major advances', 'Supporting work', 'Fine detail'] as const
