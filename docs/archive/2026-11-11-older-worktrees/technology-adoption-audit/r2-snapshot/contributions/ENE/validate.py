"""Validate ENE references and the v2 evidence contract (not historical truth)."""
import json, re
from pathlib import Path

P=Path(__file__).resolve().parent
files={n:json.loads((P/(n+'.json')).read_text()) for n in ['cases','sources','claims','graph','comparisons']}
errors=[]
warnings=[]
def check(ok,msg):
    if not ok:errors.append(msg)
def fields(records,required,kind):
    for r in records:
        for k in required:check(k in r,f'{kind} {r.get("id")} missing {k}')

cases,sources,claims,graph,comparisons=(files[n] for n in ['cases','sources','claims','graph','comparisons'])
fields(cases,['id','title','region','period','domain','outcome','summary','stages','mechanisms','counterevidence','claim_ids','source_ids','episode','actors','labour'],'case')
fields(sources,['id','title','authors','year','url','source_type','access','locator','scope_limit','accessed','evidence_lineage'],'source')
fields(claims,['id','case_ids','statement','evidence_type','confidence','causal_status','sources','counterevidence','inference_limits','test'],'claim')
fields(graph['nodes'],['id','label','kind','case_ids'],'node')
fields(graph['edges'],['id','from','to','relation','case_ids','claim_ids','source_ids','confidence','qualification','basis','scope','alternatives','joint_inputs','necessity_rationale','dispute'],'edge')
fields(comparisons,['id','question','case_ids','useful_similarities','important_differences','evidence_comparability','connections_nonindependence','omitted_countercases','conclusion_limit'],'comparison')

C={x['id'] for x in cases};S={x['id'] for x in sources};K={x['id'] for x in claims};T={x['id'] for x in graph['nodes']}
all_records=cases+sources+claims+graph['nodes']+graph['edges']+comparisons
all_ids=[x['id'] for x in all_records]
check(len(all_ids)==len(set(all_ids)),'Duplicate identifiers')
check(all(re.fullmatch(r'ENE-[CSKTEX]\d{2}',x) for x in all_ids),'Unexpected identifier prefix or shape')
for c in cases:
    for k in c['claim_ids']:check(k in K,f'{c["id"]}: unknown claim {k}')
    for s in c['source_ids']:check(s in S,f'{c["id"]}: unknown source {s}')
    fields([c['episode']],['technology_configuration','task','population','interval','contemporary_alternatives','adoption_measure','observation_limits'],c['id']+' episode')
    fields([c['actors']],['chooser','payer','operator_maintainer','affected_nonchooser','ability_to_refuse'],c['id']+' actors')
    fields([c['labour']],['tasks','entry_barriers','bargaining_ownership','transition','distribution','evidence_limit'],c['id']+' labour')
for c in claims:
    for r in c['case_ids']:check(r in C,f'{c["id"]}: unknown case {r}')
    for r in c['sources']:
        check(r['source_id'] in S,f'{c["id"]}: unknown source {r["source_id"]}')
        check(bool(r.get('locator')) and bool(r.get('supports')),f'{c["id"]}: missing locator/support')
    check(c['confidence'] in {'high','medium','low'},f'{c["id"]}: confidence')
    check(c['causal_status'] in {'descriptive','mechanism-supported','causal-identification','contested','hypothesis'},f'{c["id"]}: causal status')
    if c['causal_status']=='descriptive':
        check(c['test'].get('status')=='descriptive-only' and bool(c['test'].get('reason')),f'{c["id"]}: descriptive rationale')
    else:
        fields([c['test']],['status','mechanism_chain','strongest_rival','discriminating_observation','evidence_sought_found','remaining_ambiguity','hypothesis_timing'],c['id']+' test')
        check(c['test'].get('status') in {'evaluated','underdetermined','proposed'},f'{c["id"]}: mechanism-test status')
for n in graph['nodes']:
    check(n['kind'] in {'technology','complement','institution','resource','practice'},f'{n["id"]}: node kind')
    for c in n['case_ids']:check(c in C,f'{n["id"]}: case')
for e in graph['edges']:
    check(e['from'] in T and e['to'] in T,f'{e["id"]}: endpoints')
    check(e['relation'] in {'enables','depends-on','complements','competes-with','displaces','constrains'},f'{e["id"]}: relation')
    check(e['basis'] in {'technical-possibility','observed-contribution','documented-transmission','inferred-transmission','bounded-necessity','hypothesis'},f'{e["id"]}: basis')
    check(e['scope']['case_id'] in C and e['scope']['case_id'] in e['case_ids'],f'{e["id"]}: scope')
    check(bool(e['scope']['stage']) and bool(e['scope']['configuration']),f'{e["id"]}: scope detail')
    for c in e['case_ids']:check(c in C,f'{e["id"]}: case')
    for k in e['claim_ids']:check(k in K,f'{e["id"]}: claim')
    for s in e['source_ids']:check(s in S,f'{e["id"]}: source')
    for t in e['joint_inputs']:check(t in T,f'{e["id"]}: joint input')
    check(bool(e['alternatives']) and bool(e['dispute']),f'{e["id"]}: alternatives/dispute')
    if e['relation']=='depends-on':check(e['basis']=='bounded-necessity',f'{e["id"]}: unbounded necessity')
for x in comparisons:
    for c in x['case_ids']:check(c in C,f'{x["id"]}: case')
for s in sources:
    check(s['access'] in {'full-text','partial-text','abstract','metadata','search-excerpt'},f'{s["id"]}: access')
    check(s['url'].startswith('https://'),f'{s["id"]}: URL')
    check(s['accessed']=='2026-11-05',f'{s["id"]}: access date')
    check(bool(s['evidence_lineage']) and bool(s['scope_limit']),f'{s["id"]}: lineage/limits')

report=(P/'report.md').read_text()
reported=set(re.findall(r'ENE-K\d{2}',report))
for a,b in re.findall(r'ENE-K(\d{2})[–-]K(\d{2})',report):reported.update(f'ENE-K{i:02d}' for i in range(int(a),int(b)+1))
check(K<=reported,'Report omits claims: '+str(sorted(K-reported)))
check(2500<=len(report.split())<=3500,'Report outside requested word band')
check(set(re.findall(r'ENE-C\d{2}',report))>=C,'Report omits case IDs')
manifest=json.loads((P/'cache/download_manifest.json').read_text())
successful=[r for r in manifest if r.get('bytes',0)>0 and r.get('text_characters',0)>0 and not r.get('error')]
check(len(successful)==9,'Unexpected full local acquisition count')
warnings.extend([
 'Five sources conservatively marked partial-text: relevant web-parsed sections inspected; direct originals failed/empty. See cache/web-inspections.json.',
 'Fourteen sources are not fourteen independent evidence lineages; overlaps are recorded.',
 'Mechanism tests are primarily underdetermined historical/model comparisons; structural checks do not establish historical truth.',
 'Korean reactor subgroup denominator and Chinese PV interview-count discrepancy remain unresolved and are not reproduced as precise sample claims.'
])
result={'status':'pass' if not errors else 'fail','checked_on':'2026-11-05',
 'counts':{'cases':len(cases),'sources':len(sources),'claims':len(claims),'nodes':len(graph['nodes']),'edges':len(graph['edges']),'comparisons':len(comparisons),'report_words':len(report.split()),'local_full_source_files':len(successful),'partial_text_sources':sum(s['access']=='partial-text' for s in sources)},
 'checks':['JSON parse','required v2 fields','identifier uniqueness','foreign references','mechanism-test fields','graph scope/basis/alternatives/joint inputs','no unbounded depends-on edges','report case/claim coverage','word band','acquisition count'],
 'errors':errors,'warnings':warnings}
(P/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
raise SystemExit(bool(errors))
