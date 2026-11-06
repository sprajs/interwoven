import { TimeScale } from '../engine/time.ts'
import { NODE_TYPES, type RawDataset, type RawEpoch, type RawNode } from './types.ts'

export interface Lane {
  index: number
  id: string
  label: string
  color: string
  rgb: [number, number, number]
  y0: number
  y1: number
  center: number
  count: number
}

export interface Edge {
  source: number
  target: number
  soft: boolean
}

export interface Model {
  title: string
  synthetic: boolean
  nodes: RawNode[]
  n: number
  edges: Edge[]
  lanes: Lane[]
  epochs: RawEpoch[]
  labels: { id: string; count: number }[]
  time: TimeScale
  parents: number[][]
  children: number[][]
  /** Layout position per node, 0..1 top to bottom. */
  y: Float32Array
  /** Node radius in CSS pixels. */
  radius: Float32Array
  domainIndex: Uint8Array
  /** Number of transitive descendants. Filled for every node on small datasets, step changes otherwise. */
  impact: Int32Array
  /** Node indices with the most important first. Used to place labels greedily. */
  byPriority: Int32Array
  stepChanges: number[]
  indexById: Map<string, number>
}

const LEVEL_RADIUS = [10, 7, 5, 3.8]
const LANE_GAP = 0.012
const FULL_IMPACT_LIMIT = 4000

function hexToRgb(hex: string): [number, number, number] {
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

/**
 * Assigns each node a vertical position within its domain's lane. Important nodes
 * claim the centre rows first, so deeper nodes spread outward as the view zooms in
 * and the lane grows taller. Each node is pulled toward the rows of its neighbours
 * in the same lane, which shortens links.
 */
export function layoutLanes(model: Pick<Model, 'nodes' | 'lanes' | 'time' | 'parents' | 'domainIndex'>): Float32Array {
  const { nodes, lanes, time, parents, domainIndex } = model
  const y = new Float32Array(nodes.length)
  const row = new Int32Array(nodes.length)
  const CELLS = 1536
  const CLAIM_WIDTH = [0.05, 0.03, 0.018, 0.012]

  for (const lane of lanes) {
    const members: number[] = []
    for (let i = 0; i < nodes.length; i++) if (domainIndex[i] === lane.index) members.push(i)
    members.sort((a, b) => nodes[a]!.level - nodes[b]!.level || nodes[a]!.year - nodes[b]!.year)

    const rowCount = Math.max(5, Math.min(61, Math.ceil(Math.sqrt(members.length) * 2.4)) | 1)
    const half = (rowCount - 1) / 2
    const occupied: Uint8Array[] = Array.from({ length: rowCount }, () => new Uint8Array(CELLS))

    for (const i of members) {
      const node = nodes[i]!
      const u = time.compressed(node.year)
      const w = CLAIM_WIDTH[node.level] ?? 0.012
      const c0 = Math.max(0, Math.floor((u - w) * CELLS))
      const c1 = Math.min(CELLS - 1, Math.ceil((u + w) * CELLS))

      let sum = 0
      let weight = 0
      for (const p of parents[i]!) {
        if (domainIndex[p] === lane.index) {
          sum += row[p]!
          weight++
        }
      }
      const preferred = weight ? Math.round(sum / weight) : 0
      // Deep-level nodes stay off the central rows so step changes keep clear space.
      const minOffset = node.level >= 3 ? 1 : 0

      let chosen = NaN
      let leastLoad = Infinity
      let leastRow = preferred
      search: for (let d = 0; d <= rowCount; d++) {
        for (const s of d === 0 ? [0] : [1, -1]) {
          const candidate = preferred + s * d
          if (Math.abs(candidate) > half || Math.abs(candidate) < minOffset) continue
          const cells = occupied[candidate + half]!
          let load = 0
          for (let c = c0; c <= c1; c++) load += cells[c]!
          if (load === 0) {
            chosen = candidate
            break search
          }
          if (load < leastLoad) {
            leastLoad = load
            leastRow = candidate
          }
        }
      }
      const r = Number.isNaN(chosen) ? leastRow : chosen
      row[i] = r
      const cells = occupied[r + half]!
      for (let c = c0; c <= c1; c++) cells[c] = 1
    }

    const laneHeight = lane.y1 - lane.y0
    const pitch = (laneHeight * 0.92) / Math.max(1, rowCount - 1)
    for (const i of members) y[i] = lane.center + row[i]! * pitch
  }
  return y
}

export function buildModel(data: RawDataset, synthetic = false): Model {
  const nodes = data.nodes
  const n = nodes.length
  const indexById = new Map(nodes.map((node, i) => [node.id, i]))
  const domainOrder = new Map(data.domains.map((d, i) => [d.id, i]))
  const domainIndex = new Uint8Array(n)
  const parents: number[][] = Array.from({ length: n }, () => [])
  const children: number[][] = Array.from({ length: n }, () => [])
  const edges: Edge[] = []
  const labelCounts = new Map<string, number>()
  const domainCounts = new Array<number>(data.domains.length).fill(0)

  nodes.forEach((node, i) => {
    const d = domainOrder.get(node.domain) ?? 0
    domainIndex[i] = d
    domainCounts[d]!++
    for (const label of node.labels) labelCounts.set(label, (labelCounts.get(label) ?? 0) + 1)
    const add = (ids: string[] | undefined, soft: boolean) => {
      for (const id of ids ?? []) {
        const p = indexById.get(id)
        if (p === undefined) continue
        edges.push({ source: p, target: i, soft })
        parents[i]!.push(p)
        children[p]!.push(i)
      }
    }
    add(node.builds_on, false)
    add(node.informed_by, true)
  })

  // Lane height follows the square root of membership: busy domains get more room
  // without squeezing small ones out of sight.
  const weights = domainCounts.map((c) => Math.sqrt(c + 4))
  const total = weights.reduce((a, b) => a + b, 0)
  const usable = 1 - LANE_GAP * (data.domains.length - 1)
  let cursor = 0
  const lanes: Lane[] = data.domains.map((d, index) => {
    const h = (weights[index]! / total) * usable
    const lane: Lane = {
      index,
      id: d.id,
      label: d.label,
      color: d.color,
      rgb: hexToRgb(d.color),
      y0: cursor,
      y1: cursor + h,
      center: cursor + h / 2,
      count: domainCounts[index]!,
    }
    cursor += h + LANE_GAP
    return lane
  })

  const time = TimeScale.fromYears(nodes.map((node) => node.year))
  const y = layoutLanes({ nodes, lanes, time, parents, domainIndex })

  const radius = new Float32Array(n)
  const impact = new Int32Array(n)
  const seen = new Int32Array(n).fill(-1)
  const stepChanges: number[] = []
  nodes.forEach((node, i) => {
    if (node.step_change || node.level === 0) stepChanges.push(i)
    if (n <= FULL_IMPACT_LIMIT || node.level === 0) impact[i] = countDescendants(i, children, seen, i)
    else impact[i] = children[i]!.length
    const base = LEVEL_RADIUS[node.level] ?? 3.9
    radius[i] = base * (1 + Math.min(0.35, Math.log1p(children[i]!.length) * 0.06))
  })
  stepChanges.sort((a, b) => nodes[a]!.year - nodes[b]!.year)

  const byPriority = Int32Array.from(nodes.keys()).sort(
    (a, b) => nodes[a]!.level - nodes[b]!.level || children[b]!.length - children[a]!.length,
  )

  const labels = [...labelCounts].map(([id, count]) => ({ id, count })).sort((a, b) => b.count - a.count || a.id.localeCompare(b.id))

  return {
    title: data.meta?.title ?? 'Timeline',
    synthetic,
    nodes,
    n,
    edges,
    lanes,
    epochs: data.epochs ?? [],
    labels,
    time,
    parents,
    children,
    y,
    radius,
    domainIndex,
    impact,
    byPriority,
    stepChanges,
    indexById,
  }
}

export const SHAPE_BY_TYPE = new Map(NODE_TYPES.map((t) => [t.id, t.shape]))

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
