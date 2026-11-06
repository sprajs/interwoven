import type { Level, NodeKind, RawDataset, RawLink, RawNode } from './types.ts'

/** Deterministic synthetic data for `?stress=N`, used only to test rendering at scale. */
export function makeStressDataset(count: number): RawDataset {
  let seed = 42
  const rand = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0
    return seed / 4294967296
  }
  const inks = ['#265a96', '#b0472d', '#0c8269', '#a8761a', '#83406f', '#55772b']
  const labels = Array.from({ length: 12 }, (_, i) => ({ id: `group-${i}`, name: `Group ${i}`, ink: inks[i % inks.length]! }))
  const nodes: RawNode[] = []
  for (let i = 0; i < count; i++) {
    const year = Math.round((2026 - 30 * (Math.exp(rand() * 5.4) - 1)) * 10) / 10
    const pick = rand()
    const level = (pick < 0.002 ? 0 : pick < 0.02 ? 1 : pick < 0.2 ? 2 : 3) as Level
    const kind: NodeKind = rand() < 0.3 ? 'science' : 'technology'
    nodes.push({
      id: `s${i}`,
      title: `Synthetic ${i}`,
      kind,
      level,
      year,
      start: year,
      end: year,
      date_label: String(Math.round(year)),
      placed_by: 'synthetic',
      anchored: false,
      labels: [`group-${Math.floor(rand() * 12)}`],
      summary: 'Generated for performance testing. Not real data.',
      regions: [],
      review: 'candidate',
      sources: [],
    })
  }
  nodes.sort((a, b) => a.year - b.year)
  const links: RawLink[] = []
  nodes.forEach((node, i) => {
    if (i === 0) return
    const count = 1 + Math.floor(rand() * 2.6)
    for (let k = 0; k < count; k++) {
      const back = Math.floor(Math.pow(rand(), 3) * Math.min(i, 4000)) + 1
      const parent = nodes[i - back]
      if (parent) links.push({ from: parent.id, to: node.id, relation: 'synthetic', tentative: false })
    }
  })
  return {
    meta: { title: 'Interwoven', description: `Stress test: ${count.toLocaleString('en-US')} synthetic nodes` },
    labels,
    nodes,
    links,
  }
}
