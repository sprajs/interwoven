import { describe, expect, it } from 'vitest'
import { buildModel } from '../src/data/model.ts'
import { validateDataset } from '../src/data/validate.ts'
import { buildResearchDataset, type ResearchEvent, type ResearchNode, type ResearchRecords } from './import-research.ts'

function event(id: string, nodeId: string, type: string, year: number): ResearchEvent {
  return { id, node_id: nodeId, event_type: type,
    date: { status: 'known', earliest: { year }, latest: { year }, label: String(year), basis: 'Synthetic source date.' },
    statement: 'A scoped synthetic historical event.', evidence: [{ source_id: 'source-1' }] }
}

function node(id: string, events: ResearchEvent[], policy = 'first_commercial_availability', anchorId?: string): ResearchNode {
  return { id, label: `Entry ${id}`, kind: policy === 'scientific_event' ? 'science' : 'technology',
    configuration: 'Synthetic configuration.', labels: ['fixture'], event_ids: events.map((entry) => entry.id),
    graph_anchor: { status: anchorId ? 'selected' : 'not_yet_researched', policy, event_id: anchorId, rationale: 'Fixture anchor decision.' },
    lifecycle: Object.fromEntries(events.map((entry) => [entry.event_type, { status: 'documented', event_ids: [entry.id] }])),
    commercial_applicability: { status: policy === 'scientific_event' ? 'not_applicable' : policy === 'practical_deployment' ? 'nonmarket' : 'applicable',
      rationale: 'Explicit applicability decision.', evidence: [{ source_id: 'source-1' }] },
    provenance: { source_ids: ['source-1'] }, review: { historical_claim: 'accepted', lifecycle_classification: 'needs_review' } }
}

function records(nodes: ResearchNode[], events: ResearchEvent[]): ResearchRecords {
  return { nodes, events, relationships: [], sources: [{ id: 'source-1', title: 'Synthetic inspected source', url: 'https://example.org/source' }] }
}

describe('research importer placement', () => {
  it('keeps unresolved technology accessible without using its dated invention', () => {
    const invention = event('u-invention', 'u', 'invention', 1850)
    const data = buildResearchDataset(records([node('u', [invention])], [invention]))
    expect(data.nodes).toEqual([])
    expect(data.unplaced).toHaveLength(1)
    expect(data.unplaced![0]).toMatchObject({ id: 'u', anchor_status: 'not_yet_researched', placement_reason: 'Anchor not yet researched.', sources: ['source-1'] })
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
    const current = node('p', [deployment], 'practical_deployment', deployment.id)
    current.lifecycle!.first_commercial_availability = { status: 'unknown', event_ids: [] }
    const data = buildResearchDataset(records([current], [deployment]))
    expect(data.nodes[0]).toMatchObject({ id: 'p', year: 1976, placed_by: 'practical deployment', anchored: true, commercial_date_status: 'unknown' })
    expect(data.unplaced).toEqual([])
    expect(data.links).toEqual([])
    expect(buildModel(data).n).toBe(1)
  })

  it('requires evidence and a nonmarket decision for deployment placement', () => {
    const deployment = event('p-deployment', 'p', 'practical_deployment', 1976)
    const current = node('p', [deployment], 'practical_deployment', deployment.id)
    current.commercial_applicability = { status: 'applicable', rationale: 'A market may exist.' }
    const data = buildResearchDataset(records([current], [deployment]))
    expect(data.nodes).toEqual([])
    expect(data.unplaced![0]!.placement_reason).toMatch(/justified nonmarket/)
  })

  it.each(['observation', 'presentation'])('places science by its selected %s milestone', (stage) => {
    const milestone = event('s-milestone', 's', stage, 1845)
    const current = node('s', [milestone], 'scientific_event', milestone.id)
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
    expect(data.unplaced![0]!.placement_reason).toMatch(/does not match.*policy/)
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

  it('retains a selected open date bound without inventing the opposite limit', () => {
    const sale = event('b-sale', 'b', 'first_commercial_availability', 1910)
    sale.date = { status: 'bounded', latest: { year: 1910 }, earliest_status: 'unknown', label: 'By 1910', basis: 'Only the upper limit is supported.' }
    const data = buildResearchDataset(records([node('b', [sale], 'first_commercial_availability', sale.id)], [sale]))
    expect(data.nodes).toEqual([])
    expect(data.unplaced![0]).toMatchObject({ anchor_status: 'selected', placement_reason: expect.stringMatching(/open date bound/) })
    expect(data.unplaced![0]).not.toHaveProperty('start')
    expect(sale.date).not.toHaveProperty('earliest')
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
