import { describe, expect, it } from 'vitest'
import { buildModel, countDescendants, walk } from './model.ts'
import type { RawDataset, RawNode } from './types.ts'
import { validateDataset } from './validate.ts'

function node(id: string, year: number, labels: string[] = ['a'], level: RawNode['level'] = 1): RawNode {
  return {
    id,
    title: id,
    kind: 'technology',
    level,
    year,
    start: year,
    end: year,
    date_label: String(year),
    placed_by: 'demonstration',
    anchored: false,
    labels,
    summary: '',
    regions: [],
    review: 'accepted',
    sources: [],
  }
}

const dataset = (nodes: RawNode[], links: [string, string][] = []): RawDataset => ({
  meta: { title: 'Test' },
  labels: [
    { id: 'a', name: 'A', ink: '#265a96' },
    { id: 'b', name: 'B', ink: '#b0472d' },
  ],
  nodes,
  links: links.map(([from, to]) => ({ from, to, relation: 'builds on', tentative: false })),
})

describe('buildModel', () => {
  it('keeps noncausal companions visible without counting them as ancestors', () => {
    const data = dataset([node('a', 1800), node('b', 1850)], [['a', 'b']])
    data.links[0]!.causal = false
    data.links[0]!.relation = 'companion of'
    const model = buildModel(data)
    expect(model.edges).toHaveLength(1)
    expect(model.children[0]).toEqual([])
    expect(model.parents[1]).toEqual([])
    expect(model.impact[0]).toBe(0)
  })

  it('counts everything downstream, not only direct children', () => {
    const model = buildModel(dataset([node('a', 1800), node('b', 1850), node('c', 1900)], [['a', 'b'], ['b', 'c']]))
    expect(model.impact[model.indexById.get('a')!]).toBe(2)
    expect(model.impact[model.indexById.get('c')!]).toBe(0)
  })

})

describe('walk and countDescendants', () => {
  const children = [[1, 2], [3], [3], []]

  it('reports the shortest hop count', () => {
    expect(walk(0, children, 9).get(3)).toBe(2)
    expect(walk(0, children, 1).has(3)).toBe(false)
  })

  it('counts a shared descendant once', () => {
    expect(countDescendants(0, children, new Int32Array(4).fill(-1), 0)).toBe(3)
  })
})

describe('validateDataset', () => {
  it('rejects a dangling link and an undeclared label', () => {
    const errors = validateDataset(dataset([node('a', 1800, ['nope'])], [['a', 'ghost']])).filter((i) => i.severity === 'error')
    expect(errors.map((e) => e.message).join(' ')).toMatch(/ghost/)
    expect(errors.map((e) => e.message).join(' ')).toMatch(/nope/)
  })

  it('rejects a date range that runs backwards', () => {
    const bad = { ...node('a', 1800), start: 1900, end: 1800 }
    expect(validateDataset(dataset([bad])).some((i) => i.severity === 'error')).toBe(true)
  })
})
