import { AnimatePresence, motion } from 'motion/react'
import type { Edge, Model } from '../data/model.ts'
import { formatYear } from '../engine/time.ts'
import { focusNode, useApp } from '../store.ts'
import { CloseButton, Mark } from './icons.tsx'
import { SHEET_WIDTH } from './TimelineCanvas.tsx'

function LinkList({ title, edges, side, model }: { title: string; edges: Edge[]; side: 'source' | 'target'; model: Model }) {
  if (edges.length === 0) return null
  const sorted = [...edges].sort((a, b) => model.nodes[a[side]]!.year - model.nodes[b[side]]!.year)
  return (
    <section className="mt-5">
      <h3 className="border-b border-rule pb-1 text-[15px] italic text-ink-3">{title}</h3>
      <ul>
        {sorted.map((edge) => {
          const i = edge[side]
          const node = model.nodes[i]!
          return (
            <li key={`${edge.source}-${edge.target}`} className="border-b border-rule/50 py-2">
              <button onClick={() => focusNode(i)} className="group flex w-full items-baseline gap-2 text-left text-[16px] leading-tight">
                <span className="grid w-2.5 shrink-0 translate-y-[1px] place-items-center self-center">
                  <Mark kind={node.kind} size={9} color={`rgb(${model.ink[i * 3]! * 255} ${model.ink[i * 3 + 1]! * 255} ${model.ink[i * 3 + 2]! * 255})`} />
                </span>
                <span className={`min-w-0 flex-1 group-hover:underline group-hover:decoration-[0.5px] group-hover:underline-offset-2 ${node.kind === 'science' ? 'italic' : ''}`}>{node.title}</span>
                <span className="shrink-0 text-[14px] text-ink-3">{formatYear(node.year)}</span>
              </button>
              {edge.link.statement && (
                <p className="mt-1 pl-[18px] text-[14px] leading-snug text-ink-2">
                  {edge.link.statement}
                  {edge.tentative && <em className="text-ink-3"> Awaiting review.</em>}
                </p>
              )}
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
  const activeLabels = useApp((s) => s.activeLabels)
  const toggleLabel = useApp((s) => s.toggleLabel)
  const node = model && selected !== null ? model.nodes[selected] : null
  const impactIsFull = model && node ? model.n <= 4000 || node.level === 0 : false

  return (
    <AnimatePresence>
      {node && model && selected !== null && (
        <motion.aside
          key="detail"
          initial={{ x: SHEET_WIDTH }}
          animate={{ x: 0 }}
          exit={{ x: SHEET_WIDTH }}
          transition={{ duration: 0.26, ease: [0.2, 0.7, 0.2, 1] }}
          className="sheet thin-scroll absolute inset-x-0 bottom-0 z-30 max-h-[48vh] select-text overflow-y-auto border-t border-rule px-5 pb-8 pt-4 min-[760px]:inset-x-auto min-[760px]:inset-y-0 min-[760px]:right-0 min-[760px]:max-h-none min-[760px]:border-l min-[760px]:border-t-0"
          style={{ width: window.innerWidth >= 760 ? SHEET_WIDTH : undefined }}
          aria-label={`About ${node.title}`}
        >
          <div className="flex items-baseline justify-between gap-3">
            <p className="text-[16px] text-ink-3">{node.date_label}</p>
            <CloseButton onClick={() => select(null)} label="Close" />
          </div>
          <h2 className={`mt-1 text-[27px] font-medium leading-[1.1] tracking-[-0.005em] ${node.kind === 'science' ? 'italic' : ''}`}>{node.title}</h2>
          <p className="mt-1 text-[15px] text-ink-3">
            {node.kind === 'science' ? 'Science' : 'Technology'}
            {node.regions.length > 0 && <> · {node.regions.join('; ')}</>}
          </p>

          <p className="mt-3 text-[17px] leading-[1.32]">{node.summary}</p>
          {node.note && <p className="mt-2 text-[16px] italic leading-snug text-ink-2">{node.note}</p>}

          {node.labels.length > 0 && (
            <p className="mt-3 flex flex-wrap gap-x-3 gap-y-0.5 text-[15px]">
              {node.labels.map((id) => {
                const label = model.labelById.get(id)
                const on = activeLabels.has(id)
                return (
                  <button key={id} onClick={() => toggleLabel(id)} aria-pressed={on} className="flex items-baseline gap-1.5 text-ink-2 hover:text-ink">
                    <span className="size-1.5 shrink-0 translate-y-[-2px] rounded-full" style={{ background: label?.ink }} />
                    <span className={on ? 'text-ink underline decoration-[0.5px] underline-offset-2' : ''}>{label?.name ?? id}</span>
                  </button>
                )
              })}
            </p>
          )}

          {impactIsFull && model.impact[selected]! > 0 && (
            <p className="mt-3 text-[15px] text-ink-2">
              {model.impact[selected]!.toLocaleString('en-US')} later {model.impact[selected] === 1 ? 'entry traces' : 'entries trace'} back to this one.
            </p>
          )}

          <LinkList title="Built on" edges={model.edgesInto[selected]!} side="source" model={model} />
          <LinkList title="Led to" edges={model.edgesOutOf[selected]!} side="target" model={model} />

          <section className="mt-5">
            <h3 className="border-b border-rule pb-1 text-[15px] italic text-ink-3">How this is dated</h3>
            <p className="mt-2 text-[14.5px] leading-snug text-ink-2">
              {node.anchored
                ? `Placed by its selected anchor, a ${node.placed_by}.`
                : `Placed by its earliest dated record, a ${node.placed_by}. No anchor date has been selected yet, so this is not a claim of first availability.`}
              {node.date_basis ? ` ${node.date_basis}` : ''}
            </p>
            {node.review !== 'accepted' && <p className="mt-1.5 text-[14.5px] italic leading-snug text-ink-3">This claim is still awaiting review.</p>}
            {node.uncertainty && <p className="mt-1.5 text-[14.5px] leading-snug text-ink-2">{node.uncertainty}</p>}
          </section>

          {node.sources.length > 0 && (
            <section className="mt-5">
              <h3 className="border-b border-rule pb-1 text-[15px] italic text-ink-3">Sources</h3>
              <ul className="mt-1.5 space-y-1.5">
                {node.sources.map((id) => {
                  const source = model.sources[id]
                  if (!source) return null
                  return (
                    <li key={id} className="text-[14.5px] leading-snug text-ink-2">
                      {source.url ? (
                        <a href={source.url} target="_blank" rel="noreferrer">
                          {source.title}
                        </a>
                      ) : (
                        source.title
                      )}
                      {source.year ? ` (${source.year})` : ''}
                    </li>
                  )
                })}
              </ul>
            </section>
          )}
        </motion.aside>
      )}
    </AnimatePresence>
  )
}
