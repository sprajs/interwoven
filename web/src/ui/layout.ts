import { cornersFree, rowOrder, type RowOrder } from '../data/derive.ts'
import { modelReach, type Model } from '../data/model.ts'
import { BREAK, LAYOUT } from '../design.ts'
import { useApp } from '../store.ts'

export const COMPACT_WIDTH = BREAK.compact
export const SHEET_WIDTH = LAYOUT.sheet
export const LABELS_WIDTH = LAYOUT.labels
/** From this width the reach view's notes sit in the corners its staircase leaves empty. */
export const CARTOUCHE_WIDTH = BREAK.corner
/** What the chart keeps clear of a side sheet. */
export const SHEET_CLEARANCE = 6 * 6

interface SheetState {
  selected: number | null
  unplacedSelected: string | null
  mode: string
  model: Model | null
  rowOrder: RowOrder
}

const cornerCache = new WeakMap<Model, Map<RowOrder, boolean>>()

/** Whether the reach view's notes can sit in the corners its rows leave empty. */
export function reachCornersFree(model: Model | null, order: RowOrder): boolean {
  if (!model) return true
  let byOrder = cornerCache.get(model)
  if (!byOrder) {
    byOrder = new Map()
    cornerCache.set(model, byOrder)
  }
  let free = byOrder.get(order)
  if (free === undefined) {
    const reach = modelReach(model)
    const rows = rowOrder(model.nodes, model.children, model.parents, reach, order)
    free = cornersFree(rows, model.nodes, reach, (year) => model.time.compressed(year))
    byOrder.set(order, free)
  }
  return free
}

/** Whether a side sheet takes room from the chart on the right. */
export function rightSheetOpen(s: SheetState, width = window.innerWidth): boolean {
  if (s.unplacedSelected !== null) return true
  if (s.mode === 'reach') return s.selected !== null || width < CARTOUCHE_WIDTH || !reachCornersFree(s.model, s.rowOrder)
  return s.selected !== null || s.mode !== 'threads'
}

/** The page margins, which widen to clear whichever side sheets are open. */
export function usePageMargins(): { left: number; right: number } {
  const labelsOpen = useApp((s) => s.labelsOpen)
  const rightSheet = useApp((s) => rightSheetOpen(s))
  if (window.innerWidth < COMPACT_WIDTH) return { left: LAYOUT.marginCompact, right: LAYOUT.marginCompact }
  return {
    left: labelsOpen ? LABELS_WIDTH + SHEET_CLEARANCE : LAYOUT.margin,
    right: rightSheet ? SHEET_WIDTH + SHEET_CLEARANCE : LAYOUT.margin,
  }
}
