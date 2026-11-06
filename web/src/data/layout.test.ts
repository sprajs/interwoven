import { describe, expect, it } from 'vitest'
import { layoutStrands, type StrandInput } from './layout.ts'

const input = (over: Partial<Omit<StrandInput, 'u'>> & { u: number[] }): StrandInput => {
  const n = over.u.length
  return {
    levels: new Array(n).fill(2),
    family: new Array(n).fill('A'),
    label: new Array(n).fill('a'),
    edges: [],
    order: [{ name: 'A', ink: '#000000' }, { name: 'B', ink: '#111111' }],
    ...over,
    u: Float32Array.from(over.u),
  }
}

describe('layoutStrands', () => {
  it('keeps a thread on one row when nothing is in its way', () => {
    const { y } = layoutStrands(input({ u: [0.1, 0.4, 0.8], edges: [{ source: 0, target: 1 }, { source: 1, target: 2 }] }))
    expect(y[0]).toBe(y[1])
    expect(y[1]).toBe(y[2])
  })

  it('never lets an unrelated entry sit on a line it has nothing to do with', () => {
    const { y } = layoutStrands(input({ u: [0.1, 0.4, 0.8], edges: [{ source: 0, target: 2 }] }))
    expect(y[0]).toBe(y[2])
    expect(y[1]).not.toBe(y[0])
  })

  it('moves a second child to the next row', () => {
    const { y } = layoutStrands(input({ u: [0.1, 0.5, 0.5], edges: [{ source: 0, target: 1 }, { source: 0, target: 2 }] }))
    expect(y[1]).not.toBe(y[2])
  })

  it('keeps entries close together in time apart', () => {
    const { y } = layoutStrands(input({ u: [0.5, 0.501, 0.502] }))
    expect(new Set(y).size).toBe(3)
  })

  it('stacks families in the given order and reports each one', () => {
    const { y, families } = layoutStrands(input({ u: [0.1, 0.1], family: ['B', 'A'] }))
    expect(families.map((f) => f.name)).toEqual(['A', 'B'])
    expect(y[1]!).toBeLessThan(y[0]!)
  })

  it('keeps a thread together in the family most of it belongs to', () => {
    const { y, families } = layoutStrands(input({ u: [0.1, 0.5, 0.9], family: ['A', 'A', 'B'], edges: [{ source: 0, target: 1 }, { source: 1, target: 2 }] }))
    expect(families).toHaveLength(1)
    expect(y[2]).toBe(y[1])
  })

  it('stays on the sheet, is deterministic and stays fast at scale', () => {
    const n = 50000
    let seed = 7
    const random = () => (seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296
    const u = Array.from({ length: n }, () => random())
    const edges = Array.from({ length: n - 1 }, (_, i) => ({ source: Math.floor(random() * (i + 1)), target: i + 1 }))
    const family = u.map(() => (random() < 0.5 ? 'A' : 'B'))
    const start = performance.now()
    const a = layoutStrands(input({ u, edges, family }))
    expect(performance.now() - start).toBeLessThan(3000)
    expect(Math.min(...a.y.subarray(0, 1000))).toBeGreaterThanOrEqual(0)
    expect(Math.max(...a.y.subarray(0, 1000))).toBeLessThanOrEqual(1)
    expect(layoutStrands(input({ u, edges, family })).y).toEqual(a.y)
  })
})
