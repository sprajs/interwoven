"""Source-scoped checks for the 1950 housing census table extract."""
import copy
import unittest
from dataset import DATA, Dataset, read_json


class CensusRefrigerationTests(unittest.TestCase):
    def setUp(self):
        self.panel = read_json(DATA / 'reference/census/us-1950-mechanical-refrigeration.json')
        self.data = Dataset.load()
        self.data.discoveries = {}
        self.data.registers['leads'] = {}
        self.data.adoption_panels = {}
        self.data.eurostat_ai_panels = {}
        self.data.census_refrigeration_panels = {'us-1950-mechanical-refrigeration': self.panel}

    def errors(self):
        return '\n'.join(self.data.validate(check_files=False))

    def test_published_estimates_and_rounding(self):
        self.assertEqual('', self.errors())
        row = self.panel['observations'][0]
        self.assertEqual((33720250, 42059850, 80.2), (row['numerator'], row['denominator'], row['percent']))
        row['percent'] = 80.3
        row['percent_token'] = '80.3'
        self.assertIn('inconsistent with counts', self.errors())

    def test_missing_is_not_zero(self):
        row = self.panel['observations'][1]
        row['status'] = 'missing'
        for key in ('numerator', 'denominator', 'percent', 'numerator_token', 'denominator_token', 'percent_token'):
            row[key] = None
        self.assertEqual('', self.errors())
        row['numerator'] = 0
        self.assertIn('missing values and tokens must all be null', self.errors())

    def test_duplicate_and_bad_denominator(self):
        self.panel['observations'].append(copy.deepcopy(self.panel['observations'][0]))
        row = self.panel['observations'][1]
        row['denominator'], row['denominator_token'] = 0, '0'
        self.assertIn('duplicate residence', self.errors())
        self.assertIn('denominator or percentage bounds', self.errors())
        row['denominator'], row['denominator_token'] = -1, '-1'
        self.assertIn('invalid count or percentage token', self.errors())

    def test_provenance_and_source_integrity(self):
        self.panel['source'] = 'no-such-source'
        self.panel['geography_source'] = 'no-such-source'
        self.panel['source_sha256'] = '0' * 64
        self.panel['source_accessed'] = '2026-02-30'
        self.assertIn('not in sources', self.errors())
        self.assertIn('not one of', self.errors())
        self.assertIn('invalid access date', self.errors())

    def test_malformed_and_token_mismatches(self):
        for val in (None, [], 'bad'):
            self.data.census_refrigeration_panels['us-1950-mechanical-refrigeration'] = val
            self.assertTrue(self.errors())
        self.data.census_refrigeration_panels['us-1950-mechanical-refrigeration'] = self.panel
        self.panel['observations'][0]['numerator'] = 0
        self.assertIn('values must match source tokens', self.errors())
        self.panel['observations'][0]['numerator'] = float('nan')
        self.assertTrue(self.errors())

    def test_scope_is_fixed(self):
        self.panel['denominator'] = 'all individuals'
        self.panel['geography'] = 'current USA'
        self.panel['reference_date'] = '1950-04-31'
        self.panel['locator'] = 'table 13'
        self.assertGreaterEqual(self.errors().count('not one of'), 4)


if __name__ == '__main__':
    unittest.main()
