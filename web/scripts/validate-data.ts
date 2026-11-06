// Usage: npm run validate [path/to/timeline.json]
import { readFileSync } from 'node:fs'
import { validateDataset } from '../src/data/validate.ts'
import type { RawDataset } from '../src/data/types.ts'

const path = process.argv[2] ?? 'public/data/timeline.json'
const data = JSON.parse(readFileSync(path, 'utf8')) as RawDataset
const issues = validateDataset(data)

for (const issue of issues) console.log(`${issue.severity === 'error' ? 'ERROR' : 'warn '}  ${issue.message}`)
const edges = data.nodes.reduce((sum, n) => sum + n.builds_on.length + (n.informed_by?.length ?? 0), 0)
console.log(`${data.nodes.length} nodes, ${edges} links, ${issues.length} issue(s) in ${path}`)
if (issues.some((i) => i.severity === 'error')) process.exit(1)
