import { describe, expect, it } from 'vitest'
import { blendFolds, foldAroundYears, foldFromWindows, FoldMap, MAX_FOLD_POINTS, normalizeWindows, unfoldPleat } from './folds.ts'

const monotonic = (map: FoldMap) => {
  for (let u = 0; u < 1; u += 0.001) expect(map.map(u + 0.001)).toBeGreaterThanOrEqual(map.map(u))
}

describe('foldFromWindows', () => {
  it('opens a window and keeps the rest on the sheet', () => {
    const map = foldFromWindows([[0.4, 0.5]])
    expect(map.map(0)).toBeCloseTo(0)
    expect(map.map(1)).toBeCloseTo(1)
    // The window gets most of the page, and history on either side is still there.
    expect(map.map(0.5) - map.map(0.4)).toBeGreaterThan(0.8)
    expect(map.map(0.2)).toBeGreaterThan(0)
    expect(map.pleats).toHaveLength(2)
    monotonic(map)
  })

  it('round trips', () => {
    const map = foldFromWindows([[0.1, 0.2], [0.7, 0.75]])
    for (const u of [0, 0.05, 0.15, 0.4, 0.72, 0.9, 1]) expect(map.invert(map.map(u))).toBeCloseTo(u)
  })

  it('merges overlapping windows and is the identity when nothing is folded', () => {
    expect(normalizeWindows([[0.5, 0.2], [0.4, 0.6], [0.8, 0.9]])).toEqual([[0.2, 0.6], [0.8, 0.9]])
    expect(foldFromWindows([]).isIdentity).toBe(true)
    expect(foldFromWindows([[0, 1]]).isIdentity).toBe(true)
  })

  it('unfolds the chosen pleat by joining its neighbours', () => {
    const windows: [number, number][] = [[0.1, 0.2], [0.6, 0.8]]
    const map = foldFromWindows(windows)
    const between = map.pleats.find((p) => p.u0 === 0.2)!
    expect(unfoldPleat(windows, between)).toEqual([[0.1, 0.8]])
    const before = map.pleats.find((p) => p.u0 === 0)!
    expect(unfoldPleat(windows, before)).toEqual([[0, 0.2], [0.6, 0.8]])
  })
})

describe('foldAroundYears', () => {
  const u = (year: number) => (year + 5000) / 7030

  it('folds a gap that would dominate the story, and keeps the rest to scale', () => {
    const { windows, map } = foldAroundYears([-4650, 1250, 1260, 1275], { u })
    expect(windows).toEqual([[-4650, -4650], [1250, 1275]])
    expect(map.pleats.length).toBeGreaterThanOrEqual(3)
    monotonic(map)
  })

  it('gives a story set in one year some width', () => {
    const { map } = foldAroundYears([1044.5, 1044.5, 1044.5], { u })
    expect(map.map(u(1045)) - map.map(u(1044))).toBeGreaterThan(0.1)
    monotonic(map)
  })

  it('stays within what the shader can hold, even for a very scattered story', () => {
    const years = Array.from({ length: 200 }, (_, i) => -4000 + 2 ** (i / 18))
    const { map } = foldAroundYears(years, { u, gapShare: 0, minGapYears: 0 })
    expect(map.us.length).toBeLessThanOrEqual(MAX_FOLD_POINTS / 2)
    monotonic(map)
  })
})

describe('blendFolds', () => {
  it('moves smoothly from one map to another without crossing', () => {
    const a = foldFromWindows([[0.1, 0.2]])
    const b = foldFromWindows([[0.7, 0.8]])
    const half = blendFolds(a, b, 0.5)
    expect(half.map(0.5)).toBeCloseTo((a.map(0.5) + b.map(0.5)) / 2)
    monotonic(half)
    expect(blendFolds(a, b, 0)).toBe(a)
    expect(blendFolds(a, b, 1)).toBe(b)
  })

  it('never exceeds what the shader can hold', () => {
    const a = foldAroundYears(Array.from({ length: 200 }, (_, i) => -4000 + 2 ** (i / 18)), { u: (y) => (y + 5000) / 7030, gapShare: 0, minGapYears: 0 }).map
    const b = foldAroundYears(Array.from({ length: 200 }, (_, i) => -3900 + 2 ** (i / 17)), { u: (y) => (y + 5000) / 7030, gapShare: 0, minGapYears: 0 }).map
    expect(blendFolds(a, b, 0.5).us.length).toBeLessThanOrEqual(MAX_FOLD_POINTS)
  })
})
