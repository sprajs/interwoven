import type { Bundle, CoreBundle, Summary, Domain, Edge, LinkLayer } from './types.ts'

/** A discovery with what the views need worked out once. */
export interface Entry extends Summary {
  index: number
  /** The domain id, such as `energy`. */
  domainId: string
  /** The subject group id, such as `power`. */
  group: string
  /** Lower-case text to search. */
  haystack: string
}

/** The compiled data, indexed for the views. */
export interface Model {
  bundle: CoreBundle
  entries: Entry[]
  byId: Map<string, Entry>
  /** Entries that have a date, in date order. */
  dated: Entry[]
  domains: Map<string, Domain>
  fieldNames: Map<string, string>
  /** Established links only. */
  links: Edge[]
  /** Links touching each discovery, whatever their status. */
  linksOf: Map<string, Edge[]>
  /** The earliest and latest dated discovery. */
  extent: [number, number]
  incoming: Map<string, Edge[]>
  outgoing: Map<string, Edge[]>
  shared: Map<string, Entry[]>
}

export function buildModel(input: CoreBundle | Bundle): Model {
  // Full bundles remain accepted for offline callers and fixture compatibility.
  const bundle: CoreBundle = 'format' in input ? input : {
    ...input, format: 1, world_person_years: input.population?.person_years.world ?? null,
    details: {}, population_file: '',
  }
  const domains = new Map(bundle.taxonomy.domains.map((d) => [d.id, d]))
  const fieldNames = new Map(bundle.taxonomy.domains.flatMap((d) => d.fields.map((f) => [f.id, f.name] as const)))
  const entries: Entry[] = bundle.discoveries.map((d, index) => {
    const domainId = d.domain.split('.')[0] ?? d.domain
    const names = [
      d.name,
      d.summary,
      ...(d.aliases ?? []),
      ...(d.people ?? []).map((p) => bundle.people[p.person]?.name),
      ...(d.places ?? []).map((p) => bundle.places[p.place]?.name),
      ...(d.organizations ?? []).map((o) => bundle.organizations[o.organization]?.name),
      fieldNames.get(d.domain),
      d.concept && bundle.concepts[d.concept]?.name,
    ]
    return { ...d, index, domainId, group: domains.get(domainId)?.group ?? 'society', haystack: names.filter(Boolean).join(' ').toLowerCase() }
  })
  const byId = new Map(entries.map((e) => [e.id, e]))
  const dated = entries.filter((e) => e.t !== undefined).sort((a, b) => a.t! - b.t!)
  const linksOf = new Map<string, Edge[]>()
  const incoming = new Map<string, Edge[]>()
  const outgoing = new Map<string, Edge[]>()
  const add = <T>(map: Map<string, T[]>, key: string, value: T) => {
    const list = map.get(key)
    if (list) list.push(value)
    else map.set(key, [value])
  }
  const shared = new Map<string, Entry[]>()
  for (const entry of entries) {
    if (entry.concept) add(shared, `concept:${entry.concept}`, entry)
    for (const id of new Set((entry.people ?? []).map(p => p.person))) add(shared, `person:${id}`, entry)
    for (const id of new Set((entry.places ?? []).map(p => p.place))) add(shared, `place:${id}`, entry)
    for (const id of new Set((entry.organizations ?? []).map(p => p.organization))) add(shared, `organization:${id}`, entry)
    for (const id of new Set(entry.societies ?? [])) add(shared, `society:${id}`, entry)
  }
  for (const values of shared.values()) values.sort((a, b) => (a.t ?? 0) - (b.t ?? 0))
  for (const link of bundle.links) {
    add(incoming, link.to, link)
    add(outgoing, link.from, link)
    for (const id of [link.from, link.to]) {
      const list = linksOf.get(id)
      if (list) list.push(link)
      else linksOf.set(id, [link])
    }
  }
  return {
    bundle,
    entries,
    byId,
    dated,
    domains,
    fieldNames,
    links: bundle.links.filter((l) => l.status === 'established'),
    linksOf, incoming, outgoing, shared,
    extent: [dated[0]?.t ?? -10000, dated[dated.length - 1]?.t ?? 2000],
  }
}

/** Other discoveries that share something with this one, without any stated link. */
export interface Shared {
  what: 'place' | 'person' | 'organization' | 'society' | 'concept'
  id: string
  name: string
  entries: Entry[]
}

export function sharedWith(model: Model, entry: Entry): Shared[] {
  const { bundle } = model
  const out: Shared[] = []
  const collect = (what: Shared['what'], id: string, name: string | undefined) => {
    const others = (model.shared.get(`${what}:${id}`) ?? []).filter(e => e.id !== entry.id)
    if (others.length) out.push({what, id, name: name ?? id, entries: others})
  }
  if (entry.concept) collect('concept', entry.concept, bundle.concepts[entry.concept]?.name)
  for (const p of entry.people ?? []) collect('person', p.person, bundle.people[p.person]?.name)
  for (const o of entry.organizations ?? []) collect('organization', o.organization, bundle.organizations[o.organization]?.name)
  for (const id of entry.societies ?? []) collect('society', id, bundle.societies[id]?.name)
  for (const p of entry.places ?? []) {
    const place = bundle.places[p.place]
    if (place && ['site', 'settlement'].includes(place.kind)) collect('place', p.place, place.name)
  }
  return out
}

export const LAYERS: { id: LinkLayer; name: string; hint: string }[] = [
  { id: 'dependence', name: 'Built on', hint: 'One discovery developed from, adapted or needed another' },
  { id: 'transmission', name: 'Passed on', hint: 'Knowledge actually travelled from one to the other' },
  { id: 'parallel', name: 'Independent', hint: 'The same thing reached separately' },
  { id: 'affinity', name: 'Related', hint: 'Same principle, same family, or parts of one arrangement' },
]

/** Breadth-first traversal; shared ancestors and cycles are visited once. */
export function walk(model: Model, start: string, options: {
  direction?: 'incoming' | 'outgoing'; depth?: number; layers?: ReadonlySet<LinkLayer>; status?: Edge['status']
} = {}): {entry: Entry; depth: number}[] {
  const depth = options.depth ?? 3
  if (!Number.isInteger(depth) || depth < 0 || depth > 100) throw new Error('Depth must be an integer from 0 to 100')
  if (!model.byId.has(start)) throw new Error(`Unknown discovery: ${start}`)
  const direction = options.direction ?? 'incoming'
  const index = direction === 'incoming' ? model.incoming : model.outgoing
  const layers = options.layers ?? new Set<LinkLayer>(['dependence', 'transmission'])
  const status = options.status ?? 'established'
  const seen = new Set([start]), out: {entry: Entry; depth: number}[] = []
  let frontier = [start]
  for (let distance = 1; distance <= depth && frontier.length; distance++) {
    const next: string[] = []
    for (const id of frontier) for (const link of index.get(id) ?? []) {
      if (link.status !== status || !layers.has(link.layer)) continue
      const other = direction === 'incoming' ? link.from : link.to
      const entry = model.byId.get(other)
      if (!entry || seen.has(other)) continue
      seen.add(other); next.push(other); out.push({entry, depth: distance})
    }
    frontier = next
  }
  return out
}
