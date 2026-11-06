import { AnimatePresence, motion } from 'motion/react'
import { useMemo } from 'react'
import { NODE_TYPES } from '../data/types.ts'
import { isFilterActive, passes, useApp } from '../store.ts'
import { Icon, ShapeIcon } from './icons.tsx'

const VISIBLE_LABEL_LIMIT = 60

function Row({ on, onClick, children, count }: { on: boolean; onClick: () => void; children: React.ReactNode; count: number }) {
  return (
    <button
      onClick={onClick}
      aria-pressed={on}
      className={`flex w-full items-center gap-2.5 rounded-lg px-2 py-1.5 text-left text-[13px] transition hover:bg-white/6 ${on ? 'text-ink' : 'text-ink-3 line-through decoration-ink-3/50'}`}
    >
      {children}
      <span className="ml-auto font-mono text-[11px] text-ink-3 no-underline">{count.toLocaleString('en-US')}</span>
    </button>
  )
}

export function FilterPanel() {
  const open = useApp((s) => s.filtersOpen)
  const model = useApp((s) => s.model)
  const hiddenDomains = useApp((s) => s.hiddenDomains)
  const hiddenTypes = useApp((s) => s.hiddenTypes)
  const activeLabels = useApp((s) => s.activeLabels)
  const toggleDomain = useApp((s) => s.toggleDomain)
  const toggleType = useApp((s) => s.toggleType)
  const toggleLabel = useApp((s) => s.toggleLabel)
  const clearFilters = useApp((s) => s.clearFilters)
  const setFiltersOpen = useApp((s) => s.setFiltersOpen)

  const typeCounts = useMemo(() => {
    const counts = new Map<string, number>()
    for (const node of model?.nodes ?? []) counts.set(node.type, (counts.get(node.type) ?? 0) + 1)
    return counts
  }, [model])

  const shown = useMemo(() => {
    if (!model) return 0
    const f = { hiddenDomains, hiddenTypes, activeLabels }
    let c = 0
    for (const node of model.nodes) if (passes(node, f)) c++
    return c
  }, [model, hiddenDomains, hiddenTypes, activeLabels])

  const active = isFilterActive({ hiddenDomains, hiddenTypes, activeLabels })

  return (
    <AnimatePresence>
      {open && model && (
        <motion.aside
          initial={{ opacity: 0, x: -14 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -14 }}
          transition={{ duration: 0.18, ease: 'easeOut' }}
          className="glass thin-scroll absolute bottom-[7.2rem] left-3 top-[4.1rem] z-30 w-[min(19rem,calc(100vw-1.5rem))] overflow-y-auto rounded-2xl p-3 sm:left-4"
          aria-label="Filters"
        >
          <div className="mb-2 flex items-center justify-between px-2">
            <h2 className="text-[13px] font-semibold">
              <span className="font-mono font-normal text-ink-2">{shown.toLocaleString('en-US')}</span> of {model.n.toLocaleString('en-US')} shown
            </h2>
            <div className="flex items-center gap-1">
              {active && (
                <button onClick={clearFilters} className="rounded-md px-2 py-1 text-xs text-accent hover:bg-white/6">
                  Reset
                </button>
              )}
              <button onClick={() => setFiltersOpen(false)} className="rounded-md p-1 text-ink-2 hover:bg-white/6 hover:text-ink" aria-label="Close filters">
                <Icon name="close" />
              </button>
            </div>
          </div>

          <h3 className="mt-3 px-2 text-[11px] font-medium text-ink-3">Domain</h3>
          <div className="mt-1">
            {model.lanes.map((lane) => (
              <Row key={lane.id} on={!hiddenDomains.has(lane.id)} onClick={() => toggleDomain(lane.id)} count={lane.count}>
                <span className="size-2.5 shrink-0 rounded-full" style={{ background: lane.color, opacity: hiddenDomains.has(lane.id) ? 0.35 : 1 }} />
                {lane.label}
              </Row>
            ))}
          </div>

          <h3 className="mt-4 px-2 text-[11px] font-medium text-ink-3">Type</h3>
          <div className="mt-1">
            {NODE_TYPES.map((t) => (
              <Row key={t.id} on={!hiddenTypes.has(t.id)} onClick={() => toggleType(t.id)} count={typeCounts.get(t.id) ?? 0}>
                <span className="grid w-2.5 place-items-center">
                  <ShapeIcon type={t.id} color="#aab6cc" size={11} />
                </span>
                {t.label}
              </Row>
            ))}
          </div>

          <h3 className="mt-4 px-2 text-[11px] font-medium text-ink-3">Labels</h3>
          <div className="mt-2 flex flex-wrap gap-1.5 px-1 pb-1">
            {model.labels.slice(0, VISIBLE_LABEL_LIMIT).map((label) => {
              const on = activeLabels.has(label.id)
              return (
                <button
                  key={label.id}
                  onClick={() => toggleLabel(label.id)}
                  aria-pressed={on}
                  className={`rounded-full border px-2.5 py-1 text-xs transition ${on ? 'border-accent/60 bg-accent/20 text-ink' : 'border-white/10 text-ink-2 hover:border-white/25 hover:text-ink'}`}
                >
                  {label.id.replace(/-/g, ' ')}
                  <span className="ml-1.5 font-mono text-[10px] text-ink-3">{label.count}</span>
                </button>
              )
            })}
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  )
}
