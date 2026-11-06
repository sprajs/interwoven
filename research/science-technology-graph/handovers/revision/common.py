"""Revision helpers: preserve exact changed propositions and fresh scoped decisions."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from validate import proposition_sha256

def load():
    return {name: [json.loads(x) for x in (ROOT / 'data' / (name + '.jsonl')).read_text().splitlines()]
            for name in ('nodes', 'events', 'relationships', 'sources')}

def index(rows):
    return {x['id']: x for x in rows}

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def finish(stage, before, records, decisions, note):
    """Each changed proposition needs an explicit review scope; never auto-accept."""
    path = f'reviews/revision-{stage}.json'
    ledger = {'schema_version': 1, 'scope': note,
              'reviewer': 'Codex editorial review; not an independent historian review',
              'hash_method': 'SHA256 sorted compact UTF8 JSON, excluding top-level review',
              'records': [], 'changes': [], 'removals': []}
    for plural, rows in records.items():
        old = index(before[plural]); new = index(rows)
        for rid in old.keys() - new.keys():
            assert rid in decisions, ('Missing removal decision', rid)
            ledger['removals'].append({'record': old[rid], 'decision': decisions[rid]})
        for record in rows:
            rid = record['id']
            if old.get(rid) == record:
                continue
            assert rid in decisions, ('Missing changed-record decision', rid)
            ledger['changes'].append({'id': rid, 'type': plural, 'before': old.get(rid, {}),
                                      'decision': decisions[rid]})
            if plural != 'sources':
                prior = record.get('review', {})
                record['review'] = {'historical_claim': prior.get('historical_claim', 'accepted'),
                                    'lifecycle_classification': prior.get('lifecycle_classification', 'needs_review'),
                                    'records': [path]}
                ledger['records'].append({'id': rid, 'type': {'nodes':'node','events':'event','relationships':'relationship'}[plural],
                    'historical_claim': record['review']['historical_claim'],
                    'lifecycle_classification': record['review']['lifecycle_classification'],
                    'proposition_sha256': proposition_sha256(record), 'decision': decisions[rid]})
    write_json(ROOT / path, ledger)
    for name, rows in records.items():
        if rows != before[name]:
            write_records(name, rows)
    print(stage, len(ledger['changes']), 'changed/added;', len(ledger['removals']), 'removed')

def evidence(sid, locator, supports):
    return {'source_id': sid, 'locator': locator, 'supports': supports}

def link(rid, source, target, relation, statement, ev, temporal, uncertainty):
    return {'schema_version':1, 'id':rid, 'from':source, 'to':target, 'relation':relation,
            'statement':statement, 'scope':'Only the identified configurations and source-described contribution.',
            'evidence':ev, 'confidence':'high', 'influence':'not_assessed',
            'alternatives':'No unique historical route or universal necessity asserted.', 'uncertainty':uncertainty,
            'temporal_note':temporal, 'review':{'historical_claim':'accepted','lifecycle_classification':'needs_review'},
            'provenance':{'method':'source-evidence','source_ids':list(dict.fromkeys(e['source_id'] for e in ev)),
                          'note':'Fresh scoped source check recorded in the revision ledger.'}}


def write_records(name, rows):
    path = ROOT / 'data' / (name + '.jsonl')
    relative = path.relative_to(ROOT.parents[1])
    original = subprocess.check_output(['git','show','HEAD:'+str(relative)], cwd=ROOT, text=True).splitlines()
    saved = {json.loads(line)['id']: (json.loads(line), line) for line in original}
    path.write_text(''.join((saved[r['id']][1] if r['id'] in saved and saved[r['id']][0] == r else json.dumps(r)) + '\n' for r in rows))
