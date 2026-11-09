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
  it('never lets an unrelated entry sit on a line it has nothing to do with', () => {
    const { y } = layoutStrands(input({ u: [0.1, 0.4, 0.8], edges: [{ source: 0, target: 2 }] }))
    expect(y[0]).toBe(y[2])
    expect(y[1]).not.toBe(y[0])
  })

  it('keeps entries close together in time apart', () => {
    const { y } = layoutStrands(input({ u: [0.5, 0.501, 0.502] }))
    expect(new Set(y).size).toBe(3)
  })

  it('keeps a thread together in the family most of it belongs to', () => {
    const { y, families } = layoutStrands(input({ u: [0.1, 0.5, 0.9], family: ['A', 'A', 'B'], edges: [{ source: 0, target: 1 }, { source: 1, target: 2 }] }))
    expect(families).toHaveLength(1)
    expect(y[2]).toBe(y[1])
  })

})
