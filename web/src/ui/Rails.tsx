import { AnimatePresence } from 'motion/react'
import { useApp } from '../store.ts'
import { ReachSheet } from './ReachSheet.tsx'
import { StorySheet } from './StorySheet.tsx'

/** The sheets that belong to a view. Each stays closed until it is asked for. */
export function Rails() {
  const mode = useApp((s) => s.mode)
  const story = useApp((s) => s.story)
  const aboutOpen = useApp((s) => s.aboutOpen)
  const nothingChosen = useApp((s) => s.selected === null && s.unplacedSelected === null)
  return (
    <AnimatePresence>
      {mode === 'story' && (story !== null || (aboutOpen && nothingChosen)) && <StorySheet key="story" />}
      {mode === 'reach' && aboutOpen && nothingChosen && <ReachSheet key="reach" />}
    </AnimatePresence>
  )
}
