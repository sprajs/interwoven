/**
 * The design system's numbers, in one place for the canvas. `src/styles.css` holds the same
 * values for the interface, and `design.test.ts` fails if the two disagree.
 * `DESIGN.md` says where each value comes from.
 */

/** The baseline unit. Every leading and space is a whole multiple of this, or half of it. */
export const UNIT = 6

/** Type sizes step by 6:5 from a 17px text size, rounded to whole pixels. */
export const TYPE = {
  note: { size: 14, line: 18 },
  body: { size: 17, line: 24 },
  lead: { size: 20, line: 24 },
  head: { size: 24, line: 30 },
  title: { size: 29, line: 36 },
} as const
export type TypeStep = keyof typeof TYPE

/** Text inks. The numbers are the WCAG contrast each must keep on the paper. */
export const INK = { primary: '#26211c', secondary: '#4e463c', muted: '#6a6156' } as const
export const PAPER = '#f4efe6'
export const SHEET = '#f8f4ec'

/** Lines. A rule structures the page, and a fine rule divides rows within it. */
export const LINE = { hair: 0.75, rule: 1, stroke: 1.5 } as const
export const RULE_ALPHA = { rule: 0.22, soft: 0.11, frame: 0.55 } as const

/** EB Garamond's x-height, read from the font. Marks are sized from it. */
export const X_HEIGHT = 0.4

/** How entries are ranked on the chart: size for the first three tiers, then ink for the last. */
export const TIER_TYPE: readonly TypeStep[] = ['lead', 'body', 'note', 'note']
/** Rows are too close for the largest size, as Priestley's chart kept its names small. */
export const ROW_TIER_TYPE: readonly TypeStep[] = ['body', 'note', 'note', 'note']
export const TIER_INK: readonly (keyof typeof INK)[] = ['primary', 'primary', 'primary', 'secondary']

/** A mark's radius, so that it stands as tall as the lowercase of the name beside it. */
export const TIER_RADIUS: readonly number[] = TIER_TYPE.map((step) => (TYPE[step].size * X_HEIGHT) / 2)

/** The cuts the canvas needs loaded before it can measure text. */
export const FONT_FACES = ['400 14px "EB Garamond Variable"', 'italic 400 14px "EB Garamond Variable"']

/** Page geometry, all multiples of the unit. */
export const LAYOUT = {
  header: 9 * UNIT,
  margin: 9 * UNIT,
  marginCompact: 3 * UNIT,
  /** 53 characters of body text inside its padding. */
  sheet: 64 * UNIT,
  sheetPad: 4 * UNIT,
  labels: 46 * UNIT,
  /** 48 characters of note text, the range for text in columns. */
  column: 42 * UNIT,
  /** The ruled top of the chart, and how far below the rule its contents stay. */
  frameTop: 14 * UNIT,
  frameTopCompact: 15 * UNIT,
  frameBottom: 12 * UNIT,
  framePad: 3 * UNIT,
  overview: 4 * UNIT,
  overviewBottom: 2 * UNIT,
  bar: 4 * UNIT,
  barBottom: 7 * UNIT,
} as const

/** Screen widths at which the layout changes. */
export const BREAK = { compact: 760, wide: 1000, corner: 1180 } as const

/** A hex colour as 0 to 1 channels, for the shaders. */
export function hexUnit(hex: string): [number, number, number] {
  return [1, 3, 5].map((at) => parseInt(hex.slice(at, at + 2), 16) / 255) as [number, number, number]
}

export function hexRgb(hex: string): string {
  const v = parseInt(hex.slice(1), 16)
  return `${(v >> 16) & 255},${(v >> 8) & 255},${v & 255}`
}

/** Relative luminance and contrast, as WCAG defines them. */
export function contrast(a: string, b: string): number {
  const luminance = (hex: string) => {
    const v = parseInt(hex.slice(1), 16)
    const channel = (c: number) => {
      const s = c / 255
      return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4
    }
    return 0.2126 * channel((v >> 16) & 255) + 0.7152 * channel((v >> 8) & 255) + 0.0722 * channel(v & 255)
  }
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x) as [number, number]
  return (hi + 0.05) / (lo + 0.05)
}
