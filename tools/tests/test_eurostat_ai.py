"""Eurostat AI extracts preserve disjoint survey populations and raw observations."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from dataset import Dataset
from import_eurostat_ai import extract


class EurostatAiTests(unittest.TestCase):
    def setUp(self):
        self.data = Dataset.load()
        self.data.discoveries = {}
        self.data.registers['leads'] = {}
        self.ent = self.data.eurostat_ai_panels['eurostat-ai-enterprise-pilot']
        self.ind = self.data.eurostat_ai_panels['eurostat-ai-individual-pilot']

    def problems(self, files=False):
        return self.data.validate(check_files=files)

    def test_saved_selections_reproduce_exact_source(self):
        self.assertEqual([], self.problems(True))
        self.assertEqual(len(self.ent['observations']), 48)
        self.assertEqual(len(self.ind['observations']), 4)
        self.assertNotEqual(self.ent['denominator'], self.ind['denominator'])
        for panel in (self.ent, self.ind):
            release = panel['release']
            self.assertEqual(panel['observations'], extract(Path(release['raw_path']), panel['dataset'], release['sha256']))

    def test_duplicate_wrong_unit_range_and_malformed_dates(self):
        self.ent['observations'].append(copy.deepcopy(self.ent['observations'][0]))
        self.ent['observations'][1]['dimensions']['unit'] = 'PC_IND'
        self.ent['observations'][2]['value'] = 101
        self.ent['release']['retrieved'] = '2026-02-30'
        self.ent['release']['updated'] = '2026-01-01'
        errors = '\n'.join(self.problems())
        for expected in ['duplicate dimension key', 'PC_IND', 'above 100', 'invalid retrieval date', 'invalid update timestamp']:
            self.assertIn(expected, errors)

    def test_missing_cannot_become_zero_and_query_hash_checked(self):
        row = self.ind['observations'][0]
        row['value'], row['status'], row['flag'] = 0, 'missing', 'u'
        self.ind['release']['sha256'] = '0' * 64
        errors = '\n'.join(self.problems())
        self.assertIn('value and missing status disagree', errors)
        self.assertIn('release query, path and hash must match source', errors)

    def test_population_and_reference_window_cannot_be_cross_labelled(self):
        self.ent['definition'] = self.ind['definition']
        self.ent['denominator'] = self.ind['denominator']
        self.ent['reference_window'] = self.ind['reference_window']
        errors = '\n'.join(self.problems())
        for key in ('definition', 'denominator', 'reference_window'):
            self.assertIn('.' + key + ':', errors)

    def test_query_must_match_dataset_and_selected_dimensions(self):
        from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
        for bad in ('unit', 'geo', 'dataset'):
            panel = self.data.eurostat_ai_panels['eurostat-ai-enterprise-pilot']
            original = panel['release']['query_url']
            parts = urlsplit(original)
            params = parse_qsl(parts.query)
            if bad == 'dataset':
                parts = parts._replace(path=parts.path.replace('isoc_eb_ai', 'isoc_ai_iaiu'))
            else:
                params = [(k, ('PC_IND' if bad == 'unit' else 'ZZ') if k == bad else v) for k, v in params]
            changed = urlunsplit(parts._replace(query=urlencode(params)))
            panel['release']['query_url'] = changed
            source = self.data.sources[panel['release']['source']]
            source['url'] = changed
            self.assertTrue(any('query dimensions do not match' in e for e in self.problems()), bad)
            panel['release']['query_url'] = original
            source['url'] = original

    def test_malformed_panel_containers_report_errors(self):
        for malformed in (None, [], {'dataset': []}):
            self.data.eurostat_ai_panels['bad'] = malformed
            self.assertTrue(self.problems())

    def test_importer_rejects_boolean_category_indices_and_reordered_dimensions(self):
        release = self.ind['release']
        original = json.loads(Path(release['raw_path']).read_bytes())
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'sample.json'
            for mode in ('boolean', 'order'):
                raw = copy.deepcopy(original)
                if mode == 'boolean':
                    raw['dimension']['geo']['category']['index']['DK'] = True
                else:
                    raw['id'][0], raw['id'][1] = raw['id'][1], raw['id'][0]
                content = json.dumps(raw).encode()
                path.write_bytes(content)
                with self.assertRaises(ValueError, msg=mode):
                    extract(path, 'isoc_ai_iaiu', hashlib.sha256(content).hexdigest())

    def test_importer_preserves_sparse_missing_flags_and_hash(self):
        release = self.ind['release']
        raw = json.loads(Path(release['raw_path']).read_bytes())
        raw['value'].pop('0')
        raw['value']['1'] = 0
        raw['status'] = {'0': 'u', '1': 'b'}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'sample.json'
            content = json.dumps(raw).encode()
            path.write_bytes(content)
            digest = hashlib.sha256(content).hexdigest()
            rows = extract(path, 'isoc_ai_iaiu', digest)
            self.assertEqual((None, 'missing', 'u'), (rows[0]['value'], rows[0]['status'], rows[0]['flag']))
            self.assertEqual((0, 'reported', 'b'), (rows[1]['value'], rows[1]['status'], rows[1]['flag']))
            with self.assertRaises(ValueError):
                extract(path, 'isoc_ai_iaiu', '0' * 64)
            with self.assertRaises(ValueError):
                extract(path, 'isoc_eb_ai', digest)
