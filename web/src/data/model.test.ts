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
  it('keeps every label a node carries and inks it by the first', () => {
    const model = buildModel(dataset([node('x', 1900, ['b', 'a'])]))
    expect(model.nodes[0]!.labels).toEqual(['b', 'a'])
    expect(model.labels.map((l) => l.id).sort()).toEqual(['a', 'b'])
    expect(model.ink[0]).toBeCloseTo(0xb0 / 255)
  })

  it('counts everything downstream, not only direct children', () => {
    const model = buildModel(dataset([node('a', 1800), node('b', 1850), node('c', 1900)], [['a', 'b'], ['b', 'c']]))
    expect(model.impact[model.indexById.get('a')!]).toBe(2)
    expect(model.impact[model.indexById.get('c')!]).toBe(0)
  })

  it('accepts a link that runs against display order, since dates are not causal', () => {
    const model = buildModel(dataset([node('late', 1950), node('early', 1900)], [['late', 'early']]))
    expect(model.edges).toHaveLength(1)
  })

  it('keeps disconnected entries', () => {
    expect(buildModel(dataset([node('alone', 1500)])).n).toBe(1)
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
  it('passes a clean dataset', () => {
    expect(validateDataset(dataset([node('a', 1800), node('b', 1900)], [['a', 'b']]))).toEqual([])
  })

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
