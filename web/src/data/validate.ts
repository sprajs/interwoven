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

  const labels = new Set((data.labels ?? []).map((l) => l.id))
  const kinds = new Set(KINDS.map((k) => k.id))
  const ids = new Set<string>()

  const unplaced = Array.isArray(data.unplaced) ? data.unplaced : []
  for (const n of [...data.nodes, ...unplaced]) {
    if (!n.id) error(`Node "${n.title ?? '?'}" has no id.`)
    if (ids.has(n.id)) error(`Duplicate node id "${n.id}".`)
    ids.add(n.id)
    if ('year' in n) {
      if (!Number.isFinite(n.year) || !Number.isFinite(n.start) || !Number.isFinite(n.end)) error(`"${n.id}": date coordinates must be numbers.`)
      if (n.start > n.end) error(`"${n.id}": start is after end.`)
    }
    if (![0, 1, 2, 3].includes(n.level)) error(`"${n.id}": level must be 0, 1, 2 or 3.`)
    if (!kinds.has(n.kind)) error(`"${n.id}": unknown kind "${n.kind}".`)
    if (!Array.isArray(n.labels) || n.labels.length === 0) warn(`"${n.id}" has no labels.`)
    for (const label of n.labels ?? []) if (!labels.has(label)) error(`"${n.id}" uses undeclared label "${label}".`)
  }
  for (const n of unplaced) {
    if (!n.placement_reason || !n.anchor_status) error(`"${n.id}": unplaced entry needs its anchor status and reason.`)
    if ('year' in n || 'start' in n || 'end' in n) error(`"${n.id}": unplaced entry must not acquire timeline coordinates.`)
  }

  const seen = new Set<string>()
  for (const link of data.links ?? []) {
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
