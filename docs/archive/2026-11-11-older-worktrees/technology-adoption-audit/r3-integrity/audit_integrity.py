#!/usr/bin/env python3
"""Independent frozen-edition audit. Writes only beside this script."""
from pathlib import Path
from collections import Counter, defaultdict
from itertools import combinations
import csv, hashlib, json, re, shutil, subprocess, sys

OUT = Path(__file__).resolve().parent
R = OUT.parent / 'r3-snapshot'
load = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
result = {'scope': 'Frozen R3 snapshot only; source and executable-function inspection, not live browser verification or historical-source entailment.', 'snapshot': {k:v for k,v in load(R/'MANIFEST.json').items() if k != 'files'}}
manifest = load(R/'MANIFEST.json')
result['snapshot_integrity'] = {'checked': len(manifest['files']), 'mismatches': [x['path'] for x in manifest['files'] if not (R/x['path']).exists() or sha(R/x['path']) != x['sha256']]}
actual = {k:load(R/'data'/f'{k}.json') for k in ['cases','claims','sources','comparisons']}
graph = load(R/'data/graph.json'); actual.update({k:graph[k] for k in ['nodes','edges']})
expected = {k:[] for k in actual}; dossier_results = []
for p in sorted((R/'contributions').iterdir()):
    if not p.is_dir(): continue
    required = [f'{k}.json' for k in ['cases','sources','claims','comparisons','graph']] + ['report.md','questions.md']
    missing = [f for f in required if not (p/f).is_file()]
    if missing:
        dossier_results.append({'id':p.name, 'complete':False, 'missing':missing}); continue
    local = {k:load(p/f'{k}.json') for k in ['cases','sources','claims','comparisons']}
    local.update({k:load(p/'graph.json')[k] for k in ['nodes','edges']})
    eq = {}
    for k,rows in local.items():
        expanded = [dict(x,contribution=p.name) for x in rows]
        expected[k] += expanded
        eq[k] = expanded == [x for x in actual[k] if x.get('contribution') == p.name]
    ed = load(p/'EDITION_VALIDATION.json')
    dossier_results.append({'id':p.name, 'complete':True, 'counts':{k:len(v) for k,v in local.items()}, 'canonical_to_compiled_equal':eq, 'current_hash_mismatches':[f for f,h in ed['canonical_hashes'].items() if sha(p/f)!=h]})
result['canonical'] = {'dossiers':dossier_results, 'all_records_equal_including_order':{k:expected[k]==actual[k] for k in actual}, 'duplicates':{k:[i for i,n in Counter(x['id'] for x in rows).items() if n>1] for k,rows in actual.items()}}
csv_results={}
for k in ['cases','claims','sources','comparisons']:
    with (R/'data'/f'{k}.csv').open(newline='') as f:
        reader=csv.DictReader(f); fields=reader.fieldnames; rows=list(reader)
    issues=[]; checks=0
    if len(rows)!=len(actual[k]):issues.append('row count')
    for row,rec in zip(rows,actual[k]):
        for key,val in rec.items():
            checks+=1
            got=json.loads(row[key]) if isinstance(val,(list,dict)) else row.get(key)
            want=val if isinstance(val,(list,dict)) else '' if val is None else str(val)
            if got!=want:issues.append([rec['id'],key])
    csv_results[k]={'rows':len(rows),'fields':fields,'field_checks':checks,'issues':issues,'union_of_keys_equals_csv_fields':set(fields)==set().union(*(set(x) for x in actual[k]))}
result['csv']=csv_results
html=(R/'index.html').read_text()
payload=load(R/'data/cases.json')
payload=json.loads(re.search(r'<script id="research-data" type="application/json">(.*?)</script>',html,re.S).group(1))
result['html_payload']={k:payload[k]==load(R/'data'/f'{k}.json') for k in ['cases','claims','sources','comparisons','graph','validation','chronology']}
indices={k:{x['id']:x for x in rows} for k,rows in actual.items()}
issues=[]
for kind,rows in actual.items():
    for row in rows:
        for field,target in [('case_ids','cases'),('claim_ids','claims'),('source_ids','sources')]:
            for ident in row.get(field,[]):
                if ident not in indices[target]:issues.append([row['id'],field,ident])
        if kind=='claims':
            for ref in row['sources']:
                if ref['source_id'] not in indices['sources']:issues.append([row['id'],'sources',ref['source_id']])
        if kind=='edges':
            for field in ['from','to']:
                if row[field] not in indices['nodes']:issues.append([row['id'],field,row[field]])
result['references']={'unresolved':issues}

def components(ids, pairs):
    adjacency={i:set() for i in ids}
    for a,b in pairs: adjacency[a].add(b);adjacency[b].add(a)
    remaining=set(ids); result=[]
    while remaining:
        stack=[min(remaining)];group=set()
        while stack:
            current=stack.pop()
            if current in group:continue
            group.add(current);stack.extend(adjacency[current]-group)
        remaining-=group;result.append(sorted(group))
    return sorted(result,key=lambda x:(-len(x),x)),adjacency

comps,adjacency=components(indices['nodes'],[(e['from'],e['to']) for e in graph['edges']])
component_records=[]
for group in comps:
    edges=[e for e in graph['edges'] if e['from'] in group]
    cases=sorted({c for n in group for c in indices['nodes'][n]['case_ids']})
    component_records.append({'node_ids':group,'node_count':len(group),'edge_count':len(edges),'case_ids':cases,'contributions':sorted({indices['nodes'][n]['contribution'] for n in group})})
cross_scope=[e for e in graph['edges'] if len(e['case_ids'])>1]
cross_endpoints=[e for e in graph['edges'] if not (set(indices['nodes'][e['from']]['case_ids']) & set(indices['nodes'][e['to']]['case_ids']))]
cross_contribution=[e for e in graph['edges'] if indices['nodes'][e['from']]['contribution']!=indices['nodes'][e['to']]['contribution']]
transmission=[e for e in graph['edges'] if e['basis'] in ['documented-transmission','inferred-transmission']]
result['graph']={'node_count':len(graph['nodes']),'edge_count':len(graph['edges']),'weak_component_count':len(comps),'component_size_distribution':dict(Counter(map(len,comps))),'isolated_node_ids':[n for n,a in adjacency.items() if not a], 'components':component_records,'multi_case_node_ids':[n['id'] for n in graph['nodes'] if len(n['case_ids'])>1],'multi_case_edge_ids':[e['id'] for e in cross_scope],'endpoint_disjoint_case_ids_edge_ids':[e['id'] for e in cross_endpoints],'cross_contribution_edge_ids':[e['id'] for e in cross_contribution], 'basis_counts':dict(Counter(e['basis'] for e in graph['edges'])),'relation_counts':dict(Counter(e['relation'] for e in graph['edges'])),'transmission_edges':transmission}

comparison_pairs=[]
for x in actual['comparisons']:comparison_pairs.extend(combinations(x['case_ids'],2))
case_comps,case_adj=components(indices['cases'],comparison_pairs)
result['comparisons']={'count':len(actual['comparisons']),'case_components':case_comps,'uncompared_case_ids':[c for c,a in case_adj.items() if not a],'cross_contribution_comparison_ids':[x['id'] for x in actual['comparisons'] if len({indices['cases'][c]['contribution'] for c in x['case_ids']})>1],'case_reference_count':sum(len(x['case_ids']) for x in actual['comparisons'])}
chron=load(R/'data/chronology.json');coverage=Counter(c for route in chron['routes'] for c in route['case_ids'])
result['chronology']={'canonical_equal':chron==load(R/'analysis/chronology_routes.json'),'route_count':len(chron['routes']),'case_reference_count':sum(coverage.values()),'covered_case_count':len(coverage),'uncovered_cases':sorted(set(indices['cases'])-set(coverage)),'unknown_cases':sorted(set(coverage)-set(indices['cases'])),'route_case_counts':{r['id']:len(r['case_ids']) for r in chron['routes']},'duplicate_ids_within_routes':{r['id']:[c for c,n in Counter(r['case_ids']).items() if n>1] for r in chron['routes']},'case_membership_counts':dict(coverage)}
path_rows=[]
for c in actual['cases']:
    path_rows.append({'id':c['id'],'title':c['title'],'period':c['period'],'episode_interval':c['episode']['interval'],'regions':c['region'],'routes':[r['id'] for r in chron['routes'] if c['id'] in r['case_ids']],'comparisons':[x['id'] for x in actual['comparisons'] if c['id'] in x['case_ids']]})
(OUT/'reading-paths.json').write_text(json.dumps(path_rows,indent=2,ensure_ascii=False)+'\n')

# Stock tools run on an exact isolated copy. Snapshot omissions stay omitted.
copy=OUT/'rebuild-copy'
if copy.exists():raise SystemExit('Refusing to overwrite prior rebuild copy')
shutil.copytree(R,copy)
pre_hashes={p.relative_to(copy).as_posix():sha(p) for p in copy.rglob('*') if p.is_file()}
runs=[]
for tool in ['check_edition.py','check_review_repairs.py','verify_integrity.py','build_collection.py','build_chronology.py','build_explorer.py']:
    run=subprocess.run([sys.executable,str(copy/'tools'/tool)],capture_output=True,text=True,cwd=copy)
    log=OUT/(tool.removesuffix('.py')+'.log')
    log.write_text(run.stdout+'\nSTDERR\n'+run.stderr)
    runs.append({'tool':tool,'returncode':run.returncode,'log':log.name})
outputs=['data/'+f for f in ['cases.json','claims.json','sources.json','comparisons.json','graph.json','cases.csv','claims.csv','sources.csv','comparisons.csv','BIBLIOGRAPHY.md','CLAIM_LEDGER.md','COMPARISONS.md','GRAPH_GUIDE.md','COVERAGE_INVENTORY.md','source_url_groups.json','chronology.json','CHRONOLOGICAL_ROUTES.md']]+['cases/'+p.name for p in (R/'cases').glob('*.md')]
rebuild_validation=load(copy/'data/validation.json')
result['reproduction']={'runs':runs,'core_output_count':len(outputs),'core_byte_mismatches':[f for f in outputs if sha(copy/f)!=sha(R/f)],'all_changed_files':[p.relative_to(copy).as_posix() for p in copy.rglob('*') if p.is_file() and pre_hashes.get(p.relative_to(copy).as_posix())!=sha(p)],'link_errors_in_selected_snapshot_copy':rebuild_validation.get('local_link_errors',[]),'snapshot_omission_limit':'Nested historical review snapshots, local source caches and selected acceptance/integrity artifacts were not captured. Missing such files are not an observed live-main defect.'}
# A generation from unchanged validated inputs independently tests exact HTML determinism.
preview=OUT/'regenerated-index.html'
run=subprocess.run([sys.executable,str(copy/'tools/build_explorer.py'),'--data-dir',str(R/'data'),'--output',str(preview)],capture_output=True,text=True,cwd=OUT)
result['reproduction']['explorer_from_frozen_validated_data']={'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr,'byte_equal':preview.exists() and sha(preview)==sha(R/'index.html')}
result['snapshot_integrity_after']={'checked':len(manifest['files']),'mismatches':[x['path'] for x in manifest['files'] if sha(R/x['path'])!=x['sha256']]}
(OUT/'verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'parity':result['canonical']['all_records_equal_including_order'],'graph':{k:result['graph'][k] for k in ['node_count','edge_count','weak_component_count','component_size_distribution','multi_case_edge_ids','cross_contribution_edge_ids','basis_counts']},'comparison_component_sizes':list(map(len,case_comps)),'rebuild':result['reproduction']},indent=2))
