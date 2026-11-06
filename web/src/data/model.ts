import { TimeScale } from '../engine/time.ts'
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
  synthetic: boolean
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
  landmarks: number[]
  indexById: Map<string, number>
}

const LEVEL_RADIUS = [4.4, 3.3, 2.6, 2.1]
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

function seededRandom(seed: number): () => number {
  let s = seed >>> 0
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0
    return s / 4294967296
  }
}

/**
 * Finds vertical positions from the graph itself. Time fixes x, and y settles under
 * four forces: links pull connected work together, shared labels pull gently so related
 * threads drift near each other without forming bands, nearby marks push apart so the
 * text has room, and a weak pull keeps everything on the sheet.
 */
export function layoutThreads(nodes: RawNode[], edges: Pick<Edge, 'source' | 'target'>[], time: TimeScale): Float32Array {
  const n = nodes.length
  const y = new Float32Array(n)
  if (n === 0) return y

  const random = seededRandom(7)
  const x = Float32Array.from(nodes, (node) => time.compressed(node.year))
  for (let i = 0; i < n; i++) y[i] = random()

  // Everything sharing a label is tied to that label's centre rather than to every peer.
  const labelIndex = new Map<string, number>()
  const nodeLabels: number[][] = nodes.map((node) =>
    node.labels.map((label) => {
      if (!labelIndex.has(label)) labelIndex.set(label, labelIndex.size)
      return labelIndex.get(label)!
    }),
  )
  const labelCount = labelIndex.size

  const force = new Float32Array(n)
  const sum = new Float32Array(labelCount)
  const weight = new Float32Array(labelCount)

  const iterations = n > 8000 ? 30 : 480
  const REACH = Math.min(0.06, 6 / Math.sqrt(n + 1))
  const SPACING = Math.min(0.045, 0.62 / Math.sqrt(n + 16))
  const ROOM = [0.85, 0.6, 0.34, 0.26]

  const cellHeight = SPACING * 1.7
  const cols = Math.ceil(1 / REACH) + 1
  const rows = Math.ceil(1.2 / cellHeight) + 1
  const head = new Int32Array(cols * rows)
  const next = new Int32Array(n)
  const NEIGHBOURS = [[0, 1], [1, -1], [1, 0], [1, 1]] as const
  const cellOf = (i: number): number => {
    const col = Math.min(cols - 1, Math.floor(x[i]! / REACH))
    const row = Math.max(0, Math.min(rows - 1, Math.floor((y[i]! + 0.1) / cellHeight)))
    return row * cols + col
  }

  for (let it = 0; it < iterations; it++) {
    const cool = 1 - it / iterations
    force.fill(0)

    for (const e of edges) {
      const d = y[e.target]! - y[e.source]!
      // A long jump through time may travel further than a short one.
      const slack = 0.006 + Math.abs(x[e.target]! - x[e.source]!) * 0.3
      if (Math.abs(d) < slack) continue
      const pull = (d - Math.sign(d) * slack) * 0.3
      force[e.source]! += pull
      force[e.target]! -= pull
    }

    sum.fill(0)
    weight.fill(0)
    for (let i = 0; i < n; i++) {
      for (const l of nodeLabels[i]!) {
        sum[l]! += y[i]!
        weight[l]!++
      }
    }
    for (let i = 0; i < n; i++) {
      for (const l of nodeLabels[i]!) force[i]! += ((sum[l]! / weight[l]!) - y[i]!) * 0.007
    }

    // Only nearby marks can push on each other, so a grid keeps this close to linear.
    head.fill(-1)
    for (let i = 0; i < n; i++) {
      const c = cellOf(i)
      next[i] = head[c]!
      head[c] = i
    }
    const repel = (i: number, j: number): void => {
      const dx = Math.abs(x[j]! - x[i]!)
      if (dx > REACH) return
      const closeness = 1 - dx / REACH
      const dy = y[i]! - y[j]!
      // Prominent entries carry large text and need more room than fine detail does.
      const min = SPACING * closeness * ((ROOM[nodes[i]!.level] ?? 0.5) + (ROOM[nodes[j]!.level] ?? 0.5))
      const abs = Math.abs(dy)
      if (abs >= min) return
      const dir = dy === 0 ? (random() < 0.5 ? -1 : 1) : Math.sign(dy)
      const push = (min - abs) * 0.34 * dir
      force[i]! += push
      force[j]! -= push
    }
    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < cols; col++) {
        for (let i = head[row * cols + col]!; i !== -1; i = next[i]!) {
          for (let j = next[i]!; j !== -1; j = next[j]!) repel(i, j)
          for (const [dc, dr] of NEIGHBOURS) {
            const nc = col + dc
            const nr = row + dr
            if (nc < 0 || nc >= cols || nr < 0 || nr >= rows) continue
            for (let j = head[nr * cols + nc]!; j !== -1; j = next[j]!) repel(i, j)
          }
        }
      }
    }

    for (let i = 0; i < n; i++) {
      force[i]! += (0.5 - y[i]!) * 0.004
      y[i] = Math.min(1.1, Math.max(-0.1, y[i]! + force[i]! * (0.35 + 0.65 * cool)))
    }
  }

  // Spread to fill the sheet, half measured and half by rank, so a tight cluster
  // cannot squeeze the rest of the page into a thin strip.
  const ranked = Int32Array.from({ length: n }, (_, i) => i).sort((a, b) => y[a]! - y[b]!)
  const lo = y[ranked[0]!]!
  const hi = y[ranked[n - 1]!]!
  const range = Math.max(1e-6, hi - lo)
  const out = new Float32Array(n)
  ranked.forEach((i, rank) => {
    const measured = (y[i]! - lo) / range
    const byRank = n > 1 ? rank / (n - 1) : 0.5
    out[i] = 0.02 + 0.96 * (measured * 0.72 + byRank * 0.28)
  })
  return out
}

export function buildModel(data: RawDataset, synthetic = false): Model {
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
    parents[target]!.push(source)
    children[source]!.push(target)
    edgesInto[target]!.push(edge)
    edgesOutOf[source]!.push(edge)
  }

  const time = TimeScale.fromYears(nodes.map((node) => node.year))
  const y = layoutThreads(nodes, edges, time)

  const radius = new Float32Array(n)
  const ink = new Float32Array(n * 3)
  const impact = new Int32Array(n)
  const seen = new Int32Array(n).fill(-1)
  const landmarks: number[] = []
  nodes.forEach((node, i) => {
    if (node.level === 0) landmarks.push(i)
    impact[i] = n <= FULL_IMPACT_LIMIT || node.level === 0 ? countDescendants(i, children, seen, i) : children[i]!.length
    radius[i] = (LEVEL_RADIUS[node.level] ?? 2.4) * (1 + Math.min(0.25, Math.log1p(children[i]!.length) * 0.05))
    const primary = labelById.get(node.labels[0] ?? '')
    ink.set(hexToRgb(primary?.ink ?? FALLBACK_INK), i * 3)
  })
  landmarks.sort((a, b) => nodes[a]!.year - nodes[b]!.year)

  const byPriority = Int32Array.from(nodes.keys()).sort(
    (a, b) => nodes[a]!.level - nodes[b]!.level || children[b]!.length - children[a]!.length,
  )

  const labels = data.labels
    .map((label) => ({ ...label, count: labelCounts.get(label.id) ?? 0 }))
    .filter((label) => label.count > 0)
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))

  return {
    title: data.meta?.title ?? 'Timeline',
    description: data.meta?.description ?? '',
    synthetic,
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
    landmarks,
    indexById,
  }
}

export const SHAPE_BY_KIND = new Map(KINDS.map((k) => [k.id, k.shape]))

/** Independent style flags: kind, explicit date bound, then evidence strength. */
export function nodeMarkStyle(node: RawNode): number {
  const bound = node.date_kind === 'known_by' ? 1 : node.date_kind === 'known_from' ? 2 : 0
  const strength = node.evidence_strength === 'scoped_inference' ? 1 : node.evidence_strength === 'awareness_proxy' ? 2 : 0
  return (SHAPE_BY_KIND.get(node.kind) ?? 0) + bound * 2 + strength * 8
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
