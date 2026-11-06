import { describe, expect, it } from 'vitest'
import type { RawNode } from '../data/types.ts'
import { shortDate } from './overlay.ts'

function node(fields: Partial<RawNode>): RawNode {
  return { id: 'date-fixture', title: 'Date fixture', kind: 'technology', level: 1, year: 1910,
    date_label: 'A source description', placed_by: 'practical use', anchored: true, labels: [],
    summary: '', regions: [], review: 'accepted', sources: [], ...fields }
}

describe('shared chart and search date labels', () => {
  it('preserves the approximate upper-only birch-tar year without rounding or adding a lower bound', () => {
    const current = node({ year: -189050, end: -189050, date_kind: 'known_by',
      entry_date: { status: 'approximate', precision: 'year', latest: { year: -189050 }, earliest_status: 'unknown' } })
    const before = JSON.stringify(current)
    expect(shortDate(current)).toBe('by c. 189 050 BCE')
    expect(current).not.toHaveProperty('start')
    expect(current.entry_date).not.toHaveProperty('earliest')
    expect(JSON.stringify(current)).toBe(before)
  })

  it('keeps an approximate lower limit distinct from a claim of continued use', () => {
    const current = node({ year: -12345, start: -12345, date_kind: 'known_from',
      entry_date: { status: 'approximate', earliest: { year: -12345 }, latest_status: 'not_yet_researched' } })
    const before = JSON.stringify(current)
    expect(shortDate(current)).toBe('not before c. 12 345 BCE')
    expect(current).not.toHaveProperty('end')
    expect(current.entry_date).not.toHaveProperty('latest')
    expect(JSON.stringify(current)).toBe(before)
  })

  it('qualifies an approximate interval and retains both stored years', () => {
    const current = node({ year: -1600, start: -1650, end: -1550, date_kind: 'interval',
      entry_date: { status: 'approximate', earliest: { year: -1650 }, latest: { year: -1550 } } })
    expect(shortDate(current)).toBe('c. 1 650 BCE–1 550 BCE')
  })

  it('qualifies approximate points and reads stored years rather than a fractional render coordinate', () => {
    expect(shortDate(node({ year: 1010.5, date_kind: 'point', entry_date: { status: 'approximate', earliest: { year: 1010 }, latest: { year: 1010 } } }))).toBe('c. 1010')
    expect(shortDate(node({ year: -12345.6789, date_kind: 'point' }))).toBe('12 345.6789 BCE')
  })

  it('keeps ordinary exact dates unchanged and never infers approximation from prose', () => {
    expect(shortDate(node({ end: 1910, date_kind: 'known_by', date_label: 'Approximately 1910 in an unrelated note',
      entry_date: { status: 'bounded', latest: { year: 1910 }, earliest_status: 'unknown' } }))).toBe('by 1910')
    expect(shortDate(node({ date_kind: 'point', entry_date: { status: 'known', earliest: { year: 1910 }, latest: { year: 1910 } } }))).toBe('1910')
    expect(shortDate(node({ year: 1915, start: 1910, end: 1920, date_kind: 'interval', entry_date: { status: 'bounded', earliest: { year: 1910 }, latest: { year: 1920 } } }))).toBe('1910–1920')
  })
})
