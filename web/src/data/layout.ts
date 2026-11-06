import { connectedComponents } from './derive.ts'

/**
 * Lays entries out on strands, as a transit map lays out its lines. Time fixes each entry's
 * position across the page. Its row comes from its subject family and from what it is linked to:
 * a linked entry takes the row of its neighbour if it is free, so a thread reads as one line.
 * A row is held from an entry until the next entry on its thread, so no unrelated entry can sit
 * on a line it has nothing to do with.
 */

export interface Family {
  name: string
  ink: string
  /** Position of its first and last row, 0 to 1 down the sheet. */
  top: number
  bottom: number
  count: number
}

export interface Strands {
  y: Float32Array
  families: Family[]
  /** The distance between neighbouring rows, on the same scale as y. */
  rowStep: number
}

export interface StrandInput {
  /** Position across the sheet, 0 to 1. */
  u: Float32Array
  levels: readonly number[]
  /** The subject family of each entry, before threads are kept together. */
  family: readonly string[]
  /** The primary label, so unlinked entries gather near others on the same subject. */
  label: readonly string[]
  edges: readonly { source: number; target: number }[]
  /** Families top to bottom, with the ink each one is drawn in. */
  order: readonly { name: string; ink: string }[]
}

/** How much of the width an entry keeps clear on its row, more for those likely to be named. */
const RESERVE = [0.03, 0.022, 0.016, 0.012]
/** Rows left empty between families, which also gives each family's heading its room. */
const FAMILY_GAP = 3
const MARGIN = 0.015
/** Beyond this many entries, holding a row for a whole thread would make too many rows. */
const HOLD_LIMIT = 5000

export function layoutStrands({ u, levels, family, label, edges, order }: StrandInput): Strands {
  const n = u.length
  const y = new Float32Array(n)
  if (n === 0) return { y, families: [], rowStep: 1 }

  const neighbours: number[][] = Array.from({ length: n }, () => [])
  for (const e of edges) {
    neighbours[e.source]!.push(e.target)
    neighbours[e.target]!.push(e.source)
  }

  // A thread stays together, in whichever family most of it belongs to.
  const component = connectedComponents(n, edges)
  const votes = new Map<number, Map<string, number>>()
  for (let i = 0; i < n; i++) {
    const tally = votes.get(component[i]!) ?? new Map<string, number>()
    tally.set(family[i]!, (tally.get(family[i]!) ?? 0) + 1)
    votes.set(component[i]!, tally)
  }
  const familyOfThread = new Map<number, string>()
  for (const [thread, tally] of votes) {
    let best = ''
    let most = -1
    for (const [name, count] of tally) {
      if (count > most) {
        best = name
        most = count
      }
    }
    familyOfThread.set(thread, best)
  }

  const members = new Map<string, number[]>()
  for (let i = 0; i < n; i++) {
    const name = familyOfThread.get(component[i]!)!
    const list = members.get(name) ?? []
    list.push(i)
    members.set(name, list)
  }

  const scale = Math.min(1, 900 / n)
  const hold = n <= HOLD_LIMIT
  const row = new Int32Array(n)
  const placed = new Uint8Array(n)
  const known = order.filter((f) => members.has(f.name))
  for (const name of members.keys()) if (!known.some((f) => f.name === name)) known.push({ name, ink: '#4e463c' })

  const families: Family[] = []
  let line = 0
  for (const { name, ink } of known) {
    const list = members.get(name)!.sort((a, b) => u[a]! - u[b]! || levels[a]! - levels[b]!)
    const heldUntil = new Map<number, number>()
    const rowOfLabel = new Map<string, number>()
    for (const i of list) {
      let anchor = rowOfLabel.get(label[i]!) ?? 0
      let closest = Infinity
      for (const j of neighbours[i]!) {
        if (!placed[j]) continue
        const distance = Math.abs(u[j]! - u[i]!)
        if (distance < closest) {
          closest = distance
          anchor = row[j]!
        }
      }
      let chosen = anchor
      for (let d = 0; ; d++) {
        const below = anchor + d
        if ((heldUntil.get(below) ?? -Infinity) <= u[i]!) {
          chosen = below
          break
        }
        const above = anchor - d
        if ((heldUntil.get(above) ?? -Infinity) <= u[i]!) {
          chosen = above
          break
        }
      }
      row[i] = chosen
      placed[i] = 1
      rowOfLabel.set(label[i]!, chosen)
      let until = u[i]! + (RESERVE[levels[i]!] ?? RESERVE[3]!) * scale
      if (hold) {
        // Holds the row up to the next entry along the thread, which will want to continue it.
        let next = Infinity
        for (const j of neighbours[i]!) if (!placed[j] && u[j]! >= u[i]! && u[j]! < next) next = u[j]!
        if (next !== Infinity) until = Math.max(until, next)
      }
      heldUntil.set(chosen, until)
    }

    // Rows close up, so an unused row leaves no gap.
    const used = [...new Set(list.map((i) => row[i]!))].sort((a, b) => a - b)
    const position = new Map(used.map((r, k) => [r, k]))
    for (const i of list) y[i] = line + position.get(row[i]!)!
    families.push({ name, ink, top: line, bottom: line + used.length - 1, count: list.length })
    line += used.length + FAMILY_GAP
  }

  const total = Math.max(1, line - FAMILY_GAP - 1)
  const fit = (v: number) => MARGIN + (1 - 2 * MARGIN) * (v / total)
  for (let i = 0; i < n; i++) y[i] = fit(y[i]!)
  for (const f of families) {
    f.top = fit(f.top)
    f.bottom = fit(f.bottom)
  }
  return { y, families, rowStep: (1 - 2 * MARGIN) / total }
}
