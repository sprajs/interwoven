"""Durable, fenced research jobs; no model calls and no writes to the live dataset.

Queue.enqueue binds stable candidate identity to a committed_snapshot and per-stage
versions. screen must run before retrieval. claim returns a lease token required
by complete/fail; expired workers cannot publish. Re-enqueueing changed inputs
invalidates affected judgments while retaining reusable acquisition artifacts.
Runtime SQLite files belong outside data/. Timestamps are Unix seconds.
"""
from __future__ import annotations

import difflib
import hashlib
import io
import json
import re
import sqlite3
import subprocess
import tarfile
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

STAGES = ('screening', 'acquire', 'extract', 'mechanical', 'review', 'integrate')


def digest(value):
    """SHA-256 of canonical JSON (or exact bytes)."""
    return hashlib.sha256(value if isinstance(value, bytes) else json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def candidate_id(candidate):
    """Identity includes community/era; similar achievements never collapse by name."""
    if candidate.get('id') is not None:
        if not isinstance(candidate['id'], str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,127}', candidate['id']):
            raise ValueError('Explicit candidate ID must be a stable lowercase identifier')
        return candidate['id']
    return 'candidate-' + digest(candidate)[:24]


def _git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def _committed_data(repo, commit):
    # One Git process per immutable inventory, rather than a process per record.
    archive = _git(repo, 'archive', commit, '--', 'data')
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        return {member.name: tar.extractfile(member).read() for member in tar.getmembers() if member.isfile()}


def _data_hash(files):
    return digest([(name, digest(content)) for name, content in sorted(files.items())])


def committed_snapshot(repo, revision='HEAD'):
    """Name an immutable commit and hash every committed data byte and pathname."""
    commit = _git(repo, 'rev-parse', '--verify', revision + '^{commit}').decode().strip()
    return {'commit': commit, 'data_hash': _data_hash(_committed_data(repo, commit))}


def _records(repo, snapshot):
    files = _committed_data(repo, snapshot['commit'])
    if _data_hash(files) != snapshot['data_hash']:
        raise ValueError('Snapshot content hash mismatch')
    return [json.loads(content) for name, content in sorted(files.items()) if name.startswith('data/discoveries/') and name.endswith('.json')]


class Queue:
    """SQLite queue with atomic claims, bounded retries, and lease fencing.

    versions is a mapping from stage to a JSON object containing prompt/model/
    evidence/rubric versions as appropriate. Store immutable artifact bytes in
    complete; the queue retains their hash and optional artifact location.
    """
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS candidates(id TEXT PRIMARY KEY, candidate TEXT, snapshot TEXT);
                CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,candidate TEXT,stage TEXT,input TEXT,inputs TEXT,
                    status TEXT DEFAULT 'pending',owner TEXT,token TEXT,expires REAL,attempts INTEGER DEFAULT 0,
                    max_attempts INTEGER,reason TEXT,artifact_hash TEXT,artifact TEXT,decision TEXT,provenance TEXT,
                    UNIQUE(candidate,stage));
                CREATE TABLE IF NOT EXISTS services(name TEXT PRIMARY KEY,until REAL,reason TEXT);
                CREATE TABLE IF NOT EXISTS locks(name TEXT PRIMARY KEY,owner TEXT,token TEXT,expires REAL);
            ''')
            columns = {row[1] for row in db.execute('PRAGMA table_info(jobs)')}
            for name in ('inputs', 'provenance'):
                if name not in columns:
                    db.execute('ALTER TABLE jobs ADD COLUMN ' + name + ' TEXT')

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def enqueue(self, candidate, snapshot, versions=None, max_attempts=3):
        """Idempotently add/rebind a candidate; changed stages invalidate successors.

        A dataset-only change reruns screening/mechanical/review/integration but
        retains acquisition/extraction. A changed stage version reruns that stage
        and its successors. Rebinding fences any previous outstanding leases.
        """
        if max_attempts < 1 or set(snapshot) != {'commit', 'data_hash'}:
            raise ValueError('Need a committed snapshot and positive retry bound')
        versions = versions or {}
        key = candidate_id(candidate)
        with self._db() as db:
            previous = db.execute('SELECT snapshot FROM candidates WHERE id=?', (key,)).fetchone()
            changed_snapshot = previous and json.loads(previous[0]) != snapshot
            db.execute('INSERT OR REPLACE INTO candidates VALUES (?,?,?)', (key, json.dumps(candidate, sort_keys=True), json.dumps(snapshot, sort_keys=True)))
            invalidate = set()
            for stage in STAGES:
                own = {'version': versions.get(stage, {}), 'candidate_sha256': digest(candidate)}
                if stage in ('screening', 'mechanical', 'review', 'integrate'):
                    own['snapshot'] = snapshot
                signature = digest(own)
                job = db.execute('SELECT input FROM jobs WHERE candidate=? AND stage=?', (key, stage)).fetchone()
                if job and job[0] != signature:
                    if changed_snapshot and stage == 'screening':
                        invalidate.update(('screening', 'mechanical', 'review', 'integrate'))
                    else:
                        invalidate.update(STAGES[STAGES.index(stage):])
                db.execute('INSERT OR IGNORE INTO jobs(id,candidate,stage,input,inputs,max_attempts) VALUES (?,?,?,?,?,?)', (key + ':' + stage, key, stage, signature, json.dumps(own, sort_keys=True), max_attempts))
                db.execute('UPDATE jobs SET input=?,inputs=?,max_attempts=? WHERE candidate=? AND stage=?', (signature, json.dumps(own, sort_keys=True), max_attempts, key, stage))
            for stage in invalidate:
                db.execute("UPDATE jobs SET status='pending',owner=NULL,token=NULL,expires=NULL,attempts=0,reason=NULL,artifact_hash=NULL,artifact=NULL,decision=NULL,provenance=NULL WHERE candidate=? AND stage=?", (key, stage))
        return key

    def jobs(self, key=None):
        """Return bounded-job metadata, including attempts and failure reasons."""
        with self._db() as db:
            return [dict(r) for r in db.execute('SELECT * FROM jobs WHERE (? IS NULL OR candidate=?) ORDER BY candidate,rowid', (key, key))]

    def pause_service(self, name, until, reason):
        """Persist shared exhaustion; dispatch resumes only at until or explicit reset."""
        if not reason:
            raise ValueError('Service pause requires reason')
        with self._db() as db:
            db.execute('INSERT OR REPLACE INTO services VALUES (?,?,?)', (name, until, reason))

    def defer_pending(self, key, stage, reason):
        """Record an imported access/input failure without inventing an attempt.

        Never replace a successful artifact or an active worker. Explicit resume
        or verified artifact adoption is needed before this stage can continue.
        """
        if stage not in STAGES or not reason:
            raise ValueError('Deferral requires stage and reason')
        with self._db() as db:
            row = db.execute('SELECT status FROM jobs WHERE candidate=? AND stage=?', (key, stage)).fetchone()
            if not row or row['status'] in ('running', 'complete'):
                raise ValueError('Cannot defer successful or leased work')
            db.execute("UPDATE jobs SET status='deferred',reason=? WHERE candidate=? AND stage=?", (reason, key, stage))

    def claim(self, owner, stage=None, ttl=300, service=None, now=None):
        """Atomically claim one eligible stage; all predecessors must be complete."""
        now = time.time() if now is None else now
        if not owner or ttl <= 0 or (stage is not None and stage not in STAGES):
            raise ValueError('Invalid claim')
        with self._db() as db:
            db.execute("UPDATE jobs SET status='failed',reason='lease expired; retries exhausted',token=NULL WHERE status='running' AND expires<=? AND attempts>=max_attempts", (now,))
            rows = db.execute("SELECT * FROM jobs WHERE (status IN ('pending','retry') OR (status='running' AND expires<=?)) AND attempts<max_attempts ORDER BY rowid", (now,)).fetchall()
            for row in rows:
                if stage and row['stage'] != stage:
                    continue
                earlier = STAGES[:STAGES.index(row['stage'])]
                statuses = {r['stage']: r['status'] for r in db.execute('SELECT stage,status FROM jobs WHERE candidate=?', (row['candidate'],))}
                if any(statuses[s] != 'complete' for s in earlier):
                    continue
                needed_service = service or ('search' if row['stage'] == 'acquire' else None)
                if needed_service and db.execute('SELECT 1 FROM services WHERE name=? AND until>?', (needed_service, now)).fetchone():
                    continue
                token = uuid.uuid4().hex
                db.execute("UPDATE jobs SET status='running',owner=?,token=?,expires=?,attempts=attempts+1 WHERE id=?", (owner, token, now + ttl, row['id']))
                return dict(db.execute('SELECT * FROM jobs WHERE id=?', (row['id'],)).fetchone())
        return None

    @staticmethod
    def _owned(db, lease, now):
        row = db.execute('SELECT * FROM jobs WHERE id=?', (lease['id'],)).fetchone()
        if not row or row['status'] != 'running' or row['token'] != lease['token'] or row['expires'] <= now:
            raise ValueError('Expired or stale lease')
        return row

    def complete(self, lease, artifact, location=None, now=None):
        """Publish exact artifact hash with fenced ownership; screening uses screen()."""
        now = time.time() if now is None else now
        with self._db() as db:
            row = self._owned(db, lease, now)
            if row['stage'] == 'screening':
                raise ValueError('Screening requires explicit snapshot-bound decision')
            db.execute("UPDATE jobs SET status='complete',artifact_hash=?,artifact=?,token=NULL,expires=NULL WHERE id=?", (digest(artifact), location, row['id']))

    def fail(self, lease, reason, defer=False, now=None):
        """Record a retryable failure or explicit deferral; exhausted jobs stop."""
        if not reason:
            raise ValueError('Failure/defer reason required')
        now = time.time() if now is None else now
        with self._db() as db:
            row = self._owned(db, lease, now)
            status = 'deferred' if defer else ('retry' if row['attempts'] < row['max_attempts'] else 'failed')
            db.execute('UPDATE jobs SET status=?,reason=?,token=NULL,expires=NULL WHERE id=?', (status, reason, row['id']))

    def screen(self, lease, repo, decision=None, reason=None, now=None):
        """Screen committed inventory; fuzzy matches require an explicit decision.

        Decisions: new, distinct-community, extension, duplicate, defer. Matches
        never automatically reject regional/independent achievements. Human/model
        review must explain any decision when matches exist.
        """
        supplied_now = now
        now = time.time() if now is None else now
        with self._db() as db:
            row = self._owned(db, lease, now)
            if row['stage'] != 'screening':
                raise ValueError('Expected screening lease')
            c = db.execute('SELECT * FROM candidates WHERE id=?', (row['candidate'],)).fetchone()
            candidate, snapshot = json.loads(c['candidate']), json.loads(c['snapshot'])
        names = [str(candidate.get(k, '')) for k in ('name', 'capability')] + list(candidate.get('aliases', []))
        names = [n.casefold().strip() for n in names if n]
        matches = []
        for record in _records(repo, snapshot):
            targets = [record.get('name', ''), *record.get('aliases', [])]
            score = max((difflib.SequenceMatcher(None, n, str(t).casefold()).ratio() for n in names for t in targets), default=0)
            if record.get('id') == candidate.get('discovery_id') or score >= .72 or (candidate.get('concept') and candidate.get('concept') == record.get('concept')):
                matches.append({'id': record['id'], 'name': record['name'], 'score': round(score, 4), 'origin': record.get('origin'), 'societies': record.get('societies', [])})
        if decision is None:
            decision = 'defer' if matches else 'new'
            reason = 'Ambiguous matches require grain/community review' if matches else 'No inventory match'
        if decision not in ('new', 'distinct-community', 'extension', 'duplicate', 'defer') or (matches and not reason):
            raise ValueError('Explicit decision and reason required')
        artifact = {'snapshot': snapshot, 'matches': matches, 'decision': decision, 'reason': reason}
        with self._db() as db:
            self._owned(db, lease, time.time() if supplied_now is None else now)
            # Another enqueue may have invalidated the token during inventory reading.
            status = 'complete' if decision in ('new', 'distinct-community', 'extension') else 'deferred'
            db.execute('UPDATE jobs SET status=?,decision=?,reason=?,artifact_hash=?,artifact=?,token=NULL,expires=NULL WHERE id=?', (status, decision, reason, digest(artifact), json.dumps(artifact, sort_keys=True), row['id']))
        return artifact

    def adopt_artifact(self, key, stage, path, provenance, versions):
        """Import a retained successful acquire/extract artifact without model work.

        Explicit provenance must name its origin, exact artifact_sha256, and
        evidence_hashes. versions must equal this job's configured version map.
        Screening cannot be imported; dispatch remains blocked until it succeeds
        against the currently bound snapshot. Importing extraction also requires
        retained acquisition. Existing success is immutable and idempotent.
        """
        if stage not in ('acquire', 'extract'):
            raise ValueError('Only acquire/extract artifacts may be adopted')
        if not isinstance(provenance, dict) or not provenance.get('origin') or not isinstance(provenance.get('evidence_hashes'), list):
            raise ValueError('Adoption requires origin and evidence hashes')
        path = Path(path).resolve()
        artifact_hash = digest(path.read_bytes())
        if provenance.get('artifact_sha256') != artifact_hash:
            raise ValueError('Retained artifact hash mismatch')
        with self._db() as db:
            row = db.execute('SELECT * FROM jobs WHERE candidate=? AND stage=?', (key, stage)).fetchone()
            if not row or json.loads(row['inputs'])['version'] != versions:
                raise ValueError('Retained artifact version mismatch')
            if stage == 'extract' and db.execute("SELECT status FROM jobs WHERE candidate=? AND stage='acquire'", (key,)).fetchone()[0] != 'complete':
                raise ValueError('Retained extraction requires completed acquisition')
            if row['status'] == 'running':
                raise ValueError('Cannot replace a leased stage')
            if row['status'] == 'complete':
                if row['artifact_hash'] != artifact_hash:
                    raise ValueError('Successful artifact is immutable')
                return artifact_hash
            db.execute("UPDATE jobs SET status='complete',artifact_hash=?,artifact=?,provenance=?,reason='adopted retained artifact',token=NULL,expires=NULL WHERE id=?", (artifact_hash, str(path), json.dumps(provenance, sort_keys=True), row['id']))
        return artifact_hash

    def resume(self, key, stage, reason, reset_attempts=False):
        """Explicitly release a deferred/failed job after a recorded input decision.

        Successful stages remain untouched. Exhausted work requires an explicit
        reset_attempts=True rather than silently defeating the retry bound.
        """
        if stage not in STAGES or not reason:
            raise ValueError('Resume requires stage and reason')
        with self._db() as db:
            row = db.execute('SELECT * FROM jobs WHERE candidate=? AND stage=?', (key, stage)).fetchone()
            if not row or row['status'] not in ('deferred', 'failed'):
                raise ValueError('Only deferred/failed jobs may resume')
            if row['attempts'] >= row['max_attempts'] and not reset_attempts:
                raise ValueError('Retry bound exhausted; explicit reset required')
            db.execute("UPDATE jobs SET status='pending',reason=?,attempts=?,token=NULL,expires=NULL WHERE id=?", (reason, 0 if reset_attempts else row['attempts'], row['id']))

    def renew(self, lease, ttl=300, now=None):
        """Extend a live job lease; an expired/stale worker cannot resurrect it."""
        now = time.time() if now is None else now
        if ttl <= 0:
            raise ValueError('Lease duration must be positive')
        with self._db() as db:
            self._owned(db, lease, now)
            db.execute('UPDATE jobs SET expires=? WHERE id=?', (now + ttl, lease['id']))
            return dict(db.execute('SELECT * FROM jobs WHERE id=?', (lease['id'],)).fetchone())

    def claim_integrator(self, owner, ttl=300, now=None):
        """Acquire the single global integrator lock (independent of job leases)."""
        now = time.time() if now is None else now
        if ttl <= 0 or not owner:
            raise ValueError('Invalid integrator lease')
        with self._db() as db:
            old = db.execute("SELECT * FROM locks WHERE name='integrator'").fetchone()
            if old and old['expires'] > now:
                return None
            lease = {'owner': owner, 'token': uuid.uuid4().hex, 'expires': now + ttl}
            db.execute("INSERT OR REPLACE INTO locks VALUES ('integrator',?,?,?)", (owner, lease['token'], lease['expires']))
            return lease

    def check_integrator(self, lease):
        with self._db() as db:
            row = db.execute("SELECT * FROM locks WHERE name='integrator'").fetchone()
            if not row or row['token'] != lease['token'] or row['expires'] <= time.time():
                raise ValueError('Expired or stale integrator lease')


    def release_integrator(self, lease):
        """Release only this owner's global integration lease."""
        with self._db() as db:
            row = db.execute("SELECT * FROM locks WHERE name='integrator'").fetchone()
            if not row or row['token'] != lease['token'] or row['expires'] <= time.time():
                raise ValueError('Expired or stale integrator lease')
            db.execute("DELETE FROM locks WHERE name='integrator'")


def stage_integration(repo, snapshot, changes, queue, lease):
    """Validate exact task-owned bytes on an isolated committed snapshot.

    changes maps repository-relative paths to bytes (None deletes). Returns a
    deterministic manifest/hash and captured validation results; temporary files
    are removed. Never stages Git files or mutates the live checkout. Caller may
    publish exactly this manifest after checking its snapshot is still current.
    """
    queue.check_integrator(lease)
    if committed_snapshot(repo, snapshot['commit']) != snapshot:
        raise ValueError('Snapshot content hash mismatch')
    for name, content in changes.items():
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] == '.git' or str(path) != name:
            raise ValueError('Unsafe staging path')
        if content is not None and not isinstance(content, bytes):
            raise TypeError('Changes must contain exact bytes or None')
    with tempfile.TemporaryDirectory(prefix='research-staging-') as tmp:
        root = Path(tmp).resolve()
        archive = _git(repo, 'archive', snapshot['commit'])
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(root, filter='data')
        for name, content in sorted(changes.items()):
            path = root / name
            relative_parents = [root.joinpath(*PurePosixPath(name).parts[:n]) for n in range(1, len(PurePosixPath(name).parts) + 1)]
            if any(parent.is_symlink() for parent in relative_parents) or not path.resolve().is_relative_to(root):
                raise ValueError('Staging path escapes through symlink')
            if content is None:
                path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
        commands = [['python3', 'tools/validate.py']]
        if any(not name.startswith(('data/', 'docs/', 'research/')) for name in changes):
            if (root / 'app/package-lock.json').is_file():
                commands.append(['npm', 'ci', '--ignore-scripts', '--prefix', 'app'])
            commands.append(['npm', 'test'])
        results = []
        for command in commands:
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
            results.append({'command': command, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
            if result.returncode:
                raise ValueError('Staging validation failed: ' + json.dumps(results))
        queue.check_integrator(lease)
        manifest = [{'path': name, 'sha256': digest(content) if content is not None else None} for name, content in sorted(changes.items())]
        return {'snapshot': snapshot, 'changes': manifest, 'artifact_hash': digest({'snapshot': snapshot, 'changes': manifest}), 'checks': results}
