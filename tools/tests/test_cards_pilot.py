"""Portable pilot selection and blinded judgment checks; no provider calls."""
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/cards'))
spec=importlib.util.spec_from_file_location('pilot_workflow',ROOT/'tools/cards/pilot_workflow.py')
pilot=importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)

class PilotTest(unittest.TestCase):
    def test_preselected_confirmation_disjoint_repeatable_and_stratified(self):
        strata = ('ordinary', 'archaeology', 'contested', 'regional', 'duplicate')
        cases = {
            f'case-{group}-{n}': {'id': f'case-{group}-{n}', 'split': 'held_out', 'stratum': group}
            for group in strata for n in range(5)
        }
        cases[pilot.DIAG[0]] = {'id': pilot.DIAG[0], 'split': 'held_out', 'stratum': strata[0]}
        cases['calibration'] = {'id': 'calibration', 'split': 'calibration', 'stratum': strata[0]}
        first = pilot.confirmation(cases)
        self.assertEqual(first, pilot.confirmation(dict(reversed(list(cases.items())))))
        self.assertEqual(len(first), 12)
        self.assertEqual(len(set(first)), 12)
        self.assertTrue(set(first).isdisjoint(pilot.DIAG))
        self.assertTrue(all(cases[x]['split'] == 'held_out' for x in first))
        counts = [sum(cases[x]['stratum'] == group for x in first) for group in strata]
        self.assertLessEqual(max(counts) - min(counts), 1)

    def test_blind_judge_rejects_duplicate_labels_and_boolean_indices(self):
        case = {'id': 'synthetic-case', 'candidate': {'name': 'Synthetic'},
                'dataset_snapshot': 'synthetic', 'screen': {}, 'evidence': [],
                'source_access_status': 'missing'}
        final = {'decision': 'admit_minimal', 'claims': [{'facet': 'achievement'}]}

        class FakeExecutor:
            def __init__(self, malformed):
                self.malformed = malformed

            def call(self, _job, _model, _effort, payload):
                labels = [v['label'] for v in payload['variants']]
                if self.malformed == 'duplicate':
                    labels[1] = labels[0]
                index = True if self.malformed == 'bool_index' else 0
                return {'parsed': {'case_id': case['id'], 'reference_decision': 'admit_minimal',
                    'variants': [{'label': label, 'false_reject': False,
                                  'source_flagged_admission': False,
                                  'claims': [{'index': index, 'verdict': 'supported'}]}
                                 for label in labels]}}

        with mock.patch.object(pilot, 'variant', return_value=final):
            for malformed in ('duplicate', 'bool_index'):
                with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                    pilot.judge(case, ['a', 'b'], FakeExecutor(malformed))
