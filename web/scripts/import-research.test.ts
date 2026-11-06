import { describe, expect, it } from 'vitest'
import { buildModel, nodeMarkStyle } from '../src/data/model.ts'
import { validateDataset } from '../src/data/validate.ts'
import { buildResearchDataset, deriveEntryDate, type ResearchEvent, type ResearchNode, type ResearchRecords } from './import-research.ts'
import type { EntryBasis } from '../src/data/types.ts'
import { dateLimitNote, entryReasonLabel } from '../src/ui/entryText.ts'

function event(id: string, nodeId: string, type: string, year: number): ResearchEvent {
  return { id, node_id: nodeId, event_type: type,
    date: { status: 'known', earliest: { year }, latest: { year }, label: String(year), basis: 'Synthetic source date.' },
    statement: 'A scoped synthetic historical event.', evidence: [{ source_id: 'source-1' }] }
}

function node(id: string, events: ResearchEvent[], basis: EntryBasis = 'first_commercial_availability', anchorId?: string): ResearchNode {
  const lifecycle = new Set(['invention', 'first_commercial_availability', 'practical_deployment', 'adoption', 'discovery', 'observation', 'formulation', 'publication', 'experimental_confirmation', 'acceptance', 'decline', 'withdrawal', 'end_of_use', 'abandonment', 'revival'])
  return { id, label: `Entry ${id}`, kind: ['recognition', 'public_awareness'].includes(basis) ? 'science' : 'technology',
    configuration: 'Synthetic configuration.', labels: ['fixture'], event_ids: events.map((entry) => entry.id),
    graph_anchor: { status: anchorId ? 'selected' : 'not_yet_researched', policy: 'community_entry', event_id: anchorId,
      entry_basis: basis, evidence_strength: basis === 'public_awareness' ? 'awareness_proxy' : 'direct', date_interpretation: 'event_date',
      community: 'Named local specialist community', scope: { regions: ['Fixture region'], configuration: 'Synthetic configuration.', applications: ['Fixture application'],
        market: { status: 'unknown' }, population: { status: 'specified', value: 'Named local specialist community' } },
      evidence: [{ source_id: 'source-1', locator: 'Fixture p. 1', supports: 'The scoped entry is supported.' }],
      rationale: 'A deliberate researched entry choice.', uncertainty: 'No global or earlier uptake is inferred.',
      ...(basis === 'public_awareness' ? { proxy_justification: 'A dated publication supports an awareness opportunity; use and adoption remain unresolved.' } : {}) },
    lifecycle: Object.fromEntries(events.filter((entry) => lifecycle.has(entry.event_type)).map((entry) => [entry.event_type, { status: 'documented', event_ids: [entry.id] }])),
    commercial_applicability: { status: ['recognition', 'public_awareness'].includes(basis) ? 'not_applicable' : basis === 'practical_use' ? 'nonmarket' : 'applicable',
      rationale: 'Explicit applicability decision.', evidence: [{ source_id: 'source-1' }] },
    provenance: { source_ids: ['source-1'] }, review: { historical_claim: 'accepted', lifecycle_classification: 'needs_review' } }
}

function records(nodes: ResearchNode[], events: ResearchEvent[]): ResearchRecords {
  return { nodes, events, relationships: [], sources: [{ id: 'source-1', title: 'Synthetic inspected source', url: 'https://example.org/source' }] }
}

describe('research importer placement', () => {
  it('exports original scoped event evidence and both review axes for lifecycle presentation', () => {
    const use = event('scoped-use', 'scope', 'practical_use', 1910)
    const current = node('scope', [use], 'practical_use', use.id)
    use.scope = structuredClone(current.graph_anchor!.scope!)
    use.evidence = [{ source_id: 'source-1', locator: 'Operating record, p. 4', supports: 'Only the named local users are attested.' }]
    use.review = { historical_claim: 'accepted', lifecycle_classification: 'needs_review' }
    const before = JSON.stringify([current, use])
    const data = buildResearchDataset(records([current], [use]))
    expect(data.events![use.id]).toMatchObject({ date: use.date, scope: use.scope, evidence: use.evidence, review: 'accepted', lifecycle_review: 'needs_review' })
    expect(buildModel(data).life.get('scope')!.events[0]).toMatchObject({ scope: use.scope, evidence: use.evidence, lifecycle_review: 'needs_review' })
    expect(JSON.stringify([current, use])).toBe(before)
  })

  it('keeps unresolved technology accessible without using its dated invention', () => {
    const invention = event('u-invention', 'u', 'invention', 1850)
    const data = buildResearchDataset(records([node('u', [invention])], [invention]))
    expect(data.nodes).toEqual([])
    expect(data.unplaced).toHaveLength(1)
    expect(data.unplaced![0]).toMatchObject({ id: 'u', anchor_status: 'not_yet_researched', placement_reason: 'Community entry not yet researched.', sources: ['source-1'] })
    expect(data.unplaced![0]).not.toHaveProperty('year')
    expect(data.events!['u-invention']!.date_label).toBe('1850')
    const model = buildModel(data)
    expect(model.n).toBe(0)
    expect(model.unplaced.map((entry) => entry.id)).toEqual(['u'])
    expect(model.entryById.get('u')?.title).toBe('Entry u')
    expect(validateDataset(data)).toEqual([])
  })

  it('places a disconnected nonmarket technology only by its justified deployment anchor', () => {
    const deployment = event('p-deployment', 'p', 'practical_deployment', 1976)
    const current = node('p', [deployment], 'practical_use', deployment.id)
    current.lifecycle!.first_commercial_availability = { status: 'unknown', event_ids: [] }
    const data = buildResearchDataset(records([current], [deployment]))
    expect(data.nodes[0]).toMatchObject({ id: 'p', year: 1976, placed_by: 'practical deployment', anchored: true, commercial_date_status: 'unknown' })
    expect(data.unplaced).toEqual([])
    expect(data.links).toEqual([])
    expect(buildModel(data).n).toBe(1)
  })

  it('allows evidenced actual use in a commercial community but still requires entry evidence', () => {
    const deployment = event('p-deployment', 'p', 'practical_deployment', 1976)
    const current = node('p', [deployment], 'practical_use', deployment.id)
    current.commercial_applicability = { status: 'applicable', rationale: 'A market may exist.' }
    const data = buildResearchDataset(records([current], [deployment]))
    expect(data.nodes).toHaveLength(1)
    current.graph_anchor!.evidence = []
    expect(buildResearchDataset(records([current], [deployment])).unplaced![0]!.placement_reason).toMatch(/evidence/)
  })

  it.each(['acceptance', 'presentation'])('places science by its selected recognition or explicit proxy event: %s', (stage) => {
    const milestone = event('s-milestone', 's', stage, 1845)
    const current = node('s', [milestone], stage === 'acceptance' ? 'recognition' : 'public_awareness', milestone.id)
    if (stage === 'presentation') delete current.lifecycle!.presentation
    const data = buildResearchDataset(records([current], [milestone]))
    expect(data.nodes[0]).toMatchObject({ kind: 'science', year: 1845, placed_by: stage, anchored: true })
    expect(data.unplaced).toEqual([])
  })

  it('does not replace an invalid invention anchor with another available dated event', () => {
    const invention = event('i-invention', 'i', 'invention', 1900)
    const sale = event('i-sale', 'i', 'first_commercial_availability', 1910)
    const data = buildResearchDataset(records([node('i', [invention, sale], 'first_commercial_availability', invention.id)], [invention, sale]))
    expect(data.nodes).toEqual([])
    expect(data.unplaced![0]!.placement_reason).toMatch(/does not establish.*entry/)
    expect(data.unplaced![0]!.anchor_event_id).toBe(invention.id)
  })

  it('requires anchor ownership and documented lifecycle membership', () => {
    const sale = event('n-sale', 'n', 'first_commercial_availability', 1910)
    const current = node('n', [sale], 'first_commercial_availability', sale.id)
    current.lifecycle!.first_commercial_availability = { status: 'unknown', event_ids: [] }
    expect(buildResearchDataset(records([current], [sale])).unplaced![0]!.placement_reason).toMatch(/documented lifecycle/)
    sale.node_id = 'another-node'
    expect(buildResearchDataset(records([current], [sale])).unplaced![0]!.placement_reason).toMatch(/does not belong/)
  })

  it('plots a selected one-sided bound under event_date without inventing the opposite limit', () => {
    const sale = event('b-sale', 'b', 'first_commercial_availability', 1910)
    sale.date = { status: 'bounded', latest: { year: 1910 }, earliest_status: 'unknown', label: 'A supported upper limit', basis: 'Only the upper limit is supported.' }
    const data = buildResearchDataset(records([node('b', [sale], 'first_commercial_availability', sale.id)], [sale]))
    expect(data.unplaced).toEqual([])
    expect(data.nodes[0]).toMatchObject({ year: 1910, end: 1910, date_kind: 'known_by', date_label: 'By 1910', entry_date: { earliest_status: 'unknown' } })
    expect(data.nodes[0]).not.toHaveProperty('start')
    expect(data.nodes[0]!.entry_date).not.toHaveProperty('earliest')
    expect(sale.date).not.toHaveProperty('earliest')
  })

  it('uses a dated commercial offer as available-by while FIRST remains explicitly unknown', () => {
    const offer = event('o-offer', 'o', 'commercial_offer', 1910)
    const current = node('o', [offer], 'commercial_availability', offer.id)
    current.lifecycle!.first_commercial_availability = { status: 'unknown', event_ids: [], rationale: 'No earlier first sale is established.', evidence: [{ source_id: 'source-1' }] }
    current.graph_anchor!.date_interpretation = 'known_by'
    const before = JSON.stringify(current)
    const data = buildResearchDataset(records([current], [offer]))
    expect(data.nodes[0]).toMatchObject({ date_kind: 'known_by', date_label: 'By 1910', end: 1910, commercial_date_status: 'unknown', entry_basis: 'commercial_availability' })
    expect(data.nodes[0]).not.toHaveProperty('start')
    expect(data.nodes[0]!.entry_date).not.toHaveProperty('earliest')
    expect(data.events![offer.id]!.date).toMatchObject({ status: 'known', earliest: { year: 1910 }, latest: { year: 1910 } })
    expect(JSON.stringify(current)).toBe(before)
    expect(nodeMarkStyle(data.nodes[0]!)).toBe(2)
  })

  it.each([
    ['known_by', 'latest', 'By approximately 325'], ['event_date', 'latest', 'By approximately 325'],
    ['known_from', 'earliest', 'Not before approximately 325'], ['event_date', 'earliest', 'Not before approximately 325'],
  ] as const)('preserves an approximate one-sided date under %s with only %s', (interpretation, supplied, label) => {
    const use = event('approx-entry', 'approx', 'practical_use', 325)
    const missing = supplied === 'latest' ? 'earliest' : 'latest'
    use.date = { status: 'approximate', precision: 'year', [supplied]: { year: 325 }, [missing + '_status']: 'unknown',
      label: 'A qualified source date, not parsed for a coordinate.', basis: 'The source supports one approximate limit.' }
    const current = node('approx', [use], 'practical_use', use.id)
    current.graph_anchor!.date_interpretation = interpretation
    const before = JSON.stringify([current, use])
    const data = buildResearchDataset(records([current], [use]))
    expect(data.unplaced).toEqual([])
    expect(data.nodes[0]).toMatchObject({ year: 325, date_label: label, date_kind: supplied === 'latest' ? 'known_by' : 'known_from',
      entry_date: { status: 'approximate', [missing + '_status']: 'unknown' } })
    expect(data.nodes[0]).not.toHaveProperty(supplied === 'latest' ? 'start' : 'end')
    expect(data.nodes[0]!.entry_date).not.toHaveProperty(missing)
    expect(JSON.stringify([current, use])).toBe(before)
    delete use.date[missing + '_status' as 'earliest_status' | 'latest_status']
    expect(buildResearchDataset(records([current], [use])).nodes).toEqual([])
  })

  it('keeps a selected approximate upper limit qualified when the source supplies a range', () => {
    const date = { status: 'approximate', earliest: { year: 300 }, latest: { year: 325 } }
    expect(deriveEntryDate(date, 'known_by')).toMatchObject({ date_kind: 'known_by',
      entry_date: { status: 'approximate', label: 'By approximately 325', earliest_status: 'unknown' }, end: 325 })
    expect(date.earliest).toEqual({ year: 300 })
  })

  it('deliberately selects later adoption instead of an earlier invention', () => {
    const events = [event('a-invention', 'a', 'invention', 1800), event('a-adoption', 'a', 'adoption', 1850)]
    const data = buildResearchDataset(records([node('a', events, 'adoption', 'a-adoption')], events))
    expect(data.nodes[0]).toMatchObject({ year: 1850, entry_basis: 'adoption', anchor_event_id: 'a-adoption' })
    expect(data.events!['a-invention']!.date_label).toBe('1800')
  })

  it('does not let scientific early observation displace later community acceptance', () => {
    const events = [event('s-observed', 's', 'observation', 1800), event('s-accepted', 's', 'acceptance', 1850)]
    const current = node('s', events, 'recognition', 's-accepted')
    expect(buildResearchDataset(records([current], events)).nodes[0]).toMatchObject({ year: 1850, entry_basis: 'recognition' })
    current.graph_anchor!.event_id = 's-observed'
    const invalid = buildResearchDataset(records([current], events))
    expect(invalid.nodes).toEqual([])
    expect(invalid.unplaced![0]!.placement_reason).toMatch(/does not establish/)
  })

  it('labels public disclosure as a justified awareness proxy, never adoption', () => {
    const disclosure = event('s-disclosed', 's', 'public_disclosure', 1900)
    const current = node('s', [disclosure], 'public_awareness', disclosure.id)
    const data = buildResearchDataset(records([current], [disclosure]))
    expect(data.nodes[0]).toMatchObject({ evidence_strength: 'awareness_proxy', entry_basis: 'public_awareness', entry_community: 'Named local specialist community', proxy_justification: expect.any(String) })
    expect(nodeMarkStyle(data.nodes[0]!)).toBe(17)
    current.graph_anchor!.entry_basis = 'adoption'
    expect(buildResearchDataset(records([current], [disclosure])).unplaced![0]!.placement_reason).toMatch(/must not be called adoption/)
    current.graph_anchor!.entry_basis = 'public_awareness'
    delete current.graph_anchor!.proxy_justification
    expect(buildResearchDataset(records([current], [disclosure])).nodes).toEqual([])
  })

  it('allows a direct scientific dataset release without promoting a generic publication', () => {
    const release = event('genome-release', 'genome', 'public_availability', 2000)
    release.date!.earliest = { year: 2000, month: 7, day: 7 }
    release.date!.latest = { year: 2000, month: 7, day: 7 }
    const current = node('genome', [release], 'public_availability', release.id)
    current.kind = 'science'
    current.commercial_applicability!.status = 'not_applicable'
    const data = buildResearchDataset(records([current], [release]))
    expect(data.nodes[0]).toMatchObject({ kind: 'science', entry_basis: 'public_availability', evidence_strength: 'direct' })
    release.event_type = 'publication'
    expect(buildResearchDataset(records([current], [release])).nodes).toEqual([])
  })

  it('uses plain date explanations and treats a lower limit as no proof of continuing use', () => {
    expect(entryReasonLabel('practical_use', 'practical_use', 'known_by', 'By 1910')).toBe('In use by 1910')
    expect(entryReasonLabel('commercial_availability')).toBe('Available for purchase')
    expect(entryReasonLabel('public_awareness', 'publication')).toBe('Publication used as an awareness estimate')
    expect(dateLimitNote('known_from')).toContain('neither continuing use nor a later endpoint')
    expect(dateLimitNote('known_by')).not.toMatch(/in use or available/)
    expect(entryReasonLabel('practical_use', 'practical_use', 'known_by', 'By 900 BCE', 'scoped_inference')).toBe('Use contextually inferred by 900 BCE')
  })

  it('keeps contextual ancient use inference and its dating horizon separate', () => {
    const use = event('ancient-use', 'ancient', 'practical_use', -900)
    use.statement = 'Practical use is contextually inferred for the named workshop community.'
    use.date!.status = 'bounded'
    use.date!.earliest = { year: -1250 }
    const current = node('ancient', [use], 'practical_use', use.id)
    current.graph_anchor!.evidence_strength = 'scoped_inference'
    current.graph_anchor!.date_interpretation = 'known_by'
    current.graph_anchor!.proxy_justification = 'The workshop assemblage supports this limited contextual use inference.'
    const data = buildResearchDataset(records([current], [use]))
    expect(data.nodes[0]).toMatchObject({ year: -900, end: -900, date_kind: 'known_by', date_label: 'By 900 BCE', evidence_strength: 'scoped_inference' })
    expect(data.nodes[0]).not.toHaveProperty('start')
    expect(data.events![use.id]!.date!.earliest).toEqual({ year: -1250 })
    expect(nodeMarkStyle(data.nodes[0]!)).toBe(10)
    use.event_type = 'archaeological_evidence'
    expect(buildResearchDataset(records([current], [use])).nodes).toEqual([])
  })

  it('retains scoped specialist use of a failed branch without implying global adoption', () => {
    const events = [event('trial-use', 'trial', 'practical_use', 1969), event('trial-ended', 'trial', 'abandonment', 1970)]
    const current = node('trial', events, 'practical_use', 'trial-use')
    current.graph_anchor!.community = 'The named expedition crew'
    current.graph_anchor!.uncertainty = 'This crew’s scoped use does not establish uptake outside the failed expedition.'
    const data = buildResearchDataset(records([current], events))
    expect(data.nodes).toHaveLength(1)
    expect(data.nodes[0]).toMatchObject({ entry_basis: 'practical_use', entry_community: 'The named expedition crew' })
    expect(data.nodes[0]!.lifecycle!.abandonment!.event_ids).toEqual(['trial-ended'])
    expect(data.links).toEqual([])
  })

  it('validates supplied date limits without fabricating missing data', () => {
    expect(deriveEntryDate({ status: 'bounded', earliest: { year: 1900 }, latest_status: 'unknown' }, 'event_date')).toMatchObject({ date_kind: 'known_from', start: 1900, entry_date: { latest_status: 'unknown', label: 'Not before 1900' } })
    expect(deriveEntryDate({ status: 'bounded', latest: { year: 1900 }, earliest_status: 'not_yet_researched' }, 'known_by')).toMatchObject({ entry_date: { earliest_status: 'not_yet_researched' } })
    for (const date of [
      { status: 'bounded', latest: { year: 1900 } },
      { status: 'known', earliest: { year: 1900 } },
      { status: 'known', earliest: { year: 0 }, latest: { year: 0 } },
      { status: 'known', precision: 'day', earliest: { year: 1900 }, latest: { year: 1900 } },
    ]) expect(deriveEntryDate(date, 'event_date')).toHaveProperty('reason')
  })

  it('keeps malformed community-entry metadata unplaced without crashing the UI projection', () => {
    for (const [field, value] of [['community', 42], ['scope', null], ['evidence', {}], ['rationale', ['text']], ['uncertainty', false]] as const) {
      const offer = event('invalid-offer', 'invalid', 'commercial_offer', 1910)
      const current = node('invalid', [offer], 'commercial_availability', offer.id)
      ;(current.graph_anchor as unknown as Record<string, unknown>)[field] = value
      const data = buildResearchDataset(records([current], [offer]))
      expect(data.nodes).toEqual([])
      expect(data.unplaced).toHaveLength(1)
      expect(validateDataset(data)).toEqual([])
    }
  })

  it('retains event references and unplaced relationships regardless of commercial display order', () => {
    const events = [event('a-demo', 'a', 'demonstration', 1900), event('a-sale', 'a', 'first_commercial_availability', 1980),
      event('b-prototype', 'b', 'prototype', 1920), event('b-sale', 'b', 'first_commercial_availability', 1950),
      event('u-invention', 'u', 'invention', 1800)]
    const source = records([node('a', events.slice(0, 2), 'first_commercial_availability', 'a-sale'),
      node('b', events.slice(2, 4), 'first_commercial_availability', 'b-sale'), node('u', events.slice(4))], events)
    source.relationships = [
      { id: 'a-to-b', from: { node_id: 'a', event_id: 'a-demo' }, to: { node_id: 'b', event_id: 'b-prototype' }, relation: 'documented-development', temporal_note: '1900 preceded 1920; market dates differ.' },
      { id: 'u-to-a', from: { node_id: 'u', event_id: 'u-invention' }, to: { node_id: 'a', event_id: 'a-demo' }, relation: 'documented-development' },
    ]
    const data = buildResearchDataset(source)
    expect(data.links).toHaveLength(2)
    expect(data.links[0]).toMatchObject({ from_event_id: 'a-demo', to_event_id: 'b-prototype', temporal_note: '1900 preceded 1920; market dates differ.' })
    expect(data.nodes[0]!.year).toBeGreaterThan(data.nodes[1]!.year)
    expect(validateDataset(data)).toEqual([])
    const model = buildModel(data)
    expect(model.edges).toHaveLength(1)
    expect(model.links).toHaveLength(2)
    expect(model.entryById.get('u')?.title).toBe('Entry u')
    data.links[0]!.from_event_id = 'b-prototype'
    expect(validateDataset(data).some((issue) => issue.message.includes('does not belong'))).toBe(true)
  })
})
