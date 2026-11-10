#!/usr/bin/env python3
"""Render a compact, local, interactive view of observed workflow pilot results.

Input is the sanitized pilot-results.json file. This script never runs model calls
or infers missing source judgments, costs, or token usage.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


TEMPLATE = Path(__file__).with_name('pilot_viewer_template.html')
DEFAULT_OUT = Path('/Users/szymon/.codex/visualizations/2026/11/10/01a1c50d-701d-7572-8af7-c31c07f77ce0/workflow-pilot.html')
REQUIRED = {'id', 'stage', 'variant', 'decision'}


def checked(data: object) -> dict:
    if not isinstance(data, dict) or not isinstance(data.get('cases'), list):
        raise ValueError('Expected an object with a cases list')
    for index, row in enumerate(data['cases']):
        if not isinstance(row, dict) or not REQUIRED <= row.keys():
            raise ValueError(f'Case result {index} is missing {sorted(REQUIRED)}')
        for key in REQUIRED:
            if not isinstance(row[key], str) or not row[key].strip():
                raise ValueError(f'Case result {index}: {key} must be a nonempty string')
        for key in ('api_equivalent_usd', 'latency_seconds'):
            value = row.get(key)
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0):
                raise ValueError(f'Case result {index}: invalid {key}')
        value = row.get('source_flags')
        if value is not None and (not isinstance(value, list) or not all(isinstance(x, str) for x in value)):
            raise ValueError(f'Case result {index}: invalid source_flags')
        value = row.get('supported_claims')
        if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
            raise ValueError(f'Case result {index}: invalid supported_claims')
        for key in ('mechanical_pass', 'useful_reviewed_record', 'false_reject'):
            value = row.get(key)
            if value is not None and not isinstance(value, bool):
                raise ValueError(f'Case result {index}: invalid {key}')
    if len({(r['id'], r['stage'], r['variant']) for r in data['cases']}) != len(data['cases']):
        raise ValueError('Duplicate case/stage/variant result')
    if not data['cases']:
        raise ValueError('No observed case results')
    return data


def render(results: Path, out: Path) -> dict:
    data = checked(json.loads(results.read_text()))
    template = TEMPLATE.read_text()
    if template.count('__PILOT_DATA__') != 1:
        raise ValueError('Pilot template must have exactly one data slot')
    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False).replace('<', '\\u003c')
    html = template.replace('__PILOT_DATA__', payload)
    if len(html.encode()) >= 1_000_000:
        raise ValueError('Inline pilot view exceeds 1 MB')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    return {'path': str(out), 'case_workflow_results': len(data['cases']),
            'stages': sorted({r['stage'] for r in data['cases']}),
            'variants': sorted({r['variant'] for r in data['cases']})}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(json.dumps(render(args.results, args.out)))


if __name__ == '__main__':
    main()
