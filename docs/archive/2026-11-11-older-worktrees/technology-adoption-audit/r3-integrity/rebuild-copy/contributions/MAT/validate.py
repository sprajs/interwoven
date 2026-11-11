from pathlib import Path
import json,re,collections
P=Path(__file__).resolve().parent
load=lambda f:json.loads((P/f).read_text())
C,S,K,G,X=[load(f) for f in ['cases.json','sources.json','claims.json','graph.json','comparisons.json']]
req={
'case':set('id title region period domain outcome summary stages mechanisms counterevidence claim_ids source_ids episode actors labour'.split()),
'source':set('id title authors year url source_type access locator scope_limit accessed evidence_lineage'.split()),
'claim':set('id case_ids statement evidence_type confidence causal_status sources counterevidence inference_limits test'.split()),
'node':set('id label kind case_ids'.split()),
'edge':set('id from to relation case_ids claim_ids source_ids confidence qualification basis scope alternatives joint_inputs necessity_rationale dispute'.split()),
'comparison':set('id question case_ids useful_similarities important_differences evidence_comparability connections_nonindependence omitted_countercases conclusion_limit'.split())}
sets={'C':{v['id'] for v in C},'S':{v['id'] for v in S},'K':{v['id'] for v in K},'T':{v['id'] for v in G['nodes']},'E':{v['id'] for v in G['edges']},'X':{v['id'] for v in X}}
ids=[];errors=[]
def check(ok,msg):
 if not ok:errors.append(msg)
def refs(values,kind,loc):
 for v in values:check(v in sets[kind],f'{loc}: unknown {kind} {v}')
for typ,arr in [('case',C),('source',S),('claim',K),('node',G['nodes']),('edge',G['edges']),('comparison',X)]:
 for v in arr:
  ids.append(v['id']);check(set(v)==req[typ],f'{v["id"]}: schema fields differ: {set(v)^req[typ]}')
  check(all(value is not None for value in v.values()),f'{v["id"]}: null')
  if 'case_ids'in v:refs(v['case_ids'],'C',v['id'])
  if 'source_ids'in v:refs(v['source_ids'],'S',v['id'])
  if 'claim_ids'in v:refs(v['claim_ids'],'K',v['id'])
check(len(ids)==len(set(ids)),'Duplicate IDs')
for c in C:
 for obj,fields in [('episode','technology_configuration task population interval contemporary_alternatives adoption_measure observation_limits'),('actors','chooser payer operator_maintainer affected_nonchooser ability_to_refuse'),('labour','tasks entry_barriers bargaining_ownership transition distribution evidence_limit')]:
  check(set(c[obj])==set(fields.split()),f'{c["id"]} bad {obj} fields')
 for k in c['claim_ids']:
  ck=next(v for v in K if v['id']==k);check(c['id'] in ck['case_ids'],f'{c["id"]} and {k} not reciprocal')
for k in K:
 for v in k['sources']:
  check(set(v)=={'source_id','locator','supports'},f'{k["id"]} bad source fields');refs([v['source_id']],'S',k['id'])
 t=k['test'];check(t['status'] in {'descriptive-only','evaluated','underdetermined','proposed'},f'{k["id"]} test status')
 if t['status']=='descriptive-only':
  check(k['causal_status']=='descriptive',f'{k["id"]} causal claim lacks test');check(set(t)=={'status','reason'},f'{k["id"]} descriptive schema')
 else:check(set(t)==set('status mechanism_chain strongest_rival discriminating_observation evidence_sought_found remaining_ambiguity hypothesis_timing'.split()),f'{k["id"]} test schema')
 check(k['confidence']in{'high','medium','low'},f'{k["id"]} confidence')
for s in S:
 check(s['access']in{'full-text','partial-text','abstract','metadata','search-excerpt'},f'{s["id"]} access')
 check(s['accessed']=='2026-11-05',f'{s["id"]} date')
 check(s['url'].startswith('https://'),f'{s["id"]} URL')
for e in G['edges']:
 refs([e['from'],e['to']],'T',e['id']);refs(e['joint_inputs'],'T',e['id']);refs([e['scope']['case_id']],'C',e['id'])
 check(e['scope']['case_id']in e['case_ids'],f'{e["id"]} scope mismatch')
 check(set(e['scope'])=={'case_id','stage','configuration'},f'{e["id"]} scope schema')
 check(e['basis']in{'technical-possibility','observed-contribution','documented-transmission','inferred-transmission','bounded-necessity','hypothesis'},f'{e["id"]} basis')
 check(e['relation']in{'enables','depends-on','complements','competes-with','displaces','constrains'},f'{e["id"]} relation')
 if e['relation']=='depends-on':check(e['basis']=='bounded-necessity',f'{e["id"]} unsupported necessity')
 if e['basis']=='bounded-necessity':check(e['necessity_rationale']!='No necessity claim',f'{e["id"]} missing counterfactual')
 for k in e['claim_ids']:
  claim=next(v for v in K if v['id']==k)
  check(set(e['case_ids']) & set(claim['case_ids']),f'{e["id"]} claim scope mismatch')
text=(P/'report.md').read_text();words=len(text.split())
check(2500<=words<=4500,f'Report word count {words}')
for id in re.findall(r'MAT-[CSKTE]\d{2}',text):check(id in set(ids),f'Unknown report ID {id}')
# Check local markdown links when present; web reachability and historical truth require separate human/source audit.
for path in [P/'report.md',P/'questions.md']:
 for dest in re.findall(r'\]\(([^)]+)\)',path.read_text()):
  if not dest.startswith(('https://','http://','#')):check((path.parent/dest.split('#')[0]).exists(),f'{path.name}: missing local link {dest}')
result={'status':'passed' if not errors else 'failed','contract':'METHODS.md + METHODS_ADDENDUM_V2.md','counts':{'cases':len(C),'sources':len(S),'claims':len(K),'nodes':len(G['nodes']),'edges':len(G['edges']),'comparisons':len(X),'report_words':words},'source_access_counts':dict(collections.Counter(s['access']for s in S)),'checks':'JSON parsing, exact fields, unique IDs, references, reciprocal case/claim links, v2 nested objects, claim test requirements, edge scope and bounded-necessity rules, report word range and mentioned IDs, local markdown links','limits':'Does not independently validate historical truth, claim entailment or live source reachability. No rates of adoption, workforce displacement or national output were inferred from counts.','errors':errors}
(P/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(bool(errors))
