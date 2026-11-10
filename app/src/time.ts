/**
 * Time, and the ways of spreading it across a page.
 *
 * A moment is a number of years, `t`, where 1 CE is 1 and 1 BCE is 0. A scale turns a moment into
 * an abstract position `u`; an axis turns a window of time into pixels. Every scale is monotone,
 * so anything written against `Axis` works with all of them.
 */

/** The right-hand end of every axis. */
export const PRESENT = 2026

export type ScaleId = 'calendar' | 'log' | 'people'

export interface TimeScale {
  id: ScaleId
  name: string
  /** One line saying what equal widths mean on this scale. */
  hint: string
  u(t: number): number
  t(u: number): number
}

export const calendar: TimeScale = {
  id: 'calendar',
  name: 'Calendar',
  hint: 'Every year is the same width',
  u: (t) => t,
  t: (u) => u,
}

/** Years before the present, on a logarithm. The offset keeps the last few decades from stretching without limit. */
const LOG_OFFSET = 40
export const log: TimeScale = {
  id: 'log',
  name: 'Logarithmic',
  hint: 'Each step back in time covers ten times as many years',
  u: (t) => -Math.log10(PRESENT + LOG_OFFSET - t),
  t: (u) => PRESENT + LOG_OFFSET - 10 ** -u,
}

/** Person-years lived: every stretch of the axis holds the same amount of human life. */
export function peopleScale(personYears: [number, number][]): TimeScale {
  const years = personYears.map((p) => p[0])
  const totals = personYears.map((p) => p[1])
  const last = years.length - 1
  // Past the last estimate, carry on at the final rate.
  const finalRate = (totals[last]! - totals[last - 1]!) / (years[last]! - years[last - 1]!)
  const interpolate = (xs: number[], ys: number[], x: number, slopeAfter: number, slopeBefore: number) => {
    if (x <= xs[0]!) return ys[0]! + (x - xs[0]!) * slopeBefore
    if (x >= xs[last]!) return ys[last]! + (x - xs[last]!) * slopeAfter
    let lo = 0
    let hi = last
    while (hi - lo > 1) {
      const mid = (lo + hi) >> 1
      if (xs[mid]! <= x) lo = mid
      else hi = mid
    }
    return ys[lo]! + ((x - xs[lo]!) / (xs[hi]! - xs[lo]!)) * (ys[hi]! - ys[lo]!)
  }
  const firstRate = (totals[1]! - totals[0]!) / (years[1]! - years[0]!)
  return {
    id: 'people',
    name: 'By people alive',
    hint: 'Every stretch holds the same number of human lifetimes',
    u: (t) => interpolate(years, totals, t, finalRate, firstRate),
    t: (u) => interpolate(totals, years, u, 1 / finalRate, 1 / firstRate),
  }
}

export interface Axis {
  scale: TimeScale
  t0: number
  t1: number
  x0: number
  x1: number
  x(t: number): number
  t(x: number): number
}

export function makeAxis(scale: TimeScale, t0: number, t1: number, x0: number, x1: number): Axis {
  const u0 = scale.u(t0)
  const span = scale.u(t1) - u0 || 1
  return {
    scale,
    t0,
    t1,
    x0,
    x1,
    x: (t) => x0 + ((scale.u(t) - u0) / span) * (x1 - x0),
    t: (x) => scale.t(u0 + ((x - x0) / (x1 - x0)) * span),
  }
}

/** Zoom a window of time about a moment, keeping that moment where it is on the page. */
export function zoomWindow(scale: TimeScale, [t0, t1]: [number, number], about: number, factor: number, limits: [number, number]): [number, number] {
  const u0 = scale.u(t0)
  const u1 = scale.u(t1)
  const ua = scale.u(about)
  const lo = scale.u(limits[0])
  const hi = scale.u(limits[1])
  let n0 = ua - (ua - u0) * factor
  let n1 = ua + (u1 - ua) * factor
  const least = (hi - lo) / 4000
  if (n1 - n0 < least) return [t0, t1]
  n0 = Math.max(lo, n0)
  n1 = Math.min(hi, n1)
  return [scale.t(n0), scale.t(n1)]
}

/** Slide a window of time by a share of its own width, stopping at the limits. */
export function panWindow(scale: TimeScale, [t0, t1]: [number, number], share: number, limits: [number, number]): [number, number] {
  const u0 = scale.u(t0)
  const u1 = scale.u(t1)
  let shift = (u1 - u0) * share
  shift = Math.max(scale.u(limits[0]) - u0, Math.min(scale.u(limits[1]) - u1, shift))
  return [scale.t(u0 + shift), scale.t(u1 + shift)]
}

/**
 * The same scale with everything before `from` squeezed into a fixed share of its length. A strip
 * that must reach back millions of years for a handful of records would otherwise spend much of
 * its width on them.
 */
export function squeezePast(scale: TimeScale, from: number, [start, end]: [number, number], share: number): TimeScale {
  if (start >= from) return scale
  const uFrom = scale.u(from)
  const head = ((scale.u(end) - uFrom) * share) / (1 - share)
  const near = Math.log10(end - from)
  const far = Math.log10(end - start)
  return {
    ...scale,
    u: (t) => (t >= from ? scale.u(t) : uFrom - head * ((Math.log10(end - t) - near) / (far - near))),
    t: (u) => (u >= uFrom ? scale.t(u) : end - 10 ** (near + ((uFrom - u) / head) * (far - near))),
  }
}

/** The calendar year a moment falls in, with no year 0. */
export function yearOf(t: number): number {
  const whole = Math.floor(t)
  return whole <= 0 ? whole - 1 : whole
}

const group = (n: number) => (n < 10000 ? String(n) : groupAll(n))
const groupAll = (n: number) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')

/** A year as a reader would write it: 1850, 500 CE, 3000 BCE, 190 000 BCE. */
export function formatYear(t: number, round = 1): string {
  let year = yearOf(t)
  if (round > 1) year = Math.round(year / round) * round || 1
  if (year < 0) return `${group(-year)} BCE`
  return year < 1000 ? `${year} CE` : String(year)
}

/** A span of years in words: "40 years", "2 centuries", "12 000 years". */
export function formatSpan(years: number): string {
  if (years < 1.5) return '1 year'
  if (years < 100) return `${Math.round(years)} years`
  if (years < 1000) return `${Math.round(years / 10) * 10} years`
  return `${group(Math.round(years / 100) * 100)} years`
}

export interface Tick {
  t: number
  x: number
  label: string
  /** 0 for the coarsest ticks placed, rising as they get finer. */
  level: number
}

const STEPS = [100000, 50000, 25000, 10000, 5000, 2500, 1000, 500, 250, 100, 50, 25, 10, 5, 1]

/** The moment a calendar year stands for. There is no year 0: the tick between the eras sits at 1 CE. */
const momentOf = (year: number) => (year < 0 ? year + 1 : year === 0 ? 1 : year)

/**
 * Round years across an axis, as many as fit. Coarse years are placed first and finer ones fill
 * the room that is left, so a stretched part of a curved scale gets finer ticks than a squeezed
 * one. Every tick is a round value of its own step, no long stretch is left without a date, and
 * the start of the axis is always labelled.
 */
export function ticks(axis: Axis, minGap = 72): Tick[] {
  const out: Tick[] = []
  const free = (x: number) => out.every((other) => Math.abs(other.x - x) >= minGap)
  const y0 = yearOf(axis.t0)
  const y1 = yearOf(axis.t1)
  const inside = (x: number) => x >= axis.x0 - 0.5 && x <= axis.x1 + 0.5
  let level = 0
  let coarser = 0
  for (const step of STEPS) {
    if ((y1 - y0) / step > 3000) break
    // Each finer step must divide the one before it, so steps nest: 100, 50, 25, never 100, 40.
    if (coarser && coarser % step !== 0) continue
    let placed = false
    for (let year = Math.ceil(y0 / step) * step; year <= y1; year += step) {
      const t = momentOf(year)
      const x = axis.x(t)
      if (!inside(x) || !free(x)) continue
      // A tick needs room for a neighbour of its own step on at least one side. Without that it
      // stands alone among coarser ticks and reads as an accident: 1720 between 1700 and 1750.
      const room = Math.max(Math.abs(axis.x(t + step) - x), Math.abs(x - axis.x(t - step)))
      if (out.length && room < minGap * 0.8) continue
      out.push({ t, x, label: formatYear(t), level })
      placed = true
    }
    if (placed) {
      level += 1
      coarser = step
    }
  }
  // The start of the axis always carries its date.
  for (let i = out.length - 1; i >= 0; i--) if (out[i]!.x - axis.x0 < minGap && out[i]!.x - axis.x0 > 0.5) out.splice(i, 1)
  if (free(axis.x0)) out.push({ t: axis.t0, x: axis.x0, label: formatYear(axis.t0, y1 - y0 > 2000 ? 10 : 1), level })
  // No long stretch goes undated: put the roundest year that fits into any wide gap.
  for (let pass = 0; pass < 12; pass++) {
    out.sort((a, b) => a.x - b.x)
    const edges = [...out.map((tick) => tick.x), axis.x1]
    let widest = -1
    for (let i = 0; i + 1 < edges.length; i++) if (edges[i + 1]! - edges[i]! > minGap * 2.2 && (widest < 0 || edges[i + 1]! - edges[i]! > edges[widest + 1]! - edges[widest]!)) widest = i
    if (widest < 0) break
    const [left, right] = [edges[widest]!, edges[widest + 1]!]
    let best: Tick | null = null
    for (const step of STEPS) {
      const from = yearOf(axis.t(left))
      const to = yearOf(axis.t(right))
      if ((to - from) / step > 400) break
      for (let year = Math.ceil(from / step) * step; year <= to; year += step) {
        const t = momentOf(year)
        const x = axis.x(t)
        if (x - left < minGap || right - x < minGap || !free(x)) continue
        if (!best || Math.abs(x - (left + right) / 2) < Math.abs(best.x - (left + right) / 2)) best = { t, x, label: formatYear(t), level }
      }
      if (best) break
    }
    if (!best) break
    out.push(best)
  }
  return out.sort((a, b) => a.x - b.x)
}

/**
 * A date reduced to one year for lists and tables: "1765", "by 1776", "c. 4200 BCE". An uncertain
 * date is rounded to what it can bear, so a range midpoint never reads as an exact year.
 */
export function yearLabel(date: { t: number; t0?: number; status: string }): string {
  const loose = date.status !== 'known'
  const year = yearOf(date.t)
  const round = !loose ? 1 : year <= -20000 ? 1000 : year <= -3000 ? 100 : year <= -1000 ? 50 : year <= 1000 ? 10 : 1
  const text = formatYear(date.t, round)
  if (date.status === 'bounded' && date.t0 === undefined) return `by ${text}`
  return loose ? `c. ${text}` : text
}
