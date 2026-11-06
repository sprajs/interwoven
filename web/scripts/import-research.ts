// Builds public/data/timeline.json from the research graph.
// Usage: npm run import [path/to/science-technology-graph]
//
// The research data is read only. Labels are not part of it yet, so they come from
// the rules below, and data/label-overrides.json can replace them for any node.
import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import type { Level, RawDataset, RawLabel, RawLink, RawNode, RawSource } from '../src/data/types.ts'
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

const dir = process.argv[2] ?? join(import.meta.dirname, '../../research/science-technology-graph')
const readJsonl = (name: string): any[] =>
  readFileSync(join(dir, 'data', name), 'utf8')
    .split('\n')
    .filter((line) => line.trim())
    .map((line) => JSON.parse(line))

const rawNodes = readJsonl('nodes.jsonl')
const rawEvents = readJsonl('events.jsonl')
const rawLinks = readJsonl('relationships.jsonl')
const rawSources = readJsonl('sources.jsonl')

const overridesPath = join(import.meta.dirname, '../data/label-overrides.json')
const overrides: Record<string, string[]> = existsSync(overridesPath) ? JSON.parse(readFileSync(overridesPath, 'utf8')) : {}

const eventsByNode = new Map<string, any[]>()
for (const event of rawEvents) {
  const list = eventsByNode.get(event.node_id) ?? []
  list.push(event)
  eventsByNode.set(event.node_id, list)
}

const usedLabels = new Set<string>()
const skipped: string[] = []
const nodes: RawNode[] = []

for (const node of rawNodes) {
  const events = (eventsByNode.get(node.id) ?? []).filter((e) => e.date?.earliest && e.date?.latest)
  const anchorId = node.graph_anchor?.status === 'selected' ? node.graph_anchor.event_id : undefined
  // An undated node cannot sit on a timeline. It stays out rather than getting an invented date.
  const anchorEvent = events.find((e) => e.id === anchorId)
  const event = anchorEvent ?? [...events].sort((a, b) => a.date.earliest.year - b.date.earliest.year)[0]
  if (!event) {
    skipped.push(node.id)
    continue
  }
  const start: number = event.date.earliest.year
  const end: number = event.date.latest.year

  const haystack = `${node.id} ${node.label} icon:${node.icon ?? ''}`.toLowerCase()
  const labels = overrides[node.id] ?? node.labels ?? LABEL_RULES.filter((rule) => rule.test.test(haystack)).map((rule) => rule.id)
  labels.forEach((label: string) => usedLabels.add(label))

  const sources = new Set<string>()
  for (const e of events) for (const evidence of e.evidence ?? []) if (evidence.source_id) sources.add(evidence.source_id)

  nodes.push({
    id: node.id,
    title: node.label,
    kind: node.kind === 'science' ? 'science' : 'technology',
    level: (node.tier ?? 2) as Level,
    year: (start + end) / 2,
    start,
    end,
    date_label: event.date.label ?? (start === end ? String(start) : `${start} to ${end}`),
    date_basis: event.date.basis,
    placed_by: String(event.event_type ?? 'dated record').replace(/_/g, ' '),
    anchored: Boolean(anchorEvent),
    labels,
    summary: node.configuration ?? '',
    regions: node.regions ?? [],
    uncertainty: node.uncertainty || undefined,
    review: node.review?.historical_claim ?? 'candidate',
    sources: [...sources],
  })
}

const placed = new Set(nodes.map((n) => n.id))
const links: RawLink[] = rawLinks
  .filter((r) => placed.has(r.from?.node_id) && placed.has(r.to?.node_id))
  .map((r) => ({
    from: r.from.node_id,
    to: r.to.node_id,
    relation: String(r.relation ?? '').replace(/-/g, ' '),
    statement: r.statement,
    tentative: r.review?.historical_claim !== 'accepted',
  }))

const sources: Record<string, RawSource> = {}
const cited = new Set(nodes.flatMap((n) => n.sources))
for (const s of rawSources) if (cited.has(s.id)) sources[s.id] = { title: s.title, url: s.url, year: s.year }

const declared = new Map<string, RawLabel>(LABEL_RULES.map((r) => [r.id, { id: r.id, name: r.name, ink: r.ink }]))
const labels: RawLabel[] = [...usedLabels].map(
  (id) => declared.get(id) ?? { id, name: id.replace(/-/g, ' '), ink: '#55524c' },
)

const dataset: RawDataset = {
  meta: {
    title: 'Interwoven',
    description: 'How science and technology build on one another',
    provenance: 'Generated from research/science-technology-graph. Do not edit by hand.',
  },
  labels,
  nodes,
  links,
  sources,
}

const issues = validateDataset(dataset)
for (const issue of issues) console.log(`${issue.severity}: ${issue.message}`)
if (issues.some((i) => i.severity === 'error')) process.exit(1)

const block = (items: unknown[]) => `[\n${items.map((item) => `  ${JSON.stringify(item)}`).join(',\n')}\n]`
const out = `{\n"meta": ${JSON.stringify(dataset.meta)},\n"labels": ${block(labels)},\n"nodes": ${block(nodes)},\n"links": ${block(links)},\n"sources": ${JSON.stringify(sources)}\n}\n`
writeFileSync(join(import.meta.dirname, '../public/data/timeline.json'), out)

const unlabeled = nodes.filter((n) => n.labels.length === 0).map((n) => n.id)
const avg = nodes.reduce((sum, n) => sum + n.labels.length, 0) / Math.max(1, nodes.length)
console.log(`${nodes.length} nodes (${skipped.length} undated left out), ${links.length} links, ${labels.length} labels, ${avg.toFixed(2)} labels per node`)
if (skipped.length) console.log(`Undated: ${skipped.join(', ')}`)
if (unlabeled.length) console.log(`No label matched: ${unlabeled.join(', ')}`)
