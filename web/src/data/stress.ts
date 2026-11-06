import type { Level, NodeType, RawDataset, RawNode } from './types.ts'

/** Deterministic synthetic data for `?stress=N`, used only to test rendering at scale. */
export function makeStressDataset(base: RawDataset, count: number): RawDataset {
  let seed = 42
  const rand = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0
    return seed / 4294967296
  }
  const types: NodeType[] = ['discovery', 'theory', 'instrument', 'invention', 'system']
  const nodes: RawNode[] = []
  const end = 2026
  for (let i = 0; i < count; i++) {
    // Most entries are recent, with a long thin tail into the past.
    const year = Math.round((end - 30 * (Math.exp(rand() * 5.4) - 1)) * 10) / 10
    const pick = rand()
    const level = (pick < 0.002 ? 0 : pick < 0.02 ? 1 : pick < 0.2 ? 2 : 3) as Level
    nodes.push({
      id: `s${i}`,
      title: `Synthetic ${i}`,
      year,
      level,
      type: types[Math.floor(rand() * types.length)]!,
      domain: base.domains[Math.floor(rand() * base.domains.length)]!.id,
      labels: [`group-${Math.floor(rand() * 12)}`],
      builds_on: [],
      summary: 'Generated for performance testing. Not real data.',
    })
  }
  nodes.sort((a, b) => a.year - b.year)
  nodes.forEach((node, i) => {
    if (i === 0) return
    const links = 1 + Math.floor(rand() * 2.6)
    for (let k = 0; k < links; k++) {
      const back = Math.floor(Math.pow(rand(), 3) * Math.min(i, 4000)) + 1
      const parent = nodes[i - back]
      if (parent && !node.builds_on.includes(parent.id)) node.builds_on.push(parent.id)
    }
  })
  return { ...base, meta: { title: `Stress test: ${count.toLocaleString('en-US')} synthetic nodes` }, nodes }
}
