#!/usr/bin/env python3
"""Import a private preservation manifest into the existing queue, without dispatch.

Only retained acquisition/extraction successes are adopted. A fresh named dataset
screen, mechanical checks and semantic review remain mandatory. No web/model/Git
write occurs. Missing source artifacts remain pending with their manifest reason.
"""
import argparse
import hashlib
import json
from pathlib import Path
from workflow import Queue, committed_snapshot


def restore(manifest_path, queue_path, repo):
    manifest_path = Path(manifest_path).resolve()
    root = manifest_path.parent
    manifest = json.loads(manifest_path.read_text())
    queue = Queue(queue_path)
    snapshot = committed_snapshot(repo)
    results = []
    for row in manifest['candidates']:
        evidence = row.get('source_snapshots', [])
        hashes = [s['sha256'] for s in evidence if s.get('sha256')]
        versions = {'acquire': {'format': 'retained-source-manifest-v1', 'hashes': sorted(hashes)},
                    'extract': {'format': 'legacy-retained-card-v1', 'model': 'not_attributed_by_importer',
                                'prompt': 'retained-original-artifact', 'evidence': sorted(hashes)}}
        key = queue.enqueue({'name': row['retained_title'], 'retained_candidate_id': row['candidate_id']},
                            snapshot, versions, max_attempts=2)
        result = {'candidate_id': row['candidate_id'], 'queue_candidate_id': key, 'adopted': [],
                  'next_required': ['screening', 'mechanical', 'review'], 'snapshot': snapshot}
        available = bool(evidence)
        for source in evidence:
            path = (root / (source.get('path') or 'missing')).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                available = False
                continue
            if hashlib.sha256(path.read_bytes()).hexdigest() != source.get('sha256'):
                raise ValueError('Retained source changed: ' + str(path))
        if available:
            acquired = root / 'resume-acquisition' / (row['candidate_id'] + '.json')
            acquired.parent.mkdir(exist_ok=True)
            acquired.write_text(json.dumps(evidence, sort_keys=True) + '\n')
            provenance = {'origin': 'Private archived retained research; no new retrieval',
                          'evidence_hashes': hashes,
                          'artifact_sha256': hashlib.sha256(acquired.read_bytes()).hexdigest()}
            queue.adopt_artifact(key, 'acquire', acquired, provenance, versions['acquire'])
            result['adopted'].append('acquire')
            extraction = next((a for a in row['artifacts'] if a['stage'] == 'extraction'), None)
            if extraction:
                path = (root / extraction['path']).resolve()
                if not path.is_relative_to(root):
                    raise ValueError('Retained extraction escapes preservation root')
                provenance = dict(provenance, artifact_sha256=extraction['sha256'],
                                  card_index=extraction['card_index'],
                                  note='Legacy extraction only; no semantic admission imported')
                queue.adopt_artifact(key, 'extract', path, provenance, versions['extract'])
                result['adopted'].append('extract')
        else:
            result['reason'] = 'No complete preserved source set; retain extraction artifact but defer adoption'
            queue.defer_pending(key, 'acquire', result['reason'])
        results.append(result)
    target = root / 'resume-queue-manifest.json'
    target.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--queue', type=Path, required=True)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    rows = restore(args.manifest, args.queue, args.repo)
    print(json.dumps({'candidates': len(rows), 'retained_acquisitions': sum('acquire' in r['adopted'] for r in rows),
                      'retained_extractions': sum('extract' in r['adopted'] for r in rows), 'dispatched_jobs': 0}))
