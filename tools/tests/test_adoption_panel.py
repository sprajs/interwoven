"""Tests for a small source-preserving reference extract."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from dataset import DATA, Dataset, read_json
from import_chat_telephone import extract


class AdoptionPanelTests(unittest.TestCase):
    def setUp(self):
        self.panel = read_json(DATA / 'reference/adoption/chat-telephone-pilot.json')
        self.data = Dataset.load()
        self.data.discoveries = {}
        self.data.registers['leads'] = {}
        self.data.adoption_panels = {'chat-telephone-pilot': self.panel}

    def errors(self):
        return self.data.validate(check_files=False)

    def test_pilot_valid_and_missing_is_not_zero(self):
        self.assertEqual([], self.errors())
        row = next(r for r in self.panel['observations'] if r['country'] == 'Kenya' and r['year_token'] == '2000')
        self.assertEqual(('', None, 'missing'), (row['raw_value'], row['value'], row['status']))
        row['value'] = 0
        self.assertTrue(any('raw token' in e for e in self.errors()))

    def test_duplicate_invalid_dangling_and_denominator_rejected(self):
        self.panel['observations'].append(copy.deepcopy(self.panel['observations'][0]))
        self.panel['observations'][1]['raw_value'] = '-2'
        self.panel['release']['source'] = 'nonexistent-source'
        self.panel['indicator']['denominator'] = 'population'
        errors = '\n'.join(self.errors())
        for expected in ['duplicate country and year', 'invalid raw telephone', 'not in sources', "unknown key 'denominator'"]:
            self.assertIn(expected, errors)

    def test_wrong_indicator_and_unit_are_rejected(self):
        self.panel['indicator']['id'] = 'computer'
        self.panel['indicator']['unit'] = 'people'
        errors = '\n'.join(self.errors())
        self.assertIn("'computer' is not one of", errors)
        self.assertIn("'people' is not one of", errors)

    def test_malformed_containers_report_errors(self):
        for malformed in (None, [], 'not a panel'):
            self.data.adoption_panels['chat-telephone-pilot'] = malformed
            self.assertTrue(self.errors())
        self.data.adoption_panels['chat-telephone-pilot'] = self.panel
        for observations in (None, {}, ['not a row'], [{'country': [], 'year_token': {}}]):
            self.panel['observations'] = observations
            self.assertTrue(self.errors())

    def test_invalid_numeric_tokens_are_rejected(self):
        for token in ('NaN', 'Infinity', '-1', '1.5'):
            self.panel['observations'][0]['raw_value'] = token
            self.assertTrue(any('invalid raw telephone' in e for e in self.errors()), token)

    def test_importer_preserves_scientific_notation_blank_and_locations(self):
        raw = b'country_name,year,telephone\nA,1980,1.80E+08\nB,2000,\n'
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'data.csv'
            path.write_bytes(raw)
            digest = hashlib.sha256(raw).hexdigest()
            result = extract(path, [('A', '1980'), ('B', '2000')], digest)
            self.assertEqual((180000000, '1.80E+08', 2), (result[0]['value'], result[0]['raw_value'], result[0]['row']))
            self.assertEqual((None, 'missing', 3), (result[1]['value'], result[1]['status'], result[1]['row']))
            with self.assertRaises(ValueError):
                extract(path, [('A', '1980')], '0' * 64)
            with self.assertRaises(ValueError):
                extract(path, [('C', '2000')], digest)
            with self.assertRaises(ValueError):
                extract(path, [('A', '1980'), ('A', '1980')], digest)
