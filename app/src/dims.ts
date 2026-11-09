import type { Entry, Model } from './data/model.ts'
import { NEUTRAL, SERIES } from './theme.ts'

/** A way of sorting discoveries into a few named, coloured categories. */
export type DimId = 'subject' | 'region' | 'kind' | 'origin'

export interface Category {
  id: string
  name: string
  color: string
  hint?: string
}

export interface Dimension {
  id: DimId
  name: string
  categories: Category[]
  /** The category a discovery falls in. */
  of(entry: Entry): string
}

const [blue, vermilion, ochre, teal, plum, green] = SERIES

const SUBJECT_COLORS: Record<string, string> = {
  sustenance: green,
  information: blue,
  making: vermilion,
  power: ochre,
  understanding: teal,
  society: plum,
}

export function dimensions(model: Model): Record<DimId, Dimension> {
  const { taxonomy, vocab } = model.bundle
  return {
    subject: {
      id: 'subject',
      name: 'Subject',
      categories: taxonomy.groups.map((g) => ({
        id: g.id,
        name: g.name,
        color: SUBJECT_COLORS[g.id] ?? NEUTRAL,
        hint: taxonomy.domains.filter((d) => d.group === g.id).map((d) => d.name).join(', '),
      })),
      of: (e) => e.group,
    },
    region: {
      id: 'region',
      name: 'Region',
      categories: [
        { id: 'europe', name: 'Europe', color: blue },
        { id: 'asia', name: 'Asia', color: vermilion },
        { id: 'africa', name: 'Africa', color: ochre },
        { id: 'north_america', name: 'North America', color: teal },
        { id: 'south_america', name: 'South America', color: plum },
        { id: 'oceania', name: 'Oceania', color: green },
        { id: 'none', name: 'No place yet', color: NEUTRAL },
      ],
      of: (e) => e.at?.region ?? 'none',
    },
    kind: {
      id: 'kind',
      name: 'Kind',
      categories: [
        { id: 'technology', name: 'Technology', color: blue, hint: vocab.kind?.technology },
        { id: 'science', name: 'Science', color: vermilion, hint: vocab.kind?.science },
        { id: 'mathematics', name: 'Mathematics', color: ochre, hint: vocab.kind?.mathematics },
        { id: 'practice', name: 'Practice', color: teal, hint: vocab.kind?.practice },
      ],
      of: (e) => e.kind,
    },
    origin: {
      id: 'origin',
      name: 'Origin',
      categories: [
        { id: 'first_known', name: 'First known', color: blue, hint: vocab.origin?.first_known },
        { id: 'independent', name: 'Independent', color: vermilion, hint: vocab.origin?.independent },
        { id: 'derived', name: 'Derived', color: ochre, hint: vocab.origin?.derived },
        { id: 'revival', name: 'Revival', color: teal, hint: vocab.origin?.revival },
        { id: 'unknown', name: 'Unsettled', color: plum, hint: vocab.origin?.unknown },
        { id: 'none', name: 'Not yet assessed', color: NEUTRAL, hint: 'Nobody has researched this yet.' },
      ],
      of: (e) => e.origin ?? 'none',
    },
  }
}

export const DIM_ORDER: DimId[] = ['subject', 'region', 'kind', 'origin']
