import { useApp } from '../store.ts'

export const COMPACT_WIDTH = 760
export const SHEET_WIDTH = 348
export const LABELS_WIDTH = 268
const MARGIN = 56
const COMPACT_MARGIN = 22

/** The page margins, which widen to clear whichever side sheets are open. */
export function usePageMargins(): { left: number; right: number } {
  const labelsOpen = useApp((s) => s.labelsOpen)
  const rightSheet = useApp((s) => s.selected !== null || s.mode !== 'threads')
  if (window.innerWidth < COMPACT_WIDTH) return { left: COMPACT_MARGIN, right: COMPACT_MARGIN }
  return {
    left: labelsOpen ? LABELS_WIDTH + 36 : MARGIN,
    right: rightSheet ? SHEET_WIDTH + 36 : MARGIN,
  }
}
