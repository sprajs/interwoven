import { describe, expect, it } from 'vitest'
import { layoutPiles, PILE_PITCH, stackLevels } from './piles.ts'

const inOrder = (n: number) => Array.from({ length: n }, (_, i) => i)

/** Whether two marks at these places would cover one another. */
function touching(xs: number[], levels: ArrayLike<number>): boolean {
  for (let a = 0; a < xs.length; a++) {
    for (let b = a + 1; b < xs.length; b++) {
      if (levels[a] === levels[b] && Math.abs(xs[a]! - xs[b]!) < PILE_PITCH) return true
    }
  }
  return false
}

describe('stackLevels', () => {
  it('leaves marks that do not touch on the ground', () => {
    const xs = [0, 12, 24, 100]
    expect([...stackLevels(xs, inOrder(4))]).toEqual([0, 0, 0, 0])
  })

  it('stacks marks at one date into a column as tall as their number', () => {
    const xs = [50, 50, 50, 50]
    expect([...stackLevels(xs, inOrder(4))]).toEqual([0, 1, 2, 3])
  })

  it('fills the gaps a stair would leave, so height follows how crowded a stretch is', () => {
    const xs = inOrder(30).map((i) => i * 5)
    const levels = stackLevels(xs, inOrder(30))
    expect(Math.max(...levels)).toBeLessThanOrEqual(2)
    expect(touching(xs, levels)).toBe(false)
  })

  it('never lets two marks cover one another, across cell edges too', () => {
    const xs = inOrder(200).map((i) => (i * 37.3) % 180)
    expect(touching(xs, stackLevels(xs, inOrder(200)))).toBe(false)
  })

  it('stops growing rather than running away on a huge dataset', () => {
    const n = 2000
    const levels = stackLevels(new Float64Array(n), inOrder(n))
    expect(Math.max(...levels)).toBeLessThan(n)
  })
})

describe('layoutPiles', () => {
  const xs = [10, 10, 10, 300, 300, 600]
  const family = [0, 0, 1, 1, 2, 2]
  const base = { xs, family, families: 3, included: () => true, height: 600 }

  it('raises marks up the page from the ground', () => {
    const { y } = layoutPiles({ ...base, form: 'together' })
    const ground = Math.max(...y)
    expect(y[5]).toBe(ground)
    const at10 = [y[0]!, y[1]!, y[2]!].sort()
    expect(at10[2]).toBe(ground)
    expect(at10[0]!).toBeLessThan(ground)
  })

  it('layers families in the order of their rows, the last at the bottom', () => {
    const { y } = layoutPiles({ ...base, form: 'together' })
    // At x = 300 the last family goes down first.
    expect(y[4]!).toBeGreaterThan(y[3]!)
  })

  it('gives each family a row of its own, in order and inside the page', () => {
    const { rows, y } = layoutPiles({ ...base, form: 'subject' })
    expect(rows.map((row) => row.count)).toEqual([2, 2, 2])
    expect(rows[0]!.bottom).toBeLessThan(rows[1]!.bottom)
    expect(rows[1]!.bottom).toBeLessThan(rows[2]!.bottom)
    expect(rows[2]!.bottom).toBeLessThanOrEqual(1)
    for (const value of y) expect(value).toBeGreaterThanOrEqual(0)
  })

  it('stacks only within a family when each has its own row', () => {
    const { y, rows } = layoutPiles({ ...base, form: 'subject' })
    expect(y[2]).toBeCloseTo(rows[1]!.bottom, 5)
    expect(y[3]).toBeCloseTo(rows[1]!.bottom, 5)
  })

  it('draws one shared pile larger when that helps it fill the page, without marks touching', () => {
    const spread = Array.from({ length: 60 }, (_, i) => i * 18)
    const { markScale, y } = layoutPiles({ xs: spread, family: new Int32Array(60), families: 1, included: () => true, form: 'together', height: 700 })
    expect(markScale).toBeGreaterThan(1)
    expect(Math.min(...y)).toBeGreaterThan(0)
  })

  it('keeps the usual size where a shared pile is already tall', () => {
    const tall = new Float64Array(200)
    expect(layoutPiles({ xs: tall, family: new Int32Array(200), families: 1, included: () => true, form: 'together', height: 300 }).markScale).toBe(1)
  })

  it('squeezes a stack that would not fit, rather than leaving the page', () => {
    const tall = new Float64Array(200)
    const { y } = layoutPiles({ xs: tall, family: new Int32Array(200), families: 1, included: () => true, form: 'together', height: 300 })
    expect(Math.min(...y)).toBeGreaterThanOrEqual(0)
    expect(Math.max(...y)).toBeLessThanOrEqual(1)
  })

  it('counts only the entries that pass the filters', () => {
    const { rows, y } = layoutPiles({ ...base, included: (i) => i !== 0, form: 'subject' })
    expect(rows[0]!.count).toBe(1)
    expect(y[1]).toBeCloseTo(rows[0]!.bottom, 5)
    expect(y[0]).toBeCloseTo(rows[0]!.bottom, 5)
  })
})
