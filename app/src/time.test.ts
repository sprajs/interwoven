import { describe, expect, it } from 'vitest'
import { PRESENT, calendar, formatYear, log, makeAxis, panWindow, peopleScale, ticks, yearOf, zoomWindow, type TimeScale } from './time.ts'

/** A small cumulative person-years series shaped like the real one: slow, then faster. */
const PERSON_YEARS: [number, number][] = [
  [-200000, 0],
  [-10000, 2e11],
  [0, 1e12],
  [1000, 1.3e12],
  [1800, 2e12],
  [1950, 2.5e12],
  [2020, 3e12],
]

/** Asserts two numbers agree to a relative tolerance, since positions on the people scale run to 10^12. */
function expectNear(actual: number, expected: number, relative = 1e-9) {
  expect(Math.abs(actual - expected)).toBeLessThanOrEqual(relative * Math.max(1, Math.abs(expected)))
}

const SCALES: TimeScale[] = [calendar, log, peopleScale(PERSON_YEARS)]

/** Years spread across the whole range the app shows, including the era boundary and the present. */
const YEARS = [-200000, -150000, -50000, -10001, -10000, -3000, -500, -1, 0, 0.5, 1, 2, 500, 1000, 1500, 1800, 1900, 1950, 2000, 2020, 2025, PRESENT]

describe.each(SCALES.map((s) => [s.id, s] as const))('%s scale', (_id, scale) => {
  /** Every view relies on later moments being further right. */
  it('is strictly increasing', () => {
    for (let i = 1; i < YEARS.length; i++) expect(scale.u(YEARS[i]!)).toBeGreaterThan(scale.u(YEARS[i - 1]!))
  })

  /** Reading a moment back from a position gives the moment that was placed there. */
  it('round-trips moments through positions', () => {
    for (const t of YEARS) expect(Math.abs(scale.t(scale.u(t)) - t)).toBeLessThan(1e-6 * Math.max(1, Math.abs(t)))
  })
})

describe('makeAxis', () => {
  /** The window fills the pixel range exactly, and pixels convert back to the same moments. */
  it.each(SCALES.map((s) => [s.id, s] as const))('maps the window onto the pixels and back (%s)', (_id, scale) => {
    const axis = makeAxis(scale, -5000, 2000, 40, 1040)
    expect(axis.x(-5000)).toBeCloseTo(40, 6)
    expect(axis.x(2000)).toBeCloseTo(1040, 6)
    for (const t of [-5000, -1200, 0, 1, 1500, 2000]) expect(axis.t(axis.x(t))).toBeCloseTo(t, 4)
    for (const x of [40, 300, 777, 1040]) expect(axis.x(axis.t(x))).toBeCloseTo(x, 4)
  })
})

describe('ticks', () => {
  const MIN_GAP = 72
  const SPANS = [200000, 50000, 10000, 2000, 500, 100, 20]

  /** Labels never overlap or spill off the axis, whatever the scale or zoom. */
  for (const scale of SCALES) {
    for (const span of SPANS) {
      it(`are ordered, spaced and on the axis (${scale.id}, ${span} years)`, () => {
        const axis = makeAxis(scale, PRESENT - span, PRESENT, 0, 1200)
        const placed = ticks(axis, MIN_GAP)
        expect(placed.length).toBeGreaterThan(1)
        for (const tick of placed) {
          expect(tick.x).toBeGreaterThanOrEqual(axis.x0 - 0.5)
          expect(tick.x).toBeLessThanOrEqual(axis.x1 + 0.5)
        }
        for (let i = 1; i < placed.length; i++) expect(placed[i]!.x - placed[i - 1]!.x).toBeGreaterThanOrEqual(MIN_GAP)
      })
    }
  }

  /** There is no year 0: the boundary between the eras reads 1 CE. */
  it('label the era boundary 1 CE and never 0', () => {
    const labels = ticks(makeAxis(calendar, -60, 60, 0, 1200), MIN_GAP).map((t) => t.label)
    expect(labels).toContain('1 CE')
    expect(labels.some((l) => /^0( |$)/.test(l))).toBe(false)
  })
})

describe('formatYear', () => {
  /** Years are written as a reader would write them. */
  it('writes years the way a reader expects', () => {
    expect(formatYear(1850)).toBe('1850')
    expect(formatYear(500)).toBe('500 CE')
    expect(formatYear(-2999)).toBe('3000 BCE')
    expect(formatYear(-189999)).toBe('190 000 BCE')
  })

  /** Moments either side of the era boundary fall in 1 BCE and 1 CE. */
  it('has no year 0', () => {
    expect(yearOf(0)).toBe(-1)
    expect(yearOf(1)).toBe(1)
  })
})

describe('zoomWindow', () => {
  const LIMITS: [number, number] = [-200000, PRESENT]

  /** The moment under the pointer stays under the pointer while zooming. */
  it.each(SCALES.map((s) => [s.id, s] as const))('keeps the anchor at the same place in the window (%s)', (_id, scale) => {
    const window: [number, number] = [-3000, 1500]
    const about = 200
    const share = (w: [number, number]) => (scale.u(about) - scale.u(w[0])) / (scale.u(w[1]) - scale.u(w[0]))
    const zoomed = zoomWindow(scale, window, about, 0.5, LIMITS)
    expectNear(scale.u(zoomed[1]) - scale.u(zoomed[0]), (scale.u(window[1]) - scale.u(window[0])) * 0.5)
    expectNear(share(zoomed), share(window))
  })

  /** Zooming out never shows time outside the limits. */
  it.each(SCALES.map((s) => [s.id, s] as const))('never leaves the limits (%s)', (_id, scale) => {
    const [t0, t1] = zoomWindow(scale, [-150000, 1900], 1800, 10, LIMITS)
    expect(t0).toBeGreaterThanOrEqual(LIMITS[0] - 1e-6)
    expect(t1).toBeLessThanOrEqual(LIMITS[1] + 1e-6)
  })
})

describe('panWindow', () => {
  const LIMITS: [number, number] = [-200000, PRESENT]

  /** Panning slides the window without stretching it, and stops at either end. */
  it.each(SCALES.map((s) => [s.id, s] as const))('stops at the limits and keeps its width (%s)', (_id, scale) => {
    const window: [number, number] = [1000, 1800]
    const width = scale.u(window[1]) - scale.u(window[0])

    const moved = panWindow(scale, window, 0.25, LIMITS)
    expectNear(scale.u(moved[1]) - scale.u(moved[0]), width)
    expect(moved[0]).toBeGreaterThan(window[0])

    const right = panWindow(scale, window, 1000, LIMITS)
    expect(right[1]).toBeCloseTo(LIMITS[1], 4)
    expectNear(scale.u(right[1]) - scale.u(right[0]), width)

    const left = panWindow(scale, window, -1e9, LIMITS)
    expect(left[0]).toBeCloseTo(LIMITS[0], 2)
    expectNear(scale.u(left[1]) - scale.u(left[0]), width)
  })
})
