"""Integrity checks for the frozen comparison; no model/network calls."""
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('comparison', ROOT/'tools/cards/prepare_comparison.py')
comparison = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(comparison)
OUT = ROOT/'docs/reviews/2026-11-10-workflow-comparison'

class ComparisonTest(unittest.TestCase):
    def setUp(self):
        self.raw = (OUT/'cases.json').read_bytes()
        self.cases = json.loads(self.raw)['cases']
        self.registration = json.loads((OUT/'preregistration.json').read_text())

    def test_registration_integrity_and_fixed_splits(self):
        comparison.validate(self.cases)
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), self.registration['cases_sha256'])
        self.assertEqual(sorted(c['id'] for c in self.cases), self.registration['candidate_ids'])
        expected = {c['id']:c['split'] for c in self.cases}
        shuffled = [dict(c) for c in reversed(self.cases)]
        comparison.split_cases(shuffled)
        self.assertEqual(expected, {c['id']:c['split'] for c in shuffled})

    def test_evidence_integrity_and_excerpt_budget(self):
        words = collections.Counter()
        for case in self.cases:
            self.assertEqual(case['dataset_snapshot'], self.registration['dataset_snapshot'])
            for evidence in case['evidence']:
                words[evidence['url']] += len(evidence['text'].split())
                self.assertEqual(comparison.sha(evidence['text']), evidence['text_sha256'])
                # Public checkouts may lack the deliberately private original pages.
                path = Path(evidence['context']['private_path'])
                if path.exists():
                    raw = path.read_bytes()
                    self.assertEqual(comparison.sha(raw), evidence['sha256'])
                    text = raw.decode('utf-8','replace')
                    ctx = evidence['context']
                    self.assertTrue(0 <= ctx['start'] <= ctx['end'] <= len(text))
                    self.assertLessEqual(ctx['end']-ctx['start'],3200)
                    if evidence['quotation_status']=='exact_substring' and evidence['text']:
                        # Public excerpts collapse whitespace; originals remain intact.
                        self.assertIn(' '.join(evidence['text'].split()), ' '.join(text.split()))
        self.assertTrue(all(count<=200 for count in words.values()))

    def test_real_failures_and_scope_controls(self):
        controls = [c for c in self.cases if c['stratum']=='duplicate_extension']
        self.assertTrue(all(any(m['basis']=='exact_retained_card_name' for m in c['screen']['matches']) for c in controls))
        for case in self.cases:
            self.assertNotIn('reference_truth',case)
            contexts = case['screen']['match_context']
            self.assertEqual({m['id'] for m in case['screen']['matches']}, {m['id'] for m in contexts})
            self.assertTrue(all('name' in m and 'events' in m for m in contexts))
            if case['stratum']=='retrieval_failures':
                self.assertTrue(case['access_failure']['retained_note'])
                self.assertFalse(case['evidence'])

    def test_normalized_quote_navigation(self):
        offset,status = comparison.quote_offset('Prefix: Olivé\n and fig trees.', 'Olive and fig trees')
        self.assertEqual(offset,8)
        self.assertEqual(status,'normalized_substring')
        self.assertEqual(comparison.quote_offset('text',''),(-1,'no_retained_quotation'))

if __name__=='__main__':
    unittest.main()
