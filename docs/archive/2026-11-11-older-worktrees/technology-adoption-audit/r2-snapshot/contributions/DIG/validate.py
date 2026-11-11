from pathlib import Path
import json,re
P=Path(__file__).parent
files={x:json.loads((P/(x+'.json')).read_text()) for x in ['cases','sources','claims','graph','comparisons']}
required={
'cases':set('id title region period domain outcome summary stages mechanisms counterevidence claim_ids source_ids episode actors labour'.split()),
'sources':set('id title authors year url source_type access locator scope_limit accessed evidence_lineage'.split()),
'claims':set('id case_ids statement evidence_type confidence causal_status sources counterevidence inference_limits test'.split()),
'comparisons':set('id question case_ids useful_similarities important_differences evidence_comparability connections_nonindependence omitted_countercases conclusion_limit'.split())}
ids={}
for group,fields in required.items():
 for obj in files[group]:
  assert fields<=obj.keys(),(group,obj.get('id'),fields-obj.keys())
  assert obj['id'] not in ids,obj['id']
  ids[obj['id']]=group
node_fields=set('id label kind case_ids'.split())
edge_fields=set('id from to relation case_ids claim_ids source_ids confidence qualification basis scope alternatives joint_inputs necessity_rationale dispute'.split())
for group,fields in [('nodes',node_fields),('edges',edge_fields)]:
 for obj in files['graph'][group]:
  assert fields<=obj.keys(),(obj.get('id'),fields-obj.keys())
  assert obj['id'] not in ids
  ids[obj['id']]=group
for c in files['cases']:
 for fld,fs in [('episode','technology_configuration task population interval contemporary_alternatives adoption_measure observation_limits'),('actors','chooser payer operator_maintainer affected_nonchooser ability_to_refuse'),('labour','tasks entry_barriers bargaining_ownership transition distribution evidence_limit')]:
  assert set(fs.split())<=c[fld].keys(),(c['id'],fld)
 for fld,group in [('claim_ids','claims'),('source_ids','sources')]:
  for x in c[fld]: assert ids.get(x)==group,(c['id'],fld,x)
for c in files['claims']:
 assert c['confidence'] in ['high','medium','low']
 assert c['causal_status'] in ['descriptive','mechanism-supported','causal-identification','contested','hypothesis']
 assert c['evidence_type'] in ['historical-primary','archaeological','scholarly-analysis','official-statistics','experiment','institutional-synthesis','synthesis-inference']
 for x in c['case_ids']: assert ids.get(x)=='cases'
 for s in c['sources']:
  assert ids.get(s['source_id'])=='sources'
  assert all(s.get(x) for x in ['locator','supports'])
 if c['causal_status']=='descriptive': assert c['test']['status']=='descriptive-only'
 else:
  assert c['test']['status'] in ['evaluated','underdetermined','proposed']
  assert set('mechanism_chain strongest_rival discriminating_observation evidence_sought_found remaining_ambiguity hypothesis_timing'.split())<=c['test'].keys()
for s in files['sources']:
 assert s['access'] in ['full-text','partial-text','abstract','metadata','search-excerpt']
 assert s['url'].startswith('https://')
 assert re.fullmatch(r'\d{4}-\d{2}-\d{2}',s['accessed'])
for n in files['graph']['nodes']:
 assert n['kind'] in ['technology','complement','institution','resource','practice']
 for c in n['case_ids']: assert ids.get(c)=='cases'
for e in files['graph']['edges']:
 for v in ['from','to']: assert ids.get(e[v])=='nodes'
 for fld,group in [('case_ids','cases'),('claim_ids','claims'),('source_ids','sources'),('joint_inputs','nodes')]:
  for x in e[fld]: assert ids.get(x)==group,(e['id'],fld,x)
 assert e['scope']['case_id'] in e['case_ids']
 assert all(e['scope'].get(x) for x in ['stage','configuration'])
 assert e['relation'] in ['enables','depends-on','complements','competes-with','displaces','constrains']
 assert e['basis'] in ['technical-possibility','observed-contribution','documented-transmission','inferred-transmission','bounded-necessity','hypothesis']
 if e['relation']=='depends-on':
  assert e['basis']=='bounded-necessity'
  assert e['necessity_rationale']!='No necessity claim'
 assert e['alternatives'] and e['dispute']
for x in files['comparisons']:
 for c in x['case_ids']: assert ids.get(c)=='cases'
report=(P/'report.md').read_text()
for x in set(re.findall(r'\bDIG-[CSK]\d{2}\b',report)): assert x in ids,x
assert 2500<=len(report.split())<=4500
assert 5<=len(files['cases'])<=8
assert 10<=len(files['sources'])<=16
assert 15<=len(files['claims'])<=25
print(json.dumps({'status':'pass','cases':len(files['cases']),'sources':len(files['sources']),'claims':len(files['claims']),'nodes':len(files['graph']['nodes']),'edges':len(files['graph']['edges']),'comparisons':len(files['comparisons']),'report_words':len(report.split()),'note':'Schema/reference checks only; no historical-truth certification.'},indent=2))
