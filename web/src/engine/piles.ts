import { TYPE } from '../design.ts'

/**
 * The density view: every entry is one mark, kept at its true date and stacked on the marks
 * it would otherwise cover. Where entries gather the pile is tall, so the shape is the record
 * itself, with no smoothing, and every part of it can be counted and pointed at.
 */
export type PileForm = 'subject' | 'together'

/** Across and up, in CSS pixels. The largest mark is 11px wide, and one pixel keeps them apart. */
export const PILE_PITCH = 12
/** Larger marks to try for one shared pile, largest first, so that it can fill the page. */
const TOGETHER_PITCHES = [24, 21, 18, 15, PILE_PITCH]
/** How much of the page a shared pile may fill. */
const TOGETHER_FILL = 0.84
/** Past this many levels, a stack stops growing: only a huge dataset gets there. */
const MAX_LEVELS = 400
/** Clear space around a family's ground line, in CSS pixels. */
export const GROUND = 10
/** How far a family's first mark sits below its rule, once its heading has room. */
const HEADING = TYPE.note.line * 1.5

export interface PileRow {
  /** Where the family's heading is measured from, 0 to 1 down the sheet. */
  top: number
  /** Where its marks are centred at the bottom of a pile, 0 to 1 down the sheet. */
  bottom: number
  /** Where the feet of those marks rest. */
  base: number
  /** The top of its row, past which nothing of the family is drawn. */
  ceiling: number
  count: number
}

export interface PileLayout {
  y: Float32Array
  /** One for each family, top to bottom. Empty when the families share one pile. */
  rows: PileRow[]
  /** The tallest stack, in marks. */
  peak: number
  /** How much larger than usual to draw the marks. */
  markScale: number
  /** The area one entry takes up in a pile, in square CSS pixels. */
  markArea: number
}

/** The curve behind the piles is stored at this many steps across the sheet. */
export const CURVE_BINS = 4096
/** How widely it smooths, in CSS pixels, so it stays one kind of shape at any zoom. */
export const CURVE_SIGMA = 20

/**
 * A kernel density estimate of where entries fall across the sheet, as entries per unit of
 * position, so that its area is the number of entries. `sigma` is in the same units.
 */
export function smoothDensity(positions: ArrayLike<number>, members: readonly number[], sigma: number, bins = CURVE_BINS): Float32Array {
  const counts = new Float32Array(bins)
  for (const i of members) counts[Math.max(0, Math.min(bins - 1, Math.floor(positions[i]! * bins)))]! += 1
  const out = new Float32Array(bins)
  const spread = Math.max(1, sigma * bins)
  const reach = Math.ceil(spread * 3)
  const kernel = new Float32Array(2 * reach + 1)
  let total = 0
  for (let k = -reach; k <= reach; k++) total += kernel[k + reach] = Math.exp(-(k * k) / (2 * spread * spread))
  for (let b = 0; b < bins; b++) {
    const count = counts[b]!
    if (count === 0) continue
    const start = Math.max(0, b - reach)
    const end = Math.min(bins - 1, b + reach)
    for (let c = start; c <= end; c++) out[c]! += (count * kernel[c - b + reach]! * bins) / total
  }
  return out
}

/**
 * The lowest level each mark can take without covering another, placing them in `order`.
 * A level holds at most one mark per pitch-wide cell, since any two in one cell would touch.
 */
export function stackLevels(xs: ArrayLike<number>, order: readonly number[], pitch = PILE_PITCH, out = new Int32Array(xs.length)): Int32Array {
  const levels: Map<number, number>[] = []
  for (const i of order) {
    const x = xs[i]!
    const cell = Math.floor(x / pitch)
    let level = 0
    for (; level < MAX_LEVELS - 1; level++) {
      const taken = levels[level]
      if (!taken) break
      let clear = true
      for (let c = cell - 1; c <= cell + 1 && clear; c++) {
        const other = taken.get(c)
        if (other !== undefined && Math.abs(other - x) < pitch) clear = false
      }
      if (clear) break
    }
    ;(levels[level] ??= new Map()).set(cell, x)
    out[i] = level
  }
  return out
}

export interface PileInput {
  /** Each entry's position across the page, in CSS pixels. */
  xs: ArrayLike<number>
  /** Each entry's family, as an index into the families, top to bottom. */
  family: ArrayLike<number>
  families: number
  included: (i: number) => boolean
  form: PileForm
  /** The height of the chart, in CSS pixels. */
  height: number
}

export function layoutPiles({ xs, family, families, included, form, height }: PileInput): PileLayout {
  const n = xs.length
  const y = new Float32Array(n)
  const groups: number[][] = Array.from({ length: families }, () => [])
  for (let i = 0; i < n; i++) if (included(i)) groups[family[i]!]!.push(i)
  for (const group of groups) group.sort((a, b) => xs[a]! - xs[b]! || a - b)
  const levels = new Int32Array(n)

  if (form === 'together') {
    // The last family goes down first, so the layers run in the same order as the families' rows.
    const order = groups.slice().reverse().flat()
    // Wider marks stack higher as well as being taller, so a little more size fills a lot more page.
    let pitch = PILE_PITCH
    let peak = 0
    for (pitch of TOGETHER_PITCHES) {
      stackLevels(xs, order, pitch, levels)
      peak = 0
      for (const i of order) peak = Math.max(peak, levels[i]! + 1)
      if (peak * pitch <= height * TOGETHER_FILL) break
    }
    const ground = height - GROUND - pitch / 2
    const step = Math.min(pitch, peak > 1 ? (ground - pitch / 2) / (peak - 1) : pitch)
    y.fill(ground / height)
    for (const i of order) y[i] = (ground - levels[i]! * step) / height
    return { y, rows: [], peak, markScale: pitch / PILE_PITCH, markArea: pitch * step }
  }

  const peaks = groups.map((group) => {
    stackLevels(xs, group, PILE_PITCH, levels)
    let peak = 0
    for (const i of group) peak = Math.max(peak, levels[i]! + 1)
    return peak
  })
  const room = height - GROUND * families
  const marks = peaks.reduce((sum, peak) => sum + peak, 0)
  // One step for every family, so that heights compare across them. Spare room is shared out.
  const step = Math.min(PILE_PITCH, marks > 0 ? room / marks : PILE_PITCH)
  const spare = Math.max(0, room - marks * step) / Math.max(1, families)
  const rows: PileRow[] = []
  let cursor = 0
  groups.forEach((group, g) => {
    const ground = cursor + spare + peaks[g]! * step + GROUND / 2 - step / 2
    for (const i of group) y[i] = (ground - levels[i]! * step) / height
    // The first family's heading sits straight under the ruler, which is already a rule.
    rows.push({ top: g === 0 ? 0 : (cursor + HEADING) / height, bottom: ground / height, base: (ground + step / 2) / height, ceiling: cursor / height, count: group.length })
    cursor = ground + step / 2 + GROUND / 2
  })
  // Entries left out wait on their family's ground, faded, ready to rejoin it.
  for (let i = 0; i < n; i++) if (!included(i)) y[i] = rows[family[i]!]!.bottom
  return { y, rows, peak: Math.max(0, ...peaks), markScale: 1, markArea: PILE_PITCH * step }
}
