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

  it('spans 0 to 1', () => {
    expect(scale.compressed(scale.min)).toBeCloseTo(0, 3)
    expect(scale.compressed(scale.now)).toBeCloseTo(1, 3)
    expect(scale.linear(scale.min)).toBeCloseTo(0)
    expect(scale.linear(scale.now)).toBeCloseTo(1)
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
    const ticks = pickTicks((y) => (y + 3000) * 0.2, -3000, 2030, 1006, 70)
    expect(ticks.length).toBeGreaterThan(4)
    for (let i = 1; i < ticks.length; i++) expect(ticks[i]!.x - ticks[i - 1]!.x).toBeGreaterThanOrEqual(70)
  })
})
