"""Correctness of split payloads, independent invalidation and indexed research."""
from contextlib import closing
import copy
import json
import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build
from dataset import Dataset
from publish import encoded, publish
import research


class PublishedDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = Dataset.load()
        cls.bundle = build.build(cls.data)

    def test_every_detail_and_link_survives_split(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            manifest = publish(self.bundle, out)
            core = json.loads((out / manifest['core']).read_text())
            self.assertEqual(core['counts'], self.bundle['counts'])
            self.assertLess(len(encoded(core)), len(encoded(self.bundle)) * .3)
            for record in self.bundle['discoveries']:
                detail = json.loads((out / core['details'][record['id']]).read_text())
                self.assertEqual(detail['entry'], record)
                self.assertEqual(detail['links'], [l for l in self.bundle['links'] if record['id'] in (l['from'], l['to'])])
                self.assertTrue(all(source in self.bundle['sources'] for source in detail['sources']))
                self.assertTrue(research.evidence_ids(self.data.discoveries[record['id']]) <= detail['sources'].keys())
            self.assertEqual(json.loads((out / core['population_file']).read_text()), self.bundle['population'])
            for item in core['discoveries']:
                self.assertNotIn('events', item)
                self.assertNotIn('description', item)

    def test_unchanged_build_and_single_record_invalidation(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            first = publish(self.bundle, out)
            old = json.loads((out / first['core']).read_text())
            mtimes = {p: p.stat().st_mtime_ns for p in out.rglob('*') if p.is_file()}
            self.assertEqual(first, publish(self.bundle, out))
            self.assertEqual(mtimes, {p: p.stat().st_mtime_ns for p in mtimes})
            changed = copy.deepcopy(self.bundle)
            changed['discoveries'][0]['description'] += ' Edited only in this test.'
            new_manifest = publish(changed, out)
            new = json.loads((out / new_manifest['core']).read_text())
            differences = [key for key in old['details'] if old['details'][key] != new['details'][key]]
            self.assertEqual(differences, [changed['discoveries'][0]['id']])
            self.assertNotEqual(first['version'], new_manifest['version'])
            self.assertEqual(old['population_file'], new['population_file'])
            # Open old tabs can still resolve their immutable detail URLs.
            self.assertTrue(all((out / path).exists() for path in old['details'].values()))

    def test_related_link_edit_invalidates_both_ends_only(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            old = json.loads((out / publish(self.bundle, out)['core']).read_text())
            changed = copy.deepcopy(self.bundle)
            link = changed['links'][0]
            link['statement'] += ' test correction'
            new = json.loads((out / publish(changed, out)['core']).read_text())
            self.assertEqual({k for k in old['details'] if old['details'][k] != new['details'][k]}, {link['from'], link['to']})


class ResearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.path = Path(cls.temp.name) / 'research.sqlite'
        cls.data = Dataset.load()
        research.build_database(cls.data, cls.path, 'fixture')
        cls.con = sqlite3.connect(cls.path)
        cls.con.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        cls.temp.cleanup()

    def test_every_source_record_event_and_citation_is_lossless(self):
        for row in self.con.execute('SELECT id,path,record FROM discoveries'):
            self.assertEqual(json.loads(row['record']), self.data.discoveries[row['id']])
            self.assertEqual(json.loads((research.ROOT / row['path']).read_text()), self.data.discoveries[row['id']])
        for row in self.con.execute('SELECT id,record FROM sources'):
            self.assertEqual(json.loads(row['record']), self.data.sources[row['id']])
        self.assertEqual(self.con.execute('SELECT count(*) FROM events').fetchone()[0], sum(len(d['events']) for d in self.data.discoveries.values()))
        self.assertEqual(self.con.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_walk_matches_independent_scan_every_start_both_directions(self):
        layers = {kind: layer for layer, kinds in self.data.vocab['link']['layers'].items() for kind in kinds}
        edges = [(l['from'], d['id']) for d,l in self.data.links() if l['status'] == 'established' and layers[l['type']] in ('dependence','transmission')]
        for start in self.data.discoveries:
            for direction in ('incoming', 'outgoing'):
                seen, frontier, expected = {start}, {start}, {}
                for depth in range(1, 5):
                    next_ids = {a if direction == 'incoming' else b for a,b in edges if (b if direction == 'incoming' else a) in frontier} - seen
                    expected.update({key: depth for key in next_ids})
                    seen.update(next_ids)
                    frontier = next_ids
                self.assertEqual({r['id']:r['depth'] for r in research.walk(self.con, start, direction, 4)}, expected)

    def test_cycles_shared_ancestors_and_status_filter(self):
        con = sqlite3.connect(':memory:'); con.row_factory = sqlite3.Row
        con.executescript('CREATE TABLE discoveries(id TEXT,name TEXT,path TEXT); CREATE TABLE edges(src TEXT,dst TEXT,status TEXT,layer TEXT);')
        con.executemany('INSERT INTO discoveries VALUES (?,?,?)', [(k,k,k+'.json') for k in 'abcde'])
        con.executemany('INSERT INTO edges VALUES (?,?,?,?)', [('a','b','established','dependence'),('a','c','established','dependence'),('b','d','established','dependence'),('c','d','established','dependence'),('d','a','established','dependence'),('e','d','candidate','dependence')])
        self.assertEqual({r['id']:r['depth'] for r in research.walk(con,'d')}, {'b':1,'c':1,'a':2})
        self.assertEqual([r['id'] for r in research.walk(con,'d',status='candidate')], ['e'])
        self.assertEqual(research.walk(con,'d',depth=0), [])
        con.close()

    def test_fts_is_literal_and_returns_source_paths(self):
        self.assertTrue(research.search(self.con, 'steam'))
        self.assertEqual(research.search(self.con, ''), [])
        plain=research.search(self.con, 'steam')
        snippets=research.search(self.con, 'steam', snippets=True)
        self.assertEqual([r['id'] for r in plain], [r['id'] for r in snippets])
        self.assertTrue(any('[' in r['excerpt'] for r in snippets))
        for row in research.search(self.con, 'steam'):
            self.assertIn(row['id'], self.data.discoveries)
            self.assertTrue((research.ROOT / row['path']).exists())
        # Punctuation/FTS operators cannot execute an arbitrary FTS query.
        research.search(self.con, '" OR *')

    def test_real_edits_additions_deletions_and_snapshot_readers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(research.ROOT / 'data', root / 'data')
            (root / 'tools').mkdir()
            for name in ('research.py', 'dataset.py', 'publish.py'):
                shutil.copyfile(research.ROOT / 'tools' / name, root / 'tools' / name)
            path = root / 'research.sqlite'
            research.rebuild(path, root=root)
            key = sorted(self.data.discoveries)[0]
            record_path = root / 'data/discoveries' / self.data.discoveries[key]['domain'].split('.')[0] / (key + '.json')
            record = json.loads(record_path.read_text())
            with closing(research.connect(path,root)) as old:
                old_record = old.execute('SELECT record FROM discoveries WHERE id=?',(key,)).fetchone()[0]
                record['description'] += ' sentinel-A'
                record_path.write_text(json.dumps(record))
                with closing(research.connect(path,root)) as new:
                    self.assertIn('sentinel-A',new.execute('SELECT record FROM discoveries WHERE id=?',(key,)).fetchone()[0])
                self.assertEqual(old.execute('SELECT record FROM discoveries WHERE id=?',(key,)).fetchone()[0],old_record)
            # --verify catches tools which preserve both size and mtime deliberately.
            stat = record_path.stat()
            record_path.write_text(record_path.read_text().replace('sentinel-A','sentinel-B'))
            os.utime(record_path,ns=(stat.st_atime_ns,stat.st_mtime_ns))
            with closing(research.connect(path,root,verify=True)) as checked:
                self.assertIn('sentinel-B',checked.execute('SELECT record FROM discoveries WHERE id=?',(key,)).fetchone()[0])
            record['id'] = key + '-cache-test'; record['links'] = []
            added = record_path.with_name(record['id']+'.json')
            added.write_text(json.dumps(record))
            with closing(research.connect(path,root)) as new:
                self.assertEqual(new.execute('SELECT count(*) FROM discoveries').fetchone()[0],len(self.data.discoveries)+1)
            added.unlink()
            with closing(research.connect(path,root)) as new:
                self.assertEqual(new.execute('SELECT count(*) FROM discoveries').fetchone()[0],len(self.data.discoveries))

    def test_fts_terms_ranking_and_and_semantics(self):
        con=sqlite3.connect(':memory:'); con.row_factory=sqlite3.Row
        con.executescript("CREATE TABLE discoveries(id TEXT,name TEXT,path TEXT,year REAL,summary TEXT); CREATE VIRTUAL TABLE search USING fts5(id UNINDEXED,name,body,tokenize='unicode61');")
        records=[('a','Steam engine','a.json',1800,'Engine summary'),('b','Ship','b.json',1801,'A ship'),('c','Steamship','c.json',1802,'A steamship')]
        con.executemany('INSERT INTO discoveries VALUES (?,?,?,?,?)',records)
        con.executemany('INSERT INTO search VALUES (?,?,?)',[('a','Steam engine','engine powered by steam'),('b','Ship','steam powered ship'),('c','Steamship','a steamship')])
        self.assertEqual([r['id'] for r in research.search(con,'steam')],['a','b'])
        self.assertEqual([r['id'] for r in research.search(con,'steam engine')],['a'])
        self.assertEqual([r['id'] for r in research.search(con,'steam',limit=1)],['a'])
        self.assertEqual(research.search(con,'nonexistent'),[])
        con.close()

    def test_indexes_are_used(self):
        for sql, index in [('SELECT src FROM edges WHERE dst=? AND status=? AND layer=?', 'edges_in'), ('SELECT dst FROM edges WHERE src=? AND status=? AND layer=?','edges_out')]:
            plan = ' '.join(str(tuple(row)) for row in self.con.execute('EXPLAIN QUERY PLAN '+sql, ('x','established','dependence')))
            self.assertIn(index, plan)

    def test_freshness_checks_rebuild_changed_inputs(self):
        path = Path(self.temp.name) / 'fresh.sqlite'
        research.rebuild(path)
        with closing(research.connect(path)) as con:
            self.assertEqual(dict(con.execute('SELECT key,value FROM metadata'))['fingerprint'], research.fingerprint())
        with patch('research.signature', return_value={'changed': [1, 2]}), patch('research.rebuild', side_effect=RuntimeError('rebuild needed')):
            with self.assertRaisesRegex(RuntimeError, 'rebuild needed'):
                research.connect(path)
        with patch('research.fingerprint', return_value='changed bytes'), patch('research.rebuild', side_effect=RuntimeError('verified rebuild needed')):
            with self.assertRaisesRegex(RuntimeError, 'verified rebuild needed'):
                research.connect(path, verify=True)


if __name__ == '__main__':
    unittest.main()
