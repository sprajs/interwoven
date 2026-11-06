// Builds public/data/lifecycle.json from the research graph, as a sidecar to timeline.json.
// Usage: npm run import:lifecycle [path/to/science-technology-graph]
//
// The research data is read only. An entry stays out of the file unless the research says
// something about it beyond "not yet researched", so absence always means unresearched.
import { readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { LATER_STAGES, readEventDate, ROLE_OF_EVENT, type LifeEvent, type LifecycleFile, type LifeRecord } from '../src/data/lifecycle.ts'

const dir = process.argv[2] ?? join(import.meta.dirname, '../../research/science-technology-graph')
const readJsonl = (name: string): any[] =>
  readFileSync(join(dir, 'data', name), 'utf8')
    .split('\n')
    .filter((line) => line.trim())
    .map((line) => JSON.parse(line))

const nodes = readJsonl('nodes.jsonl')
const events = readJsonl('events.jsonl')

const eventsByNode = new Map<string, any[]>()
for (const event of events) {
  const list = eventsByNode.get(event.node_id) ?? []
  list.push(event)
  eventsByNode.set(event.node_id, list)
}

const records: Record<string, LifeRecord> = {}
for (const node of nodes) {
  const dated: LifeEvent[] = []
  for (const e of eventsByNode.get(node.id) ?? []) {
    const when = readEventDate(e.date)
    if (!when) continue
    dated.push({
      id: e.id,
      type: e.event_type,
      role: ROLE_OF_EVENT[e.event_type] ?? 'origin',
      ...when,
      label: e.date.label ?? String(when.start),
      statement: e.statement ?? '',
      review: e.review?.historical_claim ?? 'candidate',
      ...(e.uncertainty ? { uncertainty: e.uncertainty } : {}),
    })
  }
  dated.sort((a, b) => a.start - b.start)

  const status: LifeRecord['status'] = {}
  for (const stage of LATER_STAGES) {
    const value = node.lifecycle?.[stage]?.status
    if (value && value !== 'not_yet_researched') status[stage] = value
  }

  const saysSomething = Object.keys(status).length > 0 || dated.some((e) => e.role !== 'origin')
  if (saysSomething) records[node.id] = { status, events: dated }
}

const file: LifecycleFile = {
  meta: {
    provenance: 'Generated from research/science-technology-graph by scripts/import-lifecycle.ts. Do not edit by hand.',
    entries: nodes.length,
  },
  records,
}

const lines = Object.entries(records).map(([id, record]) => `  ${JSON.stringify(id)}: ${JSON.stringify(record)}`)
const out = `{\n"meta": ${JSON.stringify(file.meta)},\n"records": {\n${lines.join(',\n')}\n}\n}\n`
writeFileSync(join(import.meta.dirname, '../public/data/lifecycle.json'), out)

const later = Object.values(records).filter((r) => r.events.length > 1 && r.events.some((e) => e.role !== 'origin')).length
console.log(`${nodes.length} entries read, ${lines.length} written, ${later} with evidence beyond their origin`)
