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

  const labels = new Set((data.labels ?? []).map((l) => l.id))
  const kinds = new Set(KINDS.map((k) => k.id))
  const ids = new Set<string>()

  for (const n of data.nodes) {
    if (!n.id) error(`Node "${n.title ?? '?'}" has no id.`)
    if (ids.has(n.id)) error(`Duplicate node id "${n.id}".`)
    ids.add(n.id)
    if (!Number.isFinite(n.year)) error(`"${n.id}": year must be a number.`)
    if (n.start > n.end) error(`"${n.id}": start is after end.`)
    if (![0, 1, 2, 3].includes(n.level)) error(`"${n.id}": level must be 0, 1, 2 or 3.`)
    if (!kinds.has(n.kind)) error(`"${n.id}": unknown kind "${n.kind}".`)
    if (!Array.isArray(n.labels) || n.labels.length === 0) warn(`"${n.id}" has no labels.`)
    for (const label of n.labels ?? []) if (!labels.has(label)) error(`"${n.id}" uses undeclared label "${label}".`)
  }

  const seen = new Set<string>()
  for (const link of data.links ?? []) {
    if (!ids.has(link.from)) error(`Link starts at unknown node "${link.from}".`)
    if (!ids.has(link.to)) error(`Link ends at unknown node "${link.to}".`)
    if (link.from === link.to) error(`"${link.from}" links to itself.`)
    const key = `${link.from}>${link.to}`
    if (seen.has(key)) warn(`Duplicate link ${key}.`)
    seen.add(key)
  }

  return issues
}
