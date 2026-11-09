/** The shape of `public/data/atlas.json`, which `tools/build.py` compiles from `data/`. */

export type Basis = 'sourced' | 'recalled' | 'reviewed' | 'unknown' | 'not_applicable'
export type Kind = 'science' | 'mathematics' | 'technology' | 'practice'
export type Origin = 'first_known' | 'independent' | 'derived' | 'revival' | 'unknown'
export type Region = 'africa' | 'asia' | 'europe' | 'north_america' | 'south_america' | 'oceania'
export type LinkLayer = 'dependence' | 'transmission' | 'parallel' | 'affinity'

export interface Evidence {
  source: string
  locator?: string
  supports?: string
}

export interface DateInfo {
  /** Position in time: the latest the event can have happened, in years. 1 BCE is 0. */
  t: number
  /** The earliest it can have happened, when the evidence gives one. */
  t0?: number
  label: string
  status: 'known' | 'approximate' | 'bounded'
  precision: string
}

export interface EventRecord extends DateInfo {
  id: string
  type: string
  basis: string
  statement: string
  evidence: Evidence[]
  places?: string[]
  place_note?: string
  scope?: string
  applications?: string[]
  population?: string
  market?: string
  caveats?: string
  type_provisional?: boolean
}

export interface Discovery {
  id: string
  name: string
  aliases?: string[]
  summary?: string
  description: string
  kind: Kind
  domain: string
  fields?: string[]
  tier: number
  tier_reason?: string
  advance?: string[]
  scale?: string
  origin?: Origin
  concept?: string
  prompted_by?: string[]
  why?: string
  limit_removed?: string[]
  setting?: string[]
  funding?: string[]
  places?: { place: string; role?: string; note?: string }[]
  people?: { person: string; role: string; note?: string }[]
  organizations?: { organization: string; role: string; note?: string }[]
  societies?: string[]
  known_from?: string[]
  reception?: string
  fate?: string
  end_reason?: string[]
  market?: { status: string; note?: string }
  measures?: { quantity: string; value: number | string; unit?: string }[]
  witnesses?: { event: string; limitation: string }[]
  caveats?: string
  events: EventRecord[]
  earliest_record: { event: string | null; rationale?: string }
  community_entry?: { event: string; community?: string; basis?: string; strength?: string; rationale?: string; proxy_reason?: string; caveats?: string }
  /** Position in time, from the earliest record. Absent when no date is established. */
  t?: number
  date?: DateInfo
  entered?: { t: number; label: string }
  /** Where to draw it: its most precise known place. */
  at?: { place: string; lat: number; lon: number; kind: string; region: Region }
  research: {
    status: string
    basis: Record<string, Basis>
    unresolved?: { about: string; note: string; evidence?: Evidence[] }[]
    missing_prerequisites?: string[]
    note?: string
  }
  /** How many facets have a value. */
  filled: number
}

export interface Link {
  /** The earlier or giving discovery. */
  from: string
  /** The later or receiving discovery, which holds the link. */
  to: string
  type: string
  layer: LinkLayer
  status: 'established' | 'candidate' | 'insufficient'
  statement: string
  from_event?: string
  to_event?: string
  scope?: string
  contribution?: string[]
  carrier?: string[]
  influence?: string
  confidence?: string
  alternatives?: string
  caveats?: string
  timing?: string
  finding?: string
  evidence?: Evidence[]
}

export interface Place {
  id: string
  name: string
  kind: string
  lat: number
  lon: number
  country: string | null
  region: Region
  within: string | null
  note?: string | null
}

export interface Named {
  id: string
  name: string
  [key: string]: unknown
}

export interface Field {
  id: string
  name: string
  description: string
}

export interface Domain {
  id: string
  name: string
  group: string
  description: string
  fields: Field[]
}

export interface Bundle {
  counts: { discoveries: number; events: number; links: number; sources: number; leads: number; facets: number }
  facets: string[]
  vocab: Record<string, Record<string, string>>
  link_layers: Record<LinkLayer, string[]>
  taxonomy: { groups: { id: string; name: string }[]; domains: Domain[] }
  discoveries: Discovery[]
  links: Link[]
  places: Record<string, Place>
  people: Record<string, Named & { born?: number; died?: number; occupations?: string[] }>
  organizations: Record<string, Named & { kind: string }>
  societies: Record<string, Named & { kind: string; from?: number; to?: number }>
  concepts: Record<string, Named & { summary?: string }>
  sources: Record<string, { title: string; authors: string[]; year?: number; url?: string }>
  population: {
    sources: { covers: string; title: string; authors: string[]; year: number; citation: string; url: string; licence?: string; note: string }[]
    method: string
    series: Record<string, [number, number][]>
    /** Person-years lived since the first estimate, as [year, total] pairs. */
    person_years: Record<string, [number, number][]>
  } | null
}
