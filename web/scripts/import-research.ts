// Builds public/data/timeline.json from the research graph.
// Usage: npm run import [path/to/science-technology-graph]
//
// The research data is read only. Labels are not part of it yet, so they come from
// the rules below, and data/label-overrides.json can replace them for any node.
import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import type { Level, RawDataset, RawEntry, RawLabel, RawLink, RawNode, RawSource, RawUnplacedNode } from '../src/data/types.ts'
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
  date?: { status: string; earliest?: { year: number }; latest?: { year: number }; earliest_status?: string; latest_status?: string; label?: string; basis?: string }
  statement?: string
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
  graph_anchor?: { status: string; policy: string; event_id?: string; rationale?: string }
  lifecycle?: Record<string, { status: string; event_ids: string[]; evidence?: { source_id: string }[] }>
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

const SCIENTIFIC = new Set(['discovery', 'observation', 'formulation', 'publication', 'presentation', 'experimental_confirmation', 'acceptance'])

function selectedAnchor(node: ResearchNode, events: ResearchEvent[]): { event: ResearchEvent; start: number; end: number } | { reason: string } {
  const anchor = node.graph_anchor
  if (anchor?.status !== 'selected') return { reason: `Anchor ${anchor?.status?.replace(/_/g, ' ') ?? 'not recorded'}.` }
  const event = events.find((entry) => entry.id === anchor.event_id)
  if (!event || !node.event_ids.includes(event.id)) return { reason: 'The selected anchor event is missing or does not belong to this entry.' }
  if (node.kind === 'technology') {
    if (!['first_commercial_availability', 'practical_deployment'].includes(anchor.policy) || event.event_type !== anchor.policy) {
      return { reason: 'The selected event does not match the technology anchor policy.' }
    }
    const applicability = node.commercial_applicability
    if (anchor.policy === 'first_commercial_availability' && applicability?.status !== 'applicable') {
      return { reason: 'Commercial applicability has not been established for the selected commercial anchor.' }
    }
    if (anchor.policy === 'practical_deployment' && (!['nonmarket', 'not_applicable'].includes(applicability?.status ?? '') || !applicability?.rationale?.trim() || !applicability.evidence?.length)) {
      return { reason: 'The deployment anchor needs a justified nonmarket applicability decision.' }
    }
  } else if (anchor.policy !== 'scientific_event' || !SCIENTIFIC.has(event.event_type)) {
    return { reason: 'The selected event does not match the scientific anchor policy.' }
  }
  const stage = anchor.policy === 'scientific_event' ? event.event_type : anchor.policy
  const lifecycle = node.lifecycle?.[stage]
  if (stage !== 'presentation' && (lifecycle?.status !== 'documented' || !lifecycle.event_ids.includes(event.id))) {
    return { reason: 'The selected anchor is not recorded in its documented lifecycle stage.' }
  }
  if (!event.evidence?.length) return { reason: 'The selected anchor event has no supporting evidence.' }
  if (!['known', 'approximate', 'bounded'].includes(event.date?.status ?? '')) {
    return { reason: `The selected anchor date is ${event.date?.status?.replace(/_/g, ' ') ?? 'not recorded'}.` }
  }
  const start = event.date?.earliest?.year
  const end = event.date?.latest?.year
  if (start === undefined || end === undefined) return { reason: 'The selected anchor has an open date bound; a position on the timeline would imply an unsupported limit.' }
  if (!Number.isInteger(start) || !Number.isInteger(end) || start === 0 || end === 0 || start > end) {
    return { reason: 'The selected anchor does not supply a valid historical date interval.' }
  }
  return { event, start, end }
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
    const sourceIds = new Set(node.provenance?.source_ids ?? [])
    for (const event of events) for (const evidence of event.evidence ?? []) sourceIds.add(evidence.source_id)
    for (const stage of Object.values(node.lifecycle ?? {})) for (const evidence of stage.evidence ?? []) sourceIds.add(evidence.source_id)
    for (const evidence of node.commercial_applicability?.evidence ?? []) sourceIds.add(evidence.source_id)
    const entry: RawEntry = {
      id: node.id,
      title: node.label,
      kind: node.kind,
      level: node.tier ?? 2,
      date_label: 'Unplaced',
      anchor_status: node.graph_anchor?.status ?? 'missing',
      anchor_policy: node.graph_anchor?.policy,
      anchor_rationale: node.graph_anchor?.rationale,
      anchor_event_id: node.graph_anchor?.event_id,
      commercial_date_status: node.lifecycle?.first_commercial_availability?.status,
      commercial_applicability: node.commercial_applicability?.status,
      lifecycle_review: node.review?.lifecycle_classification,
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
      nodes.push({ ...entry, year: (anchor.start + anchor.end) / 2, start: anchor.start, end: anchor.end,
        date_label: anchor.event.date?.label ?? `${anchor.start} to ${anchor.end}`,
        date_basis: anchor.event.date?.basis, placed_by: anchor.event.event_type.replace(/_/g, ' '), anchored: true })
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
    meta: { title: 'Interwoven', description: 'How science and technology build on one another',
      provenance: 'Generated from research/science-technology-graph. Do not edit by hand.' },
    labels: [...usedLabels].map((id) => declared.get(id) ?? { id, name: id.replace(/-/g, ' '), ink: '#55524c' }),
    nodes, unplaced, links, sources,
    events: Object.fromEntries(records.events.map((event) => [event.id, { id: event.id, node_id: event.node_id,
      event_type: event.event_type, date_label: event.date?.label ?? 'Date not recorded',
      date_status: event.date?.status ?? 'missing', date_basis: event.date?.basis, statement: event.statement }])),
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
  if (issues.some((issue) => issue.severity === 'error')) process.exit(1)
  const block = (items: unknown[]) => `[\n${items.map((item) => `  ${JSON.stringify(item)}`).join(',\n')}\n]`
  const out = `{\n"meta": ${JSON.stringify(dataset.meta)},\n"labels": ${block(dataset.labels)},\n"nodes": ${block(dataset.nodes)},\n"unplaced": ${block(dataset.unplaced ?? [])},\n"links": ${block(dataset.links)},\n"events": ${JSON.stringify(dataset.events)},\n"sources": ${JSON.stringify(dataset.sources)}\n}\n`
  writeFileSync(join(import.meta.dirname, '../public/data/timeline.json'), out)
  console.log(`${dataset.nodes.length} placed, ${dataset.unplaced?.length ?? 0} unplaced, ${dataset.links.length} relationships retained`)
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main()
