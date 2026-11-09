#!/usr/bin/env python3
"""Indexed local research. JSON is authoritative; this disposable SQLite cache is rebuilt on edit.

    python3 tools/research.py search 'steam engine'
    python3 tools/research.py walk watt-separate-condenser --direction incoming --depth 3
    python3 tools/research.py show <id>
    python3 tools/research.py shared <id> --kind person
    python3 tools/research.py status --verify

Only Python's standard library is required, including SQLite with FTS5.
"""
from __future__ import annotations

from contextlib import closing
import argparse
import hashlib
import json
import os
import sqlite3
import tempfile
from pathlib import Path

from dataset import DATA, ROOT, Dataset, year_value
from publish import atomic_write, encoded, evidence_ids

DB = ROOT / '.cache' / 'research.sqlite'
SCHEMA_VERSION = '1'


def inputs(root: Path = ROOT) -> list[Path]:
    return sorted((root / 'data').rglob('*.json')) + sorted((root / 'data').rglob('*.jsonl')) + [root / 'tools' / name for name in ('research.py', 'dataset.py', 'publish.py')]


def signature(root: Path = ROOT) -> dict:
    result = {}
    for path in inputs(root):
        stat = path.stat()
        result[str(path.relative_to(root))] = [stat.st_size, stat.st_mtime_ns]
    return result


def fingerprint(root: Path = ROOT) -> str:
    h = hashlib.sha256()
    for p in inputs(root):
        h.update(str(p.relative_to(root)).encode() + b'\0' + p.read_bytes() + b'\0')
    return h.hexdigest()


def text_values(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return ' '.join(text_values(v) for v in value.values())
    if isinstance(value, list):
        return ' '.join(text_values(v) for v in value)
    return ''


def build_database(data: Dataset, target: Path, version: str) -> None:
    """Write a complete replacement without affecting readers of the old database."""
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.research-', suffix='.sqlite', dir=target.parent)
    os.close(fd)
    try:
        with closing(sqlite3.connect(name)) as con, con:
            con.executescript('''
                PRAGMA foreign_keys=ON;
                CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE discoveries(id TEXT PRIMARY KEY, name TEXT NOT NULL, domain TEXT,
                    year REAL, path TEXT NOT NULL, record TEXT NOT NULL);
                CREATE TABLE sources(id TEXT PRIMARY KEY, path TEXT NOT NULL, record TEXT NOT NULL);
                CREATE TABLE events(discovery TEXT REFERENCES discoveries(id), id TEXT, type TEXT,
                    year REAL, record TEXT, PRIMARY KEY(discovery,id));
                CREATE TABLE edges(id INTEGER PRIMARY KEY, src TEXT REFERENCES discoveries(id),
                    dst TEXT REFERENCES discoveries(id), type TEXT, layer TEXT, status TEXT, record TEXT);
                CREATE INDEX edges_out ON edges(src,status,layer,dst);
                CREATE INDEX edges_in ON edges(dst,status,layer,src);
                CREATE TABLE members(kind TEXT, entity TEXT, discovery TEXT REFERENCES discoveries(id),
                    PRIMARY KEY(kind,entity,discovery));
                CREATE INDEX members_discovery ON members(discovery,kind,entity);
                CREATE TABLE entities(kind TEXT,id TEXT,name TEXT,path TEXT,record TEXT,PRIMARY KEY(kind,id));
                CREATE TABLE facets(discovery TEXT REFERENCES discoveries(id),facet TEXT,basis TEXT,PRIMARY KEY(discovery,facet));
                CREATE INDEX facets_basis ON facets(facet,basis,discovery);
                CREATE TABLE citations(discovery TEXT REFERENCES discoveries(id), source TEXT REFERENCES sources(id),
                    PRIMARY KEY(discovery,source));
                CREATE INDEX citations_source ON citations(source,discovery);
                CREATE INDEX discoveries_domain ON discoveries(domain,year);
                CREATE INDEX events_type ON events(type,year);
                CREATE VIRTUAL TABLE search USING fts5(id UNINDEXED, name, body, tokenize='unicode61');
            ''')
            con.executemany('INSERT INTO metadata VALUES (?,?)', [('schema', SCHEMA_VERSION), ('fingerprint', version)])
            for register, values in data.registers.items():
                for key, entity in sorted(values.items()):
                    con.execute('INSERT INTO entities VALUES (?,?,?,?,?)', (register,key,entity.get('name',key),f'data/{register}.jsonl',encoded(entity).decode()))
            for key, source in sorted(data.sources.items()):
                path = data.paths.get('sources/' + key, DATA / 'sources' / key[0] / (key + '.json'))
                con.execute('INSERT INTO sources VALUES (?,?,?)', (key, str(Path('data') / 'sources' / path.parent.name / path.name), encoded(source).decode()))
            for key, record in sorted(data.discoveries.items()):
                anchor = data.earliest_record(record)
                year = year_value(anchor['date']['latest']) if anchor else None
                path = data.paths['discoveries/' + key]
                relative = str(Path('data') / 'discoveries' / path.parent.name / path.name)
                con.execute('INSERT INTO discoveries VALUES (?,?,?,?,?,?)', (key, record['name'], record['domain'], year, relative, encoded(record).decode()))
            layers = {kind: layer for layer, kinds in data.vocab['link']['layers'].items() for kind in kinds}
            for key, record in sorted(data.discoveries.items()):
                con.executemany('INSERT INTO facets VALUES (?,?,?)', [(key,facet,basis) for facet,basis in record['research']['basis'].items()])
                for event in record['events']:
                    con.execute('INSERT INTO events VALUES (?,?,?,?,?)', (key, event['id'], event['type'], year_value(event['date']['latest']), encoded(event).decode()))
                for link in record.get('links', []):
                    con.execute('INSERT INTO edges(src,dst,type,layer,status,record) VALUES (?,?,?,?,?,?)', (link['from'], key, link['type'], layers[link['type']], link['status'], encoded(link).decode()))
                related = []
                for register, field, kind in [('people', 'person', 'person'), ('places', 'place', 'place'), ('organizations', 'organization', 'organization')]:
                    for item in record.get(register, []):
                        entity = item[field]
                        con.execute('INSERT OR IGNORE INTO members VALUES (?,?,?)', (kind, entity, key))
                        related.append(data.registers[register].get(entity, {}).get('name', entity))
                for kind, ids in [('society', record.get('societies', [])), ('concept', [record['concept']] if record.get('concept') else [])]:
                    register = 'societies' if kind == 'society' else 'concepts'
                    for entity in ids:
                        con.execute('INSERT OR IGNORE INTO members VALUES (?,?,?)', (kind, entity, key))
                        related.append(data.registers[register].get(entity, {}).get('name', entity))
                for source in sorted(evidence_ids(record)):
                    con.execute('INSERT INTO citations VALUES (?,?)', (key, source))
                con.execute('INSERT INTO search VALUES (?,?,?)', (key, record['name'], text_values(record) + ' ' + ' '.join(related)))
            con.execute("INSERT INTO search(search) VALUES ('optimize')")
            con.execute('ANALYZE')
            assert con.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        os.replace(name, target)
    finally:
        Path(name).unlink(missing_ok=True)


def rebuild(path: Path = DB, data: Dataset | None = None, root: Path = ROOT) -> str:
    before = signature(root)
    version = fingerprint(root)
    data = data or Dataset.load(root / 'data')
    build_database(data, path, version)
    if before != signature(root) or version != fingerprint(root):
        # Never certify a cache built while its inputs were changing.
        path.with_suffix('.inputs.json').unlink(missing_ok=True)
        raise RuntimeError('Research inputs changed during the build; retry after the edits finish.')
    atomic_write(path.with_suffix('.inputs.json'), encoded({'schema': SCHEMA_VERSION, 'inputs': before, 'fingerprint': version}))
    return version


def connect(path: Path = DB, root: Path = ROOT, verify: bool = False) -> sqlite3.Connection:
    """Fast stat check on every command; --verify also hashes bytes, even if mtimes were restored."""
    try:
        saved = json.loads(path.with_suffix('.inputs.json').read_text())
        valid = path.exists() and saved['schema'] == SCHEMA_VERSION and saved['inputs'] == signature(root)
        if verify:
            valid = valid and saved['fingerprint'] == fingerprint(root)
    except (OSError, ValueError, KeyError):
        valid = False
    if not valid:
        rebuild(path, root=root)
    con = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    actual = dict(con.execute('SELECT key,value FROM metadata'))
    saved = json.loads(path.with_suffix('.inputs.json').read_text())
    if actual.get('schema') != SCHEMA_VERSION or actual.get('fingerprint') != saved['fingerprint']:
        con.close()
        rebuild(path, root=root)
        return connect(path, root)
    return con


def search(con: sqlite3.Connection, query: str, limit: int = 20) -> list[dict]:
    # Treat user text as literal AND terms, not an FTS expression/program.
    terms = ['"' + term.replace('"', '""') + '"' for term in query.split()]
    if not terms:
        return []
    return [dict(row) for row in con.execute('''SELECT d.id,d.name,d.path,d.year,
        snippet(search,2,'[',']','…',24) AS excerpt FROM search JOIN discoveries d ON d.id=search.id
        WHERE search MATCH ? ORDER BY bm25(search,0,5,1),d.id LIMIT ?''', (' AND '.join(terms), limit))]


def walk(con: sqlite3.Connection, start: str, direction: str = 'incoming', depth: int = 3,
         layers: tuple[str, ...] = ('dependence', 'transmission'), status: str = 'established') -> list[dict]:
    if direction not in ('incoming', 'outgoing') or not 0 <= depth <= 100:
        raise ValueError('Walk needs incoming/outgoing and a depth from 0 to 100.')
    if not con.execute('SELECT 1 FROM discoveries WHERE id=?', (start,)).fetchone():
        raise ValueError(f'Unknown discovery: {start}')
    if not layers:
        return []
    source, dest = ('dst', 'src') if direction == 'incoming' else ('src', 'dst')
    seen, frontier, result = {start}, [start], []
    for distance in range(1, depth + 1):
        next_ids = set()
        # Bounded batches also work with SQLite's older 999-variable limit.
        for offset in range(0, len(frontier), 400):
            batch = frontier[offset:offset + 400]
            sql = f'SELECT DISTINCT {dest} FROM edges WHERE {source} IN ({",".join("?" for _ in batch)}) AND status=? AND layer IN ({",".join("?" for _ in layers)})'
            next_ids.update(row[0] for row in con.execute(sql, [*batch, status, *layers]))
        frontier = sorted(next_ids - seen)
        if not frontier:
            break
        seen.update(frontier)
        for key in frontier:
            row = con.execute('SELECT id,name,path FROM discoveries WHERE id=?', (key,)).fetchone()
            result.append({**dict(row), 'depth': distance})
    return result


def shared(con: sqlite3.Connection, key: str, kind: str | None = None) -> list[dict]:
    return [dict(row) for row in con.execute('''SELECT a.kind,a.entity,d.id,d.name,d.path FROM members a
        JOIN members b ON a.kind=b.kind AND a.entity=b.entity JOIN discoveries d ON d.id=b.discovery
        WHERE a.discovery=? AND b.discovery<>? AND (? IS NULL OR a.kind=?)
        ORDER BY a.kind,a.entity,d.id''', (key, key, kind, kind))]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['search', 'walk', 'shared', 'show', 'status', 'rebuild'])
    parser.add_argument('value', nargs='?', default='')
    parser.add_argument('--db', type=Path, default=DB)
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--direction', choices=['incoming', 'outgoing'], default='incoming')
    parser.add_argument('--depth', type=int, default=3)
    parser.add_argument('--layer', action='append', choices=['dependence', 'transmission', 'parallel', 'affinity'])
    parser.add_argument('--status', default='established', choices=['established', 'candidate', 'insufficient'])
    parser.add_argument('--kind', choices=['person', 'place', 'organization', 'society', 'concept'])
    parser.add_argument('--limit', type=int, default=20)
    args = parser.parse_args()
    if args.command in ('search', 'walk', 'shared', 'show') and not args.value:
        parser.error('This command requires a search phrase or discovery id.')
    if not 1 <= args.limit <= 1000:
        parser.error('--limit must be between 1 and 1000')
    if args.command == 'rebuild':
        rebuild(args.db)
    with closing(connect(args.db, verify=args.verify)) as con:
        if args.command == 'search':
            result = search(con, args.value, args.limit)
        elif args.command == 'walk':
            result = walk(con, args.value, args.direction, args.depth, tuple(args.layer or ['dependence', 'transmission']), args.status)
        elif args.command == 'shared':
            result = shared(con, args.value, args.kind)
        elif args.command == 'show':
            row = con.execute('SELECT path,record FROM discoveries WHERE id=?', (args.value,)).fetchone()
            if not row:
                parser.error('Unknown discovery id')
            result = {'path': row['path'], 'record': json.loads(row['record'])}
        else:
            result = dict(con.execute('SELECT key,value FROM metadata'))
            result['discoveries'] = con.execute('SELECT count(*) FROM discoveries').fetchone()[0]
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
