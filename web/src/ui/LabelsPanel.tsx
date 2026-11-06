import { AnimatePresence, motion } from 'motion/react'
import { useMemo } from 'react'
import { KINDS } from '../data/types.ts'
import { passes, useApp } from '../store.ts'
import { CloseButton, Mark } from './icons.tsx'
import { LABELS_WIDTH } from './layout.ts'

export function LabelsPanel() {
  const open = useApp((s) => s.labelsOpen)
  const model = useApp((s) => s.model)
  const hiddenKinds = useApp((s) => s.hiddenKinds)
  const activeLabels = useApp((s) => s.activeLabels)
  const toggleKind = useApp((s) => s.toggleKind)
  const toggleLabel = useApp((s) => s.toggleLabel)
  const clearFilters = useApp((s) => s.clearFilters)
  const setLabelsOpen = useApp((s) => s.setLabelsOpen)

  const shown = useMemo(() => {
    if (!model) return 0
    let c = 0
    for (const node of model.nodes) if (passes(node, { hiddenKinds, activeLabels })) c++
    return c
  }, [model, hiddenKinds, activeLabels])

  const filtering = hiddenKinds.size + activeLabels.size > 0

  return (
    <AnimatePresence>
      {open && model && (
        <motion.aside
          initial={{ x: -LABELS_WIDTH }}
          animate={{ x: 0 }}
          exit={{ x: -LABELS_WIDTH }}
          transition={{ duration: 0.26, ease: [0.2, 0.7, 0.2, 1] }}
          style={{ width: `min(${LABELS_WIDTH}px, 100vw)` }}
          className="sheet thin-scroll absolute bottom-0 left-0 top-[46px] z-30 overflow-y-auto border-r border-t border-rule px-5 pb-6 pt-4"
          aria-label="Labels"
        >
          <div className="flex items-baseline justify-between">
            <h2 className="text-[21px] font-medium leading-none">Labels</h2>
            <CloseButton onClick={() => setLabelsOpen(false)} label="Close labels" />
          </div>
          <p className="caption mt-2 leading-snug">
            An entry can carry several. Choose any to follow them through the chart; the first label on an entry sets its ink.
          </p>
          <p className="mt-3 text-[15px] text-ink-2">
            {shown.toLocaleString('en-US')} of {model.n.toLocaleString('en-US')} placed entries
            {filtering && (
              <button onClick={clearFilters} className="ml-2 italic text-ink-3 underline decoration-[0.5px] underline-offset-2 hover:text-ink">
                clear
              </button>
            )}
          </p>

          <ul className="mt-4 border-t border-rule">
            {model.labels.map((label) => {
              const on = activeLabels.has(label.id)
              return (
                <li key={label.id} className="border-b border-rule/50">
                  <button onClick={() => toggleLabel(label.id)} aria-pressed={on} className="group flex w-full items-baseline gap-2.5 py-[5px] text-left text-[16px] leading-tight">
                    <span className="size-[7px] shrink-0 translate-y-[-1px] rounded-full" style={{ background: label.ink }} />
                    <span className={on ? 'font-medium text-ink underline decoration-[0.5px] underline-offset-2' : 'text-ink-2 group-hover:text-ink'}>{label.name}</span>
                    <span className="ml-auto text-[14px] text-ink-3">{label.count}</span>
                  </button>
                </li>
              )
            })}
          </ul>

          <h3 className="mt-5 text-[15px] italic text-ink-3">Show</h3>
          <div className="mt-1">
            {KINDS.map((kind) => {
              const on = !hiddenKinds.has(kind.id)
              return (
                <button key={kind.id} onClick={() => toggleKind(kind.id)} aria-pressed={on} className={`flex w-full items-center gap-2.5 py-[3px] text-left text-[16px] ${on ? 'text-ink' : 'text-ink-3 line-through decoration-[0.5px]'}`}>
                  <span className="grid w-[7px] place-items-center">
                    <Mark kind={kind.id} size={9} />
                  </span>
                  {kind.plural}
                </button>
              )
            })}
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  )
}
