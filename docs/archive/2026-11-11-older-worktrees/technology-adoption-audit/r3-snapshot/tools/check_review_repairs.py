#!/usr/bin/env python3
"""Verify reviewed record distinctions, lossless exports and validator rejection probes."""
from pathlib import Path
import csv, hashlib, json, re, shutil, subprocess, sys, tempfile
R=Path(__file__).resolve().parents[1]
load=lambda p:json.loads(p.read_text())
results=[]
def check(name,ok):
 results.append({'check':name,'passed':bool(ok)})
 if not ok:raise AssertionError(name)
g=load(R/'data/graph.json'); e={x['id']:x for x in g['edges']}
check('IND-E04 coalfield scope', 'coal-mining' in e['IND-E04']['scope']['configuration'] and e['IND-E04']['scope']['stage'].startswith('early deployment'))
check('IND-E05 dear-coal Cornwall', 'expensive imported coal' in e['IND-E05']['scope']['configuration'])
check('atmospheric coalfield/Cornish comparators distinct',e['IND-E04']['to']!=e['IND-E05']['to'])
check('ancient/replica operation distinct',e['MAT-E08']['to']!=e['MAT-E06']['from'] and e['MAT-E06']['from']==e['MAT-E07']['from'])
check('waterpower episodes distinct',e['IND-E01']['from']!=e['IND-E09']['to'] and e['IND-E01']['from']!=e['IND-E11']['to'])
check('IND-E14 hypothesis', e['IND-E14']['basis']=='hypothesis' and e['IND-E14']['confidence']=='low')
k={x['id']:x for x in load(R/'data/claims.json')}
check('IND-K10 retains uncertainty',k['IND-K10']['test']['status']=='underdetermined' and 'cannot explain timing' not in k['IND-K10']['test']['mechanism_chain'])
check('LBR-K02 genuine rival','local demand' in k['LBR-K02']['test']['strongest_rival'] and 'Aggregate recovery may conceal' not in k['LBR-K02']['test']['strongest_rival'])
c={x['id']:x for x in load(R/'data/cases.json')}
check('MAT-C06 qualified outcome',c['MAT-C06']['outcome'][1].startswith('proposed'))
check('real IND handoff and full records', (R/'contributions/IND/questions.md').stat().st_size>200 and all(f'IND-C{i:02}' in c for i in range(1,9)) and all(f'IND-K{i:02}' in k for i in range(1,26)) and all(f'IND-E{i:02}' in e for i in range(1,31)))
html=(R/'index.html').read_text(); payload=json.loads(re.search(r'<script id="research-data" type="application/json">(.*?)</script>',html,re.S).group(1))
for kind in ['cases','claims','sources','graph','comparisons','validation']:
 check(f'{kind}: embedded HTML equals compiled JSON',payload[kind]==load(R/'data'/f'{kind}.json'))
for kind in ['cases','claims','sources','comparisons']:
 compiled=load(R/'data'/f'{kind}.json'); rows=list(csv.DictReader((R/'data'/f'{kind}.csv').open()))
 reconstructed=[{key:json.loads(row[key]) if isinstance(rec[key],(dict,list)) else row[key] for key in rec} for row,rec in zip(rows,compiled)]
 # Years may be numbers; CSV scalar round-trip uses string representation.
 check(f'{kind}: CSV preserves all fields',len(rows)==len(compiled) and all(all((('' if expected[key] is None else str(expected[key]))==actual[key] if not isinstance(expected[key],(dict,list)) else expected[key]==actual[key]) for key in expected) for expected,actual in zip(compiled,reconstructed)))
manifest=load(R/'reviews/round1/snapshot/MANIFEST.json')
check('round1 snapshot remains immutable',all(hashlib.sha256((R/'reviews/round1/snapshot'/p).read_bytes()).hexdigest()==sha for p,sha in manifest['files'].items()))
# Deliberately invalid records in isolated copies must be rejected. No probe edits main data.
with tempfile.TemporaryDirectory(prefix='tech-review-probes-') as td:
 base=Path(td); (base/'tools').mkdir();(base/'contributions/MAT').mkdir(parents=True)
 shutil.copy2(R/'tools/build_collection.py',base/'tools/build_collection.py');shutil.copy2(R/'tools/build_explorer.py',base/'tools/build_explorer.py')
 for f in (R/'contributions/MAT').iterdir():
  if f.is_file() and f.suffix=='.json':shutil.copy2(f,base/'contributions/MAT'/f.name)
 for fn in ['report.md','questions.md']:(base/'contributions/MAT'/fn).write_text('Isolated validation probe, not research evidence.\n')
 probes=[('claims.json',lambda d:d[0]['test'].update(status='invented-status'),'invalid test status'),('graph.json',lambda d:d['edges'][0].update(alternatives='wrong-type'),'alternatives not array'),('graph.json',lambda d:next(x for x in d['edges'] if x['basis']=='bounded-necessity').update(necessity_rationale=''),'needs substantive rationale')]
 for filename,mutate,needle in probes:
  p=base/'contributions/MAT'/filename;original=p.read_bytes();d=json.loads(original);mutate(d);p.write_text(json.dumps(d))
  run=subprocess.run([sys.executable,str(base/'tools/build_collection.py')],capture_output=True,text=True)
  check(f'negative probe: {needle}',run.returncode!=0 and needle in run.stdout)
  p.write_bytes(original)
 # Last failed validation must block explorer; supply other payload files to isolate the guard.
 for name in ['cases','claims','sources','graph','comparisons']:shutil.copy2(R/'data'/f'{name}.json',base/'data'/f'{name}.json')
 run=subprocess.run([sys.executable,str(base/'tools/build_explorer.py')],capture_output=True,text=True)
 check('explorer refuses invalid collection',run.returncode!=0 and 'Refusing explorer generation' in run.stderr)
output={'results':results,'passed':all(x['passed'] for x in results),'limit':'Record consistency and transport checks; no new historical source entailment or visual acceptance.'}
(R/'reviews/external-r1/REPAIR_CHECKS.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({'passed':output['passed'],'checks':len(results)}))
