#!/usr/bin/env python3
"""Verify delivered byte inventories without altering research or review artifacts."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def main():
    results = []
    for name in ['data/GENERATION_MANIFEST.json', 'FINAL_INTEGRITY.json']:
        manifest = json.loads((ROOT / name).read_text())
        missing, changed = [], []
        for relative, expected in manifest['files'].items():
            path = ROOT / relative
            if not path.is_file():
                missing.append(relative)
            elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                changed.append(relative)
        identifier_ok = True
        if 'generation_id' in manifest:
            identifier_ok = hashlib.sha256(json.dumps(manifest['files'], sort_keys=True).encode()).hexdigest() == manifest['generation_id']
        if 'inventory_id' in manifest:
            identifier_ok = hashlib.sha256(json.dumps(manifest['files'], sort_keys=True).encode()).hexdigest() == manifest['inventory_id']
        results.append(dict(manifest=name, files=len(manifest['files']), missing=missing,
                            changed=changed, identifier_matches=identifier_ok,
                            passed=not missing and not changed and identifier_ok))
    print(json.dumps(dict(passed=all(r['passed'] for r in results), results=results), indent=2))
    return 0 if all(r['passed'] for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
