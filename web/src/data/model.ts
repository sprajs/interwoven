import { MARK_RADIUS } from '../design.ts'
import { TimeScale } from '../engine/time.ts'
import { computeReach, type Reach } from './derive.ts'
import { layoutStrands, type Family } from './layout.ts'
import { buildLifeRecords, type LifeRecord } from './lifecycle.ts'
import { KINDS, type RawDataset, type RawLabel, type RawLink, type RawNode, type RawUnplacedNode, type TimelineEntry } from './types.ts'

export interface Edge {
  source: number
  target: number
  tentative: boolean
  link: RawLink
}

export interface Model {
  title: string
  description: string
  nodes: RawNode[]
  unplaced: RawUnplacedNode[]
  entryById: Map<string, TimelineEntry>
  links: RawLink[]
  events: NonNullable<RawDataset['events']>
  n: number
  edges: Edge[]
  labels: (RawLabel & { count: number })[]
  labelById: Map<string, RawLabel>
  sources: NonNullable<RawDataset['sources']>
  time: TimeScale
  parents: number[][]
  children: number[][]
  edgesInto: Edge[][]
  edgesOutOf: Edge[][]
  /** Position per node, 0..1 top to bottom. */
  y: Float32Array
  /** Mark radius in CSS pixels. */
  radius: Float32Array
  ink: Float32Array
  /** Transitive descendants of each node. */
  impact: Int32Array
  /** Most important first. Used to place text greedily. */
  byPriority: Int32Array
  /** The key entries in date order, to browse before searching. */
  keyEntries: number[]
  /** Each entry's subject family, as an index into `families`. */
  familyOf: Int32Array
  /** Subject families, top to bottom. */
  families: Family[]
  /** The distance between neighbouring rows of the chart, on the same scale as y. */
  rowStep: number
  /** How long each entry went on being built on, from the links. */
  reach: Reach
  /** What the research documents about the later life of each entry, by id. */
  life: Map<string, LifeRecord>
  indexById: Map<string, number>
}

const FALLBACK_INK = '#4a433b'
const FULL_IMPACT_LIMIT = 4000

export function hexToRgb(hex: string): [number, number, number] {
  const v = parseInt(hex.replace('#', ''), 16)
  return [((v >> 16) & 255) / 255, ((v >> 8) & 255) / 255, (v & 255) / 255]
}

export function countDescendants(start: number, children: number[][], seen: Int32Array, stamp: number): number {
  const stack = [start]
  seen[start] = stamp
  let count = 0
  while (stack.length) {
    const i = stack.pop()!
    for (const c of children[i]!) {
      if (seen[c] === stamp) continue
      seen[c] = stamp
      count++
      stack.push(c)
    }
  }
  return count
}

export function buildModel(data: RawDataset): Model {
  const nodes = data.nodes
  const n = nodes.length
  const indexById = new Map(nodes.map((node, i) => [node.id, i]))
  const labelById = new Map(data.labels.map((label) => [label.id, label]))
  const parents: number[][] = Array.from({ length: n }, () => [])
  const children: number[][] = Array.from({ length: n }, () => [])
  const edgesInto: Edge[][] = Array.from({ length: n }, () => [])
  const edgesOutOf: Edge[][] = Array.from({ length: n }, () => [])
  const edges: Edge[] = []
  const labelCounts = new Map<string, number>()

  nodes.forEach((node) => {
    for (const label of node.labels) labelCounts.set(label, (labelCounts.get(label) ?? 0) + 1)
  })
  for (const link of data.links) {
    const source = indexById.get(link.from)
    const target = indexById.get(link.to)
    if (source === undefined || target === undefined) continue
    const edge: Edge = { source, target, tentative: link.tentative, link }
    edges.push(edge)
    if (link.causal !== false) {
      parents[target]!.push(source)
      children[source]!.push(target)
      edgesInto[target]!.push(edge)
      edgesOutOf[source]!.push(edge)
    }
  }

  const time = TimeScale.fromYears(nodes.map((node) => node.year))
  const familyOfLabel = (id: string | undefined) => {
    const label = id === undefined ? undefined : labelById.get(id)
    return label?.family ?? label?.name ?? 'Other'
  }
  const familyNames = nodes.map((node) => familyOfLabel(node.labels[0]))
  const { y, families, rowStep } = layoutStrands({
    u: Float32Array.from(nodes, (node) => time.compressed(node.year)),
    levels: nodes.map((node) => node.level),
    family: familyNames,
    label: nodes.map((node) => node.labels[0] ?? ''),
    edges,
    order: data.families ?? [],
  })

  const familyIndex = new Map(families.map((family, k) => [family.name, k]))
  const familyOf = Int32Array.from(familyNames, (name) => familyIndex.get(name) ?? 0)

  const radius = new Float32Array(n)
  const ink = new Float32Array(n * 3)
  const impact = new Int32Array(n)
  const seen = new Int32Array(n).fill(-1)
  const keyEntries: number[] = []
  nodes.forEach((node, i) => {
    if (node.level === 0) keyEntries.push(i)
    impact[i] = n <= FULL_IMPACT_LIMIT || node.level === 0 ? countDescendants(i, children, seen, i) : children[i]!.length
    radius[i] = MARK_RADIUS[node.level] ?? MARK_RADIUS[3]!
    const primary = labelById.get(node.labels[0] ?? '')
    ink.set(hexToRgb(primary?.ink ?? FALLBACK_INK), i * 3)
  })
  keyEntries.sort((a, b) => nodes[a]!.year - nodes[b]!.year)

  const byPriority = Int32Array.from(nodes.keys()).sort(
    (a, b) => nodes[a]!.level - nodes[b]!.level || impact[b]! - impact[a]! || children[b]!.length - children[a]!.length,
  )

  const labels = data.labels
    .map((label) => ({ ...label, count: labelCounts.get(label.id) ?? 0 }))
    .filter((label) => label.count > 0)
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))

  return {
    title: data.meta?.title ?? 'Timeline',
    description: data.meta?.description ?? '',
    nodes,
    unplaced: data.unplaced ?? [],
    entryById: new Map([...nodes, ...(data.unplaced ?? [])].map((entry) => [entry.id, entry])),
    links: data.links,
    events: data.events ?? {},
    n,
    edges,
    labels,
    labelById,
    sources: data.sources ?? {},
    time,
    parents,
    children,
    edgesInto,
    edgesOutOf,
    y,
    radius,
    ink,
    impact,
    byPriority,
    keyEntries,
    familyOf,
    families,
    rowStep,
    reach: computeReach(nodes, edges.filter((edge) => edge.link.causal !== false)),
    life: buildLifeRecords([...nodes, ...(data.unplaced ?? [])], data.events ?? {}),
    indexById,
  }
}

const SHAPE_BY_KIND = new Map(KINDS.map((k) => [k.id, k.shape]))

/** Independent style flags: kind, explicit date bound, then evidence strength. */
export function nodeMarkStyle(node: RawNode): number {
  const bound = node.date_kind === 'known_by' ? 1 : node.date_kind === 'known_from' ? 2 : 0
  const strength = node.evidence_strength === 'scoped_inference' ? 1 : node.evidence_strength === 'awareness_proxy' ? 2 : 0
  return (SHAPE_BY_KIND.get(node.kind) ?? 0) + bound * 4 + strength * 16
}

/** Hops from `start` along `adjacency`, up to `maxHops`. The start node maps to 0. */
export function walk(start: number, adjacency: number[][], maxHops: number): Map<number, number> {
  const hops = new Map<number, number>([[start, 0]])
  let frontier = [start]
  for (let h = 1; h <= maxHops && frontier.length; h++) {
    const next: number[] = []
    for (const i of frontier) {
      for (const j of adjacency[i]!) {
        if (hops.has(j)) continue
        hops.set(j, h)
        next.push(j)
      }
    }
    frontier = next
  }
  return hops
}
