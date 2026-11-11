"""Structural checks only: these cannot establish source entailment or historical truth."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
errors = []

def check(condition, message):
    if not condition:
        errors.append(message)

def load(name):
    return json.loads((ROOT / name).read_text())

cases = load('cases.json')
sources = load('sources.json')
claims = load('claims.json')
graph = load('graph.json')
comparisons = load('comparisons.json')
ci = {x['id']: x for x in cases}
si = {x['id']: x for x in sources}
ki = {x['id']: x for x in claims}
ni = {x['id']: x for x in graph['nodes']}
records = cases + sources + claims + graph['nodes'] + graph['edges'] + comparisons
ids = [x['id'] for x in records]
check(len(ids) == len(set(ids)), 'Duplicate IDs')
for x in ids:
    check(bool(re.fullmatch(r'SKL-[CSKTEX]\d{2}', x)), f'Invalid ID {x}')

required = {
    'case': 'id title region period domain outcome summary stages mechanisms counterevidence claim_ids source_ids episode actors labour'.split(),
    'source': 'id title authors year url source_type access locator scope_limit accessed evidence_lineage'.split(),
    'claim': 'id case_ids statement evidence_type confidence causal_status sources counterevidence inference_limits test'.split(),
    'edge': 'id from to relation case_ids claim_ids source_ids confidence qualification basis scope alternatives joint_inputs necessity_rationale dispute'.split(),
    'node': 'id label kind case_ids'.split(),
    'comparison': 'id question case_ids useful_similarities important_differences evidence_comparability connections_nonindependence omitted_countercases conclusion_limit'.split(),
}
for kind, collection in [('case', cases), ('source', sources), ('claim', claims), ('edge', graph['edges']), ('node', graph['nodes']), ('comparison', comparisons)]:
    for record in collection:
        check(set(required[kind]).issubset(record), f'{record["id"]}: missing {kind} fields')

case_nested = {
    'episode': 'technology_configuration task population interval contemporary_alternatives adoption_measure observation_limits'.split(),
    'actors': 'chooser payer operator_maintainer affected_nonchooser ability_to_refuse'.split(),
    'labour': 'tasks entry_barriers bargaining_ownership transition distribution evidence_limit'.split(),
}
for c in cases:
    for obj, fields in case_nested.items():
        check(set(fields).issubset(c[obj]), f'{c["id"]}: incomplete {obj}')
    for k in c['claim_ids']:
        check(k in ki, f'{c["id"]}: missing claim {k}')
        if k in ki:
            check(c['id'] in ki[k]['case_ids'], f'{c["id"]}: nonreciprocal claim {k}')
    for s in c['source_ids']:
        check(s in si, f'{c["id"]}: missing source {s}')

for s in sources:
    check(s['access'] in {'full-text', 'partial-text', 'abstract', 'metadata', 'search-excerpt'}, f'{s["id"]}: access value')
    check(s['url'].startswith('https://'), f'{s["id"]}: invalid URL')
    check(not any(k in s['url'] for k in ['X-Amz-', 'access_token', 'api_key']), f'{s["id"]}: access-bearing URL')

test_fields = {'status','mechanism_chain','strongest_rival','discriminating_observation','evidence_sought_found','remaining_ambiguity','hypothesis_timing'}
for k in claims:
    check(k['confidence'] in {'high','medium','low'}, f'{k["id"]}: confidence value')
    for c in k['case_ids']:
        check(c in ci, f'{k["id"]}: missing case {c}')
    for r in k['sources']:
        check(set(['source_id','locator','supports']).issubset(r), f'{k["id"]}: incomplete source reference')
        check(r['source_id'] in si, f'{k["id"]}: missing source {r["source_id"]}')
    if k['causal_status'] != 'descriptive':
        check(test_fields.issubset(k['test']), f'{k["id"]}: incomplete diagnostic test')
        check(k['test']['status'] in {'evaluated','underdetermined','proposed'}, f'{k["id"]}: test status')
    else:
        check(k['test'].get('status') == 'descriptive-only', f'{k["id"]}: descriptive test annotation')

for n in graph['nodes']:
    check(n['kind'] in {'technology','complement','institution','resource','practice'}, f'{n["id"]}: node kind')
    for c in n['case_ids']:
        check(c in ci, f'{n["id"]}: case {c}')

for e in graph['edges']:
    check(e['from'] in ni and e['to'] in ni, f'{e["id"]}: endpoint')
    check(e['relation'] in {'enables','depends-on','complements','competes-with','displaces','constrains'}, f'{e["id"]}: relation')
    check(e['basis'] in {'technical-possibility','observed-contribution','documented-transmission','inferred-transmission','bounded-necessity','hypothesis'}, f'{e["id"]}: basis')
    check(set(['case_id','stage','configuration']).issubset(e['scope']), f'{e["id"]}: scope')
    check(e['scope']['case_id'] in ci, f'{e["id"]}: scope case')
    check(e['scope']['case_id'] in e['case_ids'], f'{e["id"]}: inconsistent scope case')
    for c in e['case_ids']:
        check(c in ci, f'{e["id"]}: case {c}')
    for k in e['claim_ids']:
        check(k in ki, f'{e["id"]}: claim {k}')
        if k in ki:
            check(set(ki[k]['case_ids']) & set(e['case_ids']), f'{e["id"]}: claim/case mismatch')
    for s in e['source_ids']:
        check(s in si, f'{e["id"]}: source {s}')
    for n in e['joint_inputs']:
        check(n in ni, f'{e["id"]}: joint-input node {n}')
    if e['relation'] == 'depends-on':
        check(e['basis'] == 'bounded-necessity', f'{e["id"]}: depends-on without bounded necessity')
        check(e['necessity_rationale'] != 'No necessity claim', f'{e["id"]}: missing necessity rationale')

for x in comparisons:
    for c in x['case_ids']:
        check(c in ci, f'{x["id"]}: case {c}')

report = (ROOT / 'report.md').read_text()
for k in ki:
    check(k in report, f'{k}: absent from report')
for file in ['report.md','questions.md']:
    check((ROOT / file).stat().st_size > 0, f'{file}: empty')
word_count = len(report.split())
check(2500 <= word_count <= 3500, f'Report length {word_count} outside requested approximate range')

result = {
    'validated': '2026-11-05',
    'scope': 'SKL structural checks only; manual source/claim reading recorded in source-notes.md and report.md',
    'counts': {'cases':len(cases),'sources':len(sources),'claims':len(claims),'nodes':len(graph['nodes']),'edges':len(graph['edges']),'comparisons':len(comparisons),'report_words':word_count},
    'source_access': {v:sum(s['access']==v for s in sources) for v in sorted({s['access'] for s in sources})},
    'necessity_edges':sum(e['relation']=='depends-on' for e in graph['edges']),
    'errors': errors,
    'passed': not errors,
}
(ROOT / 'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))
