import { describe, expect, it } from 'vitest'
import { computeReach, connectedComponents, layoutStory, lineageOf, longestChain, parseYearQuery, rowOrder, storyIndex, threadOf } from './derive.ts'

const dated = (...years: number[]) => years.map((year) => ({ year }))
const edge = (source: number, target: number, tentative = false) => ({ source, target, tentative })

function adjacency(n: number, edges: { source: number; target: number }[]) {
  const children: number[][] = Array.from({ length: n }, () => [])
  const parents: number[][] = Array.from({ length: n }, () => [])
  for (const e of edges) {
    children[e.source]!.push(e.target)
    parents[e.target]!.push(e.source)
  }
  return { children, parents }
}

describe('computeReach', () => {
  it('runs to the latest descendant, not just the latest child', () => {
    const reach = computeReach(dated(1800, 1850, 1900), [edge(0, 1), edge(1, 2)])
    expect(reach.direct[0]).toBe(1850)
    expect(reach.any[0]).toBe(1900)
    expect(reach.any[2]).toBe(1900)
  })

  it('keeps a reach through unreviewed links apart from a reviewed one', () => {
    const reach = computeReach(dated(1800, 1850, 1900), [edge(0, 1), edge(1, 2, true)])
    expect(reach.firm[0]).toBe(1850)
    expect(reach.any[0]).toBe(1900)
  })

  it('is not extended backwards by a link against date order', () => {
    const reach = computeReach(dated(1900, 1800), [edge(0, 1)])
    expect(reach.any[0]).toBe(1900)
  })

  it('terminates on a cycle in the data', () => {
    const reach = computeReach(dated(1800, 1850), [edge(0, 1), edge(1, 0)])
    expect(reach.any[0]).toBe(1850)
    expect(reach.any[1]).toBe(1850)
  })
})

describe('rows', () => {
  const nodes = dated(1800, 1850, 1820, 1700)
  const edges = [edge(0, 1), edge(0, 2)]
  const { children, parents } = adjacency(4, edges)
  const reach = computeReach(nodes, edges)

  it('orders by origin, reach and thread', () => {
    expect([...rowOrder(nodes, children, parents, reach, 'origin')]).toEqual([3, 0, 2, 1])
    expect(rowOrder(nodes, children, parents, reach, 'reach')[0]).toBe(0)
    // The thread order keeps a parent directly above its earliest child.
    const thread = [...rowOrder(nodes, children, parents, reach, 'thread')]
    expect(thread.indexOf(2)).toBe(thread.indexOf(0) + 1)
  })

})

describe('stories', () => {
  const nodes = dated(1800, 1810, 1820, 1830, 1825, 2000)
  const edges = [edge(0, 1), edge(1, 2), edge(2, 3), edge(1, 4)]
  const input = { nodes, ...adjacency(6, edges) }

  it('a lineage holds ancestors and descendants but not cousins', () => {
    const { members } = lineageOf(2, input)
    expect(members.sort()).toEqual([0, 1, 2, 3])
  })

  it('a thread holds everything connected and nothing else', () => {
    const { members } = threadOf(3, input)
    expect(members.sort()).toEqual([0, 1, 2, 3, 4])
  })

  it('limits a very long story and says so', () => {
    const chain = dated(...Array.from({ length: 50 }, (_, i) => 1000 + i))
    const links = chain.slice(1).map((_, i) => edge(i, i + 1))
    const result = threadOf(25, { nodes: chain, ...adjacency(50, links) }, 10)
    expect(result.members).toHaveLength(10)
    expect(result.truncated).toBe(true)
  })

  it('finds the longest chain, and passes through the entry it was followed from', () => {
    expect(longestChain([0, 1, 2, 3, 4], input, null)).toEqual([0, 1, 2, 3])
    expect(longestChain([0, 1, 2, 3, 4], input, 4)).toEqual([0, 1, 4])
  })

  it('reads in date order, one row per entry', () => {
    const story = layoutStory([3, 0, 2, 1, 4], input, null)
    expect(story.members).toEqual([0, 1, 2, 4, 3])
    for (let k = 1; k < story.y.length; k++) expect(story.y[k]!).toBeGreaterThan(story.y[k - 1]!)
  })

  it('indexes threads largest first and skips short ones', () => {
    const index = storyIndex(nodes, edges)
    expect(index).toHaveLength(1)
    expect(index[0]!.size).toBe(5)
    expect(index[0]!.first).toBe(0)
    expect(connectedComponents(6, edges)[5]).not.toBe(connectedComponents(6, edges)[0])
  })
})

describe('parseYearQuery', () => {
  it('reads years and eras', () => {
    expect(parseYearQuery('1850')).toEqual({ kind: 'year', year: 1850 })
    expect(parseYearQuery('500 BCE')).toEqual({ kind: 'year', year: -500 })
    expect(parseYearQuery('44 bc')).toEqual({ kind: 'year', year: -44 })
  })

  it('reads periods in any order', () => {
    expect(parseYearQuery('1600-1700')).toEqual({ kind: 'period', start: 1600, end: 1700 })
    expect(parseYearQuery('1700 to 1600')).toEqual({ kind: 'period', start: 1600, end: 1700 })
    expect(parseYearQuery('1820–1900')).toEqual({ kind: 'period', start: 1820, end: 1900 })
    expect(parseYearQuery('3000-1000 BC')).toEqual({ kind: 'period', start: -3000, end: -1000 })
    expect(parseYearQuery('500 BC to 100 AD')).toEqual({ kind: 'period', start: -500, end: 100 })
    expect(parseYearQuery('1960s')).toEqual({ kind: 'period', start: 1960, end: 1970 })
    expect(parseYearQuery('1600s')).toEqual({ kind: 'period', start: 1600, end: 1700 })
  })

  it('leaves names alone', () => {
    expect(parseYearQuery('steam')).toBeNull()
    expect(parseYearQuery('4004')).toEqual({ kind: 'year', year: 4004 })
    expect(parseYearQuery('12')).toBeNull()
    expect(parseYearQuery('')).toBeNull()
    expect(parseYearQuery('Intel 4004')).toBeNull()
  })
})
