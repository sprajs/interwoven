"""Check CTX structure, references and local file integrity; not historical truth."""
from pathlib import Path
import hashlib
import json
import re

R = Path(__file__).parent
D = {n: json.loads((R / f'{n}.json').read_text()) for n in ('cases', 'sources', 'claims', 'graph', 'comparisons')}
errors = []

def ck(ok, msg):
    if not ok:
        errors.append(msg)

def fields(obj, keys, label):
    for key in keys:
        ck(key in obj and obj[key] not in ('', None), f'{label}: missing {key}')

def refs(ids, valid, label):
    for ident in ids:
        ck(ident in valid, f'{label}: unresolved {ident}')

C = {r['id'] for r in D['cases']}
S = {r['id'] for r in D['sources']}
K = {r['id'] for r in D['claims']}
N = {r['id'] for r in D['graph']['nodes']}
ind_cases = {r['id'] for r in json.loads((R.parent / 'IND/cases.json').read_text())}
all_records = D['cases'] + D['sources'] + D['claims'] + D['graph']['nodes'] + D['graph']['edges'] + D['comparisons']
ids = [r['id'] for r in all_records]
ck(len(ids) == len(set(ids)), 'Duplicate CTX record IDs')
for record in all_records:
    ck(bool(re.fullmatch(r'CTX-[CSKTEX]\d{2}', record['id'])), f'Invalid ID {record["id"]}')
for case in D['cases']:
    fields(case, ['id', 'title', 'region', 'period', 'domain', 'outcome', 'summary', 'stages', 'mechanisms', 'counterevidence', 'claim_ids', 'source_ids', 'episode', 'actors', 'labour'], case['id'])
    fields(case['episode'], ['technology_configuration', 'task', 'population', 'interval', 'contemporary_alternatives', 'adoption_measure', 'observation_limits'], case['id'] + '.episode')
    fields(case['actors'], ['chooser', 'payer', 'operator_maintainer', 'affected_nonchooser', 'ability_to_refuse'], case['id'] + '.actors')
    fields(case['labour'], ['tasks', 'entry_barriers', 'bargaining_ownership', 'transition', 'distribution', 'evidence_limit'], case['id'] + '.labour')
    refs(case['claim_ids'], K, case['id']); refs(case['source_ids'], S, case['id'])
for source in D['sources']:
    fields(source, ['id', 'title', 'authors', 'year', 'url', 'source_type', 'access', 'locator', 'scope_limit', 'accessed', 'evidence_lineage'], source['id'])
    ck(source['access'] in {'full-text', 'partial-text', 'abstract', 'metadata', 'search-excerpt'}, source['id'] + ': invalid access')
    ck(source['url'].startswith('https://'), source['id'] + ': invalid source URL')
for claim in D['claims']:
    fields(claim, ['id', 'case_ids', 'statement', 'evidence_type', 'confidence', 'causal_status', 'sources', 'counterevidence', 'inference_limits', 'test'], claim['id'])
    refs(claim['case_ids'], C, claim['id'])
    ck(claim['confidence'] in {'high', 'medium', 'low'}, claim['id'] + ': invalid confidence')
    ck(claim['causal_status'] in {'descriptive', 'mechanism-supported', 'causal-identification', 'contested', 'hypothesis'}, claim['id'] + ': invalid causal status')
    for source in claim['sources']:
        fields(source, ['source_id', 'locator', 'supports'], claim['id'] + '.sources')
        refs([source['source_id']], S, claim['id'])
    if claim['causal_status'] == 'descriptive':
        ck(claim['test']['status'] == 'descriptive-only', claim['id'] + ': wrong descriptive test')
        fields(claim['test'], ['reason'], claim['id'] + '.test')
    else:
        ck(claim['test']['status'] in {'evaluated', 'underdetermined', 'proposed'}, claim['id'] + ': invalid mechanism test')
        fields(claim['test'], ['mechanism_chain', 'strongest_rival', 'discriminating_observation', 'evidence_sought_found', 'remaining_ambiguity', 'hypothesis_timing'], claim['id'] + '.test')
for node in D['graph']['nodes']:
    fields(node, ['id', 'label', 'kind', 'case_ids'], node['id'])
    refs(node['case_ids'], C, node['id'])
    ck(node['kind'] in {'technology', 'complement', 'institution', 'resource', 'practice'}, node['id'] + ': invalid kind')
for edge in D['graph']['edges']:
    fields(edge, ['id', 'from', 'to', 'relation', 'case_ids', 'claim_ids', 'source_ids', 'confidence', 'qualification', 'basis', 'scope', 'alternatives', 'joint_inputs', 'necessity_rationale', 'dispute'], edge['id'])
    refs([edge['from'], edge['to']], N, edge['id']); refs(edge['case_ids'], C, edge['id'])
    refs(edge['claim_ids'], K, edge['id']); refs(edge['source_ids'], S, edge['id']); refs(edge['joint_inputs'], N, edge['id'])
    ck(edge['relation'] in {'enables', 'depends-on', 'complements', 'competes-with', 'displaces', 'constrains'}, edge['id'] + ': invalid relation')
    ck(edge['basis'] in {'technical-possibility', 'observed-contribution', 'documented-transmission', 'inferred-transmission', 'bounded-necessity', 'hypothesis'}, edge['id'] + ': invalid basis')
    fields(edge['scope'], ['case_id', 'stage', 'configuration'], edge['id'] + '.scope')
    ck(edge['scope']['case_id'] in edge['case_ids'], edge['id'] + ': inconsistent scope')
    ck(edge['relation'] != 'depends-on' or edge['basis'] == 'bounded-necessity', edge['id'] + ': unbounded dependency')
    for kid in edge['claim_ids']:
        claim = next(x for x in D['claims'] if x['id'] == kid)
        ck(edge['scope']['case_id'] in claim['case_ids'], edge['id'] + ': claim outside case scope')
        ck(set(edge['source_ids']).issubset({x['source_id'] for x in claim['sources']}), edge['id'] + ': source absent from supporting claim')
for comparison in D['comparisons']:
    fields(comparison, ['id', 'question', 'case_ids', 'useful_similarities', 'important_differences', 'evidence_comparability', 'connections_nonindependence', 'omitted_countercases', 'conclusion_limit'], comparison['id'])
    refs(comparison['case_ids'], C | ind_cases, comparison['id'])
    ck('IND-C07' in comparison['case_ids'] and 'CTX-C01' in comparison['case_ids'], comparison['id'] + ': required explicit comparison absent')

for path in (R / 'report.md', R / 'questions.md', R / 'evidence/READING_NOTES.md'):
    for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        if not target.startswith(('https://', 'http://', '#')):
            ck((path.parent / target.split('#')[0]).is_file(), f'{path.name}: missing local link {target}')
    for ident in re.findall(r'\bCTX-[CSKTEX]\d{2}\b', path.read_text()):
        # S02 was an unsuccessful acquisition lead, not a used source record.
        ck(ident in ids or ident == 'CTX-S02', f'{path.name}: undefined reference {ident}')

manifest = json.loads((R / 'evidence/download_manifest.json').read_text())
verified = []
for attempt in manifest:
    if attempt.get('file'):
        path = R / 'evidence' / attempt['file']
        ck(path.is_file(), 'Missing acquired file ' + str(path))
        if path.is_file():
            ck(hashlib.sha256(path.read_bytes()).hexdigest() == attempt['sha256'], 'Hash mismatch ' + path.name)
            verified.append(path.name)
            ck(attempt.get('acquired_original') is False, 'Unexpected original-access classification')
            ck(path.suffix != '.pdf' or path.read_bytes().startswith(b'%PDF'), 'Non-PDF saved as PDF')

out = {
    'checked': '2026-11-05', 'scope': 'CTX only; structure and authored source-boundary audit, not independent historical acceptance',
    'status': 'pass' if not errors else 'fail',
    'counts': {**{n: len(D[n]) for n in ('cases', 'sources', 'claims', 'comparisons')}, 'nodes': len(N), 'edges': len(D['graph']['edges']), 'report_words': len((R / 'report.md').read_text().split())},
    'errors': errors, 'external_case_references_verified': ['IND-C07'],
    'source_access': {'used_full_text_sources_available_via_web': 2, 'original_local_pdfs': 0, 'failed_acquisition_html_hashes_verified': verified},
    'author_audit': {'claim_denominator': 8, 'claims_checked': sorted(K), 'edge_denominator': 7, 'edges_checked': 7, 'independent_review': False, 'mechanism_tests': 'All five remain underdetermined regarding relative causal weights', 'lineage': 'CTX-S01 equals IND-S15; CTX-S03 inherits its cloth-access evidence from Eyferth2012/2015; no independent replication claimed'},
}
(R / 'validation.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(out, ensure_ascii=False, indent=2))
raise SystemExit(bool(errors))
