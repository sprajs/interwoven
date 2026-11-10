#!/usr/bin/env python3
"""Decode a locally saved Eurostat JSON-stat selection without changing its source values."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

DIMENSIONS = {
    'isoc_eb_ai': ('freq', 'size_emp', 'nace_r2', 'indic_is', 'unit', 'geo', 'time'),
    'isoc_ai_iaiu': ('freq', 'ind_type', 'indic_is', 'unit', 'geo', 'time'),
}


def extract(path: Path, dataset: str, expected_hash: str) -> list[dict]:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_hash:
        raise ValueError('input SHA-256 mismatch')
    source = json.loads(raw)
    if dataset not in DIMENSIONS or source.get('extension', {}).get('id', '').lower() != dataset:
        raise ValueError('unexpected dataset')
    ids, sizes = source.get('id'), source.get('size')
    if ids != list(DIMENSIONS[dataset]) or not isinstance(sizes, list) or len(sizes) != len(ids):
        raise ValueError('unexpected dimension structure')
    categories = []
    for name, size in zip(ids, sizes):
        if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            raise ValueError('invalid dimension size')
        index = source['dimension'][name]['category']['index']
        if (not isinstance(index, dict)
                or any(isinstance(n, bool) or not isinstance(n, int) for n in index.values())
                or sorted(index.values()) != list(range(size))):
            raise ValueError('invalid category indices')
        categories.append([code for code, _ in sorted(index.items(), key=lambda item: item[1])])
    values = source.get('value', {})
    statuses = source.get('status', {})
    if not isinstance(values, dict) or not isinstance(statuses, dict):
        raise ValueError('expected sparse JSON-stat value and status maps')
    total = math.prod(sizes)
    for key in set(values) | set(statuses):
        if not isinstance(key, str) or not key.isascii() or not key.isdigit() or str(int(key)) != key or int(key) >= total:
            raise ValueError('invalid observation index')
    result = []
    for index, codes in enumerate(itertools.product(*categories)):
        value = values.get(str(index))
        flag = statuses.get(str(index))
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 100):
            raise ValueError('invalid percentage')
        if flag is not None and (not isinstance(flag, str) or not flag):
            raise ValueError('invalid status flag')
        result.append({'dimensions': dict(zip(ids, codes)), 'value': value, 'status': 'missing' if value is None else 'reported', 'flag': flag, 'index': index})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--dataset', required=True, choices=sorted(DIMENSIONS))
    parser.add_argument('--sha256', required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(extract(args.input, args.dataset, args.sha256), indent=2, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f'{exc}\n')


if __name__ == '__main__':
    main()
