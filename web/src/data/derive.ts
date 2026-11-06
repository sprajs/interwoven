/**
 * Everything the views work out from the links alone. None of it adds a fact: reach,
 * rows and stories are all readings of the same dated entries and typed links.
 */

interface Dated {
  year: number
}

interface LinkLike {
  source: number
  target: number
  tentative: boolean
}

export interface Reach {
  /** Latest entry built directly on each entry by a reviewed link, or its own year if none. */
  direct: Float64Array
  /** Latest descendant through reviewed links only. */
  firm: Float64Array
  /** Latest descendant through any link, including those awaiting review. */
  any: Float64Array
}

/**
 * Influence reach: from an entry to the latest entry that traces back to it. This measures
 * how long something went on being built on in the research so far. It says nothing about
 * how long the thing itself lasted.
 */
export function computeReach(nodes: readonly Dated[], edges: readonly LinkLike[]): Reach {
  const n = nodes.length
  const year = Float64Array.from(nodes, (node) => node.year)
  const direct = Float64Array.from(year)
  const firm = Float64Array.from(year)
  const any = Float64Array.from(year)
  // Latest first, so one pass nearly always settles it. A few more cover links that run
  // against date order, and the cap keeps a cycle in hand-edited data from spinning.
  const order = Int32Array.from({ length: n }, (_, i) => i).sort((a, b) => year[b]! - year[a]!)
  const out: LinkLike[][] = Array.from({ length: n }, () => [])
  for (const edge of edges) {
    out[edge.source]!.push(edge)
    if (!edge.tentative && year[edge.target]! > direct[edge.source]!) direct[edge.source] = year[edge.target]!
  }
  for (let pass = 0; pass < 8; pass++) {
    let changed = false
    for (const i of order) {
      for (const edge of out[i]!) {
        const t = edge.target
        if (any[t]! > any[i]!) {
          any[i] = any[t]!
          changed = true
        }
        if (!edge.tentative && firm[t]! > firm[i]!) {
          firm[i] = firm[t]!
          changed = true
        }
      }
    }
    if (!changed) break
  }
  return { direct, firm, any }
}

/** A connected-component id per node, numbered from 0 in order of first appearance. */
export function connectedComponents(n: number, edges: readonly Pick<LinkLike, 'source' | 'target'>[]): Int32Array {
  const parent = Int32Array.from({ length: n }, (_, i) => i)
  const find = (x: number): number => {
    let root = x
    while (parent[root] !== root) root = parent[root]!
    while (parent[x] !== root) {
      const next = parent[x]!
      parent[x] = root
      x = next
    }
    return root
  }
  for (const e of edges) parent[find(e.source)] = find(e.target)
  const ids = new Map<number, number>()
  const out = new Int32Array(n)
  for (let i = 0; i < n; i++) {
    const root = find(i)
    if (!ids.has(root)) ids.set(root, ids.size)
    out[i] = ids.get(root)!
  }
  return out
}

export type RowOrder = 'thread' | 'origin' | 'reach'

/**
 * Gives every entry its own row, 0 to 1 from the top. `thread` keeps connected work together
 * with each child near its parent, so links are short. `origin` makes Priestley's staircase.
 * `reach` puts the longest influence first.
 */
export function rowOrder(nodes: readonly Dated[], children: readonly (readonly number[])[], parents: readonly (readonly number[])[], reach: Reach, order: RowOrder): Int32Array {
  const n = nodes.length
  const byYear = Int32Array.from({ length: n }, (_, i) => i).sort((a, b) => nodes[a]!.year - nodes[b]!.year || a - b)
  if (order === 'origin') return byYear
  if (order === 'reach') {
    const span = (i: number) => reach.any[i]! - nodes[i]!.year
    return Int32Array.from(byYear).sort((a, b) => span(b) - span(a) || nodes[a]!.year - nodes[b]!.year || a - b)
  }
  const rows = new Int32Array(n)
  const placed = new Uint8Array(n)
  let row = 0
  // Children go in date order, and an explicit stack keeps long chains from overflowing.
  const place = (start: number) => {
    const stack = [start]
    while (stack.length) {
      const i = stack.pop()!
      if (placed[i]) continue
      placed[i] = 1
      rows[row++] = i
      const next = [...children[i]!, ...parents[i]!].filter((j) => !placed[j])
      next.sort((a, b) => nodes[b]!.year - nodes[a]!.year || b - a)
      for (const j of next) stack.push(j)
    }
  }
  for (const i of byYear) if (!placed[i]) place(i)
  return rows
}

/** Row positions per node. Rows keep a margin so the first and last are not on the rule. */
export function rowPositions(rows: Int32Array): Float32Array {
  const n = rows.length
  const y = new Float32Array(n)
  rows.forEach((node, row) => {
    y[node] = n > 1 ? 0.012 + (0.976 * row) / (n - 1) : 0.5
  })
  return y
}

/**
 * Whether a staircase of rows leaves the top right and bottom left of the sheet empty, so that
 * notes can sit there. Dense or reordered rows fill them, and the notes then need their own sheet.
 */
export function cornersFree(rows: Int32Array, nodes: readonly Dated[], reach: Reach, u: (year: number) => number, width = 0.3): boolean {
  const n = rows.length
  if (n === 0) return true
  let intruders = 0
  rows.forEach((node, row) => {
    const position = row / Math.max(1, n - 1)
    if (position < 0.48 && u(reach.any[node]!) > 1 - width) intruders++
    if (position > 0.52 && u(nodes[node]!.year) < width) intruders++
  })
  return intruders <= Math.max(1, n * 0.02)
}

export interface Crossing {
  /** The stitch's date. */
  year: number
  /** The row it crosses. */
  y: number
  /** The crossed row's node. */
  node: number
  over: boolean
}

/**
 * Where a link's vertical stitch passes over the rule of an entry it has nothing to do with.
 * Breaking one of the two lines at each crossing is a drafting convention: it shows that
 * crossing lines are not connected. Which line goes over carries no meaning.
 */
export function findCrossings(
  rows: Int32Array,
  y: Float32Array,
  nodes: readonly Dated[],
  reach: Reach,
  edges: readonly Pick<LinkLike, 'source' | 'target'>[],
  budget = 40000,
): Crossing[] {
  const rowOf = new Int32Array(rows.length)
  rows.forEach((node, row) => {
    rowOf[node] = row
  })
  const out: Crossing[] = []
  edges.forEach((e, column) => {
    const a = Math.min(rowOf[e.source]!, rowOf[e.target]!)
    const b = Math.max(rowOf[e.source]!, rowOf[e.target]!)
    const year = nodes[e.target]!.year
    for (let r = a + 1; r < b && out.length < budget; r++) {
      const node = rows[r]!
      if (nodes[node]!.year < year && reach.any[node]! > year) {
        out.push({ year, y: y[node]!, node, over: (r + column) % 2 === 0 })
      }
    }
  })
  return out
}

// ---------------------------------------------------------------- stories

export interface StoryInput {
  nodes: readonly Dated[]
  parents: readonly (readonly number[])[]
  children: readonly (readonly number[])[]
}

export interface Story {
  /** The entry it was followed from, if any. */
  focus: number | null
  /** Every entry in it, earliest first. This is also the reading order. */
  members: number[]
  /** Row position per member, parallel to `members`. */
  y: Float32Array
  /** The longest chain of links through it, earliest first. */
  spine: number[]
  /** Whether nearer entries were kept and the rest of a very long story dropped. */
  truncated: boolean
}

/** Largest story laid out. Beyond this the nearest entries are kept, and it says so. */
export const STORY_LIMIT = 400

function nearest(starts: number[], adjacency: (i: number) => readonly number[], limit: number): { seen: Set<number>; truncated: boolean } {
  const seen = new Set<number>(starts)
  let frontier = starts
  while (frontier.length && seen.size < limit) {
    const next: number[] = []
    for (const i of frontier) {
      for (const j of adjacency(i)) {
        if (seen.has(j)) continue
        seen.add(j)
        next.push(j)
        if (seen.size >= limit) return { seen, truncated: true }
      }
    }
    frontier = next
  }
  return { seen, truncated: false }
}

/** What led to an entry and what followed from it. */
export function lineageOf(focus: number, input: StoryInput, limit = STORY_LIMIT): { members: number[]; truncated: boolean } {
  const half = Math.ceil(limit / 2)
  const up = nearest([focus], (i) => input.parents[i]!, half)
  const down = nearest([focus], (i) => input.children[i]!, half)
  return { members: [...new Set([...up.seen, ...down.seen])], truncated: up.truncated || down.truncated }
}

/** All connected work around an entry, in any direction. */
export function threadOf(start: number, input: StoryInput, limit = STORY_LIMIT): { members: number[]; truncated: boolean } {
  const { seen, truncated } = nearest([start], (i) => [...input.parents[i]!, ...input.children[i]!], limit)
  return { members: [...seen], truncated }
}

/** The longest chain through these members, passing through `focus` if one is given. */
export function longestChain(members: readonly number[], input: StoryInput, focus: number | null): number[] {
  const sorted = [...members].sort((a, b) => input.nodes[a]!.year - input.nodes[b]!.year || a - b)
  const inSet = new Set(sorted)
  const rank = new Map(sorted.map((i, k) => [i, k]))
  const before = new Map<number, number>()
  const up = new Map<number, number>()
  for (const i of sorted) {
    let best = 1
    let from = -1
    for (const p of input.parents[i]!) {
      // A link against date order cannot extend a chain that reads forward in time.
      if (!inSet.has(p) || rank.get(p)! >= rank.get(i)!) continue
      const length = up.get(p)! + 1
      if (length > best) {
        best = length
        from = p
      }
    }
    up.set(i, best)
    before.set(i, from)
  }
  const after = new Map<number, number>()
  const down = new Map<number, number>()
  for (let k = sorted.length - 1; k >= 0; k--) {
    const i = sorted[k]!
    let best = 1
    let to = -1
    for (const c of input.children[i]!) {
      if (!inSet.has(c) || rank.get(c)! <= rank.get(i)!) continue
      const length = down.get(c)! + 1
      if (length > best) {
        best = length
        to = c
      }
    }
    down.set(i, best)
    after.set(i, to)
  }
  let pivot = focus !== null && inSet.has(focus) ? focus : -1
  if (pivot === -1) {
    let best = -1
    for (const i of sorted) {
      const length = up.get(i)! + down.get(i)!
      if (length > best) {
        best = length
        pivot = i
      }
    }
  }
  if (pivot === -1) return []
  const chain = [pivot]
  for (let i = before.get(pivot)!; i !== -1 && i !== undefined; i = before.get(i)!) chain.unshift(i)
  for (let i = after.get(pivot)!; i !== -1 && i !== undefined; i = after.get(i)!) chain.push(i)
  return chain
}

/** Lays a story out one entry per row in date order, so every title has room. */
export function layoutStory(members: readonly number[], input: StoryInput, focus: number | null, truncated = false): Story {
  const sorted = [...members].sort((a, b) => input.nodes[a]!.year - input.nodes[b]!.year || a - b)
  const n = sorted.length
  const y = new Float32Array(n)
  // A short story sits in the middle of the sheet instead of stretching to fill it.
  const step = n > 1 ? Math.min(0.92 / (n - 1), 0.1) : 0
  const top = 0.5 - (step * (n - 1)) / 2
  for (let k = 0; k < n; k++) y[k] = top + step * k
  return { focus, members: sorted, y, spine: longestChain(sorted, input, focus), truncated }
}

export interface StoryIndexEntry {
  /** Earliest entry, used to open it. */
  first: number
  last: number
  size: number
  members: number[]
}

/** Connected threads worth reading on their own, largest first. */
export function storyIndex(nodes: readonly Dated[], edges: readonly Pick<LinkLike, 'source' | 'target'>[], minimum = 3): StoryIndexEntry[] {
  const ids = connectedComponents(nodes.length, edges)
  const groups = new Map<number, number[]>()
  ids.forEach((id, i) => {
    const group = groups.get(id)
    if (group) group.push(i)
    else groups.set(id, [i])
  })
  const out: StoryIndexEntry[] = []
  for (const members of groups.values()) {
    if (members.length < minimum) continue
    members.sort((a, b) => nodes[a]!.year - nodes[b]!.year || a - b)
    out.push({ first: members[0]!, last: members[members.length - 1]!, size: members.length, members })
  }
  return out.sort((a, b) => b.size - a.size || nodes[a.first]!.year - nodes[b.first]!.year)
}

// ---------------------------------------------------------------- reading the search box

export type YearQuery = { kind: 'year'; year: number } | { kind: 'period'; start: number; end: number }

/**
 * Understands a typed year or period: "1850", "1600-1700", "1600 to 1700", "1600s",
 * "500 BCE", "3000 BC to 1000 BC". Anything else is not a date and returns null.
 */
export function parseYearQuery(text: string): YearQuery | null {
  const q = text.trim().toLowerCase().replace(/[–—]/g, '-')
  const year = (value: string, era: string | undefined): number => {
    const n = Number(value.replace(/[ ,]/g, ''))
    return era && era.startsWith('b') ? -n : n
  }
  const era = '(bce|bc|ce|ad)?'
  const number = '(\\d[\\d ,]*?)'
  const range = new RegExp(`^${number}\\s*${era}\\s*(?:-|to|until)\\s*${number}\\s*${era}$`).exec(q)
  if (range) {
    // "3000-1000 BC" means both are BC.
    const a = year(range[1]!, range[2] ?? range[4])
    const b = year(range[3]!, range[4])
    if (a === b) return null
    return { kind: 'period', start: Math.min(a, b), end: Math.max(a, b) }
  }
  const decade = /^(\d{2,4})s$/.exec(q)
  if (decade) {
    const start = Number(decade[1])
    const size = start % 100 === 0 ? 100 : start % 10 === 0 ? 10 : 1
    return { kind: 'period', start, end: start + size }
  }
  const single = new RegExp(`^${number}\\s*${era}$`).exec(q)
  if (single) {
    const value = year(single[1]!, single[2])
    // A bare one or two digit number is more likely to be part of a name than a year.
    if (!single[2] && Math.abs(value) < 100) return null
    return { kind: 'year', year: value }
  }
  return null
}
