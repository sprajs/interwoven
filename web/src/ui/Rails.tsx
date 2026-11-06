import { AnimatePresence, motion } from 'motion/react'
import { useMemo } from 'react'
import { formatYear } from '../engine/time.ts'
import { focusNode, getEngine, passes, useApp } from '../store.ts'
import { ShapeIcon } from './icons.tsx'

const PANEL = 'glass thin-scroll absolute bottom-[7.2rem] right-3 top-[4.1rem] z-20 hidden w-[20rem] overflow-y-auto rounded-2xl p-3 min-[760px]:right-4 min-[760px]:block'

function StepRail() {
  const model = useApp((s) => s.model)
  const hiddenDomains = useApp((s) => s.hiddenDomains)
  const hiddenTypes = useApp((s) => s.hiddenTypes)
  const activeLabels = useApp((s) => s.activeLabels)
  if (!model) return null
  const items = model.stepChanges.filter((i) => passes(model.nodes[i]!, { hiddenDomains, hiddenTypes, activeLabels }))
  return (
    <>
      <h2 className="px-2 pt-1 text-[15px] font-semibold tracking-tight">Step changes</h2>
      <p className="mt-1 px-2 text-xs leading-relaxed text-ink-2">Advances that changed what was possible next. Select one to trace what led to it and what followed.</p>
      <ol className="mt-3">
        {items.map((i) => {
          const node = model.nodes[i]!
          const lane = model.lanes[model.domainIndex[i]!]!
          return (
            <li key={i}>
              <button onClick={() => focusNode(i)} className="group flex w-full gap-2.5 rounded-xl px-2 py-2 text-left transition hover:bg-white/7">
                <span className="mt-1 grid w-3 shrink-0 place-items-center">
                  <ShapeIcon type={node.type} color={lane.color} size={12} />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="flex items-baseline justify-between gap-2">
                    <span className="truncate text-[13.5px] font-medium">{node.title}</span>
                    <span className="shrink-0 font-mono text-[11px] text-ink-3">{formatYear(node.year)}</span>
                  </span>
                  <span className="mt-0.5 block text-xs leading-snug text-ink-2">{node.step_change}</span>
                </span>
              </button>
            </li>
          )
        })}
      </ol>
    </>
  )
}

const DECADE_LIST = 10

function DensityRail() {
  const model = useApp((s) => s.model)
  const hiddenDomains = useApp((s) => s.hiddenDomains)
  const hiddenTypes = useApp((s) => s.hiddenTypes)
  const activeLabels = useApp((s) => s.activeLabels)

  const { decades, total } = useMemo(() => {
    const counts = new Map<number, number>()
    let total = 0
    if (model) {
      const f = { hiddenDomains, hiddenTypes, activeLabels }
      for (const node of model.nodes) {
        if (!passes(node, f)) continue
        const d = Math.floor(node.year / 10) * 10
        counts.set(d, (counts.get(d) ?? 0) + 1)
        total++
      }
    }
    const decades = [...counts].sort((a, b) => b[1] - a[1] || b[0] - a[0]).slice(0, DECADE_LIST)
    return { decades, total }
  }, [model, hiddenDomains, hiddenTypes, activeLabels])

  const max = decades[0]?.[1] ?? 1
  return (
    <>
      <h2 className="px-2 pt-1 text-[15px] font-semibold tracking-tight">Density</h2>
      <p className="mt-1 px-2 text-xs leading-relaxed text-ink-2">
        Brighter regions hold more entries, coloured by domain. Move across the timeline to count what falls under the cursor.
      </p>
      <h3 className="mb-1 mt-4 flex justify-between px-2 text-[11px] font-medium text-ink-3">
        Busiest decades
        <span>entries</span>
      </h3>
      <ol>
        {decades.map(([decade, count]) => (
          <li key={decade}>
            <button onClick={() => getEngine()?.flyToYears(decade - 20, decade + 30)} className="w-full rounded-lg px-2 py-1.5 text-left transition hover:bg-white/7">
              <span className="flex items-baseline justify-between text-[13px]">
                <span>{decade < 0 ? formatYear(decade) : `${decade}s`}</span>
                <span className="font-mono text-[11px] text-ink-2">{count.toLocaleString('en-US')}</span>
              </span>
              <span className="mt-1 block h-1 overflow-hidden rounded-full bg-white/7">
                <span className="block h-full rounded-full bg-accent/80" style={{ width: `${(count / max) * 100}%` }} />
              </span>
            </button>
          </li>
        ))}
      </ol>
      {total === 0 && <p className="px-2 text-[13px] text-ink-2">No entries match the current filters.</p>}
    </>
  )
}

export function Rails() {
  const mode = useApp((s) => s.mode)
  const selected = useApp((s) => s.selected)
  const show = selected === null && mode !== 'network'
  return (
    <AnimatePresence mode="wait">
      {show && (
        <motion.aside
          key={mode}
          initial={{ opacity: 0, x: 14 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 14 }}
          transition={{ duration: 0.16, ease: 'easeOut' }}
          className={PANEL}
        >
          {mode === 'steps' ? <StepRail /> : <DensityRail />}
        </motion.aside>
      )}
    </AnimatePresence>
  )
}
