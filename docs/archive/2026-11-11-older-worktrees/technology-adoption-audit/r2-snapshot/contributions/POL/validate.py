from pathlib import Path
import json, hashlib, re
R=Path(__file__).parent
files={n:json.loads((R/(n+'.json')).read_text()) for n in ('cases','sources','claims','graph','comparisons')}
errors=[]
def ck(ok,msg):
 if not ok: errors.append(msg)
def fields(obj,keys,label):
 for k in keys: ck(k in obj and obj[k] not in ('',None),f'{label}: missing/empty {k}')
def refs(ids,valid,label):
 for x in ids:ck(x in valid,f'{label}: unresolved {x}')
case_ids={x['id'] for x in files['cases']};source_ids={x['id'] for x in files['sources']};claim_ids={x['id'] for x in files['claims']};node_ids={x['id'] for x in files['graph']['nodes']}
all_records=files['cases']+files['sources']+files['claims']+files['graph']['nodes']+files['graph']['edges']+files['comparisons']
ids=[x['id'] for x in all_records];ck(len(ids)==len(set(ids)),'IDs are not globally unique')
for x in all_records:ck(bool(re.fullmatch(r'POL-[CSKTEX]\d{2}',x['id'])),f'Unexpected ID {x["id"]}')
for c in files['cases']:
 fields(c,['id','title','region','period','domain','outcome','summary','stages','mechanisms','counterevidence','claim_ids','source_ids','episode','actors','labour'],c['id'])
 fields(c['episode'],['technology_configuration','task','population','interval','contemporary_alternatives','adoption_measure','observation_limits'],c['id']+'.episode')
 fields(c['actors'],['chooser','payer','operator_maintainer','affected_nonchooser','ability_to_refuse'],c['id']+'.actors')
 fields(c['labour'],['tasks','entry_barriers','bargaining_ownership','transition','distribution','evidence_limit'],c['id']+'.labour')
 refs(c['claim_ids'],claim_ids,c['id']);refs(c['source_ids'],source_ids,c['id'])
for s in files['sources']:
 fields(s,['id','title','authors','year','url','source_type','access','locator','scope_limit','accessed','evidence_lineage'],s['id'])
 ck(s['access'] in {'full-text','partial-text','abstract','metadata','search-excerpt'},s['id']+' access')
 ck(s['url'].startswith('https://'),s['id']+' url')
for c in files['claims']:
 fields(c,['id','case_ids','statement','evidence_type','confidence','causal_status','sources','counterevidence','inference_limits','test'],c['id'])
 refs(c['case_ids'],case_ids,c['id'])
 ck(c['confidence'] in {'high','medium','low'},c['id']+' confidence')
 ck(c['causal_status'] in {'descriptive','mechanism-supported','causal-identification','contested','hypothesis'},c['id']+' causal status')
 for s in c['sources']:fields(s,['source_id','locator','supports'],c['id']+'.sources');refs([s['source_id']],source_ids,c['id'])
 if c['causal_status']=='descriptive':ck(c['test']['status']=='descriptive-only',c['id']+' descriptive test');fields(c['test'],['reason'],c['id']+'.test')
 else:
  ck(c['test']['status'] in {'evaluated','underdetermined','proposed'},c['id']+' mechanism test status')
  fields(c['test'],['mechanism_chain','strongest_rival','discriminating_observation','evidence_sought_found','remaining_ambiguity','hypothesis_timing'],c['id']+'.test')
for n in files['graph']['nodes']:
 fields(n,['id','label','kind','case_ids'],n['id']);refs(n['case_ids'],case_ids,n['id'])
 ck(n['kind'] in {'technology','complement','institution','resource','practice'},n['id']+' kind')
for e in files['graph']['edges']:
 fields(e,['id','from','to','relation','case_ids','claim_ids','source_ids','confidence','qualification','basis','scope','alternatives','joint_inputs','necessity_rationale','dispute'],e['id'])
 refs([e['from'],e['to']],node_ids,e['id']);refs(e['case_ids'],case_ids,e['id']);refs(e['claim_ids'],claim_ids,e['id']);refs(e['source_ids'],source_ids,e['id']);refs(e['joint_inputs'],node_ids,e['id'])
 ck(e['relation'] in {'enables','depends-on','complements','competes-with','displaces','constrains'},e['id']+' relation')
 ck(e['basis'] in {'technical-possibility','observed-contribution','documented-transmission','inferred-transmission','bounded-necessity','hypothesis'},e['id']+' basis')
 fields(e['scope'],['case_id','stage','configuration'],e['id']+'.scope');refs([e['scope']['case_id']],case_ids,e['id']);ck(e['scope']['case_id'] in e['case_ids'],e['id']+' scope inconsistent')
 ck(e['relation']!='depends-on' or e['basis']=='bounded-necessity',e['id']+' unbounded dependency')
 for k in e['claim_ids']:
  cr=next(c for c in files['claims'] if c['id']==k)
  ck(e['scope']['case_id'] in cr['case_ids'],e['id']+' claim scope inconsistent')
for x in files['comparisons']:
 fields(x,['id','question','case_ids','useful_similarities','important_differences','evidence_comparability','connections_nonindependence','omitted_countercases','conclusion_limit'],x['id']);refs(x['case_ids'],case_ids,x['id'])
manifest=json.loads((R/'evidence/download_manifest.json').read_text()); verified=[]
for a in manifest:
 if a.get('file'):
  p=R/a['file'];ck(p.is_file(),f'Missing evidence: {p.name}')
  if p.is_file():ck(hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256'],f'Hash mismatch: {p.name}');verified.append(p.name)
word_count=len((R/'report.md').read_text().split());ck(2500<=word_count<=3500,'Report outside assigned word range')
counts={n:len(files[n]) for n in ('cases','sources','claims','comparisons')};counts.update(nodes=len(files['graph']['nodes']),edges=len(files['graph']['edges']),report_words=word_count,cached_pdfs_hash_verified=len(verified))
out={'checked':'2026-11-05','scope':'POL contribution only; structural validation does not establish historical truth','status':'pass' if not errors else 'fail','counts':counts,'errors':errors,'source_access_counts':{a:sum(s['access']==a for s in files['sources']) for a in sorted(set(s['access'] for s in files['sources']))},'manual_audit':{'selection':'Purposive consequential claims plus weak-access claims; not independent review or random sample','consequential_claim_ids':['POL-K01','POL-K06','POL-K07','POL-K13','POL-K15','POL-K17'],'additional_weak_access_claim_ids':['POL-K04','POL-K11'],'denominator':18,'repairs':'Localized gun counts; explicit reconstructed CPI; war/real-disaster distinctions; corrected telegraph time window/denominator/outcome; 1812 base retention; 1840 legal scope; abstract-only mechanisms downgraded.','remaining_limits':'Inherited archives, no independent statistical replication, four abstract-only source inspections, nonrepresentative local practice and missing labor trajectories.'}}
(R/'validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));raise SystemExit(bool(errors))
