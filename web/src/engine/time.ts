/**
 * Maps years to a normalised axis position `u` in [0, 1].
 *
 * Two scales are blended by `warp`: linear time, and a compressed scale where
 * distance is proportional to log(years before now). The compressed scale gives
 * recent centuries room without losing the deep past, and the vertex shaders
 * compute the same function so the two scales can morph on the GPU.
 */
export const TAU = 30

export class TimeScale {
  readonly min: number
  readonly now: number
  readonly tau = TAU
  readonly logSpan: number

  constructor(min: number, now: number) {
    this.min = min
    this.now = now
    this.logSpan = Math.log(1 + (now - min) / TAU)
  }

  static fromYears(years: Iterable<number>): TimeScale {
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
    return new TimeScale(lo - pad, Math.max(hi + 4, 2030))
  }

  linear(year: number): number {
    return (year - this.min) / (this.now - this.min)
  }

  compressed(year: number): number {
    return 1 - Math.log(1 + (this.now - year) / this.tau) / this.logSpan
  }

  u(year: number, warp: number): number {
    return this.linear(year) * (1 - warp) + this.compressed(year) * warp
  }

  /** Inverse of `u`. The blend has no closed form, so it bisects; u(year) is monotonic. */
  year(u: number, warp: number): number {
    if (warp <= 0) return this.min + u * (this.now - this.min)
    if (warp >= 1) return this.now - this.tau * (Math.exp((1 - u) * this.logSpan) - 1)
    let lo = this.min
    let hi = this.now
    for (let i = 0; i < 48; i++) {
      const mid = (lo + hi) / 2
      if (this.u(mid, warp) < u) lo = mid
      else hi = mid
    }
    return (lo + hi) / 2
  }
}

export function formatYear(year: number): string {
  const y = Math.round(year)
  if (y === 0) return '1 CE'
  if (y < 0) return `${Math.abs(y).toLocaleString('en-US').replace(/,/g, ' ')} BCE`
  return String(y)
}

const TICK_STEPS = [10000, 5000, 2000, 1000, 500, 200, 100, 50, 20, 10, 5, 2, 1]

/**
 * Picks round-numbered ticks with even on-screen spacing, even on a warped axis:
 * coarse steps are placed first and finer ones only fill the gaps they leave.
 */
export function pickTicks(
  yearToX: (year: number) => number,
  yearStart: number,
  yearEnd: number,
  width: number,
  minGap: number,
): { year: number; x: number; step: number }[] {
  const cell = minGap
  const cols = Math.ceil(width / cell) + 3
  const taken = new Uint8Array(cols)
  const ticks: { year: number; x: number; step: number }[] = []
  for (const step of TICK_STEPS) {
    const first = Math.ceil(yearStart / step) * step
    if ((yearEnd - first) / step > 4000) continue
    for (let y = first; y <= yearEnd; y += step) {
      const x = yearToX(y)
      if (x < 0 || x > width) continue
      const c = Math.floor(x / cell) + 1
      if (taken[c - 1] || taken[c] || taken[c + 1]) continue
      taken[c] = 1
      ticks.push({ year: y, x, step })
    }
  }
  return ticks.sort((a, b) => a.x - b.x)
}
