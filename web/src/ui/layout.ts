import { useApp } from '../store.ts'

export const COMPACT_WIDTH = 760
export const SHEET_WIDTH = 348
export const LABELS_WIDTH = 268
const MARGIN = 56
const COMPACT_MARGIN = 22
/** From this width the reach view's key sits in the empty corner its staircase leaves. */
export const CARTOUCHE_WIDTH = 1180

interface SheetState {
  selected: number | null
  mode: string
}

/** Whether a side sheet takes room from the chart on the right. */
export function rightSheetOpen(s: SheetState, width = window.innerWidth): boolean {
  if (s.mode === 'reach') return s.selected !== null || width < CARTOUCHE_WIDTH
  return s.selected !== null || s.mode !== 'threads'
}

/** The page margins, which widen to clear whichever side sheets are open. */
export function usePageMargins(): { left: number; right: number } {
  const labelsOpen = useApp((s) => s.labelsOpen)
  const rightSheet = useApp((s) => rightSheetOpen(s))
  if (window.innerWidth < COMPACT_WIDTH) return { left: COMPACT_MARGIN, right: COMPACT_MARGIN }
  return {
    left: labelsOpen ? LABELS_WIDTH + 36 : MARGIN,
    right: rightSheet ? SHEET_WIDTH + 36 : MARGIN,
  }
}
