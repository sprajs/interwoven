"""Deterministic, independently cacheable browser artifacts (no research decisions)."""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import tempfile
from pathlib import Path

FORMAT = 1
CORE_FIELDS = ('id', 'name', 'summary', 'aliases', 'kind', 'domain', 'fields', 'tier',
               'origin', 'concept', 'societies', 't', 'date', 'at', 'filled')
EDGE_FIELDS = ('from', 'to', 'type', 'layer', 'status')


def encoded(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode()


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def atomic_write(path: Path, raw: bytes) -> None:
    """Readers see either complete version. Unchanged files keep their inode and mtime."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() == raw:
        return
    fd, name = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(raw)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def evidence_ids(value: object) -> set[str]:
    """Include citations anywhere, including new facets, measures and contributions."""
    found: set[str] = set()
    if isinstance(value, dict):
        if isinstance(value.get('source'), str):
            found.add(value['source'])
        for child in value.values():
            found.update(evidence_ids(child))
    elif isinstance(value, list):
        for child in value:
            found.update(evidence_ids(child))
    return found


def publish(bundle: dict, out: Path) -> dict:
    def asset(kind: str, value: object) -> str:
        raw = encoded(value)
        name = f'{kind}/{digest(raw)[:24]}.json'
        atomic_write(out / name, raw)
        atomic_write(out / (name + '.gz'), gzip.compress(raw, compresslevel=9, mtime=0))
        return name

    touching: dict[str, list] = {}
    for link in bundle['links']:
        for key in {link['from'], link['to']}:
            touching.setdefault(key, []).append(link)
    details = {}
    for record in bundle['discoveries']:
        links = touching.get(record['id'], [])
        sources = {k: bundle['sources'][k] for k in sorted(evidence_ids([record, links]) | set(record.get('source_ids', []))) if k in bundle['sources']}
        # Full registers are small relative to evidence, but localise them to this detail too.
        registers = {}
        for register, field in [('people', 'person'), ('organizations', 'organization'), ('places', 'place')]:
            ids = {item[field] for item in record.get(register, [])}
            if register == 'places' and record.get('at'):
                ids.add(record['at']['place'])
                parent = bundle['places'].get(record['at']['place'], {}).get('within')
                if parent:
                    ids.add(parent)
            registers[register] = {k: bundle[register][k] for k in sorted(ids) if k in bundle[register]}
        details[record['id']] = asset('details', {'entry': record, 'links': links, 'sources': sources, **registers})

    core = {k: bundle[k] for k in ('counts', 'facets', 'vocab', 'link_layers', 'taxonomy')}
    core['discoveries'] = []
    for record in bundle['discoveries']:
        item = {k: record[k] for k in CORE_FIELDS if k in record}
        item['research'] = {k: record['research'][k] for k in ('status', 'basis')}
        for register, field in [('people', 'person'), ('places', 'place'), ('organizations', 'organization')]:
            if register in record:
                item[register] = [{field: entry[field]} for entry in record[register]]
        core['discoveries'].append(item)
    core['links'] = [{k: link[k] for k in EDGE_FIELDS} for link in bundle['links']]
    core['places'] = {k: {field: value for field, value in p.items() if field in ('id', 'name', 'kind', 'lat', 'lon', 'country', 'region', 'within')} for k, p in bundle['places'].items()}
    for register in ('people', 'organizations', 'societies', 'concepts'):
        core[register] = {k: {'id': k, 'name': value['name']} for k, value in bundle[register].items()}
    pop = bundle['population']
    core['world_person_years'] = pop['person_years']['world'] if pop else None
    core['details'] = details
    core['population_file'] = asset('population', pop)
    core['format'] = FORMAT
    core_file = asset('core', core)
    manifest = {'format': FORMAT, 'version': core_file.split('/')[1].split('.')[0], 'core': core_file}
    # Publish the pointer last; previous hashed artifacts remain available to open tabs.
    atomic_write(out / 'manifest.json', encoded(manifest))
    return manifest
