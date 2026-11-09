import { describe, expect, it } from 'vitest'
import { TimeScale, formatYear, pickTicks } from './time.ts'

describe('TimeScale', () => {
  const years = [-3000, 500, 1769, 1775, 1782, 1850, 1947, 1953, 1959, 2000]
  const scale = TimeScale.fromYears(years)

  it('is strictly increasing on both scales', () => {
    for (const warp of [0, 0.5, 1]) {
      let last = -Infinity
      for (let y = scale.min; y <= scale.now; y += 7) {
        const u = scale.u(y, warp)
        expect(u).toBeGreaterThan(last)
        last = u
      }
    }
  })

  it('inverts', () => {
    for (const warp of [0, 0.4, 1]) {
      for (const y of [-2500, 700, 1800, 1999]) expect(scale.year(scale.u(y, warp), warp)).toBeCloseTo(y, 0)
    }
  })

  it('gives busy periods more room than the same log span without data', () => {
    const empty = new TimeScale(scale.min, scale.now)
    const width = (s: TimeScale) => s.compressed(1960) - s.compressed(1940)
    expect(width(scale)).toBeGreaterThan(width(empty))
  })
})

describe('formatYear', () => {
  it('writes BCE years and never a year zero', () => {
    expect(formatYear(-3000)).toBe('3 000 BCE')
    expect(formatYear(1953)).toBe('1953')
    expect(formatYear(0)).toBe('1 CE')
  })
})

describe('pickTicks', () => {
  it('keeps ticks apart on screen', () => {
    const ticks = pickTicks((y) => (y + 3000) * 0.2, -3000, 2030, 70)
    expect(ticks.length).toBeGreaterThan(4)
    for (let i = 1; i < ticks.length; i++) expect(ticks[i]!.x - ticks[i - 1]!.x).toBeGreaterThanOrEqual(70)
  })

  it('divides a stretch evenly when it has room', () => {
    const years = pickTicks((y) => (y - 1800) * 4, 1800, 1900, 60).map((t) => t.year)
    const steps = new Set(years.slice(1).map((y, k) => y - years[k]!))
    expect(steps.size).toBe(1)
  })

  it('reaches a period opened by a fold, even with nothing either side', () => {
    // Everything is squeezed flat except 1800 to 1860.
    const toX = (y: number) => (y < 1800 ? y * 0.0001 : y > 1860 ? 1000 + y * 0.0001 : (y - 1800) * 16)
    const years = pickTicks(toX, -5000, 2026, 60).map((t) => t.year)
    expect(years.filter((y) => y > 1800 && y < 1860).length).toBeGreaterThan(3)
  })

  it('leaves out what cannot hold a tick', () => {
    const toX = (year: number) => year - 1000
    const some = pickTicks(toX, 1000, 2000, 100, (x) => x < 200).map((t) => t.year)
    expect(some.every((year) => year >= 1200)).toBe(true)
    expect(some.length).toBeGreaterThan(2)
  })
})
