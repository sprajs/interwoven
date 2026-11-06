import { describe, expect, it } from 'vitest'
import { buildLifeRecords, hasLifecycleEvidence, isReviewedLifeEvent, lifeDateLabel, plottedLifeEvents, readEventDate, ROLE_OF_EVENT, tallyLifecycle } from './lifecycle.ts'
import type { HistoricalDate, RawEvent, RawNode } from './types.ts'

const scope = { regions: ['A specified local community'], configuration: 'The scoped configuration', applications: ['A specified application'], market: { status: 'unknown' }, population: { status: 'specified', value: 'Named users' } }
const evidence = [{ source_id: 'source', locator: 'Dated operating record, p. 2', supports: 'This episode happened within the stated scope.' }]
const date = (year: number): HistoricalDate => ({ status: 'known', precision: 'year', earliest: { year }, latest: { year }, label: String(year) })
const event = (id: string, type: string, year: number): RawEvent => ({ id, node_id: 'entry', event_type: type, date: date(year), date_status: 'known', date_label: String(year),
  scope, evidence, review: 'accepted', lifecycle_review: 'accepted', statement: 'A scoped episode.' })
const entry = (): RawNode => ({ id: 'entry', title: 'Entry', kind: 'technology', level: 1, year: 1900, date_label: '1900', labels: ['test'], sources: ['source'], review: 'accepted', lifecycle_review: 'needs_review', summary: 'A scoped configuration', regions: ['A specified local community'], placed_by: 'practical use', anchored: true,
  lifecycle: { withdrawal: { status: 'documented', event_ids: ['withdrawal'], evidence }, end_of_use: { status: 'unknown', event_ids: [], rationale: 'No last use is established.', evidence } } })
const record = (events: RawEvent[], current = entry()) => buildLifeRecords([current], Object.fromEntries(events.map(e => [e.id, e]))).get('entry')!

describe('scoped lifecycle evidence', () => {
  it('retains approximate day precision and an absent lower limit in the full date', () => {
    const d: HistoricalDate = { status: 'approximate', precision: 'day', latest: { year: 2023, month: 3, day: 15 }, earliest_status: 'unknown', label: 'A qualified source description', basis: 'Only an approximate upper limit is supported.' }
    const before = JSON.stringify(d)
    const result = readEventDate(d)!
    expect(result).toMatchObject({ bound: 'by', date: d })
    expect(result.year).toBeGreaterThan(2023)
    expect(result.year).toBeLessThan(2024)
    expect(result).not.toHaveProperty('start')
    expect(result.date).not.toHaveProperty('earliest')
    const built = record([{ ...event('withdrawal', 'withdrawal', 2023), date: d }])
    expect(lifeDateLabel(built.events[0]!)).toBe('By approximately 15 March 2023')
    expect(JSON.stringify(d)).toBe(before)
    result.date!.latest!.day = 1
    expect(d.latest!.day).toBe(15)
  })

  it('preserves a lower-only limit without filling the unknown upper end', () => {
    const d: HistoricalDate = { status: 'bounded', earliest: { year: 1885, month: 4 }, latest_status: 'not_yet_researched' }
    const result = readEventDate(d)!
    expect(result).toMatchObject({ bound: 'from', date: d })
    expect(result).not.toHaveProperty('end')
    expect(result.date).not.toHaveProperty('latest')
    expect(lifeDateLabel({ ...record([event('a', 'practical_use', 1885)]).events[0]!, date: d })).toBe('Not before April 1885')
    expect(readEventDate(date(1910))).toMatchObject({ start: 1910, end: 1910, year: 1910 })
  })

  it('never parses prose into dates or accepts missing uncertainty/invalid date fields', () => {
    for (const d of [
      { status: 'unknown', label: 'By approximately 325 CE' },
      { status: 'approximate', latest: { year: 325 }, label: 'By 325' },
      { status: 'known', latest: { year: 325 }, earliest_status: 'unknown' },
      { status: 'bounded', latest: { year: 0 }, earliest_status: 'unknown' },
      { status: 'bounded', latest: { year: 2023, month: 4, day: 31 }, earliest_status: 'unknown' },
      { status: 'bounded', precision: 'day', latest: { year: 2023 }, earliest_status: 'unknown' },
    ]) expect(readEventDate(d)).toBeNull()
  })

  it('keeps recognition and disclosure distinct from actual use and from unclassified events', () => {
    expect(ROLE_OF_EVENT.practical_use).toBe('use')
    expect(ROLE_OF_EVENT.commercial_availability).toBe('availability')
    expect(ROLE_OF_EVENT.public_availability).toBe('availability')
    expect(ROLE_OF_EVENT.recognition).toBe('recognition')
    const r = record([event('paper', 'publication', 1900), event('unknown-type', 'future_event_type', 1901)])
    expect(r.events.map(e => e.role)).toEqual(['awareness', 'unclassified'])
    expect(hasLifecycleEvidence(r)).toBe(false)
    expect(plottedLifeEvents(r)).toEqual([])
  })

  it('preserves the full scope, evidence, dates and both review axes without mutating input', () => {
    const e = event('use', 'practical_use', 1910), n = entry()
    const before = JSON.stringify([n, e])
    const r = record([e], n)
    expect(r.events[0]).toMatchObject({ scope, evidence, date: e.date, review: 'accepted', lifecycle_review: 'accepted' })
    expect(r.review).toEqual({ historical_claim: 'accepted', lifecycle_classification: 'needs_review' })
    expect(r.stages.end_of_use).toEqual(n.lifecycle!.end_of_use)
    r.events[0]!.scope!.regions.push('Changed display copy')
    expect(JSON.stringify([n, e])).toBe(before)
  })

  it('counts a single accepted scoped episode without inventing an earlier origin or a duration', () => {
    const r = record([event('use', 'practical_use', 1910)])
    expect(hasLifecycleEvidence(r)).toBe(true)
    expect(plottedLifeEvents(r)).toHaveLength(1)
    expect(r).not.toHaveProperty('span')
    expect(r).not.toHaveProperty('duration')
    expect(r).not.toHaveProperty('final')
  })

  it('does not connect distant episodes or turn abandonment/sale/support cutoff into global last use', () => {
    const r = record([event('use', 'practical_use', 1910), event('withdrawal', 'withdrawal', 1980), event('support', 'support_end', 1985), event('abandoned', 'abandonment', 1990)])
    expect(plottedLifeEvents(r).map(e => e.year)).toEqual([1910, 1980, 1985, 1990])
    expect(r.status.end_of_use).toBe('unknown')
    expect(r).not.toHaveProperty('span')
    expect(r).not.toHaveProperty('final')
    expect(tallyLifecycle([r], 1).counts).toEqual({ adoption: 0, decline: 0, withdrawal: 1, end_of_use: 0, abandonment: 1, revival: 0 })
  })

  it('requires accepted classification and scoped source evidence for episode counts', () => {
    const r = record([event('withdrawal', 'withdrawal', 2023)])
    const e = r.events[0]!
    expect(isReviewedLifeEvent(e)).toBe(true)
    expect(tallyLifecycle([r], 1).counts.withdrawal).toBe(1)
    for (const changed of [
      { ...e, review: 'candidate' }, { ...e, lifecycle_review: 'needs_review' }, { ...e, scope: undefined },
      { ...e, evidence: [] }, { ...e, scope: { ...scope, population: { status: 'specified' } } },
    ]) {
      expect(isReviewedLifeEvent(changed)).toBe(false)
      expect(tallyLifecycle([{ ...r, events: [changed] }], 1).counts.withdrawal).toBe(0)
    }
    r.stages.withdrawal!.event_ids = ['different-event']
    expect(tallyLifecycle([r], 1).counts.withdrawal).toBe(1)
  })

  it('counts multiple scoped retirements while the broader family end remains unknown', () => {
    const n = entry(), before = JSON.stringify(n)
    const r = record([event('site-a', 'end_of_use', 1978), event('site-b', 'end_of_use', 2009), event('adopted', 'adoption', 1930),
      { ...event('pending', 'end_of_use', 2010), lifecycle_review: 'needs_review' }], n)
    expect(tallyLifecycle([r], 1)).toMatchObject({ withLifecycleEvidence: 1, statedUnknown: 1, counts: { adoption: 1, end_of_use: 2 } })
    expect(r.status.end_of_use).toBe('unknown')
    expect(r.stages.end_of_use!.event_ids).toEqual([])
    expect(JSON.stringify(n)).toBe(before)
    expect(r).not.toHaveProperty('span')
    expect(r).not.toHaveProperty('final')
  })

  it('retains unknown-date episodes and explicit unknown states without plotting fabricated coordinates', () => {
    const e = { ...event('undated', 'practical_use', 1910), date: { status: 'unknown', label: 'Date unknown' } }
    const r = record([e])
    expect(r.events[0]).not.toHaveProperty('year')
    expect(r.events[0]).not.toHaveProperty('start')
    expect(r.events[0]).not.toHaveProperty('end')
    expect(r.events[0]!.date).toEqual(e.date)
    expect(plottedLifeEvents(r)).toEqual([])
    expect(r.status.end_of_use).toBe('unknown')
    expect(buildLifeRecords([], {})).toEqual(new Map())
  })
})
