import { KINDS, type RawDataset } from './types.ts'

export interface Issue {
  severity: 'error' | 'warning'
  message: string
}

/** Checks a dataset before use. Errors would break the graph or rendering. */
export function validateDataset(data: RawDataset): Issue[] {
  const issues: Issue[] = []
  const error = (message: string) => issues.push({ severity: 'error', message })
  const warn = (message: string) => issues.push({ severity: 'warning', message })

  if (!Array.isArray(data?.nodes)) return [{ severity: 'error', message: 'Dataset has no "nodes" array.' }]
  if (!Array.isArray(data.links)) error('Dataset has no "links" array.')
  if (!Array.isArray(data.labels)) error('Dataset has no "labels" array.')
  if (data.unplaced !== undefined && !Array.isArray(data.unplaced)) error('Dataset "unplaced" must be an array.')
  if (issues.some((issue) => issue.severity === 'error')) return issues

  const labels = new Set<string>()
  for (const label of data.labels) {
    if (!label || typeof label.id !== 'string' || typeof label.name !== 'string' || typeof label.ink !== 'string') error('Every label needs string id, name and ink fields.')
    else labels.add(label.id)
  }
  const kinds = new Set(KINDS.map((k) => k.id))
  const ids = new Set<string>()

  const unplaced = Array.isArray(data.unplaced) ? data.unplaced : []
  for (const n of [...data.nodes, ...unplaced]) {
    if (!n || typeof n !== 'object' || typeof n.id !== 'string' || typeof n.title !== 'string' || typeof n.summary !== 'string') {
      error('Every entry needs a string id, title and summary.')
      continue
    }
    if (!n.id) error(`Node "${n.title ?? '?'}" has no id.`)
    if (ids.has(n.id)) error(`Duplicate node id "${n.id}".`)
    ids.add(n.id)
    if ('year' in n) {
      if (!Number.isFinite(n.year) || n.start !== undefined && !Number.isFinite(n.start) || n.end !== undefined && !Number.isFinite(n.end)) error(`"${n.id}": supplied date coordinates must be numbers.`)
      if (n.start !== undefined && n.end !== undefined && n.start > n.end) error(`"${n.id}": start is after end.`)
      if (n.date_kind === 'known_by' && (n.start !== undefined || n.end === undefined || n.year !== n.end)) error(`"${n.id}": known-by entry must retain only its upper limit.`)
      if (n.date_kind === 'known_from' && (n.end !== undefined || n.start === undefined || n.year !== n.start)) error(`"${n.id}": known-from entry must retain only its lower limit.`)
      if (n.start === undefined && n.date_kind !== 'known_by' || n.end === undefined && n.date_kind !== 'known_from') error(`"${n.id}": a missing entry limit must be explicitly qualified.`)
      if (n.date_kind && !['point', 'interval', 'known_by', 'known_from'].includes(n.date_kind)) error(`"${n.id}": unsupported date mark.`)
    }
    if (n.evidence_strength === 'awareness_proxy' && n.entry_basis !== 'public_awareness') error(`"${n.id}": an awareness proxy must not be labelled adoption or use.`)
    if (n.evidence_strength === 'scoped_inference' && !['practical_use', 'public_availability'].includes(n.entry_basis ?? '')) error(`"${n.id}": scoped inference must qualify use or availability.`)
    for (const source of Array.isArray(n.sources) ? n.sources : []) if (typeof source !== 'string' || data.sources && !data.sources[source]) error(`"${n.id}" refers to missing or invalid source "${source}".`)
    if (n.lifecycle !== undefined) {
      if (!n.lifecycle || typeof n.lifecycle !== 'object' || Array.isArray(n.lifecycle)) error(`"${n.id}": lifecycle must be an object.`)
      else for (const state of Object.values(n.lifecycle)) if (!state || typeof state.status !== 'string' || !Array.isArray(state.event_ids)) error(`"${n.id}": invalid lifecycle state.`)
    }
    if (![0, 1, 2, 3].includes(n.level)) error(`"${n.id}": level must be 0, 1, 2 or 3.`)
    if (!kinds.has(n.kind)) error(`"${n.id}": unknown kind "${n.kind}".`)
    if (!['accepted', 'candidate', 'withheld'].includes(n.review)) error(`"${n.id}": invalid historical review status.`)
    if (!Array.isArray(n.regions) || n.regions.some((region) => typeof region !== 'string') || !Array.isArray(n.sources)) error(`"${n.id}": regions and sources must be string arrays.`)
    if (!Array.isArray(n.labels)) error(`"${n.id}": labels must be an array.`)
    else if (n.labels.length === 0) warn(`"${n.id}" has no labels.`)
    for (const label of Array.isArray(n.labels) ? n.labels : []) if (!labels.has(label)) error(`"${n.id}" uses undeclared label "${label}".`)
  }
  for (const n of unplaced) {
    if (!n || typeof n !== 'object') continue
    if (!n.placement_reason || !n.anchor_status) error(`"${n.id}": unplaced entry needs its anchor status and reason.`)
    if ('year' in n || 'start' in n || 'end' in n) error(`"${n.id}": unplaced entry must not acquire timeline coordinates.`)
  }

  const seen = new Set<string>()
  for (const link of data.links ?? []) {
    if (!link || typeof link !== 'object') { error('Every relationship must be an object.'); continue }
    if (!ids.has(link.from)) error(`Link starts at unknown node "${link.from}".`)
    if (!ids.has(link.to)) error(`Link ends at unknown node "${link.to}".`)
    if (link.from === link.to) error(`"${link.from}" links to itself.`)
    for (const [side, eventId] of [['from', link.from_event_id], ['to', link.to_event_id]] as const) {
      if (!eventId) continue
      const event = data.events?.[eventId]
      if (!event) error(`Link ${link.id ?? `${link.from}>${link.to}`} refers to unknown event "${eventId}".`)
      else if (event.node_id !== link[side]) error(`Link event "${eventId}" does not belong to "${link[side]}".`)
    }
    const key = `${link.from}>${link.to}`
    if (seen.has(key)) warn(`Duplicate link ${key}.`)
    seen.add(key)
  }

  return issues
}
