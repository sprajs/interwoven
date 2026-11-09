/** Colours and type for everything drawn on a canvas. `styles.css` holds the same values for the interface. */

export const PAPER = '#f6f2e9'
export const SHEET = '#fcfaf5'
export const INK = '#1f1b16'
export const INK_2 = '#4a4238'
export const INK_3 = '#6b6254'
export const RULE = 'rgba(31, 27, 22, 0.20)'
export const RULE_SOFT = 'rgba(31, 27, 22, 0.09)'
export const TINT = 'rgba(31, 27, 22, 0.045)'
export const LAND = '#e6dfd0'
export const LAND_EDGE = '#cfc6b3'

/** Categorical colours, always assigned in this order and never recycled. */
export const SERIES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948'] as const
export const NEUTRAL = '#a8a091'

export const SERIF = "'Source Serif', Georgia, 'Times New Roman', serif"

export function font(size: number, weight = 400, italic = false): string {
  return `${italic ? 'italic ' : ''}${weight} ${size}px ${SERIF}`
}

/** A colour with its alpha set, for fades. Takes #rrggbb. */
export function alpha(hex: string, a: number): string {
  const n = parseInt(hex.slice(1), 16)
  return `rgba(${n >> 16}, ${(n >> 8) & 255}, ${n & 255}, ${a})`
}
