import { AnimatePresence, motion } from 'motion/react'
import { useMemo } from 'react'
import { formatYear } from '../engine/time.ts'
import { focusNode, getEngine, passes, useApp } from '../store.ts'
import { Mark } from './icons.tsx'
import { SHEET_WIDTH } from './layout.ts'

function LandmarkRail() {
  const model = useApp((s) => s.model)
  const hiddenKinds = useApp((s) => s.hiddenKinds)
  const activeLabels = useApp((s) => s.activeLabels)
  if (!model) return null
  const items = model.landmarks.filter((i) => passes(model.nodes[i]!, { hiddenKinds, activeLabels }))
  return (
    <>
      <h2 className="text-[21px] font-medium leading-none">Landmarks</h2>
      <p className="caption mt-2 leading-snug">Placed entries the research marks as most prominent. Choose one to trace their recorded connections.</p>
      <ol className="mt-4 border-t border-rule">
        {items.map((i) => {
          const node = model.nodes[i]!
          return (
            <li key={i} className="border-b border-rule/50">
              <button onClick={() => focusNode(i)} className="group flex w-full items-baseline gap-2.5 py-[6px] text-left text-[16px] leading-tight">
                <span className="grid w-2.5 shrink-0 translate-y-[1px] place-items-center self-center">
                  <Mark kind={node.kind} strength={node.evidence_strength} size={9} color={`rgb(${model.ink[i * 3]! * 255} ${model.ink[i * 3 + 1]! * 255} ${model.ink[i * 3 + 2]! * 255})`} />
                </span>
                <span className={`min-w-0 flex-1 group-hover:underline group-hover:decoration-[0.5px] group-hover:underline-offset-2 ${node.kind === 'science' ? 'italic' : ''}`}>{node.title}</span>
                <span className="shrink-0 text-[14px] text-ink-3">{node.date_kind && node.date_kind !== 'point' ? node.date_label : formatYear(node.year)}</span>
              </button>
            </li>
          )
        })}
      </ol>
      {items.length === 0 && <p className="mt-3 text-[15px] italic text-ink-3">None match the chosen labels.</p>}
    </>
  )
}

const DECADE_LIST = 10

function DensityRail() {
  const model = useApp((s) => s.model)
  const hiddenKinds = useApp((s) => s.hiddenKinds)
  const activeLabels = useApp((s) => s.activeLabels)

  const decades = useMemo(() => {
    const counts = new Map<number, number>()
    if (model) {
      for (const node of model.nodes) {
        if (!passes(node, { hiddenKinds, activeLabels })) continue
        const d = Math.floor(node.year / 10) * 10
        counts.set(d, (counts.get(d) ?? 0) + 1)
      }
    }
    return [...counts].sort((a, b) => b[1] - a[1] || b[0] - a[0]).slice(0, DECADE_LIST)
  }, [model, hiddenKinds, activeLabels])

  const max = decades[0]?.[1] ?? 1
  return (
    <>
      <h2 className="text-[21px] font-medium leading-none">Density</h2>
      <p className="caption mt-2 leading-snug">The hatching counts selected community-entry choices, including labelled awareness estimates and contextual inferences. Move across the chart to count them; details give their community and evidence. Further research remains available in Unplaced.</p>
      <h3 className="mt-4 flex items-baseline justify-between border-b border-rule pb-1 text-[15px] italic text-ink-3">
        Busiest decades
        <span>entries</span>
      </h3>
      <ol>
        {decades.map(([decade, count]) => (
          <li key={decade} className="border-b border-rule/50">
            <button onClick={() => getEngine()?.flyToYears(decade - 15, decade + 25)} className="group w-full py-[5px] text-left">
              <span className="flex items-baseline justify-between text-[16px] leading-tight">
                <span className="group-hover:underline group-hover:decoration-[0.5px] group-hover:underline-offset-2">{decade < 0 ? formatYear(decade) : `${decade}s`}</span>
                <span className="text-[14px] text-ink-3">{count.toLocaleString('en-US')}</span>
              </span>
              <span className="mt-1 block h-[3px] rounded-r-[2px] bg-ink-2" style={{ width: `${(count / max) * 100}%` }} />
            </button>
          </li>
        ))}
      </ol>
      {decades.length === 0 && <p className="mt-3 text-[15px] italic text-ink-3">None match the chosen labels.</p>}
    </>
  )
}

export function Rails() {
  const mode = useApp((s) => s.mode)
  const selected = useApp((s) => s.selected)
  const unplacedSelected = useApp((s) => s.unplacedSelected)
  const show = selected === null && unplacedSelected === null && mode !== 'threads'
  return (
    <AnimatePresence>
      {show && (
        <motion.aside
          key={mode}
          initial={{ x: SHEET_WIDTH }}
          animate={{ x: 0 }}
          exit={{ x: SHEET_WIDTH }}
          transition={{ duration: 0.26, ease: [0.2, 0.7, 0.2, 1] }}
          style={{ width: SHEET_WIDTH }}
          className="sheet thin-scroll absolute bottom-0 right-0 top-[46px] z-20 hidden overflow-y-auto border-l border-t border-rule px-5 pb-6 pt-4 min-[760px]:block"
        >
          {mode === 'landmarks' ? <LandmarkRail /> : <DensityRail />}
        </motion.aside>
      )}
    </AnimatePresence>
  )
}
