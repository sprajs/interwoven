#!/usr/bin/env python3
"""Validate and compile the research ledger. No external dependencies or network."""
from __future__ import annotations
import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
REQUIRED = {
 'cases': {'id','title','region','period','domain','outcome','summary','stages','mechanisms','counterevidence','claim_ids','source_ids','episode','actors','labour'},
 'sources': {'id','title','authors','year','url','source_type','access','locator','scope_limit','accessed','evidence_lineage'},
 'claims': {'id','case_ids','statement','evidence_type','confidence','causal_status','sources','counterevidence','inference_limits','test'},
 'nodes': {'id','label','kind','case_ids'},
 'edges': {'id','from','to','relation','case_ids','claim_ids','source_ids','confidence','qualification','basis','scope','alternatives','joint_inputs','necessity_rationale','dispute'},
 'comparisons': {'id','question','case_ids','useful_similarities','important_differences','evidence_comparability','connections_nonindependence','omitted_countercases','conclusion_limit'},
}
ACCESS = {'full-text','partial-text','abstract','metadata','search-excerpt'}
CONFIDENCE = {'high','medium','low'}
RELATIONS = {'enables','depends-on','complements','competes-with','displaces','constrains'}
TEST_STATUS = {'descriptive-only','evaluated','underdetermined','proposed'}
CAUSAL = {'descriptive','mechanism-supported','causal-identification','contested','hypothesis'}
errors, warnings = [], []
records = {k: [] for k in REQUIRED}
origins = {}
complete, incomplete = [], []

def fail(msg): errors.append(msg)
def warn(msg): warnings.append(msg)
def text(value):
 if isinstance(value, list): return '; '.join(map(str,value))
 if isinstance(value, dict): return json.dumps(value,ensure_ascii=False)
 return str(value)
def esc(value): return text(value).replace('|','\\|').replace('\n',' ')
def read(path):
 try: return json.loads(path.read_text())
 except Exception as e: fail(f'{path.relative_to(ROOT)}: {e}'); return None

for folder in sorted((ROOT/'contributions').iterdir()):
 if not folder.is_dir(): continue
 expected = [folder/f'{k}.json' for k in ['cases','sources','claims','graph','comparisons']]+[folder/'report.md',folder/'questions.md']
 if not all(p.exists() for p in expected):
  incomplete.append(folder.name); continue
 complete.append(folder.name)
 for kind in ['cases','sources','claims','comparisons']:
  items=read(folder/f'{kind}.json')
  if not isinstance(items,list): fail(f'{folder.name}/{kind}.json must be an array'); continue
  for item in items:
   if not isinstance(item,dict): fail(f'{folder.name}/{kind}: record not object'); continue
   item=dict(item); item['contribution']=folder.name
   records[kind].append(item)
 graph=read(folder/'graph.json')
 if not isinstance(graph,dict): fail(f'{folder.name}/graph.json must be object'); continue
 for kind in ['nodes','edges']:
  if not isinstance(graph.get(kind),list): fail(f'{folder.name}/graph: {kind} not array'); continue
  for item in graph[kind]:
   item=dict(item); item['contribution']=folder.name; records[kind].append(item)

index={}
for kind,items in records.items():
 index[kind]={}
 for item in items:
  missing=REQUIRED[kind]-item.keys()
  ident=item.get('id','<missing-id>')
  if missing: fail(f'{ident} missing {sorted(missing)}')
  if ident in origins: fail(f'duplicate ID {ident}: {origins[ident]} and {kind}')
  origins[ident]=kind; index[kind][ident]=item
  if not re.match(r'^[A-Z]+-[A-Z][0-9]+$',ident): fail(f'ID format {ident}')
  if kind in {'claims','edges'} and item.get('confidence') not in CONFIDENCE: fail(f'{ident} invalid confidence')
  if kind=='sources':
   if item.get('access') not in ACCESS: fail(f'{ident} invalid access {item.get("access")}')
   if not re.match(r'^https?://',str(item.get('url',''))): fail(f'{ident} needs public HTTP(S) source URL')
  if kind=='claims':
   if item.get('causal_status') not in CAUSAL: fail(f'{ident} invalid causal_status {item.get("causal_status")}')
   if not item.get('sources'): fail(f'{ident} has no source support')
  if kind=='edges' and item.get('relation') not in RELATIONS: fail(f'{ident} invalid relation')
  if kind=='cases':
   if not isinstance(item.get('stages'),dict): fail(f'{ident} stages not object')
   for field in ['region','domain','outcome','mechanisms','claim_ids','source_ids']:
    if not isinstance(item.get(field),list): fail(f'{ident} {field} not array')


# Version 2: preserve the unit of analysis and distinguish graph/test semantics.
for c in records['cases']:
 for field,keys in {
  'episode':['technology_configuration','task','population','interval','contemporary_alternatives','adoption_measure','observation_limits'],
  'actors':['chooser','payer','operator_maintainer','affected_nonchooser','ability_to_refuse'],
  'labour':['tasks','entry_barriers','bargaining_ownership','transition','distribution','evidence_limit'],
 }.items():
  obj=c.get(field,{})
  if not isinstance(obj,dict): fail(f'{c["id"]} {field} not object'); continue
  for key in keys:
   if key not in obj or obj[key] in [None,'']: fail(f'{c["id"]} {field}.{key} missing')
for c in records['claims']:
 test=c.get('test',{})
 if not isinstance(test,dict): fail(f'{c["id"]} test not object'); continue
 if test.get('status') not in TEST_STATUS: fail(f'{c["id"]} invalid test status')
 if test.get('status')=='descriptive-only':
  if c.get('causal_status')!='descriptive': fail(f'{c["id"]} causal claim has descriptive-only test')
  if not test.get('reason'): fail(f'{c["id"]} descriptive test needs reason')
 else:
  for key in ['status','mechanism_chain','strongest_rival','discriminating_observation','evidence_sought_found','remaining_ambiguity','hypothesis_timing']:
   if not test.get(key): fail(f'{c["id"]} test.{key} missing')
for e in records['edges']:
 if e.get('basis') not in {'technical-possibility','observed-contribution','documented-transmission','inferred-transmission','bounded-necessity','hypothesis'}: fail(f'{e["id"]} invalid edge basis')
 if e.get('relation')=='depends-on' and e.get('basis')!='bounded-necessity': fail(f'{e["id"]} depends-on without bounded necessity')
 scope=e.get('scope',{})
 if not isinstance(scope,dict): fail(f'{e["id"]} scope not object'); continue
 for key in ['case_id','stage','configuration']:
  if not scope.get(key): fail(f'{e["id"]} scope.{key} missing')
 if scope.get('case_id') not in e.get('case_ids',[]): fail(f'{e["id"]} scope case not listed')
 for field in ['alternatives','joint_inputs']:
  if not isinstance(e.get(field),list): fail(f'{e["id"]} {field} not array')
 if isinstance(e.get('alternatives'),list) and any(not isinstance(x,str) for x in e['alternatives']): fail(f'{e["id"]} alternatives must contain strings')
 if e.get('basis')=='bounded-necessity' and (not isinstance(e.get('necessity_rationale'),str) or not e['necessity_rationale'].strip() or e['necessity_rationale']=='No necessity claim'): fail(f'{e["id"]} bounded necessity needs substantive rationale')
 for nid in e.get('joint_inputs',[]) if isinstance(e.get('joint_inputs'),list) else []:
  if nid not in index['nodes']: fail(f'{e["id"]} unknown joint input {nid}')

def refs(item,field,kind):
 values=item.get(field,[])
 if not isinstance(values,list): fail(f'{item["id"]} {field} not array'); return
 for value in values:
  if value not in index[kind]: fail(f'{item["id"]} unresolved {field}: {value}')

for kind,items in records.items():
 for item in items:
  for field,target in [('case_ids','cases'),('claim_ids','claims'),('source_ids','sources')]:
   if field in item: refs(item,field,target)
  if kind=='claims':
   for support in item.get('sources',[]):
    if not isinstance(support,dict): fail(f'{item["id"]} support not object'); continue
    for key in ['source_id','locator','supports']:
     if not support.get(key): fail(f'{item["id"]} support missing {key}')
    sid=support.get('source_id')
    if sid not in index['sources']: fail(f'{item["id"]} unknown source {sid}')
    elif index['sources'][sid]['access'] in {'abstract','metadata','search-excerpt'}:
     warn(f'{item["id"]} uses limited-access source {sid} ({index["sources"][sid]["access"]})')
  if kind=='edges':
   for field in ['from','to']:
    if item.get(field) not in index['nodes']: fail(f'{item["id"]} unknown {field} node')
   if not item.get('claim_ids') or not item.get('source_ids'): fail(f'{item["id"]} lacks claim/source provenance')

summary={
 'edition_date':'2026-11-05',
 'completed_contributions':complete,
 'incomplete_contributions':incomplete,
 'counts':{k:len(v) for k,v in records.items()},
 'unique_source_urls':len({s['url'] for s in records['sources']}),
 'source_access':dict(Counter(s['access'] for s in records['sources'])),
 'claim_confidence':dict(Counter(c['confidence'] for c in records['claims'])),
 'claim_causal_status':dict(Counter(c['causal_status'] for c in records['claims'])),
 'errors':errors,'warnings':warnings,
 'limits':'Structural validation checks consistency, not historical truth, independent source entailment or exhaustive coverage.',
}
DATA.mkdir(exist_ok=True)
(DATA/'validation.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
if errors:
 print(json.dumps(summary,indent=2,ensure_ascii=False)); sys.exit(1)

for kind in ['cases','sources','claims','comparisons']:
 (DATA/f'{kind}.json').write_text(json.dumps(records[kind],indent=2,ensure_ascii=False)+'\n')
 fields=['id']+sorted({k for row in records[kind] for k in row if k!='id'})
 with (DATA/f'{kind}.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader()
  for row in records[kind]: writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()})
(DATA/'graph.json').write_text(json.dumps({'nodes':records['nodes'],'edges':records['edges'],'semantics':'Typed directed multigraph. All relations are scoped to listed cases. Depends-on reverses the enabling direction. Disconnected components and repeated concepts are retained; node identity is not inferred from similar names.'},indent=2,ensure_ascii=False)+'\n')

# Canonical URL groups are a discovery aid, not a declaration that editions match.
groups=defaultdict(list)
for s in records['sources']: groups[s['url'].rstrip('/')].append(s['id'])
(DATA/'source_url_groups.json').write_text(json.dumps([{'url':u,'source_ids':ids} for u,ids in sorted(groups.items())],indent=2)+'\n')

lines=['# Source bibliography','', 'Generated from the inspected-source ledger. Access means the material available to the researcher; each scope note states limitations. Different records/editions are retained. Source counts are not counts of independent confirmations.','']
for s in records['sources']:
 lines += [f'## {s["id"]} — {s["title"]}', '',f'{text(s["authors"])} ({text(s["year"])}). [{s["title"]}]({s["url"]}).', '',f'**Type:** {s["source_type"]}. **Access:** {s["access"]}. **Accessed:** {s["accessed"]}.', '',f'**Inspected locator:** {text(s["locator"])}', '',f'**Scope limit:** {text(s["scope_limit"])}','',f'**Evidence lineage:** {text(s["evidence_lineage"])}','']
(DATA/'BIBLIOGRAPHY.md').write_text('\n'.join(lines))

lines=['# Claim-level evidence ledger','','Generated from researcher ledgers. Confidence concerns the bounded statement; causal status is separate. No claim is certified solely by inclusion here.','']
for c in records['claims']:
 lines += [f'## {c["id"]}', '',c['statement'],'',f'**Cases:** {text(c["case_ids"]) or "method/synthesis"}. **Evidence:** {c["evidence_type"]}. **Confidence:** {c["confidence"]}. **Causal status:** {c["causal_status"]}.','']
 for sup in c['sources']:
  s=index['sources'][sup['source_id']]
  lines += [f'- [{s["id"]}: {s["title"]}]({s["url"]}), {text(sup["locator"])}. Supports: {text(sup["supports"])}']
 lines += ['', '**Diagnostic test:**', '']
 for key,value in c['test'].items(): lines += [f'- **{key.replace("_"," ")}:** {text(value)}']
 lines += ['',f'**Counterevidence/rival:** {text(c["counterevidence"])}','',f'**Inference limit:** {text(c["inference_limits"])}','']
(DATA/'CLAIM_LEDGER.md').write_text('\n'.join(lines))

library=ROOT/'cases'; library.mkdir(exist_ok=True)
lines=['# Case library','','Each case card links to the independent narrative dossier and its claim evidence. These are bounded comparative episodes, not an exhaustive catalogue. Cases may overlap; counts are not independent observations.','','| Case | Period | Geography | Outcome |','|---|---|---|---|']
for c in records['cases']:
 name=c['id']+'.md'
 lines += [f'| [{c["id"]}: {esc(c["title"])}]({name}) | {esc(c["period"])} | {esc(c["region"])} | {esc(c["outcome"])} |']
 card=[f'# {c["id"]} — {c["title"]}', '',f'**Period:** {text(c["period"])}. **Region:** {text(c["region"])}. **Domain:** {text(c["domain"])}.', '',c['summary'],'',f'[Read the substantive research dossier](../contributions/{c["contribution"]}/report.md).','', '## Stages','']
 for stage,description in c['stages'].items(): card += [f'**{stage}:** {text(description)}','']
 for field in ['episode','actors','labour']:
  card += [f'## {field.title()}','']
  for key,value in c[field].items(): card += [f'**{key.replace("_"," ")}:** {text(value)}','']
 card += ['## Mechanisms and counterevidence','',f'Candidate/supported mechanisms: {text(c["mechanisms"])}','',text(c['counterevidence']),'','## Evidence links','']
 for cid in c['claim_ids']:
  cl=index['claims'][cid]
  card += [f'- [{cid}](../data/CLAIM_LEDGER.md#{cid.lower()}): {cl["statement"]}']
 card += ['','Sources: '+', '.join(f'[{sid}]({index["sources"][sid]["url"]})' for sid in c['source_ids'])+'.','']
 (library/name).write_text('\n'.join(card))
(library/'README.md').write_text('\n'.join(lines)+'\n')

lines=['# Contribution and coverage inventory','','Generated counts describe this purposive collection, not historical prevalence or research quality. Region and mechanism tags are researcher-supplied and may overlap. A separate editorial coverage assessment identifies blind spots.','','| Strand | Cases | Claims | Source records | Nodes | Edges |','|---|---:|---:|---:|---:|---:|']
for prefix in complete:
 counts=[sum(r['contribution']==prefix for r in records[k]) for k in ['cases','claims','sources','nodes','edges']]
 lines += [f'| [{prefix}](../contributions/{prefix}/report.md) | '+' | '.join(map(str,counts))+' |']
for title,field in [('Region tags','region'),('Domain tags','domain'),('Outcome tags','outcome')]:
 lines += ['',f'## {title}','','| Tag | Case records |','|---|---:|']
 for tag,count in sorted(Counter(x for c in records['cases'] for x in c[field]).items()): lines += [f'| {esc(tag)} | {count} |']
(DATA/'COVERAGE_INVENTORY.md').write_text('\n'.join(lines)+'\n')


lines=['# Comparison ledger','','Comparisons preserve useful similarities, important differences, source limits and non-independent settings. They are not a matched statistical sample.','']
for x in records['comparisons']:
 lines += [f'## {x["id"]} — {x["question"]}','']
 for key,value in x.items():
  if key not in ['id','question','contribution']: lines += [f'**{key.replace("_"," ")}:** {text(value)}','']
(DATA/'COMPARISONS.md').write_text('\n'.join(lines)+'\n')
lines=['# Graph guide and edge inventory','','The graph is a typed, directed multigraph. `depends-on` points from a dependent system to a bounded requirement; `enables` points from a contributor to a beneficiary. `complements` does not assert universal necessity. `displaces` is scoped to the listed task, population and period.','', 'Node identities remain local to their contribution. Similar labels do not silently become identical technologies. No global invention ancestry or transitive causal closure is asserted. Multiple incoming edges do not by themselves establish joint requirements, alternatives or sufficient causes. Every edge carries an explicit basis, scope, alternatives, joint-input list, necessity rationale and dispute.','', '| Edge | From | Relation | To | Basis | Cases / claims |','|---|---|---|---|---|---|']
for e in records['edges']:
 lines += [f'| {e["id"]} | {esc(index["nodes"][e["from"]]["label"])} | {e["relation"]} | {esc(index["nodes"][e["to"]]["label"])} | {e["basis"]} | {esc(e["case_ids"])} / {esc(e["claim_ids"])} |']
(DATA/'GRAPH_GUIDE.md').write_text('\n'.join(lines)+'\n')

# Local links: exclude external URLs, mail, anchor-only links, and Mermaid/code text.
local_link_errors=[]
for path in ROOT.rglob('*.md'):
 # Historical/selective snapshots retain their own frozen checks; validate live artifacts here.
 if any(part in {'snapshot','design-snapshot','recheck-snapshot'} for part in path.relative_to(ROOT).parts): continue
 for target in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)',path.read_text()):
  target=target.split('#')[0].strip('<>')
  if not target or re.match(r'^[a-zA-Z]+:',target): continue
  target=target.split(' "')[0]
  target=re.sub(r':\d+$','',target)
  if not (path.parent/target).exists(): local_link_errors.append(f'{path.relative_to(ROOT)} -> {target}')
summary['local_link_scope']='Live Markdown artifacts, excluding immutable selected review snapshots'
summary['local_link_errors']=local_link_errors
summary['errors'] += [f'broken local link: {x}' for x in local_link_errors]
(DATA/'validation.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='warnings'},indent=2,ensure_ascii=False))
print(f'Limited-access support flags: {len(warnings)} (inspect data/validation.json)')
if summary['errors']: sys.exit(1)
