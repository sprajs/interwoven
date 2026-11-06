import { AnimatePresence, motion } from 'motion/react'
import { useMemo } from 'react'
import { formatYear } from '../engine/time.ts'
import { focusNode, getEngine, passes, useApp } from '../store.ts'
import { Mark } from './icons.tsx'
import { SHEET_WIDTH } from './layout.ts'
import { ReachSheet } from './ReachSheet.tsx'
import { StorySheet } from './StorySheet.tsx'

function LandmarkRail() {
  const model = useApp((s) => s.model)
  const hiddenKinds = useApp((s) => s.hiddenKinds)
  const activeLabels = useApp((s) => s.activeLabels)
  if (!model) return null
  const items = model.landmarks.filter((i) => passes(model.nodes[i]!, { hiddenKinds, activeLabels }))
  return (
    <>
      <h2 className="text-head">Landmarks</h2>
      <p className="note mt-1">The entries the research marks as most prominent. Choose one to trace what led to it and what followed.</p>
      <ol className="mt-4 border-t border-rule">
        {items.map((i) => {
          const node = model.nodes[i]!
          return (
            <li key={i} className="border-b border-rule-soft">
              <button onClick={() => focusNode(i)} className="group flex w-full items-baseline gap-2 py-1 text-left text-body">
                <span className="grid w-2 shrink-0 translate-y-px place-items-center self-center">
                  <Mark kind={node.kind} strength={node.evidence_strength} color={`rgb(${model.ink[i * 3]! * 255} ${model.ink[i * 3 + 1]! * 255} ${model.ink[i * 3 + 2]! * 255})`} />
                </span>
                <span className={`link-hover min-w-0 flex-1 ${node.kind === 'science' ? 'science' : ''}`}>{node.title}</span>
                <span className="note shrink-0">{node.date_kind && node.date_kind !== 'point' ? node.date_label : formatYear(node.year)}</span>
              </button>
            </li>
          )
        })}
      </ol>
      {items.length === 0 && <p className="note mt-2">None match the chosen labels.</p>}
    </>
  )
}

const DECADE_LIST = 10
/** Below this, a list of the busiest decades would be ranking ones and twos. */
const FEW_ENTRIES = 60

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
  const few = (model?.n ?? 0) < FEW_ENTRIES
  return (
    <>
      <h2 className="text-head">Density</h2>
      <p className="note mt-1">The hatching grows with the number of entries per year, on a root scale so quiet eras stay visible. It counts the date each entry was chosen to stand on, including labelled awareness estimates and inferences, so it shows where research has placed things, not how much happened. Move across the chart to count them.</p>
      {few ? (
        <p className="note mt-4">With {model?.n} entries placed, this is still a sketch. It becomes a real picture of activity as more dates are researched.</p>
      ) : (
        <>
          <h3 className="section-head flex items-baseline justify-between">
            Busiest decades
            <span className="font-normal text-ink-3">entries</span>
          </h3>
          <ol>
            {decades.map(([decade, count]) => (
              <li key={decade} className="border-b border-rule-soft">
                <button onClick={() => getEngine()?.flyToYears(decade - 15, decade + 25)} className="group w-full py-1 text-left">
                  <span className="flex items-baseline justify-between text-body">
                    <span className="link-hover">{decade < 0 ? formatYear(decade) : `${decade}s`}</span>
                    <span className="figures note">{count.toLocaleString('en-US')}</span>
                  </span>
                  <span className="mt-1 block h-px bg-ink-2" style={{ width: `${(count / max) * 100}%` }} />
                </button>
              </li>
            ))}
          </ol>
          {decades.length === 0 && <p className="note mt-2">None match the chosen labels.</p>}
        </>
      )}
    </>
  )
}

export function Rails() {
  const mode = useApp((s) => s.mode)
  const selected = useApp((s) => s.selected)
  const unplacedSelected = useApp((s) => s.unplacedSelected)
  const show = selected === null && unplacedSelected === null && (mode === 'density' || mode === 'landmarks')
  return (
    <AnimatePresence>
      {mode === 'story' && <StorySheet key="story" />}
      {mode === 'reach' && selected === null && unplacedSelected === null && <ReachSheet key="reach" />}
      {show && (
        <motion.aside
          key={mode}
          initial={{ x: SHEET_WIDTH }}
          animate={{ x: 0 }}
          exit={{ x: SHEET_WIDTH }}
          transition={{ duration: 0.26, ease: [0.2, 0.7, 0.2, 1] }}
          style={{ width: SHEET_WIDTH }}
          className="sheet thin-scroll absolute bottom-0 right-0 top-18 z-20 hidden overflow-y-auto border-l border-t border-rule px-8 pb-8 pt-4 compact:block"
        >
          {mode === 'landmarks' ? <LandmarkRail /> : <DensityRail />}
        </motion.aside>
      )}
    </AnimatePresence>
  )
}
