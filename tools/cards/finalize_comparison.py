#!/usr/bin/env python3
"""Rebuild final comparison artifacts from observed private records; no model calls."""
import argparse
import hashlib
import json
from pathlib import Path
import analyze_comparison as analysis_tool
import compare


def finalize(state, out):
    state, out = Path(state), Path(out)
    compare.audit_saved_calls(state)
    analysis, rows, safe = analysis_tool.analyze(state, out / 'cases.json', state / 'judgments.json')
    if analysis['coverage']['completed_review_counts'] != {'A': 100, 'B': 100}:
        raise ValueError('Finalization requires both arms on exactly 100 candidates')
    if any(q['judged_cases'] != 80 for q in analysis['quality']['arms'].values()):
        raise ValueError('Finalization requires all held-out judgments')
    analysis_tool.write_report(analysis, rows, safe, out)

    generated = json.loads((state / 'proposal-results.json').read_text())
    quality = json.loads((state / 'proposal-quality.json').read_text())
    calls = [json.loads(p.read_text()) for p in (state / 'calls').glob('*.json')]
    proposals = []
    for model in generated['models']:
        call = next(c for c in calls if c['fingerprint'] == model['request_fingerprint'])
        q = next(q for q in quality['models'] if (q['model'], q['effort']) == (model['model'], model['effort']))
        cost = sum(compare.api_cost(model['model'], u) for u in call['usage_records'].values())
        proposals.append({'model': model['model'], 'effort': model['effort'],
            'generated': len(model['proposals']), 'textUseful': q['text_judged_useful_hypotheses'],
            'textNovel': q['text_judged_novel'], 'ambiguousScope': q['ambiguous_scope'],
            'exactNameDuplicates': q['exact_inventory_duplicates'], 'genCostUsd': cost,
            'genSeconds': call['elapsed_seconds'], 'verifiedCandidates': None,
            'costPerTextUsefulHypothesisUsd': cost / q['text_judged_useful_hypotheses'] if q['text_judged_useful_hypotheses'] else None})
    proposal_summary = {'models': proposals, 'same_inventory_sha256': generated['inventory_sha256'],
        'opportunity_budget': generated['opportunity_budget'], 'historical_quality': 'unmeasured',
        'quality_reference': 'Blinded same-family model assessment of proposal text only',
        'admitted_to_fixed_comparison': 0, 'admitted_to_dataset': 0,
        'protocol_limit': 'Equal inventory, proposal count and answer target; no enforceable equal reasoning ceiling or equal realized spend.'}
    compare.write_json(out / 'proposal-summary.json', proposal_summary)

    auxiliary = json.loads((state / 'secondary-review-usage.json').read_text())
    seen, totals = set(), {k: 0 for k in ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'output_tokens', 'reasoning_output_tokens')}
    auxiliary_cost = 0
    primary_ids={rid for c in calls for rid in c.get('usage_records',{})}
    for response in auxiliary['unique_responses']:
        rid = response['response_id']
        if not isinstance(rid,str) or not rid:
            raise ValueError('Auxiliary usage requires actual response IDs')
        if rid in primary_ids:
            raise ValueError('Auxiliary response already counted in primary ledger')
        if rid in seen:
            continue
        seen.add(rid)
        for key in totals:
            totals[key] += response['usage'].get(key, 0)
        auxiliary_cost += compare.api_cost(response['model'], response['usage'])
    auxiliary_summary = {'stage': 'targeted_secondary_source_review', 'unique_responses': len(seen),
        'tokens': totals, 'api_equivalent_usd': auxiliary_cost, 'elapsed_seconds': None,
        'usage_file_sha256': hashlib.sha256((state / 'secondary-review-usage.json').read_bytes()).hexdigest(),
        'included_in_primary_cli_total': False,
        'primary_cli_api_equivalent_usd': analysis['accounting']['totals']['api_equivalent_usd'],
        'combined_observed_model_api_equivalent_usd': analysis['accounting']['totals']['api_equivalent_usd'] + auxiliary_cost,
        'billing_or_subscription_credits': None,
        'scope': 'Five targeted source disputes via Sol medium agent; observed response usage only. Implementation/coordination development work is outside this benchmark total. Agent/system prompt overhead is not byte-replayable outside its framework.'}
    auxiliary_summary['capability_probe_accounting']='Probe-turn usage is retained separately in execution.json. Ephemeral probes lack per-response IDs and are excluded from the unique-response audited total.'
    compare.write_json(out / 'auxiliary-usage.json', auxiliary_summary)

    policy = {'schema_version': 1, 'decision': 'No tested mix meets the declared quality gate; no confident winner.',
        'comparison_snapshot': json.loads((out / 'preregistration.json').read_text())['dataset_snapshot'],
        'quality_reference': 'Provisional same-family model source readings with preserved disagreements',
        'selected_interim_route': 'B', 'selection_status': 'Conservative operational default, not a passing or certified winner',
        'proposal': {'model': 'gpt-6.1-sol', 'effort': 'medium', 'status': 'Lowest observed proposal cost at equal text-only yield; historical proposal accuracy unmeasured'},
        'extract': {'model': 'gpt-6.1-terra', 'effort': 'low'},
        'review': {'model': 'gpt-6.1-sol', 'effort': 'medium', 'mandatory_for_every_admission': True},
        'disputes': {'model': 'gpt-6-astra', 'effort': 'medium', 'route': 'Targeted original-source reading; human/historian review where consequential ambiguity remains'},
        'automatic_admission': False, 'new_large_campaign_started': False,
        'gate_failures': {a: {'source_flagged_admissions': q['false_admissions'], 'mechanical_failures': q['mechanical_failure_count']} for a, q in analysis['quality']['arms'].items()},
        'required_before_integration': ['Current snapshot duplicate/extension screen', 'Exact source/version and mechanical checks', 'Independent semantic acceptance of every retained facet/relation', 'Resolve or defer consequential source disputes', 'Single integrator; isolated validation and affected tests']}
    compare.write_json(out / 'decision.json', policy)
    compare.write_json(compare.ROOT / 'docs/research-agents/model-policy.json', policy)

    costs = {a: sum(g['api_equivalent_usd'] for k, g in analysis['accounting']['groups'].items() if k.startswith(a + '|')) for a in ('A', 'B')}
    q = analysis['quality']['arms']
    lead = f'''# Neither tested workflow met the quality gate

Retain **Terra low extraction + Sol medium semantic review (Arm B)** as a conservative interim route, with selective escalation and no automatic admission. No new large campaign was started.

On the 80 held-out cases, the primary blinded source assessment flagged {q['A']['false_admissions']} admission proposals in A and {q['B']['false_admissions']} in B. Final mechanical checks failed {q['A']['mechanical_failure_count']} reviewed outputs in A and {q['B']['mechanical_failure_count']} in B. Both arms therefore failed the declared gate. These are model-reference judgments and protocol failures, not certified historical error rates. The targeted secondary reading disagreed on five claim labels; see [adjudication process and sensitivity](adjudication.json).

Across all 100 candidates, extraction/review cost was **${costs['A']:.3f} for A** and **${costs['B']:.3f} for B**, a standard API-equivalent scenario excluding evaluation overhead. B cost {costs['B']/costs['A']:.2f} times as much. Source/referee overhead must remain visible: the primary CLI run totals ${analysis['accounting']['totals']['api_equivalent_usd']:.3f}; targeted secondary review adds ${auxiliary_cost:.3f}, for ${auxiliary_summary['combined_observed_model_api_equivalent_usd']:.3f} combined observed model equivalent. This is not observed billing or subscription-credit usage.

The primary metrics below preserve one consistent full-set assessment. Secondary model disagreement is reported separately rather than resolved by majority vote. A 100-case set, same-family references and no independent historian/human reference cannot establish a sub-1% error rate or a confident passing winner.

'''
    report = (out / 'report.md').read_text()
    report = lead + report.split('\n\n', 2)[2]
    report += '\n## Proposal comparison\n\nThe three generators received the same 886-record inventory plus 213 pending titles, at most 12 proposals, the same 1800-token answer target and 150-second timeout, with no web tools. The CLI could not enforce equal reasoning-token ceilings or equal realized spend. All three produced 12 text-judged useful hypotheses; historical accuracy and source-verified novelty remain unmeasured. No suggestion entered the 100-case set or dataset.\n\n'
    report += '| Model / effort | Hypotheses | Text useful | Generation API-equivalent USD | Seconds |\n| --- | ---: | ---: | ---: | ---: |\n'
    for p in proposals:
        report += f"| {p['model']} / {p['effort']} | {p['generated']} | {p['textUseful']} | {p['genCostUsd']:.5f} | {p['genSeconds']:.1f} |\n"
    report += '\nUse Sol medium for initial proposals on observed cost. This does not establish equal historical knowledge or rule out value from targeted Astra critique. [Proposal measurements](proposal-summary.json) separate text quality from source verification.\n\n## Reference sensitivity\n\n'
    report += 'The initial Astra-medium source reading and fresh Astra-low reference decision differed on one of the 100 cases. A targeted blinded Sol-medium reading of five cases differed on five claim labels. Those cases were selected for disputes, not randomly: no disagreement rate or historical error estimate follows. The consistent full-set primary assessment remains visible alongside the secondary reading; no label was promoted to truth by model agreement. Some disagreements concern the conservative corroboration rule rather than literal passage entailment. See [adjudication details](adjudication.json).\n\n## Interpretation and preserved work\n\n'
    report += '“Unsupported links” in the table counts explicit link-facet records. No such link claims were retained. Relational assertions embedded in achievement statements were still assessed: '
    report += ', '.join(f"Arm {a}: {q[a]['unsupported_relation_assertions']} unsupported relation assertion(s)" for a in ('A','B')) + '. Zero explicit links is not evidence of validated transmission precision.\n\n'
    report += 'The comparison reused 113 frozen saved source pages across 90 cases; ten retained source failures stayed missing. Historical retrieval/search was not repeated, so these costs do not estimate a full search campaign. All 92 original working files were privately archived and remain separate from implementation. The 213-candidate resume queue adopted 181 retained acquisition/extraction pairs, with 32 incomplete source sets explicitly deferred. No legacy review became current semantic admission. The committed baseline plus exact task changes is validated separately from the preserved live tree’s 33 unfinished-reference errors.\n\n'
    report += 'The source sample is predominantly English; translated/non-Latin normalization and global language coverage were not validated. One source-ID copying failure and three overlength quotations show sensitivity to the benchmark representation/bounds; these are distinguished from historical support failures. The production card compiler uses integer source references.\n\n'
    report += 'Public outputs contain structured answers, quotation hashes, scalar/claim labels and provenance; full source pages, prompts and raw conversations remain private. Exact model/effort, prompt/evidence versions, response IDs and parameters are retained in the private call artifacts. See [execution constraints](execution.json), [selected interim policy](decision.json), [auxiliary review accounting](auxiliary-usage.json) and [official OpenAI pricing](https://developers.openai.com/api/docs/pricing).\n'
    (out / 'report.md').write_text(report)
    return {'costs': costs, 'primary_cli_responses': analysis['accounting']['totals']['unique_responses'],
            'auxiliary_responses': len(seen), 'proposals': proposals}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, default=compare.DEFAULT_STATE)
    parser.add_argument('--out', type=Path, default=analysis_tool.DEFAULT_OUT)
    args = parser.parse_args()
    print(json.dumps(finalize(args.state, args.out)))
