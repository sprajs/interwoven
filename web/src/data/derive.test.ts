import { describe, expect, it } from 'vitest'
import { computeReach, connectedComponents, cornersFree, findCrossings, layoutStory, lineageOf, longestChain, parseYearQuery, rowOrder, rowPositions, storyIndex, threadOf } from './derive.ts'
import { documentedSpan, hasLaterLife, indexLifecycle, isFinal, readEventDate, tallyLifecycle, type LifeEvent, type LifeRecord } from './lifecycle.ts'

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

  it('gives an entry with no descendants no reach at all', () => {
    const reach = computeReach(dated(1800), [])
    expect(reach.any[0]).toBe(1800)
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

  it('gives every entry exactly one row in every order', () => {
    for (const order of ['thread', 'origin', 'reach'] as const) {
      expect([...rowOrder(nodes, children, parents, reach, order)].sort()).toEqual([0, 1, 2, 3])
    }
  })

  it('orders by origin, reach and thread', () => {
    expect([...rowOrder(nodes, children, parents, reach, 'origin')]).toEqual([3, 0, 2, 1])
    expect(rowOrder(nodes, children, parents, reach, 'reach')[0]).toBe(0)
    // The thread order keeps a parent directly above its earliest child.
    const thread = [...rowOrder(nodes, children, parents, reach, 'thread')]
    expect(thread.indexOf(2)).toBe(thread.indexOf(0) + 1)
  })

  it('keeps rows on the sheet', () => {
    const y = rowPositions(rowOrder(nodes, children, parents, reach, 'origin'))
    for (const v of y) {
      expect(v).toBeGreaterThanOrEqual(0)
      expect(v).toBeLessThanOrEqual(1)
    }
  })

  it('only counts a crossing where the crossed rule actually exists at that date', () => {
    // Rows 0, 1, 2 from the top. The stitch from 0 to 2 falls in 1900 and passes row 1.
    const rows = Int32Array.from([0, 1, 2])
    const y = rowPositions(rows)
    const long = computeReach(dated(1800, 1850, 1900, 1950), [edge(0, 2), edge(1, 3)])
    const hit = findCrossings(rows, y, dated(1800, 1850, 1900, 1950), long, [edge(0, 2)])
    expect(hit).toHaveLength(1)
    expect(hit[0]!.node).toBe(1)
    const short = computeReach(dated(1800, 1850, 1900), [edge(0, 2)])
    expect(findCrossings(rows, y, dated(1800, 1850, 1900), short, [edge(0, 2)])).toHaveLength(0)
  })
})

describe('cornersFree', () => {
  const u = (year: number) => (year - 1000) / 1000

  it('sees the empty corners a staircase leaves', () => {
    const nodes = dated(...Array.from({ length: 100 }, (_, i) => 1000 + i * 10))
    const reach = computeReach(nodes, [])
    const rows = rowOrder(nodes, adjacency(100, []).children, adjacency(100, []).parents, reach, 'origin')
    expect(cornersFree(rows, nodes, reach, u)).toBe(true)
  })

  it('sees long rules crossing the top right', () => {
    const nodes = dated(...Array.from({ length: 100 }, (_, i) => 1000 + i * 10))
    const edges = Array.from({ length: 40 }, (_, i) => edge(i, 99))
    const reach = computeReach(nodes, edges)
    const { children, parents } = adjacency(100, edges)
    expect(cornersFree(rowOrder(nodes, children, parents, reach, 'origin'), nodes, reach, u)).toBe(false)
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

const event = (type: string, role: LifeEvent['role'], start: number, end = start): LifeEvent => ({
  id: `${type}-${start}`,
  type,
  role,
  start,
  end,
  label: String(start),
  statement: '',
  review: 'accepted',
})

describe('lifecycle', () => {
  const zeiss: LifeRecord = { status: { withdrawal: 'documented' }, events: [event('commercial_offer', 'use', 1885), event('withdrawal', 'end', 1885, 1889)] }
  const glass: LifeRecord = { status: { withdrawal: 'documented', end_of_use: 'unknown' }, events: [event('documented_description', 'origin', 2018), event('commercial_offer', 'use', 2019), event('withdrawal', 'end', 2023), event('support_end', 'end', 2023)] }
  const ra: LifeRecord = { status: { abandonment: 'documented' }, events: [event('production', 'use', 1969), event('practical_deployment', 'use', 1969), event('abandonment', 'end', 1969)] }
  const single: LifeRecord = { status: { end_of_use: 'unknown' }, events: [event('first_commercial_availability', 'use', 1960)] }

  it('keeps a bounded date marked, so "by 2023" cannot read as "in 2023"', () => {
    expect(readEventDate({ latest: { year: 2023 } })).toEqual({ start: 2023, end: 2023, bound: 'by' })
    expect(readEventDate({ earliest: { year: 1885 }, latest: { year: 1889 } })).toEqual({ start: 1885, end: 1889 })
    expect(readEventDate({})).toBeNull()
  })

  it('does not treat a single dated record as evidence of a later life', () => {
    expect(hasLaterLife(single)).toBe(false)
    expect(hasLaterLife(undefined)).toBe(false)
    expect(hasLaterLife(glass)).toBe(true)
  })

  it('tallies what is documented and nothing else', () => {
    const tally = tallyLifecycle(new Map([[0, zeiss], [1, glass], [2, ra], [3, single]]), 143)
    expect(tally.withLaterLife).toBe(3)
    expect(tally.counts).toEqual({ decline: 0, withdrawal: 2, end_of_use: 0, abandonment: 1, revival: 0 })
    expect(tally.statedUnknown).toBe(2)
    expect(tally.total).toBe(143)
  })

  it('does not stretch a documented span into an uncertain date range', () => {
    expect(documentedSpan(zeiss)).toBeNull()
    const span = documentedSpan(glass)
    expect(span?.start).toBe(2018)
    expect(span?.end).toBe(2023)
  })

  it('has no span at all for an entry with no evidence', () => {
    expect(documentedSpan(undefined)).toBeNull()
  })

  it('counts withdrawal from sale as not being the end of the thing', () => {
    expect(isFinal(glass)).toBe(false)
    expect(isFinal(ra)).toBe(true)
    // Researched and found to be unknown stays unknown, even after an abandonment.
    expect(isFinal({ ...ra, status: { abandonment: 'documented', end_of_use: 'unknown' } })).toBe(false)
  })

  it('drops records for entries that are not on the chart', () => {
    const index = indexLifecycle({ meta: { entries: 2 }, records: { here: zeiss, gone: glass } }, new Map([['here', 7]]))
    expect([...index.keys()]).toEqual([7])
  })
})
