"""The published view keeps observed metrics while excluding private source text."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'cards/quality_sweep_view.py'
SPEC = importlib.util.spec_from_file_location('quality_sweep_view', SCRIPT)
VIEW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VIEW)


class QualitySweepViewTests(unittest.TestCase):
    def test_private_context_excluded_and_unknown_judge_remains_unknown(self):
        row = {'id': 'c1', 'title': 'Source <script> title', 'group': 'fresh',
               'variant': 'terra_high', 'model': 'gpt-6.1-terra', 'effort': 'high',
               'decision': 'admit_minimal', 'mechanical_pass': True,
               'judges': {'astra_medium': {'source_flagged_admission': False,
                                           'false_reject': False, 'useful_record': True,
                                           'claim_verdicts': ['supported'],
                                           'private_explanation': 'PRIVATE SOURCE TEXT'},
                          'sol_high': None},
               'review_api_usd': 0.01, 'review_seconds': 12,
               'original_context': 'PRIVATE SOURCE TEXT'}
        with tempfile.TemporaryDirectory() as directory:
            results = Path(directory) / 'results.json'
            output = Path(directory) / 'view.html'
            results.write_text(json.dumps({'cases': [row], 'limitations': []}))
            VIEW.render(results, output)
            markup = output.read_text()
            self.assertNotIn('PRIVATE SOURCE TEXT', markup)
            self.assertIn('Source \\u003cscript\\u003e title', markup)
            self.assertIn('"sol_high":null', markup)


if __name__ == '__main__':
    unittest.main()
