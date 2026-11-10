#!/usr/bin/env python3
"""Render sanitized source-review measurements as a compact interactive view.

The generator reads already-observed public results. It never dispatches model
calls or infers unavailable judgments. All calculations in the browser are
presentation-only aggregations of these saved rows.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


TEMPLATE = Path(__file__).with_name('quality_sweep_view_template.html')
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS = ROOT / 'docs/reviews/2026-11-10-quality-sweep/view.json'
DEFAULT_OUT = Path('/Users/szymon/.codex/visualizations/2026/11/10/01a1c50d-701d-7572-8af7-c31c07f77ce0/quality-sweep.html')
GROUPS = {'fresh', 'regression', 'repeat'}
JUDGES = ('astra_medium', 'sol_high')


def _number(value, label):
    if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                              or not math.isfinite(value) or value < 0):
        raise ValueError(f'Invalid {label}: expected nonnegative finite number or null')


def checked(data):
    if not isinstance(data, dict) or not isinstance(data.get('cases'), list) or not data['cases']:
        raise ValueError('Expected a nonempty cases list')
    if not isinstance(data.get('limitations', []), list):
        raise ValueError('Limitations must be a list')
    identities = set()
    rows = []
    for position, row in enumerate(data['cases']):
        if not isinstance(row, dict):
            raise ValueError(f'Case row {position} is not an object')
        for key in ('id', 'title', 'group', 'variant', 'model', 'effort', 'decision'):
            if not isinstance(row.get(key), str) or not row[key]:
                raise ValueError(f'Case row {position} has invalid {key}')
        if row['group'] not in GROUPS:
            raise ValueError(f'Unknown result group: {row["group"]}')
        identity = (row['group'], row['id'], row['variant'])
        if identity in identities:
            raise ValueError(f'Duplicate result {identity}')
        identities.add(identity)
        mechanical = row.get('mechanical_pass')
        if mechanical is not None and type(mechanical) is not bool:
            raise ValueError(f'Invalid mechanical result {identity}')
        grade_excluded = row.get('grade_excluded', False)
        if type(grade_excluded) is not bool:
            raise ValueError(f'Invalid grade exclusion {identity}')
        _number(row.get('review_api_usd'), 'review cost')
        _number(row.get('review_seconds'), 'review duration')
        judges = row.get('judges')
        if not isinstance(judges, dict):
            raise ValueError(f'Judgments missing for {identity}')
        for label in JUDGES:
            judgment = judges.get(label)
            if judgment is None:
                continue
            if not isinstance(judgment, dict):
                raise ValueError(f'Invalid {label} judgment for {identity}')
            for flag in ('source_flagged_admission', 'false_reject', 'useful_record'):
                value = judgment.get(flag)
                if value is not None and type(value) is not bool:
                    raise ValueError(f'Invalid {label} {flag} for {identity}')
            reference = judgment.get('reference_decision')
            if reference is not None and (not isinstance(reference, str) or not reference):
                raise ValueError(f'Invalid {label} reference decision for {identity}')
            verdicts = judgment.get('claim_verdicts')
            if verdicts is not None:
                if not isinstance(verdicts, list):
                    raise ValueError(f'Invalid {label} claim verdicts for {identity}')
                if verdicts and isinstance(verdicts[0], dict):
                    if (any(not isinstance(v, dict) or type(v.get('index')) is not int or
                            v.get('verdict') not in ('supported', 'unsupported', 'unresolved') for v in verdicts)
                            or sorted(v['index'] for v in verdicts) != list(range(len(verdicts)))):
                        raise ValueError(f'Incomplete {label} claim indices for {identity}')
                elif any(v not in ('supported', 'unsupported', 'unresolved') for v in verdicts):
                    raise ValueError(f'Invalid {label} claim verdicts for {identity}')
        # Whitelist fields. Original quotations and contextual evidence never
        # enter the visualization even if present in the upstream result file.
        rows.append({key: row[key] for key in ('id', 'title', 'group', 'variant', 'model', 'effort', 'decision')}
                    | {'mechanical_pass': mechanical,
                       'grade_excluded': grade_excluded,
                       'review_api_usd': row.get('review_api_usd'),
                       'review_seconds': row.get('review_seconds'),
                       'judges': {label: (None if judges.get(label) is None else {
                           **{key: judges[label].get(key) for key in
                              ('source_flagged_admission', 'false_reject', 'useful_record', 'reference_decision')},
                           'claim_verdicts': (None if judges[label].get('claim_verdicts') is None else
                                              [v['verdict'] for v in sorted(judges[label]['claim_verdicts'],key=lambda v:v['index'])]
                                              if judges[label]['claim_verdicts'] and isinstance(judges[label]['claim_verdicts'][0],dict)
                                              else judges[label]['claim_verdicts'])})
                                  for label in JUDGES}})
    return {'cases': rows, 'limitations': [str(x) for x in data.get('limitations', [])],
            'accounting': {key: data.get('accounting', {}).get(key) for key in
                           ('new_calls', 'api_equivalent_usd', 'wall_seconds')} if isinstance(data.get('accounting', {}), dict) else {}}


def render(results=DEFAULT_RESULTS, out=DEFAULT_OUT):
    data = checked(json.loads(Path(results).read_text()))
    template = TEMPLATE.read_text()
    if template.count('__SWEEP_DATA__') != 1:
        raise ValueError('Template needs exactly one data slot')
    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    payload = payload.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    markup = template.replace('__SWEEP_DATA__', payload)
    if len(markup.encode()) >= 1_000_000:
        raise ValueError('Visualization exceeds 1 MB')
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markup)
    return {'path': str(out), 'case_workflow_rows': len(data['cases']),
            'groups': sorted({row['group'] for row in data['cases']}),
            'variants': sorted({row['variant'] for row in data['cases']})}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, default=DEFAULT_RESULTS)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(json.dumps(render(args.results, args.out)))
