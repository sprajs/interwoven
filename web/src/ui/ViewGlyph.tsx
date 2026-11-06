import { useMemo } from 'react'
import { rowOrder, storyIndex } from '../data/derive.ts'
import type { Model } from '../data/model.ts'
import type { Mode } from '../engine/Engine.ts'

const W = 42
const H = 18
/** Tiny drawings stay cheap on huge datasets by drawing a sample. */
const SAMPLE = 260

const fmt = (v: number) => v.toFixed(1)

function sampled<T>(items: readonly T[]): readonly T[] {
  if (items.length <= SAMPLE) return items
  const step = items.length / SAMPLE
  return Array.from({ length: SAMPLE }, (_, i) => items[Math.floor(i * step)]!)
}

/** Each view's button carries a small drawing of that view, made from the actual data. */
function drawGlyph(model: Model, mode: Mode): string {
  const x = (i: number) => model.time.compressed(model.nodes[i]!.year) * W
  if (mode === 'threads') {
    return sampled(model.edges)
      .map((e) => `M${fmt(x(e.source))} ${fmt(model.y[e.source]! * H)}L${fmt(x(e.target))} ${fmt(model.y[e.target]! * H)}`)
      .join('')
  }
  if (mode === 'density') {
    const bins = new Float32Array(Math.floor(W / 2))
    for (const node of sampled(model.nodes)) bins[Math.min(bins.length - 1, Math.floor(model.time.compressed(node.year) * bins.length))]! += 1
    const max = Math.max(1, ...bins)
    return [...bins]
      .map((count, b) => {
        const h = Math.sqrt(count / max) * H * 0.5
        return h > 0 ? `M${b * 2 + 1} ${fmt(H / 2 - h)}V${fmt(H / 2 + h)}` : ''
      })
      .join('')
  }
  if (mode === 'reach') {
    const reach = model.reach
    const rows = rowOrder(model.nodes, model.children, model.parents, reach, 'thread')
    const n = rows.length
    return sampled([...rows.keys()])
      .map((row) => {
        const i = rows[row]!
        const y = (row / Math.max(1, n - 1)) * H
        const end = model.time.compressed(reach.any[i]!) * W
        return `M${fmt(x(i))} ${fmt(y)}H${fmt(Math.max(end, x(i) + 1.2))}`
      })
      .join('')
  }
  const story = storyIndex(model.nodes, model.edges)[0]
  if (!story) return ''
  const rows = new Map(story.members.map((i, k) => [i, k]))
  const first = model.nodes[story.first]!.year
  const span = Math.max(1, model.nodes[story.last]!.year - first)
  const sx = (i: number) => ((model.nodes[i]!.year - first) / span) * (W - 2) + 1
  const sy = (i: number) => (rows.get(i)! / Math.max(1, story.members.length - 1)) * (H - 1) + 0.5
  return sampled(model.edges)
    .filter((e) => rows.has(e.source) && rows.has(e.target))
    .map((e) => `M${fmt(sx(e.source))} ${fmt(sy(e.source))}V${fmt(sy(e.target))}H${fmt(sx(e.target))}`)
    .join('')
}

export function ViewGlyph({ model, mode }: { model: Model | null; mode: Mode }) {
  const path = useMemo(() => (model ? drawGlyph(model, mode) : ''), [model, mode])
  return (
    <svg width={W} height={H} viewBox={`0 ${-0.5} ${W} ${H + 1}`} aria-hidden className="block overflow-visible">
      <path d={path} fill="none" stroke="currentColor" strokeWidth={mode === 'density' ? 1 : mode === 'threads' ? 0.6 : 0.75} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
