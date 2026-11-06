import { NODE_TYPES, type RawDataset } from './types.ts'

export interface Issue {
  severity: 'error' | 'warning'
  message: string
}

/**
 * Checks a dataset before use. Errors would break rendering or the graph;
 * warnings are data that renders but is probably not what the author meant.
 */
export function validateDataset(data: RawDataset): Issue[] {
  const issues: Issue[] = []
  const error = (message: string) => issues.push({ severity: 'error', message })
  const warn = (message: string) => issues.push({ severity: 'warning', message })

  if (!Array.isArray(data?.nodes)) return [{ severity: 'error', message: 'Dataset has no "nodes" array.' }]
  if (!Array.isArray(data.domains) || data.domains.length === 0) error('Dataset has no "domains".')
  if (!Array.isArray(data.epochs)) error('Dataset has no "epochs" array.')

  const domains = new Set((data.domains ?? []).map((d) => d.id))
  const types = new Set(NODE_TYPES.map((t) => t.id))
  const years = new Map<string, number>()

  for (const n of data.nodes) {
    if (!n.id) error(`Node "${n.title ?? '?'}" has no id.`)
    if (years.has(n.id)) error(`Duplicate node id "${n.id}".`)
    years.set(n.id, n.year)
    if (!Number.isFinite(n.year)) error(`"${n.id}": year must be a number.`)
    if (![0, 1, 2, 3].includes(n.level)) error(`"${n.id}": level must be 0, 1, 2 or 3.`)
    if (!types.has(n.type)) error(`"${n.id}": unknown type "${n.type}".`)
    if (!domains.has(n.domain)) error(`"${n.id}": unknown domain "${n.domain}".`)
    if (!Array.isArray(n.labels)) error(`"${n.id}": labels must be an array.`)
    if (!Array.isArray(n.builds_on)) error(`"${n.id}": builds_on must be an array.`)
  }

  for (const n of data.nodes) {
    for (const dep of [...(n.builds_on ?? []), ...(n.informed_by ?? [])]) {
      const y = years.get(dep)
      if (y === undefined) error(`"${n.id}" links to unknown node "${dep}".`)
      else if (dep === n.id) error(`"${n.id}" links to itself.`)
      else if (y > n.year) warn(`"${n.id}" (${n.year}) builds on "${dep}" (${y}), which is later.`)
    }
    if (n.level === 0 && !n.step_change) warn(`"${n.id}" is level 0 but has no step_change text.`)
  }

  // A cycle would make lineage and impact counts meaningless.
  const deps = new Map(data.nodes.map((n) => [n.id, [...(n.builds_on ?? []), ...(n.informed_by ?? [])]]))
  const state = new Map<string, 1 | 2>()
  for (const start of deps.keys()) {
    if (state.has(start)) continue
    const stack: [string, number][] = [[start, 0]]
    state.set(start, 1)
    while (stack.length) {
      const top = stack[stack.length - 1]!
      const list = deps.get(top[0]) ?? []
      if (top[1] >= list.length) {
        state.set(top[0], 2)
        stack.pop()
        continue
      }
      const next = list[top[1]++]!
      if (state.get(next) === 1) error(`Cycle through "${next}" and "${top[0]}".`)
      else if (!state.has(next) && deps.has(next)) {
        state.set(next, 1)
        stack.push([next, 0])
      }
    }
  }

  return issues
}
