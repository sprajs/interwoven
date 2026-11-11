#!/usr/bin/env python3
"""Validate authored navigation coverage and render dated routes, without inferring chronology."""
from pathlib import Path
import json
r=Path(__file__).resolve().parents[1]
d=json.loads((r/'analysis/chronology_routes.json').read_text())
cases={c['id']:c for p in (r/'contributions').glob('*/cases.json') for c in json.loads(p.read_text())}
covered={i for a in d['routes'] for i in a['case_ids']}
if covered-set(cases) or set(cases)-covered:raise SystemExit(f'Chronology unresolved={covered-set(cases)} uncovered={set(cases)-covered}')
(r/'data/chronology.json').write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
lines=['# Dated case routes','',d['caution'],'',f'All {len(cases)} cases have at least one route. Route membership is editorial navigation, not an additional historical claim.','']
for a in d['routes']:
 lines += [f'## {a["title"]}','',a['scope'],'','| Case | Observed interval |','|---|---|']
 for i in a['case_ids']:
  c=cases[i];title=c['title'].replace('|','\\|');period=c['period'].replace('|','\\|')
  lines.append(f'| [{i} — {title}](../cases/{i}.md) | {period} |')
 lines.append('')
(r/'data/CHRONOLOGICAL_ROUTES.md').write_text('\n'.join(lines)+'\n')
print(f'Validated {len(cases)} cases in {len(d["routes"])} overlapping routes')
