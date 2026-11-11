#!/usr/bin/env python3
"""Read-only frozen-input audit; execute frozen builders only in a temporary copy."""
import collections, csv, hashlib, json, pathlib, re, shutil, subprocess, sys, tempfile

OUT = pathlib.Path(__file__).resolve().parent
ROOT = OUT.parent / 'r1-snapshot'
PREFIXES = ['MAT', 'ANC', 'IND', 'LBR']
records = {k: [] for k in ['cases','claims','sources','comparisons','nodes','edges']}
paths = {}
for prefix in PREFIXES:
    for kind in ['cases','claims','sources','comparisons','graph']:
        path = ROOT/'contributions'/prefix/(kind+'.json')
        obj = json.loads(path.read_text())
        for subkind, rows in (obj.items() if kind == 'graph' else [(kind,obj)]):
            for i,row in enumerate(rows):
                records[subkind].append(row)
                paths[row['id']] = {'file':str(path.relative_to(ROOT)), 'json_pointer':f'/{subkind}/{i}' if kind=='graph' else f'/{i}'}
indices = {k:{x['id']:x for x in v} for k,v in records.items()}
errors=[]
all_ids=[x['id'] for rows in records.values() for x in rows]
if len(set(all_ids)) != len(all_ids): errors.append('duplicate ids')
def check(ok,msg):
    if not ok: errors.append(msg)
for kind, rows in records.items():
    for row in rows:
        ident=row['id']
        for field,target in [('case_ids','cases'),('claim_ids','claims'),('source_ids','sources')]:
            if field in row:
                check(isinstance(row[field],list),ident+': '+field+' not list')
                for ref in row[field]: check(ref in indices[target],ident+': unresolved '+ref)
for c in records['cases']:
    for field,keys in {
        'episode':['technology_configuration','task','population','interval','contemporary_alternatives','adoption_measure','observation_limits'],
        'actors':['chooser','payer','operator_maintainer','affected_nonchooser','ability_to_refuse'],
        'labour':['tasks','entry_barriers','bargaining_ownership','transition','distribution','evidence_limit']}.items():
        for key in keys: check(bool(c.get(field,{}).get(key)),c['id']+': missing '+field+'.'+key)
    check(isinstance(c['episode']['contemporary_alternatives'],list),c['id']+': alternatives not list')
for c in records['claims']:
    t=c['test']; status=t.get('status')
    check(status in ['descriptive-only','evaluated','underdetermined','proposed'],c['id']+': invalid test status')
    if status=='descriptive-only':
        check(c['causal_status']=='descriptive' and bool(t.get('reason')),c['id']+': invalid descriptive test')
    else:
        for key in ['mechanism_chain','strongest_rival','discriminating_observation','evidence_sought_found','remaining_ambiguity','hypothesis_timing']:
            check(bool(t.get(key)),c['id']+': missing test '+key)
    for s in c['sources']: check(s['source_id'] in indices['sources'],c['id']+': unresolved support')
confidence={'low':0,'medium':1,'high':2}
flags=[]
for e in records['edges']:
    ident=e['id']; sc=e['scope']
    for field in ['from','to']: check(e[field] in indices['nodes'],ident+': unresolved endpoint')
    check(sc.get('case_id') in e['case_ids'],ident+': scope case mismatch')
    for key in ['stage','configuration']: check(bool(sc.get(key)),ident+': missing scope '+key)
    for key in ['alternatives','joint_inputs']: check(isinstance(e.get(key),list),ident+': '+key+' not array')
    for n in e['joint_inputs']: check(n in indices['nodes'],ident+': unresolved joint input')
    check(e['basis'] in ['technical-possibility','observed-contribution','documented-transmission','inferred-transmission','bounded-necessity','hypothesis'],ident+': invalid basis')
    if e['relation']=='depends-on':
        check(e['basis']=='bounded-necessity',ident+': depends-on not bounded')
        check(bool(e['necessity_rationale']) and e['necessity_rationale']!='No necessity claim',ident+': missing necessity rationale')
    support={s['source_id'] for k in e['claim_ids'] for s in indices['claims'][k]['sources']}
    check(set(e['source_ids']).issubset(support),ident+': edge source absent from linked claims')
    if confidence[e['confidence']]>max(confidence[indices['claims'][k]['confidence']] for k in e['claim_ids']):
        flags.append({'edge_id':ident,'edge_confidence':e['confidence'],'claim_confidences':{k:indices['claims'][k]['confidence'] for k in e['claim_ids']},'interpretation':'Review flag only: narrower physical claims may warrant greater confidence.'})
for s in records['sources']: check(bool(s.get('evidence_lineage')),s['id']+': missing lineage')
cross=[]
for a in records['edges']:
    for b in records['edges']:
        if a['to']==b['from'] and a['scope']['case_id']!=b['scope']['case_id']:
            cross.append({'edges':[a['id'],b['id']],'shared_node':a['to'],'relation_sequence':[a['relation'],b['relation']],'scope_cases':[a['scope']['case_id'],b['scope']['case_id']],'warning':'Directed adjacency only; this is not a causal or transmission inference.'})
manifest=json.loads((ROOT/'MANIFEST.json').read_text())
hash_checks=[{'path':x['path'],'matches':hashlib.sha256((ROOT/x['path']).read_bytes()).hexdigest()==x['sha256']} for x in manifest['files']]
export={}
with tempfile.TemporaryDirectory(prefix='export-check-',dir=OUT) as td:
    clone=pathlib.Path(td)/'snapshot';shutil.copytree(ROOT,clone)
    run=subprocess.run([sys.executable,str(clone/'tools/build_collection.py')],capture_output=True,text=True)
    val=json.loads((clone/'data/validation.json').read_text())
    export['builder_returncode']=run.returncode
    export['builder_errors']=val['errors']
    export['builder_non_link_errors']=[x for x in val['errors'] if not x.startswith('broken local link:')]
    export['unmodified_snapshot_counts']=val['counts']
    export['unmodified_snapshot_incomplete_contributions']=val['incomplete_contributions']
    export['unmodified_snapshot_omitted_ids']={kind:sorted(set(indices[kind])-set(x['id'] for x in json.loads((clone/'data'/(kind+'.json')).read_text()))) for kind in ['cases','claims','sources','comparisons']}
    export['note']='Snapshot intentionally excludes other dossiers and integration targets. However IND/questions.md is also absent and the completeness gate excludes IND. The frozen validation metadata already records its broken report link. Current main state was not inspected.'
    # Controlled counterfactual: satisfy the gate without supplying invented research content.
    (clone/'contributions/IND/questions.md').write_text('# Audit-only placeholder\nNo research content. Temporary file only to test export of the frozen IND JSON.\n')
    fullrun=subprocess.run([sys.executable,str(clone/'tools/build_collection.py')],capture_output=True,text=True)
    fullval=json.loads((clone/'data/validation.json').read_text())
    export['controlled_placeholder_run']={'change':'Added IND/questions.md in temporary copy only, with explicit audit-only placeholder text.','counts':fullval['counts'],'returncode':fullrun.returncode,'errors':fullval['errors']}
    export['json_roundtrip']={};export['csv_roundtrip']={}
    for kind in ['cases','claims','sources','comparisons']:
        compiled=json.loads((clone/'data'/(kind+'.json')).read_text())
        restored=[{k:v for k,v in x.items() if k!='contribution'} for x in compiled]
        export['json_roundtrip'][kind]=sorted(restored,key=lambda x:x['id'])==sorted(records[kind],key=lambda x:x['id'])
        with (clone/'data'/(kind+'.csv')).open() as f: csvrows=list(csv.DictReader(f))
        lookup={x['id']:x for x in csvrows}; failures=[]
        for row in compiled:
            for k,v in row.items():
                expected=json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else str(v)
                if lookup[row['id']][k]!=expected:failures.append([row['id'],k])
        export['csv_roundtrip'][kind]={'rows':len(csvrows),'field_mismatches':failures}
    graph=json.loads((clone/'data/graph.json').read_text())
    export['json_roundtrip']['graph']=all(sorted([{k:v for k,v in x.items() if k!='contribution'} for x in graph[kind]],key=lambda x:x['id'])==sorted(records[kind],key=lambda x:x['id']) for kind in ['nodes','edges'])
    erun=subprocess.run([sys.executable,str(clone/'tools/build_explorer.py')],capture_output=True,text=True)
    html=(clone/'index.html').read_text()
    payload=json.loads(re.search(r'<script id="research-data" type="application/json">(.*?)</script>',html,re.S).group(1))
    export['explorer_returncode']=erun.returncode
    export['explorer_payload_equal']={kind:payload[kind]==json.loads((clone/'data'/(kind+'.json')).read_text()) for kind in ['cases','claims','sources','graph','comparisons','validation']}
    export['explorer_render_contract']={key:token in html for key,token in {'actors':'pairs(c.actors)','labour':'pairs(c.labour)','episode':'pairs(c.episode)','tests':'pairs(k.test)','edge_scope':'val(e.scope)','edge_basis':'h(e.basis)','edge_dispute':'dispute:e.dispute','edge_joint_inputs':'joint_inputs:e.joint_inputs','source_lineage':'evidence_lineage:s.evidence_lineage'}.items()}
    # Negative probes isolate omissions in the frozen validator; all mutations stay in the temporary copy.
    probes=[]
    for name,file,mutate in [
        ('invalid_test_status','contributions/ANC/claims.json',lambda rows:rows[1]['test'].__setitem__('status','invalid-status')),
        ('alternatives_string','contributions/ANC/graph.json',lambda g:g['edges'][0].__setitem__('alternatives','not-an-array')),
        ('empty_necessity_rationale','contributions/ANC/graph.json',lambda g:g['edges'][0].__setitem__('necessity_rationale',''))]:
        path=clone/file; original=path.read_text();obj=json.loads(original);mutate(obj);path.write_text(json.dumps(obj))
        subprocess.run([sys.executable,str(clone/'tools/build_collection.py')],capture_output=True,text=True)
        ev=json.loads((clone/'data/validation.json').read_text())
        nonlink=[x for x in ev['errors'] if not x.startswith('broken local link:')]
        probes.append({'probe':name,'rejected_by_schema':bool(nonlink),'schema_errors':nonlink})
        path.write_text(original)
    export['validator_negative_probes']=probes
result={'input_root':str(ROOT),'counts':{k:len(v) for k,v in records.items()},'ids':{k:[x['id'] for x in v] for k,v in records.items()},'json_locations':paths,'structural_errors':errors,'test_status_counts':dict(collections.Counter(c['test']['status'] for c in records['claims'])),'edge_basis_counts':dict(collections.Counter(e['basis'] for e in records['edges'])),'nonempty_joint_bundles':[e['id'] for e in records['edges'] if e['joint_inputs']],'cross_case_directed_adjacencies':cross,'confidence_review_flags':flags,'multi_case_nodes':[n for n in records['nodes'] if len(n['case_ids'])>1],'export':export,'snapshot_manifest_checks':hash_checks,'all_manifest_hashes_match':all(x['matches'] for x in hash_checks)}
(OUT/'structural_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['counts','structural_errors','test_status_counts','edge_basis_counts','nonempty_joint_bundles','cross_case_directed_adjacencies','all_manifest_hashes_match']},indent=2))
print(json.dumps(export,indent=2))
