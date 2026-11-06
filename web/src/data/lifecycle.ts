import type { EntryScope, HistoricalBound, HistoricalDate, LifecycleState, RawEvent, TimelineEntry } from './types.ts'

/** Separate recorded episodes; neither intervening use nor a global ending is inferred. */
export type LifeStatus = 'documented' | 'unknown' | 'ongoing' | 'not_applicable' | 'not_yet_researched'
export const LATER_STAGES = ['adoption', 'decline', 'withdrawal', 'end_of_use', 'abandonment', 'revival'] as const
export type LaterStage = (typeof LATER_STAGES)[number]
export type EventRole = 'context' | 'use' | 'availability' | 'recognition' | 'awareness' | 'production' | 'launch' | 'decline' | 'end' | 'revival' | 'unclassified'

export interface LifeEvent {
  id: string
  type: string
  role: EventRole
  /** Render coordinate only; the full date below defines what is actually known. */
  year?: number
  start?: number
  end?: number
  date?: HistoricalDate
  label: string
  statement: string
  review?: string
  lifecycle_review?: string
  scope?: EntryScope
  evidence?: RawEvent['evidence']
  uncertainty?: string
  bound?: 'by' | 'from'
}
export interface LifeRecord {
  status: Partial<Record<LaterStage, LifeStatus>>
  stages: Record<string, LifecycleState>
  review: { historical_claim?: string; lifecycle_classification?: string }
  events: LifeEvent[]
}

function validBound(bound: HistoricalBound | undefined, precision?: string): bound is HistoricalBound {
  if (!bound || !Number.isInteger(bound.year) || bound.year === 0) return false
  if (bound.month !== undefined && (!Number.isInteger(bound.month) || bound.month < 1 || bound.month > 12)) return false
  if (bound.day !== undefined && (bound.month === undefined || !Number.isInteger(bound.day) || bound.day < 1 || bound.day > [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][bound.month - 1]!)) return false
  return !(precision === 'day' && (bound.month === undefined || bound.day === undefined) || precision === 'month' && bound.month === undefined)
}
/** Month/day fractions locate a mark on a year axis; they are never used as elapsed duration. */
function position(bound: HistoricalBound): number {
  return bound.year + (bound.month === undefined ? 0 : (bound.month - 1 + (bound.day === undefined ? 0 : (bound.day - 1) / 31)) / 12)
}
export function readEventDate(date: HistoricalDate | undefined): Pick<LifeEvent, 'year' | 'start' | 'end' | 'bound' | 'date'> | null {
  if (!date || !['known', 'approximate', 'bounded'].includes(date.status)) return null
  if (date.earliest !== undefined && !validBound(date.earliest, date.precision) || date.latest !== undefined && !validBound(date.latest, date.precision)) return null
  const a = date.earliest, b = date.latest
  if (!a && !b || date.status === 'known' && (!a || !b)) return null
  if (a && date.earliest_status !== undefined || b && date.latest_status !== undefined) return null
  if (!a && !['unknown', 'not_yet_researched'].includes(date.earliest_status ?? '') || !b && !['unknown', 'not_yet_researched'].includes(date.latest_status ?? '')) return null
  if (a && b && position(a) > position(b)) return null
  const preserved = structuredClone(date)
  if (!a) return { year: position(b!), end: position(b!), bound: 'by', date: preserved }
  if (!b) return { year: position(a), start: position(a), bound: 'from', date: preserved }
  return { year: (position(a) + position(b)) / 2, start: position(a), end: position(b), date: preserved }
}

export const ROLE_OF_EVENT: Record<string, EventRole> = {
  invention: 'context', prototype: 'context', construction: 'context', discovery: 'context', observation: 'context', formulation: 'context',
  experimental_confirmation: 'context', demonstration: 'context', dated_assertion: 'unclassified',
  publication: 'awareness', presentation: 'awareness', public_disclosure: 'awareness',
  commercial_offer: 'availability', commercial_availability: 'availability', first_commercial_availability: 'availability', public_availability: 'availability',
  practical_use: 'use', practical_deployment: 'use', adoption: 'use', recognition: 'recognition', acceptance: 'recognition',
  production: 'production', launch: 'launch', decline: 'decline', withdrawal: 'end', support_end: 'end', end_of_use: 'end', abandonment: 'end', revival: 'revival',
}
export const EVENT_NAMES: Record<string, string> = {
  commercial_offer: 'Offered for sale', commercial_availability: 'Commercially available', first_commercial_availability: 'First commercially available',
  public_availability: 'Publicly available', practical_use: 'In use', practical_deployment: 'Put to use', adoption: 'Adoption',
  recognition: 'Recognition', acceptance: 'Acceptance', publication: 'Publication', presentation: 'Presentation', public_disclosure: 'Public disclosure',
  production: 'Production', launch: 'Launch', decline: 'Decline', withdrawal: 'Withdrawal from sale', support_end: 'Support cutoff',
  end_of_use: 'Scoped last-use claim', abandonment: 'Scoped abandonment', revival: 'Scoped revival',
}
const EPISODE_ROLES = new Set<EventRole>(['use', 'availability', 'recognition', 'production', 'launch', 'decline', 'end', 'revival'])
export function isReviewedLifeEvent(event: LifeEvent): boolean {
  const text = (value: unknown): value is string => typeof value === 'string' && value.trim().length > 0
  const scoped = (value: EntryScope['market'] | undefined) => value && ['specified', 'unknown', 'not_yet_researched', 'not_applicable'].includes(value.status)
    && (value.status === 'specified' ? text(value.value) : value.value === undefined)
  return event.review === 'accepted' && event.lifecycle_review === 'accepted'
    && Boolean(text(event.scope?.configuration) && Array.isArray(event.scope?.regions) && event.scope.regions.every(text)
      && Array.isArray(event.scope?.applications) && event.scope.applications.every(text) && scoped(event.scope.market) && scoped(event.scope.population))
    && Boolean(event.evidence?.length && event.evidence.every((e) => text(e.source_id) && text(e.locator) && text(e.supports)))
}
export function reviewedLifeEvents(record: LifeRecord | undefined): LifeEvent[] {
  return record?.events.filter((event) => EPISODE_ROLES.has(event.role) && isReviewedLifeEvent(event)) ?? []
}
export function plottedLifeEvents(record: LifeRecord | undefined): (LifeEvent & { year: number })[] {
  return reviewedLifeEvents(record).filter((event): event is LifeEvent & { year: number } => typeof event.year === 'number' && Number.isFinite(event.year))
}
export const hasLifecycleEvidence = (record: LifeRecord | undefined): boolean => reviewedLifeEvents(record).length > 0

function boundLabel(bound: HistoricalBound): string {
  let text = bound.year < 0 ? `${-bound.year} BCE` : String(bound.year)
  if (bound.month !== undefined) {
    text = `${'January February March April May June July August September October November December'.split(' ')[bound.month - 1]} ${text}`
    if (bound.day !== undefined) text = `${bound.day} ${text}`
  }
  return text
}
/** Format structured bounds, never mine a prose label for a date or approximation. */
export function lifeDateLabel(event: LifeEvent): string {
  const d = event.date
  if (!d || !readEventDate(d)) return event.label
  const q = d.status === 'approximate' ? 'approximately ' : ''
  if (!d.earliest) return `By ${q}${boundLabel(d.latest!)}`
  if (!d.latest) return `Not before ${q}${boundLabel(d.earliest)}`
  const a = boundLabel(d.earliest), b = boundLabel(d.latest)
  return `${q ? 'Approximately ' : ''}${a === b ? a : `${a} to ${b}`}`
}
export interface LifeTally {
  total: number
  withLifecycleEvidence: number
  counts: Record<'decline' | 'withdrawal' | 'end_of_use' | 'abandonment' | 'revival', number>
  statedUnknown: number
}
export function tallyLifecycle(records: Iterable<LifeRecord>, total: number): LifeTally {
  const counts: LifeTally['counts'] = { decline: 0, withdrawal: 0, end_of_use: 0, abandonment: 0, revival: 0 }
  let withLifecycleEvidence = 0, statedUnknown = 0
  for (const record of records) {
    if (hasLifecycleEvidence(record)) withLifecycleEvidence++
    const accepted = reviewedLifeEvents(record)
    for (const key of Object.keys(counts) as (keyof LifeTally['counts'])[]) {
      if (record.status[key] === 'documented' && accepted.some((e) => e.type === key && record.stages[key]?.event_ids.includes(e.id))) counts[key]++
    }
    if (record.status.end_of_use === 'unknown') statedUnknown++
  }
  return { total, withLifecycleEvidence, counts, statedUnknown }
}

/** Preserve original episodes and assessments; no event pair creates an interval of continued life. */
export function buildLifeRecords(entries: readonly TimelineEntry[], events: Record<string, RawEvent>): Map<string, LifeRecord> {
  const byNode = new Map<string, RawEvent[]>()
  for (const event of Object.values(events)) {
    const list = byNode.get(event.node_id) ?? []; list.push(event); byNode.set(event.node_id, list)
  }
  const records = new Map<string, LifeRecord>()
  for (const entry of entries) {
    if (!entry.lifecycle && !byNode.has(entry.id)) continue
    const episodes: LifeEvent[] = []
    for (const event of byNode.get(entry.id) ?? []) {
      const when = readEventDate(event.date)
      episodes.push({ id: event.id, type: event.event_type, role: ROLE_OF_EVENT[event.event_type] ?? 'unclassified',
        ...(when ?? {}), date: event.date ? structuredClone(event.date) : undefined, label: event.date_label, statement: event.statement ?? '',
        review: event.review, lifecycle_review: event.lifecycle_review,
        scope: event.scope ? structuredClone(event.scope) : undefined, evidence: event.evidence ? structuredClone(event.evidence) : undefined,
        ...(event.uncertainty ? { uncertainty: event.uncertainty } : {}) })
    }
    episodes.sort((a, b) => (a.year ?? Infinity) - (b.year ?? Infinity) || a.id.localeCompare(b.id))
    const status: LifeRecord['status'] = {}
    for (const stage of LATER_STAGES) {
      const value = entry.lifecycle?.[stage]?.status as LifeStatus | undefined
      if (value) status[stage] = value
    }
    records.set(entry.id, { status, stages: structuredClone(entry.lifecycle ?? {}),
      review: { historical_claim: entry.review, lifecycle_classification: entry.lifecycle_review }, events: episodes })
  }
  return records
}
