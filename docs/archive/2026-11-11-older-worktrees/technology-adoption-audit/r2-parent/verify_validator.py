from pathlib import Path
import json,shutil,subprocess,sys,tempfile
R=Path(__file__).resolve().parents[1]/'r2-snapshot';rows=[]
with tempfile.TemporaryDirectory(prefix='r2-invalid-records-') as td:
 base=Path(td);(base/'tools').mkdir();(base/'contributions').mkdir()
 shutil.copytree(R/'contributions/MAT',base/'contributions/MAT')
 for tool in ['build_collection.py','build_explorer.py']:shutil.copy2(R/'tools'/tool,base/'tools'/tool)
 for kind,mutate,expected in [('claims',lambda a:a[0]['test'].update(status='invalid-for-audit'),'invalid test status'),('graph',lambda a:a['edges'][0].update(alternatives='invalid-for-audit'),'alternatives not array'),('graph',lambda a:next(x for x in a['edges'] if x['basis']=='bounded-necessity').update(necessity_rationale=''),'needs substantive rationale')]:
  p=base/'contributions/MAT'/f'{kind}.json';raw=p.read_bytes();obj=json.loads(raw);mutate(obj);p.write_text(json.dumps(obj))
  run=subprocess.run([sys.executable,str(base/'tools/build_collection.py')],capture_output=True,text=True)
  validation=json.loads((base/'data/validation.json').read_text());errors=validation['errors']
  rows.append({'probe':expected,'exit_code':run.returncode,'matched_errors':[e for e in errors if expected in e],'passed':run.returncode!=0 and any(expected in e for e in errors)})
  p.write_bytes(raw)
 for name in ['cases','claims','sources','graph','comparisons']:shutil.copy2(R/'data'/f'{name}.json',base/'data'/f'{name}.json')
 run=subprocess.run([sys.executable,str(base/'tools/build_explorer.py')],capture_output=True,text=True)
 rows.append({'probe':'explorer rejects validation errors','exit_code':run.returncode,'stderr':run.stderr,'passed':run.returncode!=0 and 'Refusing explorer generation' in run.stderr})
output={'probes':rows,'all_passed':all(x['passed'] for x in rows),'scope':'Isolated invalid copies only. Real MAT report/questions retained. Existing unrelated link warnings are not used as the rejection signal.'}
(R.parent/'r2-parent/validator-verification.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))
