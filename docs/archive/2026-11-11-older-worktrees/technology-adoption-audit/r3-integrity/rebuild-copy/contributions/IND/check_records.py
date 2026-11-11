"""Validate IND contribution-contract v2 structure and internal references."""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

P = Path(__file__).parent
data = {name: json.loads((P / f'{name}.json').read_text())
        for name in ('cases', 'claims', 'sources', 'graph', 'comparisons')}
errors = []

def require(condition, message):
    if not condition:
        errors.append(message)

def fields(record, expected):
    for field in expected.split():
        require(field in record, f"{record.get('id', 'object')}: missing {field}")

def identifiers(records, prefix):
    ids = [r['id'] for r in records]
    require(len(ids) == len(set(ids)), f'Duplicate {prefix} identifiers')
    require(all(i.startswith(f'IND-{prefix}') for i in ids), f'Unexpected {prefix} identifier')
    return set(ids)

cases, claims, sources = (data[name] for name in ('cases', 'claims', 'sources'))
nodes, edges = data['graph']['nodes'], data['graph']['edges']
case_ids = identifiers(cases, 'C')
claim_ids = identifiers(claims, 'K')
source_ids = identifiers(sources, 'S')
node_ids = identifiers(nodes, 'T')
identifiers(edges, 'E')
identifiers(data['comparisons'], 'X')

def refs(record, field, available):
    require(isinstance(record.get(field), list), f"{record['id']}: {field} is not an array")
    for reference in record.get(field, []):
        require(reference in available, f"{record['id']}: unknown {field} reference {reference}")

for case in cases:
    fields(case, 'id title region period domain outcome summary stages mechanisms counterevidence claim_ids source_ids episode actors labour')
    fields(case['episode'], 'technology_configuration task population interval contemporary_alternatives adoption_measure observation_limits')
    fields(case['actors'], 'chooser payer operator_maintainer affected_nonchooser ability_to_refuse')
    fields(case['labour'], 'tasks entry_barriers bargaining_ownership transition distribution evidence_limit')
    refs(case, 'claim_ids', claim_ids)
    refs(case, 'source_ids', source_ids)

for claim in claims:
    fields(claim, 'id case_ids statement evidence_type confidence causal_status sources counterevidence inference_limits test')
    refs(claim, 'case_ids', case_ids)
    require(claim['confidence'] in {'high', 'medium', 'low'}, f"{claim['id']}: confidence")
    require(claim['causal_status'] in {'descriptive', 'mechanism-supported', 'causal-identification', 'contested', 'hypothesis'}, f"{claim['id']}: causal status")
    require(bool(claim['sources']), f"{claim['id']}: no evidence")
    for citation in claim['sources']:
        fields(citation, 'source_id locator supports')
        require(citation['source_id'] in source_ids, f"{claim['id']}: unknown source")
    if claim['causal_status'] == 'descriptive':
        fields(claim['test'], 'status reason')
        require(claim['test']['status'] == 'descriptive-only', f"{claim['id']}: descriptive test status")
    else:
        fields(claim['test'], 'status mechanism_chain strongest_rival discriminating_observation evidence_sought_found remaining_ambiguity hypothesis_timing')
        require(claim['test']['status'] in {'evaluated', 'underdetermined', 'proposed'}, f"{claim['id']}: mechanism test status")

for source in sources:
    fields(source, 'id title authors year url source_type access locator scope_limit accessed evidence_lineage')
    require(source['access'] in {'full-text', 'partial-text', 'abstract', 'metadata', 'search-excerpt'}, f"{source['id']}: access")
    require(source['url'].startswith('https://'), f"{source['id']}: URL scheme")

node_map = {node['id']: node for node in nodes}
claim_map = {claim['id']: claim for claim in claims}
for node in nodes:
    fields(node, 'id label kind case_ids')
    refs(node, 'case_ids', case_ids)
    require(node['kind'] in {'technology', 'complement', 'institution', 'resource', 'practice'}, f"{node['id']}: kind")
for edge in edges:
    fields(edge, 'id from to relation case_ids claim_ids source_ids confidence qualification basis scope alternatives joint_inputs necessity_rationale dispute')
    refs(edge, 'case_ids', case_ids)
    refs(edge, 'claim_ids', claim_ids)
    refs(edge, 'source_ids', source_ids)
    refs(edge, 'joint_inputs', node_ids)
    fields(edge['scope'], 'case_id stage configuration')
    require(edge['scope']['case_id'] in edge['case_ids'], f"{edge['id']}: scope mismatch")
    require(edge['relation'] in {'enables', 'depends-on', 'complements', 'competes-with', 'displaces', 'constrains'}, f"{edge['id']}: relation")
    require(edge['basis'] in {'technical-possibility', 'observed-contribution', 'documented-transmission', 'inferred-transmission', 'bounded-necessity', 'hypothesis'}, f"{edge['id']}: basis")
    for endpoint in ('from', 'to'):
        require(edge[endpoint] in node_ids, f"{edge['id']}: unknown endpoint")
        if edge[endpoint] in node_ids:
            require(edge['scope']['case_id'] in node_map[edge[endpoint]]['case_ids'], f"{edge['id']}: endpoint outside local case")
    for claim_id in edge['claim_ids']:
        if claim_id in claim_map:
            require(edge['scope']['case_id'] in claim_map[claim_id]['case_ids'], f"{edge['id']}: claim outside local case")
    if edge['relation'] == 'depends-on':
        require(edge['basis'] == 'bounded-necessity', f"{edge['id']}: unsupported necessity")
    if edge['basis'] == 'bounded-necessity':
        require(edge['necessity_rationale'] != 'No necessity claim', f"{edge['id']}: missing necessity rationale")
    require(bool(edge['alternatives']), f"{edge['id']}: alternatives not recorded")

for comparison in data['comparisons']:
    fields(comparison, 'id question case_ids useful_similarities important_differences evidence_comparability connections_nonindependence omitted_countercases conclusion_limit')
    refs(comparison, 'case_ids', case_ids)

for required_file in ('report.md', 'questions.md'):
    require((P / required_file).is_file(), f'Missing {required_file}')

result = {
    'checked_utc': datetime.now(timezone.utc).isoformat(),
    'contract': 'METHODS.md plus METHODS_ADDENDUM_V2.md',
    'status': 'pass' if not errors else 'fail',
    'counts': {'cases': len(cases), 'claims': len(claims), 'sources': len(sources),
               'nodes': len(nodes), 'edges': len(edges), 'comparisons': len(data['comparisons'])},
    'source_access': dict(Counter(source['access'] for source in sources)),
    'claim_causal_status': dict(Counter(claim['causal_status'] for claim in claims)),
    'edge_basis': dict(Counter(edge['basis'] for edge in edges)),
    'errors': errors,
    'limit': 'Structural integrity and internal scope only; this is not independent historical or causal validation.'
}
(P / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(bool(errors))
