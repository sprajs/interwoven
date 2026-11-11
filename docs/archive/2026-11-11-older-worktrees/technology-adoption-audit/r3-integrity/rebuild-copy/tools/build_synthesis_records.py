#!/usr/bin/env python3
"""Compile deliberately authored synthesis specifications, preserving case provenance."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
p=root/'contributions/SYN'
allclaims={c['id']:c for f in (root/'contributions').glob('*/claims.json') for c in json.loads(f.read_text()) if f.parent.name!='SYN'}
base=[c for c in json.loads((p/'claims.json').read_text()) if int(c['id'].split('K')[1])<10]
specs=json.loads((p/'synthesis_specs.json').read_text())
new=[]
for s in specs:
 refs=s.pop('underlying_claim_ids');missing=[r for r in refs if r not in allclaims]
 if missing:raise SystemExit(f'Missing underlying claims: {missing}')
 supports=[];seen=set()
 for r in refs:
  for sup in allclaims[r]['sources']:
   key=(sup['source_id'],str(sup['locator']))
   if key in seen:continue
   seen.add(key);supports.append(dict(source_id=sup['source_id'],locator=sup['locator'],supports=f'Bounded evidence in {r}: '+sup['supports']))
 s.update(case_ids=sorted({x for r in refs for x in allclaims[r]['case_ids']}),sources=supports,evidence_type='synthesis-inference',underlying_claim_ids=refs)
 if s['test']['status']!='descriptive-only':
  s['test']['evidence_sought_found']='Compared case-level claims '+', '.join(refs)+'. '+s['test']['evidence_sought_found']
 new.append(s)
(p/'claims.json').write_text(json.dumps(base+new,indent=2,ensure_ascii=False)+'\n')
print(f'Wrote {len(base)+len(new)} synthesis claims. comparisons.json is separately authored canonical data.')
