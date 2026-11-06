import { formatYear } from '../engine/time.ts'
import { getEngine, useApp } from '../store.ts'
import { EvidenceBadge } from './icons.tsx'

const firstSentence = (text: string) => {
  const match = /^.+?[.!?](\s|$)/.exec(text)
  return match ? match[0].trim() : text
}

const WIDTH = 276

export function Tooltip() {
  const hover = useApp((s) => s.hover)
  const model = useApp((s) => s.model)
  const selected = useApp((s) => s.selected)
  const mode = useApp((s) => s.mode)
  if (!hover || !model || hover.index === selected) return null
  const node = model.nodes[hover.index]
  if (!node) return null
  const reachEnd = getEngine()?.reach?.any[hover.index]
  const loose = model.links.filter((link) => (link.from === node.id && !model.indexById.has(link.to)) || (link.to === node.id && !model.indexById.has(link.from))).length
  const flip = hover.x + WIDTH + 24 > window.innerWidth
  const left = flip ? hover.x - WIDTH - 12 : hover.x + 12
  const top = Math.min(window.innerHeight - 192, hover.y + 12)
  return (
    <div className="sheet pointer-events-none absolute z-40 border border-rule px-4 py-2" style={{ left, top, width: WIDTH }} role="status">
      <p className="note">{node.date_label}</p>
      <EvidenceBadge strength={node.evidence_strength} />
      <h3 className={`text-body ${node.kind === 'science' ? 'science' : ''}`}>{node.title}</h3>
      <EvidenceBadge strength={node.evidence_strength} />
      <p className="mt-1 text-note text-ink-2">{firstSentence(node.summary)}</p>
      {node.entry_community && <p className="note mt-1">{node.entry_community}</p>}
      {loose > 0 && <p className="note mt-1">{loose} {loose === 1 ? 'link goes' : 'links go'} to entries not yet placed.</p>}
      {model.parents[hover.index]!.length + model.children[hover.index]!.length > 0 && mode !== 'story' && <p className="note mt-1">Click twice to follow its thread.</p>}
      {mode === 'reach' && reachEnd !== undefined && reachEnd > node.year && <p className="note mt-1">Built on until {formatYear(reachEnd)}. How long it lasted is another question.</p>}
    </div>
  )
}
