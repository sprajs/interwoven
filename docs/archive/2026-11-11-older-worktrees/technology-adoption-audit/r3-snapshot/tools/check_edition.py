#!/usr/bin/env python3
"""Check complete canonical/export parity and frozen review integrity. No factual certification."""
from pathlib import Path
import json,csv,re,hashlib
R=Path(__file__).resolve().parents[1]
load=lambda p:json.loads(p.read_text())
checks=[]
def check(name,ok,detail=None):
 checks.append(dict(check=name,passed=bool(ok),detail=detail))
 if not ok:raise AssertionError(f'{name}: {detail}')
v=load(R/'data/validation.json')
check('collection validation has no errors',not v['errors'],v['errors'])
check('all contribution directories included',not v['incomplete_contributions'],v['incomplete_contributions'])
expected={k:[] for k in ['cases','sources','claims','comparisons','nodes','edges']}
for pre in v['completed_contributions']:
 p=R/'contributions'/pre
 for kind in ['cases','sources','claims','comparisons']:
  expected[kind]+=[dict(x,contribution=pre) for x in load(p/f'{kind}.json')]
 current=load(p/'EDITION_VALIDATION.json')
 check(f'{pre} current validation hashes',all(hashlib.sha256((p/f).read_bytes()).hexdigest()==sha for f,sha in current['canonical_hashes'].items()))
 g=load(p/'graph.json')
 for kind in ['nodes','edges']:expected[kind]+=[dict(x,contribution=pre) for x in g[kind]]
actual={k:load(R/'data'/f'{k}.json') for k in ['cases','sources','claims','comparisons']}
actual.update({k:load(R/'data/graph.json')[k] for k in ['nodes','edges']})
for kind in expected:
 check(f'canonical {kind} equals complete compiled records',{x['id']:x for x in expected[kind]}=={x['id']:x for x in actual[kind]},f'{len(expected[kind])} records')
 check(f'{kind} count matches validation',len(actual[kind])==v['counts'][kind])
for kind in ['cases','sources','claims','comparisons']:
 rows=list(csv.DictReader((R/'data'/f'{kind}.csv').open()));a=actual[kind]
 check(f'{kind} CSV row count',len(rows)==len(a))
 for row,record in zip(rows,a):
  for key,val in record.items():
   got=json.loads(row[key]) if isinstance(val,(dict,list)) else row[key]
   want=val if isinstance(val,(dict,list)) else '' if val is None else str(val)
   if got!=want:raise AssertionError(f'CSV {kind} {record["id"]} {key}')
 check(f'{kind} CSV all fields round-trip',True)
html=(R/'index.html').read_text();m=re.search(r'<script id="research-data" type="application/json">(.*?)</script>',html,re.S)
check('HTML payload found',m is not None);payload=json.loads(m.group(1))
for kind in ['cases','sources','claims','comparisons','graph','validation','chronology']:
 check(f'HTML {kind} equals compiled file',payload[kind]==load(R/'data'/f'{kind}.json'))
chron=load(R/'data/chronology.json');covered={i for a in chron['routes'] for i in a['case_ids']}
check('chronology covers exactly all cases',covered=={c['id'] for c in actual['cases']})
for c in actual['cases']:
 check(f'case page {c["id"]} exists',(R/'cases'/f'{c["id"]}.md').exists())
manifest_count=0;file_count=0
for p in sorted((R/'reviews').rglob('MANIFEST.json')):
 if not (p.parent.name.endswith('snapshot') or p.parent.name in {'later-selected','integration-specs-supplement'}):continue
 m=load(p)
 entries=m.get('files')
 if isinstance(entries,list):entries={x.get('path',x.get('snapshot_path')):x['sha256'] for x in entries}
 check(f'recognized snapshot manifest: {p.relative_to(R)}',isinstance(entries,dict) and all(isinstance(k,str) and isinstance(v,str) for k,v in entries.items()))
 bad=[f for f,sha in entries.items() if not (p.parent/f).exists() or hashlib.sha256((p.parent/f).read_bytes()).hexdigest()!=sha]
 check(f'preserved review snapshot: {p.relative_to(R)}',not bad,bad)
 manifest_count+=1;file_count+=len(entries)
# These objects were previously stale in otherwise internally consistent exports.
g={x['id']:x for x in actual['nodes']+actual['edges']};k={x['id']:x for x in actual['claims']}
check('reviewed OCE governance is in final export','OCE-T26' in g and 'OCE-E19' in g)
check('Martu mechanism remains underdetermined',k['OCE-K11']['test']['status']=='underdetermined')
check('SKL distinct build configurations',len({g[e]['to'] for e in ['SKL-E16','SKL-E17','SKL-E18','SKL-E19']})==4)
result=dict(passed=all(x['passed'] for x in checks),counts=v['counts'],checks=checks,review_snapshots_checked=manifest_count,review_files_checked=file_count,limits='Structural integrity and exact transport, not historical truth, full-source audit, graph causal closure or browser verification.')
(R/'data/EDITION_CHECKS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(passed=result['passed'],checks=len(checks),snapshots=manifest_count,files=file_count,counts=v['counts'])))
