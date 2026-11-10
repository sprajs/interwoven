"""Durable queue contract tests: real SQLite races and isolated Git snapshots."""
import concurrent.futures
import json
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cards'))
from workflow import Queue, STAGES, candidate_id, committed_snapshot, digest, stage_integration


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.email', 'tests@example.invalid')
        self.git('config', 'user.name', 'Tests')
        self.write('data/discoveries/a/alpha.json', json.dumps({'id': 'alpha', 'name': 'Paper printing', 'concept': 'printing', 'societies': ['community-a']}))
        self.write('tools/validate.py', "from pathlib import Path\nassert all('invalid' not in p.read_text() for p in Path('data').rglob('*.json'))\n")
        self.write('package.json', json.dumps({'scripts': {'test': 'node -e "process.exit(0)"'}}))
        self.commit()
        self.snapshot = committed_snapshot(self.repo)
        self.db = self.root / 'queue.sqlite'
        self.queue = Queue(self.db)
        self.candidate = {'name': 'Water lifting screw', 'community': 'community-b', 'era': 'ancient'}
        self.key = self.queue.enqueue(self.candidate, self.snapshot)

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.STDOUT)

    def write(self, name, content):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'Fixture')

    def screen(self, key=None):
        lease = self.queue.claim('screener', 'screening')
        self.assertIsNotNone(lease)
        return self.queue.screen(lease, self.repo)

    def complete_until(self, stage):
        self.screen()
        for target in STAGES[1:STAGES.index(stage) + 1]:
            lease = self.queue.claim('worker', target)
            self.assertIsNotNone(lease)
            self.queue.complete(lease, target.encode())

    def test_identity_and_duplicate_enqueue_survive_restart(self):
        self.assertEqual(candidate_id(self.candidate), candidate_id(dict(reversed(list(self.candidate.items())))))
        self.assertNotEqual(self.key, candidate_id({**self.candidate, 'community': 'other'}))
        self.assertEqual(Queue(self.db).enqueue(self.candidate, self.snapshot), self.key)
        self.assertEqual(len(self.queue.jobs()), 6)
        self.complete_until('extract')
        self.assertEqual(Queue(self.db).claim('restarted')['stage'], 'mechanical')

    def test_explicit_id_survives_correction_and_invalidates_old_work(self):
        self.screen()
        candidate = dict(self.candidate, id='retained-lead-001', question='Initial scope')
        key = self.queue.enqueue(candidate, self.snapshot)
        self.assertEqual(key, 'retained-lead-001')
        old = self.queue.claim('first', 'screening')
        changed = dict(candidate, question='Corrected scope')
        self.assertEqual(self.queue.enqueue(changed, self.snapshot), key)
        new_jobs = self.queue.jobs(key)
        self.assertTrue(all(j['status'] == 'pending' for j in new_jobs))
        self.assertIn('candidate_sha256', json.loads(new_jobs[0]['inputs']))
        with self.assertRaisesRegex(ValueError, 'stale'):
            self.queue.fail(old, 'Late result from old scope')
        with self.assertRaises(ValueError):
            candidate_id(dict(candidate, id='../escape'))

    def test_imported_missing_evidence_defers_without_invented_attempt(self):
        self.queue.defer_pending(self.key, 'acquire', 'Retained source missing')
        acquire = next(j for j in self.queue.jobs(self.key) if j['stage'] == 'acquire')
        self.assertEqual((acquire['status'], acquire['attempts']), ('deferred', 0))
        self.screen()
        self.assertIsNone(self.queue.claim('retriever', 'acquire'))
        self.queue.resume(self.key, 'acquire', 'Source access restored')
        lease = self.queue.claim('retriever', 'acquire')
        with self.assertRaisesRegex(ValueError, 'leased'):
            self.queue.defer_pending(self.key, 'acquire', 'Would steal ownership')
        self.queue.complete(lease, b'saved evidence')
        with self.assertRaisesRegex(ValueError, 'successful'):
            self.queue.defer_pending(self.key, 'acquire', 'Would erase success')

    def test_atomic_concurrent_claim_and_stale_owner(self):
        def claim(n):
            return Queue(self.db).claim(str(n), now=10, ttl=5)
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            leases = [x for x in pool.map(claim, range(8)) if x]
        self.assertEqual(len(leases), 1)
        replacement = self.queue.claim('replacement', now=16, ttl=5)
        self.assertEqual(replacement['attempts'], 2)
        with self.assertRaisesRegex(ValueError, 'stale'):
            self.queue.fail(leases[0], 'late owner', now=17)
        self.queue.fail(replacement, 'transient', now=17)
        last = self.queue.claim('last', now=18, ttl=5)
        self.queue.fail(last, 'exhausted', now=19)
        self.assertIsNone(self.queue.claim('fourth', now=20))
        self.assertEqual(self.queue.jobs()[0]['reason'], 'exhausted')

    def test_screening_mandatory_and_fuzzy_requires_review(self):
        self.assertIsNone(self.queue.claim('retriever', 'acquire'))
        lease = self.queue.claim('screen', 'screening')
        with self.assertRaisesRegex(ValueError, 'explicit'):
            self.queue.complete(lease, b'pretend screening')
        self.queue.screen(lease, self.repo)
        self.assertIsNotNone(self.queue.claim('retriever', 'acquire'))
        other = self.queue.enqueue({'name': 'Paper printin', 'community': 'community-b'}, self.snapshot)
        lease = self.queue.claim('screen', 'screening')
        decision = self.queue.screen(lease, self.repo)
        self.assertEqual(decision['decision'], 'defer')
        self.assertEqual(decision['matches'][0]['id'], 'alpha')
        self.assertEqual(decision['snapshot'], self.snapshot)
        self.assertEqual(self.queue.jobs(other)[0]['status'], 'deferred')
        self.assertIsNone(self.queue.claim('retriever', 'acquire'))

    def test_explicit_distinct_community_preserved(self):
        self.screen()
        key = self.queue.enqueue({'name': 'Paper printing', 'community': 'community-b'}, self.snapshot)
        lease = self.queue.claim('reviewer', 'screening')
        decision = self.queue.screen(lease, self.repo, decision='distinct-community', reason='Separate community achievement; evidence review follows')
        self.assertEqual(decision['decision'], 'distinct-community')
        self.assertEqual(self.queue.jobs(key)[0]['status'], 'complete')

    def test_deferred_review_resume_and_lease_renewal(self):
        self.screen()
        key = self.queue.enqueue({'name': 'Paper printing', 'community': 'community-b'}, self.snapshot)
        lease = self.queue.claim('screen', 'screening', now=10, ttl=5)
        renewed = self.queue.renew(lease, now=14, ttl=20)
        self.assertEqual(renewed['expires'], 34)
        self.queue.screen(renewed, self.repo, now=20)
        self.queue.resume(key, 'screening', 'Community grain reviewed')
        lease = self.queue.claim('screen', 'screening', now=21, ttl=5)
        self.queue.screen(lease, self.repo, decision='distinct-community', reason='Independent community record', now=22)
        self.assertEqual(self.queue.jobs(key)[0]['status'], 'complete')
        with self.assertRaisesRegex(ValueError, 'stale'):
            self.queue.renew(renewed, now=23)

    def test_integrator_stale_owner_fenced(self):
        old = self.queue.claim_integrator('old', now=10, ttl=5)
        current = self.queue.claim_integrator('new')
        with self.assertRaisesRegex(ValueError, 'stale'):
            self.queue.release_integrator(old)
        self.queue.check_integrator(current)
        self.queue.release_integrator(current)
        self.assertIsNotNone(self.queue.claim_integrator('third'))

    def test_snapshot_rebinding_preserves_saved_sources_and_extraction(self):
        self.complete_until('review')
        self.write('data/discoveries/a/beta.json', json.dumps({'id': 'beta', 'name': 'Another achievement'}))
        self.commit()
        new = committed_snapshot(self.repo)
        self.queue.enqueue(self.candidate, new)
        states = {j['stage']: j['status'] for j in self.queue.jobs(self.key)}
        self.assertEqual(states, {'screening': 'pending', 'acquire': 'complete', 'extract': 'complete', 'mechanical': 'pending', 'review': 'pending', 'integrate': 'pending'})
        self.assertIsNone(self.queue.claim('reviewer', 'review'))
        self.assertEqual(self.screen()['snapshot'], new)

    def test_prompt_version_invalidates_only_affected_successors(self):
        self.complete_until('review')
        self.queue.enqueue(self.candidate, self.snapshot, {'review': {'prompt': 'v2', 'model': 'reviewer-v2'}})
        states = {j['stage']: j['status'] for j in self.queue.jobs(self.key)}
        self.assertEqual(states['extract'], 'complete')
        self.assertEqual(states['mechanical'], 'complete')
        self.assertEqual(states['review'], 'pending')
        self.queue.enqueue(self.candidate, self.snapshot, {'extract': {'evidence': 'hash-v2'}, 'review': {'prompt': 'v2', 'model': 'reviewer-v2'}})
        self.assertEqual(self.queue.jobs(self.key)[2]['status'], 'pending')

    def test_shared_service_pause_allows_saved_work(self):
        self.complete_until('acquire')
        self.queue.pause_service('search', time.time() + 1000, 'search-budget-exhausted')
        self.assertEqual(self.queue.claim('extractor')['stage'], 'extract')
        self.queue.enqueue({'name': 'Independent second candidate'}, self.snapshot)
        self.screen()
        self.assertIsNone(Queue(self.db).claim('retriever', 'acquire'))
        self.queue.pause_service('search', 0, 'Budget restored')
        self.assertIsNotNone(self.queue.claim('retriever', 'acquire'))

    def test_integrator_and_staging_do_not_touch_live_files(self):
        lease = self.queue.claim_integrator('one')
        self.assertIsNone(Queue(self.db).claim_integrator('two'))
        changes = {'data/discoveries/b/new.json': b'{"id":"new","name":"New achievement"}'}
        result = stage_integration(self.repo, self.snapshot, changes, self.queue, lease)
        repeat = stage_integration(self.repo, self.snapshot, changes, self.queue, lease)
        self.assertEqual(result['artifact_hash'], repeat['artifact_hash'])
        self.assertEqual(result['changes'][0]['sha256'], digest(next(iter(changes.values()))))
        self.assertFalse((self.repo / next(iter(changes))).exists())
        self.assertEqual(self.git('status', '--porcelain'), b'')
        with self.assertRaisesRegex(ValueError, 'validation failed'):
            stage_integration(self.repo, self.snapshot, {'data/invalid.json': b'invalid'}, self.queue, lease)
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            stage_integration(self.repo, self.snapshot, {'../escape': b'x'}, self.queue, lease)
        result = stage_integration(self.repo, self.snapshot, {'tools/example.py': b'pass\n'}, self.queue, lease)
        self.assertEqual(result['checks'][1]['command'], ['npm', 'test'])

    def test_retained_artifact_adoption_requires_provenance_and_fresh_screen(self):
        artifact = self.root / 'retained-card.json'
        artifact.write_bytes(b'{"retained":true}')
        provenance = {'origin': 'preserved earlier batch', 'artifact_sha256': digest(artifact.read_bytes()), 'evidence_hashes': [digest(b'original evidence')]}
        with self.assertRaisesRegex(ValueError, 'Only acquire/extract'):
            self.queue.adopt_artifact(self.key, 'screening', artifact, provenance, {})
        with self.assertRaisesRegex(ValueError, 'version mismatch'):
            self.queue.adopt_artifact(self.key, 'acquire', artifact, provenance, {'prompt': 'wrong'})
        with self.assertRaisesRegex(ValueError, 'requires completed acquisition'):
            self.queue.adopt_artifact(self.key, 'extract', artifact, provenance, {})
        self.queue.adopt_artifact(self.key, 'acquire', artifact, provenance, {})
        self.queue.adopt_artifact(self.key, 'extract', artifact, provenance, {})
        self.assertIsNone(self.queue.claim('worker', 'mechanical'))
        self.assertEqual(self.queue.jobs(self.key)[1]['provenance'], json.dumps(provenance, sort_keys=True))
        self.screen()
        self.assertEqual(self.queue.claim('worker')['stage'], 'mechanical')
        self.queue.adopt_artifact(self.key, 'extract', artifact, provenance, {})
        artifact.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            self.queue.adopt_artifact(self.key, 'extract', artifact, provenance, {})

    def test_isolated_code_validation_installs_frozen_app_lock(self):
        self.write('app/package-lock.json', '{"lockfileVersion":3}')
        self.commit()
        snapshot = committed_snapshot(self.repo)
        lease = self.queue.claim_integrator('one')
        original_run = subprocess.run
        checks = []
        def run(command, **kwargs):
            if command[0] == 'git':
                return original_run(command, **kwargs)
            checks.append(command)
            self.assertNotEqual(Path(kwargs['cwd']), self.repo)
            self.assertEqual((Path(kwargs['cwd']) / 'app/package-lock.json').read_text(), '{"lockfileVersion":3}')
            return subprocess.CompletedProcess(command, 0, 'passed', '')
        with patch('workflow.subprocess.run', side_effect=run) as execute:
            result = stage_integration(self.repo, snapshot, {'tools/new.py': b'pass'}, self.queue, lease)
        self.assertEqual([check['command'] for check in result['checks']], [['python3', 'tools/validate.py'], ['npm', 'ci', '--ignore-scripts', '--prefix', 'app'], ['npm', 'test']])
        self.assertEqual(len(checks), 3)
        self.assertFalse((self.repo / 'app/node_modules').exists())

    def test_changed_commit_isolation_and_hash_tamper(self):
        self.write('data/discoveries/a/alpha.json', 'invalid live uncommitted file')
        self.screen()
        lease = self.queue.claim_integrator('one')
        stage_integration(self.repo, self.snapshot, {}, self.queue, lease)
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            stage_integration(self.repo, {**self.snapshot, 'data_hash': 'wrong'}, {}, self.queue, lease)
        self.assertEqual((self.repo / 'data/discoveries/a/alpha.json').read_text(), 'invalid live uncommitted file')


if __name__ == '__main__':
    unittest.main()
