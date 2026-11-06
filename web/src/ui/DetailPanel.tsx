import { AnimatePresence, motion } from 'motion/react'
import { LEVEL_NAMES, NODE_TYPES } from '../data/types.ts'
import type { Model } from '../data/model.ts'
import { formatYear } from '../engine/time.ts'
import { focusNode, useApp } from '../store.ts'
import { Icon, ShapeIcon } from './icons.tsx'

function NodeList({ title, items, model }: { title: string; items: number[]; model: Model }) {
  if (items.length === 0) return null
  const sorted = [...items].sort((a, b) => model.nodes[a]!.year - model.nodes[b]!.year)
  return (
    <section className="mt-5">
      <h3 className="mb-1 flex items-baseline justify-between px-2 text-[11px] font-medium text-ink-3">
        {title}
        <span className="font-mono">{items.length}</span>
      </h3>
      <ul>
        {sorted.map((i) => {
          const node = model.nodes[i]!
          const lane = model.lanes[model.domainIndex[i]!]!
          return (
            <li key={i}>
              <button onClick={() => focusNode(i)} className="flex w-full items-center gap-2.5 rounded-lg px-2 py-1.5 text-left text-[13px] text-ink transition hover:bg-white/7">
                <span className="grid w-3 shrink-0 place-items-center">
                  <ShapeIcon type={node.type} color={lane.color} size={11} />
                </span>
                <span className="min-w-0 flex-1 truncate">{node.title}</span>
                <span className="font-mono text-[11px] text-ink-3">{formatYear(node.year)}</span>
              </button>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

export function DetailPanel() {
  const model = useApp((s) => s.model)
  const selected = useApp((s) => s.selected)
  const select = useApp((s) => s.select)
  const node = model && selected !== null ? model.nodes[selected] : null
  const lane = model && selected !== null ? model.lanes[model.domainIndex[selected]!] : null
  const typeLabel = node ? NODE_TYPES.find((t) => t.id === node.type)?.label : ''
  // Large synthetic sets only compute full impact for step changes.
  const impactIsFull = model && node ? model.n <= 4000 || node.level === 0 : false

  return (
    <AnimatePresence>
      {node && lane && model && selected !== null && (
        <motion.aside
          key="detail"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 12 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
          className="glass thin-scroll absolute inset-x-3 bottom-3 z-30 max-h-[46vh] select-text overflow-y-auto rounded-2xl p-3 min-[760px]:inset-x-auto min-[760px]:bottom-[7.2rem] min-[760px]:right-4 min-[760px]:top-[4.1rem] min-[760px]:max-h-none min-[760px]:w-[20rem]"
          aria-label={`Details for ${node.title}`}
        >
          <div className="flex items-start gap-2 px-2 pt-1">
            <div className="min-w-0 flex-1">
              <p className="font-mono text-xs text-ink-2">{formatYear(node.year)}</p>
              <h2 className="mt-1 text-[19px] font-semibold leading-tight tracking-tight">{node.title}</h2>
            </div>
            <button onClick={() => select(null)} className="-mr-1 -mt-0.5 rounded-md p-1 text-ink-2 hover:bg-white/6 hover:text-ink" aria-label="Close details">
              <Icon name="close" />
            </button>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 px-2 text-xs text-ink-2">
            <span className="flex items-center gap-1.5">
              <ShapeIcon type={node.type} color={lane.color} size={11} />
              {typeLabel}
            </span>
            <span>{lane.label}</span>
            <span>{LEVEL_NAMES[node.level]}</span>
          </div>

          <p className="mt-3 px-2 text-[13.5px] leading-relaxed text-ink">{node.summary}</p>

          {node.step_change && (
            <div className="mx-1 mt-3 rounded-xl border border-white/10 bg-white/4 p-2.5">
              <h3 className="text-[11px] font-medium text-ink-2">Why it was a step change</h3>
              <p className="mt-1 text-[13px] leading-relaxed text-ink">{node.step_change}</p>
            </div>
          )}

          {impactIsFull && model.impact[selected]! > 0 && (
            <p className="mt-3 px-2 text-xs text-ink-2">
              <span className="font-mono text-ink">{model.impact[selected]!.toLocaleString('en-US')}</span> later {model.impact[selected] === 1 ? 'entry traces' : 'entries trace'} back to this.
            </p>
          )}

          {node.labels.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1 px-2">
              {node.labels.map((label) => (
                <span key={label} className="rounded-full border border-white/10 px-2 py-0.5 text-[11px] text-ink-2">
                  {label.replace(/-/g, ' ')}
                </span>
              ))}
            </div>
          )}

          <NodeList title="Built on" items={model.parents[selected]!} model={model} />
          <NodeList title="Led to" items={model.children[selected]!} model={model} />
        </motion.aside>
      )}
    </AnimatePresence>
  )
}
