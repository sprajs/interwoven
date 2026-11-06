// Builds public/data/timeline.json from the research graph.
// Usage: npm run import [path/to/science-technology-graph]
//
// The research data is read only. Labels are not part of it yet, so they come from
// the rules below, and data/label-overrides.json can replace them for any node.
import { existsSync, readFileSync, writeFileSync } from 'node:fs'
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

/**
 * A node takes every label whose test matches, so one entry can belong to several
 * threads at once. The first match sets its ink, so order runs from specific to broad.
 */
const LABEL_RULES: { id: string; name: string; ink: string; test: RegExp }[] = [
  { id: 'genetics', name: 'Genetics', ink: INK.plum, test: /^bio-/ },
  { id: 'computing', name: 'Computing', ink: INK.plum, test: /4004|micrologic|flip-flop|cpu|kilby|noyce|multiplexer|icon:logic.*elec|icon:computer/ },
  { id: 'semiconductors', name: 'Semiconductors', ink: INK.indigo, test: /fairchild|hoerni|planar|bardeen|point-contact|oxide|atalla|mos-|kilby|noyce|intel|4004|photolithographic|multiplexer|surface/ },
  { id: 'radio', name: 'Radio waves', ink: INK.indigo, test: /hertz|marconi|branly|helmholtz|maxwell/ },
  { id: 'electromagnetism', name: 'Electromagnetism', ink: INK.indigo, test: /oersted|ampere|faraday-(rotation|ring|moving|disc|magneto)|maxwell|helmholtz|hertz|magnetocalorimeter|volta/ },
  { id: 'batteries', name: 'Batteries', ink: INK.indigo, test: /volta|trough-battery/ },
  { id: 'wayfinding', name: 'Wayfinding', ink: INK.verdigris, test: /hokulea|mau-|malindi|marshall|korent|planetarium|ra-i-/ },
  { id: 'water', name: 'Water works', ink: INK.verdigris, test: /muldoons|dholavira|aqueduct/ },
  { id: 'mills', name: 'Mills', ink: INK.verdigris, test: /mill|barbegal/ },
  { id: 'metallurgy', name: 'Metals', ink: INK.madder, test: /copper(?!-disc)|bronze|iron(?!-plate)|steel|bessemer|crucible|cofusion|linz|gerlafingen|edsken/ },
  { id: 'heat', name: 'Heat & energy', ink: INK.ochre, test: /joule|clausius|carnot|clapeyron|thomson|regnault|rumford|friction/ },
  { id: 'steam', name: 'Steam power', ink: INK.ochre, test: /^mech-(condenser|soho|bloomfield|rotative|double-acting|expansion|papplewick|bersham|wilkinson)|regnault|carnot|clapeyron/ },
  { id: 'machining', name: 'Precision making', ink: INK.ochre, test: /bersham|wilkinson|engine-shop|rumford/ },
  { id: 'printing', name: 'Printing', ink: INK.moss, test: /sutra|jikji|bi-sheng/ },
  { id: 'arithmetic', name: 'Arithmetic', ink: INK.moss, test: /brahmagupta|khwarizmi|uqlidisi|algorizmi|alchorismi|bugia|liber-abaci|ibn-banna|hawari/ },
  { id: 'calculation', name: 'Calculating tools', ink: INK.moss, test: /napier|briggs|gunter|oughtred|allen/ },
  { id: 'optics', name: 'Optics & glass', ink: INK.plum, test: /spyglass|telescope|reflector|refraction|(?<!google-)glass|apochromat|eyepiece|optical|zeiss|lunar|jupiter|microscope/ },
  { id: 'astronomy', name: 'Astronomy', ink: INK.indigo, test: /galileo|telescope|reflector|jupiter|lunar|spyglass/ },
  { id: 'instruments', name: 'Instruments', ink: INK.moss, test: /calorimeter|apparatus|spyglass|telescope|reflector|detector|objective|eyepiece|gunter|oughtred|allen|diffraction|polymerase/ },
  // Broad threads last. They cross the specific ones without changing a node's ink.
  { id: 'energy', name: 'Energy', ink: INK.ochre, test: /steam|engine|condenser|mill|battery|generator|volta|carnot|joule|clausius/ },
  { id: 'electronics', name: 'Electronics', ink: INK.indigo, test: /fairchild|hoerni|planar|point-contact|atalla|kilby|noyce|intel|multiplexer|marconi|branly/ },
  { id: 'materials', name: 'Materials', ink: INK.madder, test: /copper(?!-disc)|bronze|iron(?!-plate)|steel|bessemer|crucible|(?<!google-)glass|oxide|silicon|germanium|fired-types/ },
  { id: 'measurement', name: 'Measurement', ink: INK.moss, test: /joule|regnault|rumford|calorimeter|comparisons|diffraction|base-ratios|survey|observation|absolute-scale/ },
  { id: 'knowledge', name: 'Spread of knowledge', ink: INK.moss, test: /latin|teaching|bugia|liber|malindi|hawari|printing|jikji|sutra|bi-sheng/ },
]

export interface ResearchEvent {
  id: string
  node_id: string
  event_type: string
  date?: HistoricalDate
  statement?: string
  scope?: EntryScope
  uncertainty?: string
  evidence?: { source_id: string }[]
}

export interface ResearchNode {
  id: string
  label: string
  kind: 'science' | 'technology'
  tier?: Level
  icon?: string
  labels?: string[]
  configuration?: string
  regions?: string[]
  uncertainty?: string
  event_ids: string[]
  graph_anchor?: { status: string; policy: string; event_id?: string; rationale?: string;
    entry_basis?: EntryBasis; evidence_strength?: EvidenceStrength; date_interpretation?: DateInterpretation;
    community?: string; scope?: EntryScope; evidence?: EntryEvidence[]; uncertainty?: string; proxy_justification?: string }
  lifecycle?: RawEntry['lifecycle']
  commercial_applicability?: { status: string; rationale?: string; evidence?: { source_id: string }[] }
  provenance?: { source_ids: string[] }
  review?: { historical_claim: RawEntry['review']; lifecycle_classification?: string }
}

export interface ResearchRecords {
  nodes: ResearchNode[]
  events: ResearchEvent[]
  relationships: { id: string; from: { node_id: string; event_id?: string }; to: { node_id: string; event_id?: string }; relation: string; statement?: string; temporal_note?: string; review?: { historical_claim: string } }[]
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
  if (['known', 'approximate'].includes(date.status) && (!date.earliest || !date.latest)) return { reason: 'Known and approximate events require both supplied date limits.' }
  if (date.earliest && date.latest) {
    const a = date.earliest, b = date.latest
    const before = a.year < b.year || a.year === b.year && ((a.month ?? 1) < (b.month ?? 12) || (a.month ?? 1) === (b.month ?? 12) && (a.day ?? 1) <= (b.day ?? 31))
    if (!before) return { reason: 'The selected entry has reversed date limits.' }
  } else if (!date.earliest && !['unknown', 'not_yet_researched'].includes(date.earliest_status ?? '') || !date.latest && !['unknown', 'not_yet_researched'].includes(date.latest_status ?? '')) {
    return { reason: 'An omitted date limit needs its explicit uncertainty status.' }
  }
  const result = { ...date }
  if (interpretation === 'known_by') {
    if (!result.latest) return { reason: 'Known-by entry needs the selected event’s supplied latest limit.' }
    delete result.earliest; delete result.latest_status
    result.earliest_status = date.earliest === undefined ? date.earliest_status ?? 'unknown' : 'unknown'; result.status = 'bounded'
  } else if (interpretation === 'known_from') {
    if (!result.earliest) return { reason: 'Known-from entry needs the selected event’s supplied earliest limit.' }
    delete result.latest; delete result.earliest_status
    result.latest_status = date.latest === undefined ? date.latest_status ?? 'unknown' : 'unknown'; result.status = 'bounded'
  } else if (interpretation !== 'event_date') return { reason: 'The community-entry date interpretation is missing or invalid.' }
  if (!result.earliest) {
    result.label = `By ${boundLabel(result.latest!)}`
    return { entry_date: result, date_kind: 'known_by', year: result.latest!.year, end: result.latest!.year }
  }
  if (!result.latest) {
    result.label = `Not before ${boundLabel(result.earliest)}`
    return { entry_date: result, date_kind: 'known_from', year: result.earliest.year, start: result.earliest.year }
  }
  return { entry_date: result, date_kind: JSON.stringify(result.earliest) === JSON.stringify(result.latest) ? 'point' : 'interval',
    year: (result.earliest.year + result.latest.year) / 2, start: result.earliest.year, end: result.latest.year }
}

function selectedAnchor(node: ResearchNode, events: ResearchEvent[]) {
  const anchor = node.graph_anchor
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

/** No record is placed by an unselected invention or other dated event. */
export function buildResearchDataset(records: ResearchRecords, overrides: Record<string, string[]> = {}): RawDataset {
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
    const haystack = `${node.id} ${node.label} icon:${node.icon ?? ''}`.toLowerCase()
    const labels = overrides[node.id] ?? node.labels ?? LABEL_RULES.filter((rule) => rule.test.test(haystack)).map((rule) => rule.id)
    labels.forEach((label) => usedLabels.add(label))
    const sourceIds = new Set<string>(Array.isArray(node.provenance?.source_ids) ? node.provenance.source_ids.filter(hasText) : [])
    const cite = (entries: unknown) => { if (Array.isArray(entries)) for (const evidence of entries) if (evidence && hasText(evidence.source_id)) sourceIds.add(evidence.source_id) }
    for (const event of events) cite(event.evidence)
    for (const stage of Object.values(node.lifecycle ?? {})) cite(stage?.evidence)
    cite(node.commercial_applicability?.evidence)
    cite(node.graph_anchor?.evidence)
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
      entry_basis: node.graph_anchor?.entry_basis,
      evidence_strength: node.graph_anchor?.evidence_strength,
      date_interpretation: node.graph_anchor?.date_interpretation,
      entry_community: hasText(node.graph_anchor?.community) ? node.graph_anchor.community : undefined,
      entry_scope: validScope(node.graph_anchor?.scope) ? node.graph_anchor.scope : undefined,
      entry_evidence: Array.isArray(node.graph_anchor?.evidence) ? node.graph_anchor.evidence.filter((item) => item && hasText(item.source_id) && hasText(item.locator) && hasText(item.supports)) : undefined,
      entry_uncertainty: hasText(node.graph_anchor?.uncertainty) ? node.graph_anchor.uncertainty : undefined,
      proxy_justification: hasText(node.graph_anchor?.proxy_justification) ? node.graph_anchor.proxy_justification : undefined,
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
    relation: link.relation.replace(/-/g, ' '), statement: link.statement,
    temporal_note: link.temporal_note, tentative: link.review?.historical_claim !== 'accepted',
  }))
  const cited = new Set([...nodes, ...unplaced].flatMap((node) => node.sources))
  const sources: Record<string, RawSource> = {}
  for (const source of records.sources) if (cited.has(source.id)) sources[source.id] = {
    title: source.title, url: source.url, year: Array.isArray(source.year) ? source.year.join(', ') : source.year,
  }
  const declared = new Map<string, RawLabel>(LABEL_RULES.map((rule) => [rule.id, { id: rule.id, name: rule.name, ink: rule.ink }]))
  return {
    meta: { title: 'Interwoven', description: 'Availability, use and recognition across communities',
      provenance: 'Generated from research/science-technology-graph. Do not edit by hand.' },
    labels: [...usedLabels].map((id) => declared.get(id) ?? { id, name: id.replace(/-/g, ' '), ink: '#55524c' }),
    nodes, unplaced, links, sources,
    events: Object.fromEntries(records.events.map((event) => [event.id, { id: event.id, node_id: event.node_id,
      event_type: event.event_type, date_label: event.date?.label ?? 'Date not recorded',
      date_status: event.date?.status ?? 'missing', date_basis: event.date?.basis, date: event.date, statement: event.statement,
      scope: event.scope, uncertainty: event.uncertainty }])),
  }
}

function main(): void {
  const dir = process.argv[2] ?? join(import.meta.dirname, '../../research/science-technology-graph')
  const readJsonl = (name: string) => readFileSync(join(dir, 'data', name), 'utf8').split('\n').filter((line) => line.trim()).map((line) => JSON.parse(line))
  const overridesPath = join(import.meta.dirname, '../data/label-overrides.json')
  const overrides = existsSync(overridesPath) ? JSON.parse(readFileSync(overridesPath, 'utf8')) : {}
  const dataset = buildResearchDataset({ nodes: readJsonl('nodes.jsonl'), events: readJsonl('events.jsonl'),
    relationships: readJsonl('relationships.jsonl'), sources: readJsonl('sources.jsonl') }, overrides)
  const issues = validateDataset(dataset)
  for (const issue of issues) console.log(`${issue.severity}: ${issue.message}`)
  const invalidSelections = (dataset.unplaced ?? []).filter((entry) => entry.anchor_status === 'selected')
  for (const entry of invalidSelections) console.log(`error: selected community entry ${entry.id}: ${entry.placement_reason}`)
  if (issues.some((issue) => issue.severity === 'error') || invalidSelections.length) process.exit(1)
  const block = (items: unknown[]) => `[\n${items.map((item) => `  ${JSON.stringify(item)}`).join(',\n')}\n]`
  const out = `{\n"meta": ${JSON.stringify(dataset.meta)},\n"labels": ${block(dataset.labels)},\n"nodes": ${block(dataset.nodes)},\n"unplaced": ${block(dataset.unplaced ?? [])},\n"links": ${block(dataset.links)},\n"events": ${JSON.stringify(dataset.events)},\n"sources": ${JSON.stringify(dataset.sources)}\n}\n`
  writeFileSync(join(import.meta.dirname, '../public/data/timeline.json'), out)
  console.log(`${dataset.nodes.length} placed, ${dataset.unplaced?.length ?? 0} unplaced, ${dataset.links.length} relationships retained`)
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main()
