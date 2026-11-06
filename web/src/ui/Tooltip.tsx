import { useApp } from '../store.ts'

const firstSentence = (text: string) => {
  const match = /^.+?[.!?](\s|$)/.exec(text)
  return match ? match[0].trim() : text
}

export function Tooltip() {
  const hover = useApp((s) => s.hover)
  const model = useApp((s) => s.model)
  const selected = useApp((s) => s.selected)
  if (!hover || !model || hover.index === selected) return null
  const node = model.nodes[hover.index]
  if (!node) return null
  const width = 268
  const flip = hover.x + width + 24 > window.innerWidth
  const left = flip ? hover.x - width - 14 : hover.x + 14
  const top = Math.min(window.innerHeight - 190, hover.y + 14)
  return (
    <div className="sheet pointer-events-none absolute z-40 border border-rule px-3 py-2" style={{ left, top, width }} role="status">
      <p className="text-[14px] text-ink-3">{node.date_label}</p>
      <h3 className={`text-[17px] font-medium leading-tight ${node.kind === 'science' ? 'italic' : ''}`}>{node.title}</h3>
      <p className="mt-1 text-[14.5px] leading-snug text-ink-2">{firstSentence(node.summary)}</p>
    </div>
  )
}
