import type { Bundle, Discovery, Domain, Link, LinkLayer } from './types.ts'

/** A discovery with what the views need worked out once. */
export interface Entry extends Discovery {
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
  bundle: Bundle
  entries: Entry[]
  byId: Map<string, Entry>
  /** Entries that have a date, in date order. */
  dated: Entry[]
  domains: Map<string, Domain>
  fieldNames: Map<string, string>
  /** Established links only. */
  links: Link[]
  /** Links touching each discovery, whatever their status. */
  linksOf: Map<string, Link[]>
  /** The earliest and latest dated discovery. */
  extent: [number, number]
}

export async function loadModel(): Promise<Model> {
  const response = await fetch(`${import.meta.env.BASE_URL}data/atlas.json`)
  if (!response.ok) throw new Error(`The data file could not be read (${response.status}). Run python3 tools/build.py.`)
  return buildModel((await response.json()) as Bundle)
}

export function buildModel(bundle: Bundle): Model {
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
  const linksOf = new Map<string, Link[]>()
  for (const link of bundle.links) {
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
    linksOf,
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
  const collect = (what: Shared['what'], id: string, name: string | undefined, has: (e: Entry) => boolean) => {
    const others = model.entries.filter((e) => e.id !== entry.id && has(e))
    if (others.length) out.push({ what, id, name: name ?? id, entries: others.sort((a, b) => (a.t ?? 0) - (b.t ?? 0)) })
  }
  if (entry.concept) collect('concept', entry.concept, bundle.concepts[entry.concept]?.name, (e) => e.concept === entry.concept)
  for (const p of entry.people ?? []) collect('person', p.person, bundle.people[p.person]?.name, (e) => !!e.people?.some((x) => x.person === p.person))
  for (const o of entry.organizations ?? [])
    collect('organization', o.organization, bundle.organizations[o.organization]?.name, (e) => !!e.organizations?.some((x) => x.organization === o.organization))
  for (const p of entry.places ?? []) {
    const place = bundle.places[p.place]
    // Sharing a country says little. Sharing a workshop or a town says a lot.
    if (!place || !['site', 'settlement'].includes(place.kind)) continue
    collect('place', p.place, place.name, (e) => !!e.places?.some((x) => x.place === p.place))
  }
  return out
}

export const LAYERS: { id: LinkLayer; name: string; hint: string }[] = [
  { id: 'dependence', name: 'Built on', hint: 'One discovery developed from, adapted or needed another' },
  { id: 'transmission', name: 'Passed on', hint: 'Knowledge actually travelled from one to the other' },
  { id: 'parallel', name: 'Independent', hint: 'The same thing reached separately' },
  { id: 'affinity', name: 'Related', hint: 'Same principle, same family, or parts of one arrangement' },
]
