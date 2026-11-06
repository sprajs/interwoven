import { NODE_TYPES } from '../data/types.ts'
import { formatYear } from '../engine/time.ts'
import { useApp } from '../store.ts'
import { ShapeIcon } from './icons.tsx'

export function Tooltip() {
  const hover = useApp((s) => s.hover)
  const model = useApp((s) => s.model)
  const selected = useApp((s) => s.selected)
  if (!hover || !model || hover.index === selected) return null
  const node = model.nodes[hover.index]
  if (!node) return null
  const lane = model.lanes[model.domainIndex[hover.index]!]!
  const width = 272
  const flip = hover.x + width + 24 > window.innerWidth
  const left = flip ? hover.x - width - 16 : hover.x + 16
  const top = Math.min(window.innerHeight - 170, hover.y + 14)
  return (
    <div className="glass pointer-events-none absolute z-40 rounded-xl p-3" style={{ left, top, width }} role="status">
      <div className="flex items-baseline justify-between gap-2">
        <h3 className="text-[13.5px] font-semibold leading-snug">{node.title}</h3>
        <span className="shrink-0 font-mono text-[11px] text-ink-2">{formatYear(node.year)}</span>
      </div>
      <p className="mt-1 flex items-center gap-1.5 text-[11.5px] text-ink-2">
        <ShapeIcon type={node.type} color={lane.color} size={10} />
        {NODE_TYPES.find((t) => t.id === node.type)?.label} in {lane.label}
      </p>
      <p className="mt-1.5 text-xs leading-relaxed text-ink">{node.summary}</p>
    </div>
  )
}
