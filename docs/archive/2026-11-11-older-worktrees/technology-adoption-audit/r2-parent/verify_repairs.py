from pathlib import Path
import csv,hashlib,json,re,shutil,subprocess,sys,tempfile
A=Path(__file__).resolve().parents[1];R=A/'r2-snapshot'; checks=[]
def add(name,ok,detail=None):
 checks.append({'name':name,'passed':bool(ok),'detail':detail})
load=lambda p:json.loads(p.read_text())
m=load(R/'MANIFEST.json')
add('frozen files match capture hashes',all(hashlib.sha256((R/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in m['files']),len(m['files']))
d={k:load(R/'data'/f'{k}.json') for k in ['cases','claims','sources','comparisons','graph','validation']}
c={x['id']:x for x in d['cases']};k={x['id']:x for x in d['claims']};e={x['id']:x for x in d['graph']['edges']};n={x['id']:x for x in d['graph']['nodes']}
for pref in ['IND','MAT','LBR']:
 for kind in ['cases','claims','sources','comparisons','graph']:
  own=load(R/'contributions'/pref/(kind+'.json'))
  groups=['nodes','edges'] if kind=='graph' else [kind]
  for g in groups:
   compiled=d['graph'][g] if kind=='graph' else d[kind]
   selected=[{a:b for a,b in x.items() if a!='contribution'} for x in compiled if x['contribution']==pref]
   add(f'{pref}/{g} equals compiled',selected==(own[g] if kind=='graph' else own))
add('R1-01 cheap coal now bounded to early British coalfields','coal-mining' in e['IND-E04']['scope']['configuration'] and 'after 1712' in e['IND-E04']['scope']['stage'] and e['IND-E04']['to']=='IND-T05')
add('R1-01 dear coal comparison retains separate Cornwall instance','expensive imported coal' in e['IND-E05']['scope']['configuration'] and e['IND-E05']['to']=='IND-T34' and e['IND-E04']['to']!=e['IND-E05']['to'])
add('R1-02 Meroe actual and experimental operations are separate',e['MAT-E08']['to']=='MAT-T30' and e['MAT-E06']['from']==e['MAT-E07']['from']=='MAT-T28')
add('R1-02 local waterpower configurations are separate',e['IND-E01']['from']=='IND-T02' and e['IND-E09']['to']==e['IND-E11']['to']=='IND-T33')
incident={nid:[x['id'] for x in e.values() if nid in [x['from'],x['to']]] for nid in ['MAT-T28','MAT-T30','IND-T02','IND-T33','IND-T05','IND-T34']}
add('R1-03 K10 retains underdetermination and marginal-cost distinction',k['IND-K10']['test']['status']=='underdetermined' and 'weakens the proposed general wage-surge premise' in k['IND-K10']['test']['mechanism_chain'] and 'exclude wage incentives' in k['IND-K10']['test']['mechanism_chain'])
add('R1-04 MAT-C06 proposed transmission outcome',c['MAT-C06']['outcome'][1].startswith('proposed '))
add('R1-04 LBR-K02 genuine demand/selection rival', 'local demand trends' in k['LBR-K02']['test']['strongest_rival'] and 'pre-trends' in k['LBR-K02']['test']['discriminating_observation'])
add('R1-OPEN-01 E14 qualified hypothesis with provenance',e['IND-E14']['basis']=='hypothesis' and e['IND-E14']['confidence']=='low' and 'projected wage savings' in e['IND-E14']['scope']['configuration'] and 'not measured recruitment effects' in e['IND-E14']['dispute'])
add('R1-HANDOFF-01 real IND questions and complete intended IDs',(R/'contributions/IND/questions.md').stat().st_size>9000 and all(f'IND-C{i:02}' in c for i in range(1,9)) and all(f'IND-K{i:02}' in k for i in range(1,26)) and all(f'IND-E{i:02}' in e for i in range(1,31)))
for eid,kid in [('MAT-E03','MAT-K04'),('MAT-E12','MAT-K10')]:add('R1-LEAD-01 '+eid+' aligned with rationale',e[eid]['confidence']==k[kid]['confidence']=='medium' and 'narrower-proposition' in e[eid]['dispute'])
h=(R/'index.html').read_text();payload=json.loads(re.search(r'<script id="research-data" type="application/json">(.*?)</script>',h,re.S).group(1))
for kind in d:add(kind+' exact HTML data parity',payload[kind]==d[kind])
for kind in ['cases','claims','sources','comparisons']:
 with (R/'data'/f'{kind}.csv').open() as f: rows=list(csv.DictReader(f))
 ok=len(rows)==len(d[kind]); count=0
 for rec,row in zip(d[kind],rows):
  for field,v in rec.items():
   count+=1
   if isinstance(v,(dict,list)):ok=ok and json.loads(row[field])==v
   else:ok=ok and row[field]==('' if v is None else str(v))
 add(kind+' CSV field preservation',ok,{'rows':len(rows),'fields':count})
for phrase,fn in [('weakens the proposed general wage-surge premise','data/CLAIM_LEDGER.md'),('Different local demand trends','data/CLAIM_LEDGER.md'),('Hosler proposed South/Central American transmission','cases/MAT-C06.md'),('| IND-E14 | Cheap and controlled labour recruitment | complements | Mechanised British spinning | hypothesis |','data/GRAPH_GUIDE.md')]:add('Markdown retains: '+phrase,phrase in (R/fn).read_text(),fn)
with tempfile.TemporaryDirectory(prefix='external-r2-rebuild-') as td:
 dst=Path(td)/'frozen-copy';shutil.copytree(R,dst)
 for pref in m['incomplete_at_capture']:(dst/'contributions'/pref).mkdir(exist_ok=True)
 run=subprocess.run([sys.executable,str(dst/'tools/build_collection.py')],capture_output=True,text=True)
 v=load(dst/'data/validation.json')
 rebuilt={kind:load(dst/'data'/f'{kind}.json') for kind in ['cases','claims','sources','comparisons','graph']}
 add('unmodified builder preserves all completed records',all(rebuilt[k]==d[k] for k in rebuilt),{'returncode':run.returncode,'counts':v['counts'],'record_differences':{kind:{'missing_from_compiled':[x for x in (rebuilt['graph'][kind] if kind in ['nodes','edges'] else rebuilt[kind]) if x['id'] not in {y['id'] for y in (d['graph'][kind] if kind in ['nodes','edges'] else d[kind])}],'changed_ids':[x['id'] for x in (rebuilt['graph'][kind] if kind in ['nodes','edges'] else rebuilt[kind]) if x['id'] in {y['id'] for y in (d['graph'][kind] if kind in ['nodes','edges'] else d[kind])} and x!={y['id']:y for y in (d['graph'][kind] if kind in ['nodes','edges'] else d[kind])}[x['id']]]} for kind in ['cases','claims','sources','comparisons','nodes','edges']},'errors':v['errors'],'local_link_errors':v.get('local_link_errors',[])})
 add('real IND gate succeeds on rebuild','IND' in v['completed_contributions'] and all(sum(x['contribution']=='IND' for x in (rebuilt['graph'][kind] if kind in ['nodes','edges'] else rebuilt[kind]))==num for kind,num in [('cases',8),('claims',25),('edges',30)]))
 # Snapshot deliberately excludes review archives and source-note assets; link-only errors reflect that selection, not historical readiness.
 add('rebuild has no non-link validation errors',all('broken local link' in err for err in v['errors']),v['errors'])
out={'snapshot_manifest_sha256':hashlib.sha256((R/'MANIFEST.json').read_bytes()).hexdigest(),'checks':checks,'incident_edges':incident,'all_passed':all(x['passed'] for x in checks),'limits':'Source-passage adjudication is in the report/R1 audit, not inferred from these consistency checks. Frozen snapshot excludes review archives and source-note assets; temporary rebuild may report those omitted local links. No main or snapshot files changed.'}
(A/'r2-parent/repair-verification.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'all_passed':out['all_passed'],'failed':[x for x in checks if not x['passed']],'incident_edges':incident},indent=2))
