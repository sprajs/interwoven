#!/usr/bin/env python3
"""Freeze a diverse 24-new/16-regression source fixture without model or network calls."""
from __future__ import annotations
import argparse
import collections
import hashlib
import io
import json
import re
import subprocess
import tarfile
from pathlib import Path

import prepare_comparison as previous

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT.parent / 'big_idea-research-state/workflow-20261110'
RETAINED = STATE / 'retained/expand'
DEFAULT_PRIVATE = STATE / 'quality-sweep'
DEFAULT_PUBLIC = ROOT / 'docs/reviews/2026-11-10-quality-sweep'
OLD = ROOT / 'docs/reviews/2026-11-10-workflow-comparison/cases.json'
PILOT = ROOT / 'docs/reviews/2026-11-10-workflow-pilot/registration.json'
COMMIT = '42d6e8829d1ed4d320468613137771cd67c2818f'
SEED = 'quality-sweep-2026-11-10-v1'


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode()


def frozen_records():
    raw = subprocess.check_output(['git', 'archive', COMMIT, '--', 'data/discoveries'], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
        return [json.load(tar.extractfile(m)) for m in tar.getmembers() if m.isfile() and m.name.endswith('.json')]


def lead_card(manifest_row):
    artifact = next(a for a in manifest_row['artifacts'] if a['stage'] == 'extraction')
    card_path = STATE / artifact['path']
    raw = card_path.read_bytes()
    if sha(raw) != artifact['sha256']:
        raise ValueError('Retained card hash mismatch: ' + str(card_path))
    cards = json.loads(raw)['cards']
    card = cards[artifact['card_index']]
    match = re.search(r'batch-(\d+)-cards\.json$', card_path.name)
    if not match:
        raise ValueError('Unexpected retained batch path')
    input_path = card_path.with_name('batch-' + match.group(1) + '-input.json')
    lead = next(l for l in json.loads(input_path.read_text())['leads'] if l['title'] == manifest_row['retained_title'])
    if card['lead'] != lead['title'] or manifest_row['candidate_id'] != 'candidate-' + sha(lead['title'])[:16]:
        raise ValueError('Retained lead/card identity mismatch')
    return lead, card, artifact, card_path


def source_candidates(manifest_row):
    return [s for s in manifest_row['source_snapshots'] if s.get('sha256') and (STATE / s['path']).is_file()]


def select_new(rows, old_ids):
    groups = collections.defaultdict(list)
    for row in rows:
        if row['candidate_id'] in old_ids or not source_candidates(row):
            continue
        lead, _, _, _ = lead_card(row)
        group = lead.get('field', '').split('.')[0] or 'unspecified'
        groups[group].append(row)
    for group, members in groups.items():
        members.sort(key=lambda r: sha(SEED + ':fresh:' + r['candidate_id']))
    picked = []
    while len(picked) < 24 and any(groups.values()):
        for group in sorted(groups):
            if groups[group] and len(picked) < 24:
                picked.append((group, groups[group].pop(0)))
    if len(picked) != 24:
        raise ValueError(f'Only {len(picked)} source-backed new candidates')
    return picked


def select_regression(old_cases, pilot):
    by_id = {c['id']: c for c in old_cases}
    diagnostic = pilot['diagnostic_ids']
    exclude = set(diagnostic + pilot['confirmation_ids'])
    groups = collections.defaultdict(list)
    for case in old_cases:
        if case['id'] not in exclude:
            groups[case['stratum']].append(case)
    for group in groups:
        groups[group].sort(key=lambda c: sha(SEED + ':regression:' + c['id']))
    extra = []
    while len(extra) < 8:
        for group in sorted(groups):
            if groups[group] and len(extra) < 8:
                extra.append(groups[group].pop(0))
    cases = [by_id[cid] for cid in diagnostic] + extra
    if len(cases) != 16 or len({c['id'] for c in cases}) != 16:
        raise ValueError('Bad regression selection')
    return cases


def screen(card, records):
    exact = [r['id'] for r in records if r.get('name') == card.get('name')]
    related = [r['id'] for r in records if card.get('concept') and r.get('concept') == card['concept'] and r['id'] not in exact]
    hits = exact + related
    matches = [{'id': key, 'basis': 'exact_retained_card_name' if key in exact else 'same_concept_only'} for key in hits]
    return {'decision': 'review_existing_scope' if hits else 'research',
            'matches': matches,
            'rationale': 'Mechanical current-snapshot scope screen; name/concept similarity alone does not prove historical duplication.',
            'match_context': [previous.match_context(r) for r in records if r['id'] in hits],
            'matched_records': [{k: r.get(k) for k in ('id', 'name', 'description', 'concept', 'origin', 'societies', 'places', 'events')} for r in records if r['id'] in hits]}


def save_source(raw, source_hash, destination):
    if sha(raw) != source_hash:
        raise ValueError('Saved original source bytes changed')
    path = destination / (source_hash + '.txt')
    if path.exists() and sha(path.read_bytes()) != source_hash:
        raise ValueError('Content-addressed evidence collision')
    if not path.exists():
        path.write_bytes(raw)
    return path


def new_case(group, row, records, evidence_dir, word_budget):
    lead, card, artifact, card_path = lead_card(row)
    snapshots = {s['url']: s for s in row['source_snapshots']}
    cid = row['candidate_id']
    evidence = []
    for i, source in enumerate(card.get('sources', [])):
        url = source['url']
        snap = snapshots.get(url)
        raw = (STATE / snap['path']).read_bytes() if snap and snap.get('sha256') and (STATE / snap['path']).is_file() else b''
        if raw:
            private_path = save_source(raw, snap['sha256'], evidence_dir)
            full = raw.decode('utf-8', 'replace')
        else:
            private_path, full = None, ''
        events = [e for e in card.get('events', []) if e.get('source') == i and e.get('quote')]
        quote = events[0]['quote'] if events else ''
        pos, status = previous.quote_offset(full, quote)
        start = max(0, pos - 800) if pos >= 0 else 0
        quote_limit = max(0, 200 - word_budget[url])
        text = ' '.join(quote.split()[:min(80, quote_limit)])
        word_budget[url] += len(text.split())
        evidence.append({'id': f'{cid}-source-{i+1}', 'url': url, 'title': source.get('title'),
                         'sha256': sha(raw) if raw else None, 'text': text, 'text_sha256': sha(text),
                         'locator': events[0].get('locator', 'Retained quotation') if events else 'Saved source text',
                         'context': {'private_path': str(private_path) if private_path else None,
                                     'start': start, 'end': min(len(full), start + 3200), 'encoding': 'utf-8',
                                     'navigation_anchor_offset': pos},
                         'access_status': 'saved_page' if raw else 'missing_saved_original',
                         'quotation_status': status,
                         'retained_card_locator': f'{card_path.name}#/cards/{artifact["card_index"]}/sources/{i}',
                         'original_context': full[start:start + 3200] if raw else ''})
    case = {'id': cid, 'stratum': 'fresh_' + group,
            'split': 'held_out', 'candidate': {'name': lead['title'], 'community': lead.get('where'),
            'question': lead.get('verify'), 'hypothesis': {k: lead[k] for k in ('concept','kind','field','region','date','year','origin') if k in lead},
            'hypothesis_status': 'Unverified retained lead, not reference truth'},
            'dataset_snapshot': COMMIT, 'screen': screen(card, records), 'evidence': evidence,
            'source_access_status': 'saved_evidence' if evidence and all(s['sha256'] for s in evidence) else 'missing_or_incomplete',
            'provenance': {'retained_file': str(card_path), 'retained_file_sha256': sha(card_path.read_bytes()),
                           'card_index': artifact['card_index'], 'resume_manifest_candidate_id': cid},
            'fixture_group': 'fresh'}
    return case


def old_case(case, records, evidence_dir, word_budget):
    result = json.loads(json.dumps(case))
    result['dataset_snapshot'] = COMMIT
    result['split'] = 'held_out'
    result['fixture_group'] = 'regression'
    artifact_path = Path(case['provenance']['retained_file'])
    if not artifact_path.is_file() or sha(artifact_path.read_bytes()) != case['provenance']['retained_file_sha256']:
        raise ValueError('Old retained card changed: ' + str(artifact_path))
    card = json.loads(artifact_path.read_text())['cards'][case['provenance']['card_index']]
    result['screen'] = screen(card, records)
    for source in result['evidence']:
        context = source['context']
        if source.get('sha256'):
            raw = Path(context['private_path']).read_bytes()
            path = save_source(raw, source['sha256'], evidence_dir)
            context['private_path'] = str(path)
            text = raw.decode('utf-8', 'replace')
            start, end = context['start'], context['end']
            if not 0 <= start <= end <= len(text):
                raise ValueError('Old source window invalid')
            source['original_context'] = text[start:end]
        else:
            source['original_context'] = ''
        quote_limit = max(0, 200 - word_budget[source['url']])
        source['text'] = ' '.join(source.get('text', '').split()[:quote_limit])
        source['text_sha256'] = sha(source['text'])
        word_budget[source['url']] += len(source['text'].split())
    return result


def public_case(case):
    copy = json.loads(json.dumps(case))
    for source in copy['evidence']:
        source.pop('original_context', None)
        source['context'].pop('private_path', None)
    copy['screen'].pop('matched_records', None)
    return copy


def prepare(private=DEFAULT_PRIVATE, public=DEFAULT_PUBLIC):
    private, public = Path(private), Path(public)
    private.mkdir(parents=True, exist_ok=True); public.mkdir(parents=True, exist_ok=True)
    evidence_dir = private / 'evidence'; evidence_dir.mkdir(exist_ok=True)
    old_cases = json.loads(OLD.read_text())['cases']
    pilot = json.loads(PILOT.read_text())
    manifest_path = STATE / 'resume-manifest.json'
    manifest = json.loads(manifest_path.read_text())['candidates']
    records = frozen_records()
    fresh = select_new(manifest, {c['id'] for c in old_cases})
    regression = select_regression(old_cases, pilot)
    words = collections.Counter()
    cases = [new_case(group, row, records, evidence_dir, words) for group, row in fresh]
    cases += [old_case(row, records, evidence_dir, words) for row in regression]
    if len(cases) != 40 or len({c['id'] for c in cases}) != 40 or sum(c['fixture_group'] == 'fresh' for c in cases) != 24:
        raise ValueError('Invalid fixture counts')
    if any(not any(s['sha256'] for s in c['evidence']) for c in cases if c['fixture_group'] == 'fresh'):
        raise ValueError('Fresh case lacks original source')
    cases.sort(key=lambda c: c['id'])
    private_payload = {'schema_version': 1, 'cases': cases}
    public_payload = {'schema_version': 1, 'cases': [public_case(c) for c in cases]}
    private_bytes, public_bytes = encoded(private_payload), encoded(public_payload)
    registration = {'schema_version': 1, 'registered_before_model_calls': True,
        'selection_seed': SEED, 'dataset_snapshot': COMMIT,
        'resume_manifest_sha256': sha(manifest_path.read_bytes()),
        'prior_100_cases_sha256': sha(OLD.read_bytes()),
        'pilot_registration_sha256': sha(PILOT.read_bytes()),
        'private_case_sha256': sha(private_bytes), 'public_case_sha256': sha(public_bytes),
        'fresh_candidate_ids': sorted(c['id'] for c in cases if c['fixture_group'] == 'fresh'),
        'regression_candidate_ids': sorted(c['id'] for c in cases if c['fixture_group'] == 'regression'),
        'selection': 'Round-robin over current retained lead field families, deterministic hash within family; 8 pilot diagnostic cases plus 8 hash-selected old controls excluding all pilot cases.',
        'strata': dict(collections.Counter(c['stratum'] for c in cases)),
        'source_policy': 'Saved original page bytes hash-verified and copied to private content-addressed store. Model payload uses bounded 3200-character windows. Public excerpts at most 200 words per URL across fixture. Missing source windows remain explicit.',
        'freshness_limit': 'Fresh candidate IDs absent from prior 100-case benchmark; retained leads and source pages are historical research already collected, not new web retrieval. Regression cases appeared in previous benchmark.'}
    registration_bytes = encoded(registration)
    for path, data in [(private/'cases.json', private_bytes), (private/'registration.json', registration_bytes),
                       (public/'cases.json', public_bytes), (public/'registration.json', registration_bytes)]:
        if path.exists() and path.read_bytes() != data:
            raise ValueError('Frozen fixture mismatch: ' + str(path))
        path.write_bytes(data)
    return registration


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private', type=Path, default=DEFAULT_PRIVATE)
    parser.add_argument('--public', type=Path, default=DEFAULT_PUBLIC)
    args = parser.parse_args()
    result = prepare(args.private, args.public)
    print(json.dumps({'fresh': len(result['fresh_candidate_ids']), 'regression': len(result['regression_candidate_ids']),
                      'source_pages': len(list((args.private/'evidence').glob('*.txt'))),
                      'private_case_sha256': result['private_case_sha256'], 'public_case_sha256': result['public_case_sha256']}))

if __name__ == '__main__': main()
