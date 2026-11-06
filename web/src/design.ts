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
export const INK = { primary: '#1f1b16', secondary: '#443c32', muted: '#5c5347' } as const
export const PAPER = '#f4efe6'
export const SHEET = '#fbf8f1'
/** The ruler's light cells. Its dark cells are the primary ink. */
export const RULER_LIGHT = '#e4dccb'
/** The ruler's other cell: enough to mark the step, without a hard edge across the top of the page. */
export const RULER_DARK = '#d2c8b4'

/** Lines. A rule structures the page, and a fine rule divides rows within it. */
export const LINE = { hair: 0.75, rule: 1, stroke: 1.5 } as const
export const RULE_ALPHA = { rule: 0.22, soft: 0.11, frame: 0.55, band: 0.045 } as const

/** Source Serif 4's measured x-height and average character width, in em. */
export const X_HEIGHT = 0.475
export const CHAR_WIDTH = 0.454

/** How entries are ranked on the chart: a larger, heavier name for the key discoveries. */
export const NAME_STYLE: readonly { step: TypeStep; weight: number }[] = [
  { step: 'body', weight: 600 },
  { step: 'note', weight: 600 },
  { step: 'note', weight: 500 },
  { step: 'note', weight: 500 },
]
/** A mark's radius by rank, all large enough to see and pick out at a glance. */
export const MARK_RADIUS: readonly number[] = [5.5, 4.5, 4, 3.5]

/** A named entry is a flag: a solid pole at its date, then its date, then its name. */
export const BOX = { edge: 3, pad: UNIT, border: 1, chipAlpha: 0.14, borderAlpha: 0.6, lift: 3 } as const
/** Screen area allowed per name. Zooming puts fewer entries in view, so lower ranks earn names. */
export const NAME_AREA = 230 * 30 * 5

export const FONT_FAMILY = '"Source Serif", Georgia, "Times New Roman", serif'
/** The cuts the canvas needs loaded before it can measure text. */
export const FONT_FACES = ['500 14px "Source Serif"', '600 17px "Source Serif"', 'italic 500 14px "Source Serif"', 'italic 600 17px "Source Serif"']

/** Page geometry, all multiples of the unit. */
export const LAYOUT = {
  header: 9 * UNIT,
  margin: 9 * UNIT,
  marginCompact: 3 * UNIT,
  /** 49 characters of body text inside its padding. */
  sheet: 70 * UNIT,
  sheetPad: 4 * UNIT,
  labels: 46 * UNIT,
  /** 42 characters of note text, the range for text in columns. */
  column: 45 * UNIT,
  /** The top of the chart, under the ruler, and how far below it its contents stay. */
  frameTop: 16 * UNIT,
  frameTopCompact: 19 * UNIT,
  ruler: 5 * UNIT,
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
