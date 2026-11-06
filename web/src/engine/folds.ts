/**
 * Folding the sheet. A fold map bends axis position `u` to display position `v` piecewise,
 * so a chosen period opens up while the rest of history pleats into narrow strips instead of
 * leaving the page. Everything keeps its true order, and links stay drawn across a fold.
 */

/** Enough for any story and for a blend of two maps. Shaders hold the same number. */
export const MAX_FOLD_POINTS = 128
const MAX_MAP_POINTS = MAX_FOLD_POINTS / 2

export interface Pleat {
  /** Axis positions the pleat folds away. */
  u0: number
  u1: number
}

export interface FoldSegment {
  u0: number
  u1: number
  /** Share of the sheet this stretch gets, relative to the others. */
  weight: number
  open: boolean
}

export class FoldMap {
  readonly us: Float64Array
  readonly vs: Float64Array
  readonly pleats: Pleat[]

  constructor(us: ArrayLike<number>, vs: ArrayLike<number>, pleats: Pleat[] = []) {
    this.us = Float64Array.from(us as ArrayLike<number>)
    this.vs = Float64Array.from(vs as ArrayLike<number>)
    this.pleats = pleats
  }

  static identity(): FoldMap {
    return new FoldMap([0, 1], [0, 1])
  }

  get isIdentity(): boolean {
    return this.us.length === 2 && this.vs[0] === 0 && this.vs[1] === 1 && this.us[0] === 0 && this.us[1] === 1
  }

  map(u: number): number {
    return interpolate(this.us, this.vs, u)
  }

  invert(v: number): number {
    return interpolate(this.vs, this.us, v)
  }
}

function interpolate(xs: Float64Array, ys: Float64Array, x: number): number {
  const last = xs.length - 1
  if (x <= xs[0]!) return ys[0]! + (x - xs[0]!)
  if (x >= xs[last]!) return ys[last]! + (x - xs[last]!)
  let lo = 0
  let hi = last
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1
    if (xs[mid]! <= x) lo = mid
    else hi = mid
  }
  const span = xs[hi]! - xs[lo]!
  return span > 0 ? ys[lo]! + ((ys[hi]! - ys[lo]!) * (x - xs[lo]!)) / span : ys[lo]!
}

/** Lays segments end to end across the sheet, each taking its share of the width. */
export function buildFold(segments: readonly FoldSegment[]): FoldMap {
  if (segments.length === 0) return FoldMap.identity()
  const total = segments.reduce((sum, s) => sum + Math.max(0, s.weight), 0)
  if (total <= 0) return FoldMap.identity()
  const us: number[] = [segments[0]!.u0]
  const vs: number[] = [0]
  const pleats: Pleat[] = []
  let v = 0
  for (const s of segments) {
    v += Math.max(0, s.weight) / total
    us.push(s.u1)
    vs.push(v)
    if (!s.open) pleats.push({ u0: s.u0, u1: s.u1 })
  }
  vs[vs.length - 1] = 1
  return new FoldMap(us, vs, pleats)
}

/** Merges windows that overlap or touch and puts them in order. */
export function normalizeWindows(windows: readonly [number, number][]): [number, number][] {
  const sorted = windows
    .map(([a, b]): [number, number] => [Math.max(0, Math.min(a, b)), Math.min(1, Math.max(a, b))])
    .filter(([a, b]) => b > a)
    .sort((a, b) => a[0] - b[0])
  const out: [number, number][] = []
  for (const w of sorted) {
    const last = out[out.length - 1]
    if (last && w[0] <= last[1]) last[1] = Math.max(last[1], w[1])
    else out.push([w[0], w[1]])
  }
  return out
}

/** How much of the sheet each pleat takes, as a share of its width. */
const PLEAT_SHARE = 0.055

/**
 * Opens windows of the axis and pleats everything else. Open windows share what is left
 * in proportion to their length, so two open periods stay on one scale.
 */
export function foldFromWindows(windows: readonly [number, number][]): FoldMap {
  const open = normalizeWindows(windows)
  if (open.length === 0) return FoldMap.identity()
  const segments: FoldSegment[] = []
  const totalOpen = open.reduce((sum, [a, b]) => sum + (b - a), 0)
  const pleat = (u0: number, u1: number) => {
    if (u1 - u0 > 1e-6) segments.push({ u0, u1, weight: PLEAT_SHARE, open: false })
  }
  let cursor = 0
  for (const [a, b] of open) {
    pleat(cursor, a)
    segments.push({ u0: a, u1: b, weight: 0, open: true })
    cursor = b
  }
  pleat(cursor, 1)
  const pleats = segments.filter((s) => !s.open).length
  const room = Math.max(0.2, 1 - pleats * PLEAT_SHARE)
  for (const s of segments) if (s.open) s.weight = (room * (s.u1 - s.u0)) / totalOpen
  if (segments[0]!.open && segments[0]!.u1 >= 1 && segments[0]!.u0 <= 0) return FoldMap.identity()
  return buildFold(segments)
}

/**
 * Unfolds one pleat by joining the windows on either side of it. Unfolding an outer pleat
 * lets the neighbouring window run to the edge of the sheet.
 */
export function unfoldPleat(windows: readonly [number, number][], pleat: Pleat): [number, number][] {
  return normalizeWindows([...windows, [pleat.u0, pleat.u1]])
}

export interface StoryFoldOptions {
  /** Axis position of a year at the scale in use. */
  u(year: number): number
  /** A gap must be wider than this share of the story still unfolded to be folded. */
  gapShare?: number
  /** And at least this many years. */
  minGapYears?: number
}

export interface StoryFold {
  map: FoldMap
  /** Runs of the story that keep one scale, in years. */
  windows: [number, number][]
}

const PLEAT_WEIGHT_IN_STORY = 0.05
const END_PLEAT_WEIGHT = 0.02

/**
 * Folds away the empty stretches of a story. Gaps that would dominate the sheet become pleats
 * and everything else stays to one scale, so distances within a window can be compared.
 */
export function foldAroundYears(years: readonly number[], options: StoryFoldOptions): StoryFold {
  const sorted = [...years].sort((a, b) => a - b)
  if (sorted.length === 0) return { map: FoldMap.identity(), windows: [] }
  const gapShare = options.gapShare ?? 0.6
  const minGap = options.minGapYears ?? 8

  const gaps = sorted.slice(1).map((year, k) => ({ at: k, size: year - sorted[k]! })).sort((a, b) => b.size - a.size)
  const span = sorted[sorted.length - 1]! - sorted[0]!
  const folded = new Set<number>()
  let remaining = span
  for (const gap of gaps) {
    if (gap.size < minGap) break
    // Stops at the first gap that the rest of the story can comfortably span.
    if (gap.size <= gapShare * remaining) break
    folded.add(gap.at)
    remaining -= gap.size
    if (folded.size >= (MAX_MAP_POINTS - 4) / 2 - 1) break
  }

  const windows: [number, number][] = []
  let start = sorted[0]!
  sorted.forEach((year, k) => {
    if (k === sorted.length - 1 || folded.has(k)) {
      windows.push([start, year])
      if (k + 1 < sorted.length) start = sorted[k + 1]!
    }
  })

  // Every window gets a little air, so a lone year still has width.
  const total = windows.reduce((sum, [a, b]) => sum + (b - a), 0)
  const pad = Math.max(1, total * 0.04)
  const padded = windows.map(([a, b]): [number, number] => [a - pad, b + pad])
  const openYears = padded.reduce((sum, [a, b]) => sum + (b - a), 0)

  const segments: FoldSegment[] = []
  const pleats = padded.length + 1
  const pleatTotal = (pleats - 2) * PLEAT_WEIGHT_IN_STORY + 2 * END_PLEAT_WEIGHT
  const room = Math.max(0.2, 1 - pleatTotal)
  let cursor = 0
  padded.forEach(([a, b], k) => {
    const ua = Math.max(cursor + 1e-6, options.u(a))
    const ub = Math.max(ua + 1e-6, options.u(b))
    if (ua > cursor) segments.push({ u0: cursor, u1: ua, weight: k === 0 ? END_PLEAT_WEIGHT : PLEAT_WEIGHT_IN_STORY, open: false })
    segments.push({ u0: ua, u1: ub, weight: (room * (b - a)) / openYears, open: true })
    cursor = ub
  })
  if (cursor < 1) segments.push({ u0: cursor, u1: 1, weight: END_PLEAT_WEIGHT, open: false })
  return { map: buildFold(segments), windows }
}

/** A map partway between two others. Both are monotonic, so the blend is too. */
export function blendFolds(a: FoldMap, b: FoldMap, t: number): FoldMap {
  if (t <= 0) return a
  if (t >= 1) return b
  const us = [...new Set([...a.us, ...b.us])].sort((x, y) => x - y)
  const vs = us.map((u) => a.map(u) * (1 - t) + b.map(u) * t)
  return new FoldMap(us, vs, b.pleats)
}
