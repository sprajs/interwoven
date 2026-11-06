import { BREAK, LAYOUT } from '../design.ts'
import { useApp } from '../store.ts'

export const COMPACT_WIDTH = BREAK.compact
export const SHEET_WIDTH = LAYOUT.sheet
export const LABELS_WIDTH = LAYOUT.labels
/** What the chart keeps clear of a side sheet. */
export const SHEET_CLEARANCE = 6 * 6

interface SheetState {
  selected: number | null
  unplacedSelected: string | null
  mode: string
  story: unknown
  aboutOpen: boolean
}

/** Whether a side sheet takes room from the chart on the right. One opens only when asked for. */
export function rightSheetOpen(s: SheetState): boolean {
  if (s.unplacedSelected !== null || s.selected !== null) return true
  return (s.mode === 'story' && s.story !== null) || (s.aboutOpen && (s.mode === 'story' || s.mode === 'reach'))
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
