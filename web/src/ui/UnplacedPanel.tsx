import { AnimatePresence, motion } from 'motion/react'
import { useState } from 'react'
import { focusEntry, useApp } from '../store.ts'
import { CloseButton, Mark } from './icons.tsx'
import { LABELS_WIDTH } from './layout.ts'

export function UnplacedPanel() {
  const open = useApp((s) => s.unplacedOpen)
  const model = useApp((s) => s.model)
  const setOpen = useApp((s) => s.setUnplacedOpen)
  const [query, setQuery] = useState('')
  const needle = query.trim().toLowerCase()
  const entries = model?.unplaced.filter((entry) => `${entry.title} ${entry.id} ${entry.summary} ${entry.placement_reason}`.toLowerCase().includes(needle)) ?? []

  return (
    <AnimatePresence>
      {open && model && (
        <motion.aside initial={{ x: -LABELS_WIDTH }} animate={{ x: 0 }} exit={{ x: -LABELS_WIDTH }}
          transition={{ duration: 0.26, ease: [0.2, 0.7, 0.2, 1] }}
          style={{ width: `min(${LABELS_WIDTH}px, 100vw)` }}
          className="sheet thin-scroll absolute bottom-0 left-0 top-[110px] z-30 overflow-y-auto border-r border-t border-rule px-5 pb-6 pt-4 min-[760px]:top-[46px]"
          aria-label="Unplaced entries">
          <div className="flex items-baseline justify-between gap-2">
            <h2 className="text-[21px] font-medium leading-none">Unplaced entries</h2>
            <CloseButton onClick={() => setOpen(false)} label="Close unplaced entries" />
          </div>
          <p className="caption mt-2 leading-snug">These entries remain in the research. A selected, supported anchor with both date limits is needed to place a mark.</p>
          <input value={query} onChange={(event) => setQuery(event.target.value)} aria-label="Filter unplaced entries"
            placeholder="Find an unplaced entry" className="mt-3 w-full border-b border-rule bg-transparent py-1 text-[16px] outline-none placeholder:italic placeholder:text-ink-3" />
          <p className="mt-2 text-[14px] text-ink-3">{entries.length} of {model.unplaced.length} unplaced entries</p>
          <ul className="mt-3 border-t border-rule">
            {entries.map((entry) => (
              <li key={entry.id} className="border-b border-rule/50">
                <button onClick={() => focusEntry(entry.id)} className="group flex w-full items-start gap-2.5 py-2 text-left">
                  <span className="mt-1.5 shrink-0"><Mark kind={entry.kind} size={8} color={model.labelById.get(entry.labels[0] ?? '')?.ink} /></span>
                  <span>
                    <span className={`block text-[16px] leading-tight group-hover:underline ${entry.kind === 'science' ? 'italic' : ''}`}>{entry.title}</span>
                    <span className="mt-1 block text-[13.5px] leading-snug text-ink-3">{entry.placement_reason}</span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
          {entries.length === 0 && <p className="mt-3 text-[15px] italic text-ink-3">No unplaced entries match.</p>}
        </motion.aside>
      )}
    </AnimatePresence>
  )
}
