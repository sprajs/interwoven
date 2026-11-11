from pathlib import Path
import json,re,hashlib
p=Path(__file__).resolve().parent
records={n:json.loads((p/f'{n}.json').read_text()) for n in ['cases','sources','claims','graph','comparisons']}
errors=[]
def check(ok,msg):
 if not ok:errors.append(msg)
def required(obj,keys,tag):
 for k in keys.split():check(k in obj,f'{tag}: missing {k}')
cs={x['id'] for x in records['cases']};ss={x['id'] for x in records['sources']};ks={x['id'] for x in records['claims']};ts={x['id'] for x in records['graph']['nodes']}
all_ids=[]
for group in [records['cases'],records['sources'],records['claims'],records['comparisons'],records['graph']['nodes'],records['graph']['edges']]:
 for r in group:all_ids.append(r['id']);check(bool(re.fullmatch(r'PSY-[CSKTEX]\d{2}',r['id'])),f'Bad ID {r["id"]}')
check(len(all_ids)==len(set(all_ids)),'Duplicate IDs')
def refs(items,valid,tag):
 for x in items:check(x in valid,f'{tag}: dangling {x}')
for r in records['cases']:
 tag=r['id'];required(r,'title region period domain outcome summary stages mechanisms counterevidence claim_ids source_ids episode actors labour',tag)
 required(r['episode'],'technology_configuration task population interval contemporary_alternatives adoption_measure observation_limits',tag+'.episode')
 required(r['actors'],'chooser payer operator_maintainer affected_nonchooser ability_to_refuse',tag+'.actors')
 required(r['labour'],'tasks entry_barriers bargaining_ownership transition distribution evidence_limit',tag+'.labour')
 refs(r['claim_ids'],ks,tag);refs(r['source_ids'],ss,tag)
for r in records['sources']:
 required(r,'title authors year url source_type access locator scope_limit evidence_lineage accessed',r['id'])
 check(r['access'] in ['full-text','partial-text','abstract','metadata','search-excerpt'],r['id']+' invalid access')
 if r.get('local_file'):check((p/r['local_file']).is_file(),r['id']+' local source absent')
for r in records['claims']:
 tag=r['id'];required(r,'case_ids statement evidence_type confidence causal_status sources counterevidence inference_limits test',tag)
 refs(r['case_ids'],cs,tag)
 check(r['confidence'] in ['high','medium','low'],tag+' confidence')
 check(r['evidence_type'] in ['historical-primary','archaeological','scholarly-analysis','official-statistics','experiment','institutional-synthesis','synthesis-inference'],tag+' evidence type')
 check(r['causal_status'] in ['descriptive','mechanism-supported','causal-identification','contested','hypothesis'],tag+' causal status')
 for x in r['sources']:required(x,'source_id locator supports',tag);refs([x['source_id']],ss,tag)
 if r['causal_status']=='descriptive':check(r['test']['status']=='descriptive-only',tag+' descriptive test')
 else:
  required(r['test'],'status mechanism_chain strongest_rival discriminating_observation evidence_sought_found remaining_ambiguity hypothesis_timing',tag+'.test')
  check(r['test']['status'] in ['evaluated','underdetermined','proposed'],tag+' test status')
for r in records['graph']['nodes']:required(r,'label kind case_ids',r['id']);refs(r['case_ids'],cs,r['id'])
for r in records['graph']['edges']:
 tag=r['id'];required(r,'from to relation case_ids claim_ids source_ids confidence qualification basis scope alternatives joint_inputs necessity_rationale dispute',tag)
 refs([r['from'],r['to']],ts,tag);refs(r['case_ids'],cs,tag);refs(r['claim_ids'],ks,tag);refs(r['source_ids'],ss,tag);refs(r['joint_inputs'],ts,tag)
 required(r['scope'],'case_id stage configuration',tag+'.scope');check(r['scope']['case_id'] in r['case_ids'],tag+' scope outside cases')
 check(r['basis'] in ['technical-possibility','observed-contribution','documented-transmission','inferred-transmission','bounded-necessity','hypothesis'],tag+' basis')
 check(r['relation'] in ['enables','depends-on','complements','competes-with','displaces','constrains'],tag+' relation')
 if r['relation']=='depends-on':check(r['basis']=='bounded-necessity',tag+' unsupported necessity')
 if r['basis']!='bounded-necessity':check(r['necessity_rationale']=='No necessity claim',tag+' unexpected necessity rationale')
for r in records['comparisons']:
 required(r,'question case_ids useful_similarities important_differences evidence_comparability connections_nonindependence omitted_countercases conclusion_limit',r['id']);refs(r['case_ids'],cs,r['id'])
report=(p/'report.md').read_text();words=len(report.split());check(2500<=words<=3500,f'Report word count {words}')
# Every claim is cited singly or in an inclusive claim range in the report.
mentioned=set(re.findall(r'PSY-K\d{2}',report))
for a,b in re.findall(r'PSY-K(\d{2})[–-](\d{2})',report):mentioned.update(f'PSY-K{i:02}' for i in range(int(a),int(b)+1))
check(ks<=mentioned,'Claims absent from report: '+str(ks-mentioned))
manifest=json.loads((p/'cache/download_manifest.json').read_text());verified=0
for r in records['sources']:
 if not r.get('local_file'):continue
 f=p/r['local_file'];h=hashlib.sha256(f.read_bytes()).hexdigest()
 entries=[m for m in manifest if m.get('source_id')==r['id'].replace('PSY-','') and m.get('sha256')==h]
 check(bool(entries),r['id']+' source hash not in acquisition manifest')
 if entries:verified+=1
summary={'status':'pass' if not errors else 'fail','errors':errors,'counts':{'cases':len(cs),'sources':len(ss),'claims':len(ks),'graph_nodes':len(ts),'graph_edges':len(records['graph']['edges']),'comparisons':len(records['comparisons']),'report_words':words},'source_access':{'full_text':sum(r['access']=='full-text' for r in records['sources']),'abstract':sum(r['access']=='abstract' for r in records['sources']),'hash_verified_local_sources':verified},'scope':'Structural fields, enum values, IDs/references, scoped graph semantics, claim coverage, report length and downloaded-byte hashes. Not an independent source-entailment or historical-truth audit.'}
(p/'validation.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
raise SystemExit(bool(errors))
