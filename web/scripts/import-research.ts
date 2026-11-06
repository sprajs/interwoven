// Builds public/data/timeline.json from the research graph.
// Usage: npm run import [path/to/science-technology-graph]
//
// The research data is read only. Every entry carries explicit reviewed topics.
import { readFileSync, writeFileSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import type { DateInterpretation, DateKind, EntryBasis, EntryEvidence, EntryScope, EvidenceStrength, HistoricalBound, HistoricalDate, Level, RawDataset, RawEntry, RawLabel, RawLink, RawNode, RawSource, RawUnplacedNode } from '../src/data/types.ts'
import { validateDataset } from '../src/data/validate.ts'

const INK = {
  indigo: '#265a96',
  madder: '#b0472d',
  verdigris: '#0c8269',
  ochre: '#a8761a',
  plum: '#83406f',
  moss: '#55772b',
}

/** Explicit reviewed topic vocabulary; assignments live on canonical entries. */
const LABEL_CATALOG: RawLabel[] = JSON.parse(readFileSync(join(import.meta.dirname, '../data/label-catalog.json'), 'utf8'))

/** Each label belongs to one subject family, which sets its ink and where it sits on the chart. */
const FAMILIES: { name: string; ink: string; labels: string[] }[] = [
  { name: 'Number & print', ink: INK.moss, labels: ['mathematics', 'arithmetic', 'calculation', 'accounting', 'printing', 'knowledge-transmission', 'timekeeping', 'measurement'] },
  { name: 'Water & wayfinding', ink: INK.verdigris, labels: ['water', 'mills', 'navigation', 'transport', 'agriculture', 'aquaculture'] },
  { name: 'Materials', ink: INK.madder, labels: ['metallurgy', 'materials', 'ceramics', 'polymers', 'chemistry', 'glass'] },
  { name: 'Heat & power', ink: INK.ochre, labels: ['heat', 'steam', 'energy', 'machining', 'electric-power', 'mechanisms'] },
  { name: 'Electricity & computing', ink: INK.indigo, labels: ['electromagnetism', 'radio', 'batteries', 'communication', 'electronics', 'semiconductors', 'computing', 'integrated-circuits'] },
  { name: 'Light & life', ink: INK.plum, labels: ['optics', 'astronomy', 'instruments', 'molecular-biology', 'medicine'] },
]
const FAMILY_OF = new Map(FAMILIES.flatMap((family) => family.labels.map((id) => [id, family] as const)))

export interface ResearchEvent {
  id: string
  node_id: string
  event_type: string
  date?: HistoricalDate
  statement?: string
  scope?: EntryScope
  uncertainty?: string
  review?: { historical_claim?: string; lifecycle_classification?: string }
  evidence?: { source_id: string; locator?: string; supports?: string }[]
}

export interface ResearchNode {
  id: string
  label: string
  kind: 'science' | 'technology' | 'mathematics' | 'practice'
  tier?: Level
  icon?: string
  labels?: string[]
  configuration?: string
  regions?: string[]
  uncertainty?: string
  event_ids: string[]
  community_entry?: { status: string; policy: string; event_id?: string; rationale?: string;
    entry_basis?: EntryBasis; evidence_strength?: EvidenceStrength; date_interpretation?: DateInterpretation;
    community?: string; scope?: EntryScope; evidence?: EntryEvidence[]; uncertainty?: string; proxy_justification?: string }
  graph_anchor?: { status: string; policy: string; event_id?: string; rationale?: string; date_interpretation?: DateInterpretation; scope?: EntryScope; evidence?: EntryEvidence[]; uncertainty?: string }
  witnesses?: { event_id: string; limitation: string }[]
  lifecycle?: RawEntry['lifecycle']
  commercial_applicability?: { status: string; rationale?: string; evidence?: { source_id: string }[] }
  provenance?: { source_ids: string[] }
  review?: { historical_claim: RawEntry['review']; lifecycle_classification?: string }
}

export interface ResearchRecords {
  nodes: ResearchNode[]
  events: ResearchEvent[]
  relationships: { id: string; from: { node_id: string; event_id?: string }; to: { node_id: string; event_id?: string }; relation: string; statement?: string; influence?: string; confidence?: string; temporal_note?: string; review?: { historical_claim: string } }[]
  sources: { id: string; title: string; url?: string; year?: string | number | (string | number)[] }[]
}

const ENTRY_EVENT_TYPES: Record<EntryBasis, string[]> = {
  first_commercial_availability: ['first_commercial_availability'],
  commercial_availability: ['commercial_offer', 'commercial_availability'],
  practical_use: ['practical_use', 'practical_deployment'],
  adoption: ['adoption'], public_availability: ['public_availability'],
  recognition: ['recognition', 'acceptance'], public_awareness: ['publication', 'presentation', 'public_disclosure'],
}
const hasText = (value: unknown): value is string => typeof value === 'string' && value.trim().length > 0
function validScope(value: unknown): value is EntryScope {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false
  const scope = value as Partial<EntryScope>
  const scopedValue = (entry: EntryScope['market'] | undefined) => entry && typeof entry === 'object'
    && ['specified', 'unknown', 'not_yet_researched', 'not_applicable'].includes(entry.status)
    && (entry.status === 'specified' ? hasText(entry.value) : entry.value === undefined)
  return hasText(scope.configuration) && Array.isArray(scope.regions) && scope.regions.every(hasText)
    && Array.isArray(scope.applications) && scope.applications.every(hasText) && Boolean(scopedValue(scope.market)) && Boolean(scopedValue(scope.population))
}

function validBound(bound: HistoricalBound | undefined): bound is HistoricalBound {
  if (!bound || !Number.isInteger(bound.year) || bound.year === 0) return false
  if (bound.month !== undefined && (!Number.isInteger(bound.month) || bound.month < 1 || bound.month > 12)) return false
  if (bound.day !== undefined) {
    if (bound.month === undefined || !Number.isInteger(bound.day) || bound.day < 1 || bound.day > [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][bound.month - 1]!) return false
  }
  return true
}

function boundLabel(bound: HistoricalBound): string {
  let label = bound.year < 0 ? `${-bound.year} BCE` : String(bound.year)
  if (bound.month !== undefined) {
    label = `${'January February March April May June July August September October November December'.split(' ')[bound.month - 1]} ${label}`
    if (bound.day !== undefined) label = `${bound.day} ${label}`
  }
  return label
}

/** A bound is a display limit, never an invented closed interval or exact entry date. */
export function deriveEntryDate(date: HistoricalDate, interpretation: DateInterpretation):
  { entry_date: HistoricalDate; date_kind: DateKind; year: number; start?: number; end?: number } | { reason: string } {
  if (!['known', 'approximate', 'bounded'].includes(date.status)) return { reason: `The selected entry date is ${String(date.status ?? 'missing').replace(/_/g, ' ')}.` }
  if (date.earliest !== undefined && !validBound(date.earliest) || date.latest !== undefined && !validBound(date.latest)) return { reason: 'The selected entry supplies an invalid historical limit.' }
  for (const limit of [date.earliest, date.latest]) {
    if (!limit) continue
    if (date.precision === 'day' && (limit.month === undefined || limit.day === undefined) || date.precision === 'month' && limit.month === undefined) return { reason: 'The supplied entry limit does not match its declared precision.' }
  }
  if (date.earliest && date.earliest_status !== undefined || date.latest && date.latest_status !== undefined) return { reason: 'A supplied date limit cannot also be marked unknown.' }
  if (!date.earliest && !date.latest) return { reason: 'The selected entry has no supplied date limit.' }
  if (date.status === 'known' && (!date.earliest || !date.latest)) return { reason: 'Known events require both supplied date limits.' }
  if (date.earliest && date.latest) {
    const a = date.earliest, b = date.latest
    const before = a.year < b.year || a.year === b.year && ((a.month ?? 1) < (b.month ?? 12) || (a.month ?? 1) === (b.month ?? 12) && (a.day ?? 1) <= (b.day ?? 31))
    if (!before) return { reason: 'The selected entry has reversed date limits.' }
  } else if (!date.earliest && !['unknown', 'not_yet_researched'].includes(date.earliest_status ?? '') || !date.latest && !['unknown', 'not_yet_researched'].includes(date.latest_status ?? '')) {
    return { reason: 'An omitted date limit needs its explicit uncertainty status.' }
  }
  const result = { ...date }
  const qualification = date.status === 'approximate' ? 'approximately ' : ''
  if (interpretation === 'known_by') {
    if (!result.latest) return { reason: 'Known-by entry needs the selected event’s supplied latest limit.' }
    delete result.earliest; delete result.latest_status
    result.earliest_status = date.earliest === undefined ? date.earliest_status ?? 'unknown' : 'unknown'; result.status = date.status === 'approximate' ? 'approximate' : 'bounded'
  } else if (interpretation === 'known_from') {
    if (!result.earliest) return { reason: 'Known-from entry needs the selected event’s supplied earliest limit.' }
    delete result.latest; delete result.earliest_status
    result.latest_status = date.latest === undefined ? date.latest_status ?? 'unknown' : 'unknown'; result.status = date.status === 'approximate' ? 'approximate' : 'bounded'
  } else if (interpretation !== 'event_date') return { reason: 'The community-entry date interpretation is missing or invalid.' }
  if (!result.earliest) {
    result.label = `By ${qualification}${boundLabel(result.latest!)}`
    return { entry_date: result, date_kind: 'known_by', year: result.latest!.year, end: result.latest!.year }
  }
  if (!result.latest) {
    result.label = `Not before ${qualification}${boundLabel(result.earliest)}`
    return { entry_date: result, date_kind: 'known_from', year: result.earliest.year, start: result.earliest.year }
  }
  return { entry_date: result, date_kind: JSON.stringify(result.earliest) === JSON.stringify(result.latest) ? 'point' : 'interval',
    year: (result.earliest.year + result.latest.year) / 2, start: result.earliest.year, end: result.latest.year }
}

function selectedCommunity(node: ResearchNode, events: ResearchEvent[]) {
  const anchor = node.community_entry
  if (anchor?.status !== 'selected') return { reason: `Community entry ${typeof anchor?.status === 'string' ? anchor.status.replace(/_/g, ' ') : anchor ? 'has an invalid status' : 'not recorded'}.` }
  if (anchor.policy !== 'community_entry') return { reason: 'A researched community-entry choice is required.' }
  if (!hasText(anchor.community) || !validScope(anchor.scope) || !hasText(anchor.rationale) || !hasText(anchor.uncertainty)
      || !Array.isArray(anchor.evidence) || !anchor.evidence.length || anchor.evidence.some((item) => !item || !hasText(item.source_id) || !hasText(item.locator) || !hasText(item.supports))) {
    return { reason: 'The entry needs its named community, scope, evidence, rationale and explicit uncertainty.' }
  }
  const basis = anchor.entry_basis
  const strength = anchor.evidence_strength
  if (!basis || !ENTRY_EVENT_TYPES[basis]) return { reason: 'The community-entry basis is missing or unsupported.' }
  if (!['direct', 'scoped_inference', 'awareness_proxy'].includes(strength ?? '')) return { reason: 'The entry needs an explicit evidence-strength assessment.' }
  if ((basis === 'public_awareness') !== (strength === 'awareness_proxy')) return { reason: 'Public awareness must be an explicit proxy and must not be called adoption or actual use.' }
  if (strength === 'scoped_inference' && !['practical_use', 'public_availability'].includes(basis)) return { reason: 'Scoped inference is limited to contextual use or availability.' }
  if (strength !== 'direct' && !hasText(anchor.proxy_justification)) return { reason: 'The awareness proxy or scoped inference needs an explicit justification.' }
  if (node.kind === 'science' && !['practical_use', 'adoption', 'public_availability', 'recognition', 'public_awareness'].includes(basis)) return { reason: 'Science entry needs use, uptake, recognition or an explicit awareness proxy.' }
  if (['first_commercial_availability', 'commercial_availability'].includes(basis) && node.commercial_applicability?.status !== 'applicable') return { reason: 'Commercial entry needs applicable commercial scope.' }
  const event = events.find((entry) => entry.id === anchor.event_id)
  if (!event || !Array.isArray(node.event_ids) || !node.event_ids.includes(event.id)) return { reason: 'The selected entry event is missing or does not belong to this entry.' }
  if (!ENTRY_EVENT_TYPES[basis].includes(event.event_type)) return { reason: 'The selected event does not establish the chosen community entry; invention or discovery is not a fallback.' }
  const lifecycle = node.lifecycle?.[event.event_type]
  if (lifecycle && (lifecycle.status !== 'documented' || !Array.isArray(lifecycle.event_ids) || !lifecycle.event_ids.includes(event.id))) return { reason: 'The selected entry event disagrees with its documented lifecycle stage.' }
  if (!Array.isArray(event.evidence) || !event.evidence.length || !event.date) return { reason: 'The selected entry event needs supporting evidence and a usable date.' }
  const placement = deriveEntryDate(event.date, anchor.date_interpretation!)
  return 'reason' in placement ? placement : { event, ...placement }
}

/** The chart uses an explicitly reviewed record; community entry remains separate. */
function selectedAnchor(node: ResearchNode, events: ResearchEvent[]) {
  const anchor = node.graph_anchor
  if (anchor?.status !== 'selected') return { reason: `Earliest record ${anchor?.status?.replace(/_/g, ' ') ?? 'not recorded'}.` }
  if (anchor.policy !== 'earliest_record') return { reason: 'An earliest-record choice is required.' }
  if (!hasText(anchor.rationale) || !hasText(anchor.uncertainty) || !validScope(anchor.scope) || !anchor.evidence?.length
      || anchor.evidence.some((e) => !hasText(e.source_id) || !hasText(e.locator) || !hasText(e.supports))) return { reason: 'The earliest record needs scope, evidence and explicit uncertainty.' }
  const event = events.find((e) => e.id === anchor.event_id)
  if (!event?.date || !node.event_ids.includes(event.id) || !event.evidence?.length) return { reason: 'The earliest-record event is missing, lacks evidence, or does not belong to this entry.' }
  if (node.witnesses?.some((w) => w.event_id === event.id)) return { reason: 'A surviving copy is not automatically an earliest-record anchor.' }
  if (node.community_entry?.status === 'selected') {
    const community = selectedCommunity(node, events)
    if ('reason' in community) return community
  }
  const placement = deriveEntryDate(event.date, anchor.date_interpretation!)
  return 'reason' in placement ? placement : { event, ...placement }
}


export function buildResearchDataset(records: ResearchRecords): RawDataset {
  const eventsByNode = new Map<string, ResearchEvent[]>()
  for (const event of records.events) {
    const list = eventsByNode.get(event.node_id) ?? []
    list.push(event)
    eventsByNode.set(event.node_id, list)
  }
  const usedLabels = new Set<string>()
  const nodes: RawNode[] = []
  const unplaced: RawUnplacedNode[] = []
  for (const node of records.nodes) {
    const events = eventsByNode.get(node.id) ?? []
    const anchor = selectedAnchor(node, events)
    const labels = node.labels
    if (!labels?.length || labels.some((id) => !LABEL_CATALOG.some((label) => label.id === id))) throw new Error(`Entry ${node.id} needs explicit reviewed labels from the topic vocabulary.`)
    labels.forEach((label) => usedLabels.add(label))
    const sourceIds = new Set<string>(Array.isArray(node.provenance?.source_ids) ? node.provenance.source_ids.filter(hasText) : [])
    const cite = (entries: unknown) => { if (Array.isArray(entries)) for (const evidence of entries) if (evidence && hasText(evidence.source_id)) sourceIds.add(evidence.source_id) }
    for (const event of events) cite(event.evidence)
    for (const stage of Object.values(node.lifecycle ?? {})) cite(stage?.evidence)
    cite(node.commercial_applicability?.evidence)
    cite(node.community_entry?.evidence)
    cite(node.community_entry?.evidence)
    const entry: RawEntry = {
      id: node.id,
      title: node.label,
      kind: node.kind,
      level: node.tier ?? 2,
      date_label: 'Unplaced',
      anchor_status: typeof node.graph_anchor?.status === 'string' ? node.graph_anchor.status : 'missing or invalid',
      anchor_policy: node.graph_anchor?.policy,
      anchor_rationale: hasText(node.graph_anchor?.rationale) ? node.graph_anchor.rationale : undefined,
      anchor_event_id: hasText(node.graph_anchor?.event_id) ? node.graph_anchor.event_id : undefined,
      community_event_id: node.community_entry?.event_id,
      community_date_label: events.find((e) => e.id === node.community_entry?.event_id)?.date?.label,
      record_uncertainty: node.graph_anchor?.uncertainty,
      entry_basis: node.community_entry?.entry_basis,
      evidence_strength: node.community_entry?.evidence_strength,
      date_interpretation: node.graph_anchor?.date_interpretation,
      entry_community: hasText(node.community_entry?.community) ? node.community_entry.community : undefined,
      entry_scope: validScope(node.community_entry?.scope) ? node.community_entry.scope : undefined,
      entry_evidence: Array.isArray(node.community_entry?.evidence) ? node.community_entry.evidence.filter((item) => item && hasText(item.source_id) && hasText(item.locator) && hasText(item.supports)) : undefined,
      entry_uncertainty: hasText(node.community_entry?.uncertainty) ? node.community_entry.uncertainty : undefined,
      proxy_justification: hasText(node.community_entry?.proxy_justification) ? node.community_entry.proxy_justification : undefined,
      commercial_date_status: node.lifecycle?.first_commercial_availability?.status,
      commercial_applicability: node.commercial_applicability?.status,
      lifecycle_review: node.review?.lifecycle_classification,
      lifecycle: node.lifecycle,
      labels,
      summary: node.configuration ?? '',
      regions: node.regions ?? [],
      uncertainty: node.uncertainty || undefined,
      review: node.review?.historical_claim ?? 'candidate',
      sources: [...sourceIds],
    }
    if ('reason' in anchor) {
      unplaced.push({ ...entry, anchor_status: entry.anchor_status!, placement_reason: anchor.reason })
    } else {
      const { event, ...placement } = anchor
      nodes.push({ ...entry, ...placement, date_label: placement.entry_date.label ?? String(placement.year),
        date_basis: event.date?.basis, placed_by: event.event_type.replace(/_/g, ' '), anchored: true })
    }
  }
  const links: RawLink[] = records.relationships.map((link) => ({
    id: link.id, from: link.from.node_id, to: link.to.node_id,
    from_event_id: link.from.event_id, to_event_id: link.to.event_id,
    influence: link.influence, confidence: link.confidence, causal: !['same-principle','same-family','companion-of'].includes(link.relation),
    relation: link.relation.replace(/-/g, ' '), statement: link.statement,
    temporal_note: link.temporal_note, tentative: link.review?.historical_claim !== 'accepted',
  }))
  const cited = new Set([...nodes, ...unplaced].flatMap((node) => node.sources))
  const sources: Record<string, RawSource> = {}
  for (const source of records.sources) if (cited.has(source.id)) sources[source.id] = {
    title: source.title, url: source.url, year: Array.isArray(source.year) ? source.year.join(', ') : source.year,
  }
  const declared = new Map<string, RawLabel>(LABEL_CATALOG.map((label) => [label.id, { id: label.id, name: label.name, ink: label.ink }]))
  return {
    meta: { title: 'Interwoven', description: 'A selective, growing record of science, mathematics, technology and practice; dates mark the earliest evidenced record, with community entry shown separately',
      provenance: 'Generated from research/science-technology-graph. Do not edit by hand.' },
    families: FAMILIES.map(({ name, ink }) => ({ name, ink })),
    labels: [...usedLabels].map((id) => {
      const family = FAMILY_OF.get(id)
      const label = declared.get(id) ?? { id, name: id.replace(/-/g, ' '), ink: '#55524c' }
      return family ? { ...label, ink: family.ink, family: family.name } : label
    }),
    nodes, unplaced, links, sources,
    events: Object.fromEntries(records.events.map((event) => [event.id, { id: event.id, node_id: event.node_id,
      event_type: event.event_type, date_label: event.date?.label ?? 'Date not recorded',
      date_status: event.date?.status ?? 'missing', date_basis: event.date?.basis, date: event.date, statement: event.statement,
      scope: event.scope, uncertainty: event.uncertainty, review: event.review?.historical_claim,
      lifecycle_review: event.review?.lifecycle_classification,
      evidence: event.evidence }])),
  }
}

function main(): void {
  const dir = process.argv[2] ?? join(import.meta.dirname, '../../research/science-technology-graph')
  const readJsonl = (name: string) => readFileSync(join(dir, 'data', name), 'utf8').split('\n').filter((line) => line.trim()).map((line) => JSON.parse(line))
  const dataset = buildResearchDataset({ nodes: readJsonl('nodes.jsonl'), events: readJsonl('events.jsonl'),
    relationships: readJsonl('relationships.jsonl'), sources: readJsonl('sources.jsonl') })
  const issues = validateDataset(dataset)
  for (const issue of issues) console.log(`${issue.severity}: ${issue.message}`)
  const invalidSelections = (dataset.unplaced ?? []).filter((entry) => entry.anchor_status === 'selected')
  for (const entry of invalidSelections) console.log(`error: selected community entry ${entry.id}: ${entry.placement_reason}`)
  if (issues.some((issue) => issue.severity === 'error') || invalidSelections.length) process.exit(1)
  const block = (items: unknown[]) => `[\n${items.map((item) => `  ${JSON.stringify(item)}`).join(',\n')}\n]`
  const out = `{\n"meta": ${JSON.stringify(dataset.meta)},\n"families": ${JSON.stringify(dataset.families)},\n"labels": ${block(dataset.labels)},\n"nodes": ${block(dataset.nodes)},\n"unplaced": ${block(dataset.unplaced ?? [])},\n"links": ${block(dataset.links)},\n"events": ${JSON.stringify(dataset.events)},\n"sources": ${JSON.stringify(dataset.sources)}\n}\n`
  writeFileSync(join(import.meta.dirname, '../public/data/timeline.json'), out)
  console.log(`${dataset.nodes.length} placed, ${dataset.unplaced?.length ?? 0} unplaced, ${dataset.links.length} relationships retained`)
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main()
