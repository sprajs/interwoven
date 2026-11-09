import { describe, expect, it } from 'vitest'
import { buildModel, sharedWith } from './model.ts'
import type { Bundle, Discovery, Link } from './types.ts'

/** A compiled discovery with only what the model reads. */
function discovery(id: string, t: number | undefined, extra: Partial<Discovery> = {}): Discovery {
  return {
    id,
    name: id,
    description: `The ${id}.`,
    kind: 'technology',
    domain: 'energy.steam',
    tier: 1,
    events: [],
    earliest_record: { event: t === undefined ? null : 'made' },
    research: { status: 'draft', basis: {} },
    filled: 0,
    ...(t === undefined ? {} : { t }),
    ...extra,
  }
}

const place = (id: string, name: string, kind: string, within: string | null) => ({ id, name, kind, lat: 0, lon: 0, country: 'GB', region: 'europe' as const, within })

const link: Link = { from: 'pump', to: 'engine', type: 'builds_on', layer: 'dependence', status: 'established', statement: 'The engine built on the pump.' }

/** Three discoveries: two share a person, a town and a country; the third shares only the country and has no date. */
const bundle = {
  taxonomy: {
    groups: [{ id: 'power', name: 'Power' }],
    domains: [{ id: 'energy', name: 'Energy', group: 'power', description: '', fields: [{ id: 'energy.steam', name: 'Steam', description: '' }] }],
  },
  vocab: {},
  discoveries: [
    discovery('engine', 1776, {
      people: [{ person: 'james-watt', role: 'originator' }],
      places: [{ place: 'glasgow' }, { place: 'scotland' }],
    }),
    discovery('pump', 1712, {
      people: [{ person: 'james-watt', role: 'contributor' }],
      places: [{ place: 'glasgow' }, { place: 'scotland' }],
    }),
    discovery('kettle', undefined, { places: [{ place: 'scotland' }] }),
  ],
  links: [link],
  places: {
    scotland: place('scotland', 'Scotland', 'country', null),
    glasgow: place('glasgow', 'Glasgow', 'settlement', 'scotland'),
  },
  people: { 'james-watt': { id: 'james-watt', name: 'James Watt' } },
  organizations: {},
  societies: {},
  concepts: {},
  sources: {},
  population: null,
} as unknown as Bundle

describe('buildModel', () => {
  const model = buildModel(bundle)

  /** Timelines read `dated`, so it holds only dated entries, earliest first. */
  it('orders dated discoveries by date and leaves out undated ones', () => {
    expect(model.dated.map((e) => e.id)).toEqual(['pump', 'engine'])
    expect(model.extent).toEqual([1712, 1776])
  })

  /** A link shows on the detail of both discoveries it joins. */
  it('indexes each link under both ends', () => {
    expect(model.linksOf.get('engine')).toEqual([link])
    expect(model.linksOf.get('pump')).toEqual([link])
    expect(model.linksOf.get('kettle')).toBeUndefined()
  })

  /** Search finds a discovery by the people and places attached to it, case-insensitively. */
  it('builds a search haystack from names of related things', () => {
    const engine = model.byId.get('engine')!
    expect(engine.haystack).toContain('james watt')
    expect(engine.haystack).toContain('glasgow')
    expect(engine.haystack).toContain('steam')
    expect(engine.group).toBe('power')
  })
})

describe('sharedWith', () => {
  const model = buildModel(bundle)
  const shared = sharedWith(model, model.byId.get('engine')!)

  /** Sharing a person or a town is a meaningful connection worth showing. */
  it('reports a shared person and a shared settlement', () => {
    const person = shared.find((s) => s.what === 'person')
    expect(person?.id).toBe('james-watt')
    expect(person?.name).toBe('James Watt')
    expect(person?.entries.map((e) => e.id)).toEqual(['pump'])

    const town = shared.find((s) => s.what === 'place' && s.id === 'glasgow')
    expect(town?.entries.map((e) => e.id)).toEqual(['pump'])
  })

  /** Sharing only a country says little, so it is not reported. */
  it('does not report a shared country', () => {
    expect(shared.some((s) => s.id === 'scotland')).toBe(false)
  })
})

describe('directed graph traversal', () => {
  it('indexes directions without treating candidate links as established', async () => {
    const {walk} = await import('./model.ts')
    const cycle = {...link, from:'engine', to:'pump'}
    const candidate = {...link, from:'kettle', to:'engine', status:'candidate' as const}
    const model = buildModel({...bundle, links:[link,cycle,candidate]})
    expect(model.incoming.get('engine')).toEqual([link,candidate])
    expect(walk(model,'engine').map(r=>[r.entry.id,r.depth])).toEqual([['pump',1]])
    expect(walk(model,'engine',{status:'candidate'}).map(r=>r.entry.id)).toEqual(['kettle'])
    expect(walk(model,'engine',{depth:0})).toEqual([])
    expect(walk(model,'engine',{layers:new Set(['affinity'])})).toEqual([])
    expect(() => walk(model,'missing')).toThrow('Unknown')
    expect(() => walk(model,'engine',{depth:-1})).toThrow('Depth')
  })
  it('visits a shared ancestor only once and reports shortest depth', async () => {
    const {walk} = await import('./model.ts')
    const m = buildModel({...bundle, discoveries:[...bundle.discoveries,discovery('fourth',1900)], links:[link,{...link,from:'pump',to:'kettle'},{...link,from:'engine',to:'fourth'},{...link,from:'kettle',to:'fourth'}]})
    expect(walk(m,'fourth').map(r=>[r.entry.id,r.depth])).toEqual([['engine',1],['kettle',1],['pump',2]])
    expect(walk(m,'pump',{direction:'outgoing'}).map(r=>r.entry.id)).toEqual(['engine','kettle','fourth'])
  })
})
