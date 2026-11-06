/**
 * Maps years to a normalised axis position `u` in [0, 1].
 *
 * Two scales are blended by `warp`: linear time, and a compressed scale. The compressed
 * scale starts from log(years before now), which gives recent centuries room without
 * losing the deep past, and then widens whatever periods hold the most entries, so links
 * within a busy period can run across the page instead of stacking up. Vertex shaders read
 * the same table, which lets the two scales morph on the GPU.
 */
export const TAU = 16
export const LUT_SIZE = 1024
/** How strongly entry density shapes the axis. 0 is pure log time. */
const DENSITY_SHARE = 0.62
const SMOOTHING_BINS = 22

export class TimeScale {
  readonly min: number
  readonly now: number
  readonly tau = TAU
  readonly logSpan: number
  /** Compressed u for evenly spaced steps of log time, from now (index 0) to `min`. */
  readonly lut: Float32Array

  constructor(min: number, now: number, years: Iterable<number> = []) {
    this.min = min
    this.now = now
    this.logSpan = Math.log(1 + (now - min) / TAU)
    this.lut = buildLut(this, years)
  }

  static fromYears(years: number[]): TimeScale {
    let lo = Infinity
    let hi = -Infinity
    for (const y of years) {
      if (y < lo) lo = y
      if (y > hi) hi = y
    }
    if (!Number.isFinite(lo)) {
      lo = 1900
      hi = 2030
    }
    const pad = Math.max(10, (hi - lo) * 0.02)
    return new TimeScale(lo - pad, Math.max(hi + 4, 2030), years)
  }

  /** Log time before now, from 0 at `now` to 1 at `min`. */
  logPosition(year: number): number {
    return Math.min(1, Math.max(0, Math.log(1 + (this.now - year) / this.tau) / this.logSpan))
  }

  linear(year: number): number {
    return (year - this.min) / (this.now - this.min)
  }

  compressed(year: number): number {
    const f = this.logPosition(year) * (LUT_SIZE - 1)
    const i = Math.min(LUT_SIZE - 2, Math.floor(f))
    const a = this.lut[i]!
    return a + (this.lut[i + 1]! - a) * (f - i)
  }

  u(year: number, warp: number): number {
    return this.linear(year) * (1 - warp) + this.compressed(year) * warp
  }

  /** Inverse of `u`. The blend has no closed form, so it bisects; u(year) is monotonic. */
  year(u: number, warp: number): number {
    if (warp <= 0) return this.min + u * (this.now - this.min)
    let lo = this.min
    let hi = this.now
    for (let i = 0; i < 44; i++) {
      const mid = (lo + hi) / 2
      if (this.u(mid, warp) < u) lo = mid
      else hi = mid
    }
    return (lo + hi) / 2
  }
}

function buildLut(scale: TimeScale, years: Iterable<number>): Float32Array {
  const counts = new Float32Array(LUT_SIZE)
  let total = 0
  for (const year of years) {
    const f = scale.logPosition(year) * (LUT_SIZE - 1)
    counts[Math.round(f)]!++
    total++
  }

  const smooth = new Float32Array(LUT_SIZE)
  if (total > 0) {
    const kernel: number[] = []
    for (let d = -SMOOTHING_BINS * 3; d <= SMOOTHING_BINS * 3; d++) kernel.push(Math.exp(-(d * d) / (2 * SMOOTHING_BINS * SMOOTHING_BINS)))
    for (let i = 0; i < LUT_SIZE; i++) {
      if (counts[i] === 0) continue
      kernel.forEach((w, k) => {
        const j = i + k - SMOOTHING_BINS * 3
        if (j >= 0 && j < LUT_SIZE) smooth[j]! += counts[i]! * w
      })
    }
  }
  const smoothSum = smooth.reduce((a, b) => a + b, 0)

  // Every step keeps a share of width, so the axis stays strictly monotonic.
  const lut = new Float32Array(LUT_SIZE)
  let used = 0
  for (let i = 0; i < LUT_SIZE; i++) {
    lut[i] = used
    const density = smoothSum > 0 ? smooth[i]! / smoothSum : 1 / LUT_SIZE
    used += (1 - DENSITY_SHARE) / LUT_SIZE + DENSITY_SHARE * density
  }
  // Scaled so the axis runs from exactly 1 at the present to exactly 0 at the start.
  const end = lut[LUT_SIZE - 1]!
  for (let i = 0; i < LUT_SIZE; i++) lut[i] = 1 - lut[i]! / end
  return lut
}

export function formatYear(year: number): string {
  const y = Math.round(year)
  if (y === 0) return '1 CE'
  if (y < 0) return `${Math.abs(y).toLocaleString('en-US').replace(/,/g, ' ')} BCE`
  return String(y)
}

/** Each step divides the one above it evenly, so neighbouring ticks share a step. */
const TICK_STEPS = [5000, 1000, 500, 100, 50, 10, 5, 1]

/**
 * Picks round-numbered years for the ruler. The axis is warped, so one even step cannot suit all
 * of it. Each stretch divides at the coarsest step that has room, working back from its recent
 * end where there is most room, then each part divides again. That keeps the ruler regular where
 * it can be: 1800, 1850, 1900, and never 1800, 1820, 1850.
 */
export function pickTicks(
  yearToX: (year: number) => number,
  yearStart: number,
  yearEnd: number,
  minGap: number,
  /** Positions that cannot hold a tick. */
  reject?: (x: number) => boolean,
): { year: number; x: number }[] {
  const top = TICK_STEPS[0]!
  // Years past the end of the axis have no position, so they never limit the division.
  const place = (year: number) => (year > yearEnd ? Infinity : yearToX(year))
  const years: number[] = []
  const divide = (a: number, b: number): void => {
    const start = place(a)
    for (const step of TICK_STEPS) {
      if (step >= b - a || (b - a) % step !== 0) continue
      const kept: number[] = []
      let right = place(b)
      for (let y = b - step; y > a; y -= step) {
        const x = place(y)
        if (right - x >= minGap && x - start >= minGap) {
          kept.push(y)
          right = x
        } else if (kept.length > 0) {
          // Older years have less room. Stopping here keeps the run of ticks regular.
          break
        }
      }
      if (kept.length === 0) {
        // Only a wide stretch is worth a finer step. It may hold a period opened by a fold.
        if (place(b) - start < 3 * minGap) return
        continue
      }
      let upper = b
      for (const y of kept) {
        years.push(y)
        divide(y, upper)
        upper = y
      }
      divide(a, upper)
      return
    }
  }
  const first = Math.floor(yearStart / top) * top
  const last = Math.ceil(yearEnd / top) * top
  for (let a = first; a < last; a += top) {
    years.push(a)
    divide(a, a + top)
  }
  years.push(last)
  return years
    .filter((year) => year >= yearStart && year <= yearEnd)
    .sort((p, q) => p - q)
    .map((year) => ({ year, x: yearToX(year) }))
    .filter((tick) => !reject?.(tick.x))
}
