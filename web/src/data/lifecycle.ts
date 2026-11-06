/**
 * The documented lives of entries, read from a sidecar file written by
 * `npm run import:lifecycle`. An entry that is not in the file has no later-life evidence,
 * which must always read as "not researched" and never as "it ended" or "it continued".
 */

/** How the research describes each stage: documented, unknown, ongoing, and so on. */
export type LifeStatus = 'documented' | 'unknown' | 'ongoing' | 'not_applicable' | 'not_yet_researched'

export const LATER_STAGES = ['adoption', 'decline', 'withdrawal', 'end_of_use', 'abandonment', 'revival'] as const
export type LaterStage = (typeof LATER_STAGES)[number]

export type EventRole = 'origin' | 'use' | 'decline' | 'end' | 'revival'

export interface LifeEvent {
  id: string
  /** The research event type, such as "withdrawal" or "commercial_offer". */
  type: string
  role: EventRole
  start: number
  end: number
  label: string
  statement: string
  review: 'accepted' | 'candidate' | string
  uncertainty?: string
  /** "by" means the date is only a latest possible one, and "from" only an earliest. */
  bound?: 'by' | 'from'
}

export interface LifeRecord {
  status: Partial<Record<LaterStage, LifeStatus>>
  events: LifeEvent[]
}

export interface LifecycleFile {
  meta: { provenance?: string; entries: number }
  records: Record<string, LifeRecord>
}

/**
 * Reads a research event's date. A bounded date such as "by 15 March 2023" has only one end,
 * and it stays marked as such, so it cannot be mistaken for the day the event happened.
 */
export function readEventDate(date: { earliest?: { year: number }; latest?: { year: number } } | undefined): Pick<LifeEvent, 'start' | 'end' | 'bound'> | null {
  const earliest = date?.earliest?.year
  const latest = date?.latest?.year
  if (earliest !== undefined && latest !== undefined) return { start: earliest, end: latest }
  if (latest !== undefined) return { start: latest, end: latest, bound: 'by' }
  if (earliest !== undefined) return { start: earliest, end: earliest, bound: 'from' }
  return null
}

export const ROLE_OF_EVENT: Record<string, EventRole> = {
  commercial_offer: 'use',
  first_commercial_availability: 'use',
  practical_deployment: 'use',
  adoption: 'use',
  production: 'use',
  launch: 'use',
  decline: 'decline',
  withdrawal: 'end',
  support_end: 'end',
  end_of_use: 'end',
  abandonment: 'end',
  revival: 'revival',
}

/** The event types that say something about a thing's life after it first appeared. */
export const isLaterLife = (type: string): boolean => type in ROLE_OF_EVENT

export const EVENT_NAMES: Record<string, string> = {
  commercial_offer: 'Offered for sale',
  first_commercial_availability: 'First on sale',
  practical_deployment: 'Put to use',
  adoption: 'Adopted',
  production: 'Made',
  launch: 'Launched',
  decline: 'Decline',
  withdrawal: 'Withdrawn from sale',
  support_end: 'Support ended',
  end_of_use: 'Last use',
  abandonment: 'Abandoned',
  revival: 'Revived',
}

export interface LifeTally {
  /** Entries the file could speak about. */
  total: number
  /** Entries with any evidence of life after their origin. */
  withLaterLife: number
  counts: Record<'decline' | 'withdrawal' | 'end_of_use' | 'abandonment' | 'revival', number>
  /** Entries researched closely enough to say a later stage is unknown. */
  statedUnknown: number
}

/** Counts what the evidence actually holds. This is computed, so it grows with the research. */
export function tallyLifecycle(records: Map<number, LifeRecord>, total: number): LifeTally {
  const counts: LifeTally['counts'] = { decline: 0, withdrawal: 0, end_of_use: 0, abandonment: 0, revival: 0 }
  let withLaterLife = 0
  let statedUnknown = 0
  for (const record of records.values()) {
    if (hasLaterLife(record)) withLaterLife++
    for (const key of Object.keys(counts) as (keyof LifeTally['counts'])[]) {
      if (record.status[key] === 'documented') counts[key]++
    }
    if (record.status.end_of_use === 'unknown') statedUnknown++
  }
  return { total, withLaterLife, counts, statedUnknown }
}

export function hasLaterLife(record: LifeRecord | undefined): boolean {
  if (!record) return false
  const later = record.events.filter((e) => e.role !== 'origin')
  // A later-life event only counts as "beyond the origin" if something dated came before it.
  return later.length > 0 && record.events.length > 1
}

export interface DocumentedSpan {
  start: number
  end: number
  /** The event with the latest date, which is what the span runs up to. */
  last: LifeEvent
}

/**
 * The stretch the evidence itself covers: from the earliest dated event to the earliest date
 * the last event could have happened. A range such as "between the 1885 and 1889 catalogues"
 * therefore stays outside the solid part of the span and is drawn as a range.
 */
export function documentedSpan(record: LifeRecord | undefined): DocumentedSpan | null {
  if (!record || !hasLaterLife(record)) return null
  const events = [...record.events].sort((a, b) => a.start - b.start)
  const last = events.reduce((latest, e) => (e.start > latest.start ? e : latest), events[0]!)
  const start = events[0]!.start
  if (last.start <= start) return null
  return { start, end: last.start, last }
}

/** True once an event says the thing itself stopped, not only that its sale or support did. */
export const isFinal = (record: LifeRecord | undefined): boolean =>
  Boolean(record?.status.end_of_use !== 'unknown' && record?.events.some((e) => e.type === 'abandonment' || e.type === 'end_of_use'))

/** Joins the sidecar to the loaded entries. Records for entries not on the chart are dropped. */
export function indexLifecycle(file: LifecycleFile | null, indexById: Map<string, number>): Map<number, LifeRecord> {
  const out = new Map<number, LifeRecord>()
  if (!file) return out
  for (const [id, record] of Object.entries(file.records)) {
    const i = indexById.get(id)
    if (i !== undefined) out.set(i, record)
  }
  return out
}
