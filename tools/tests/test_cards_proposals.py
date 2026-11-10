"""Proposal comparison keeps equal inputs and does not admit suggestions."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cards'))
import compare_proposals


class ProposalComparison(unittest.TestCase):
    def test_same_inventory_and_presets_with_pending_duplicate_screening(self):
        class FakeExecutor:
            calls = []
            def __init__(self, *args, **kwargs):
                self.kwargs = kwargs
            def call(self, job, model, effort, payload):
                self.calls.append((job, model, effort, json.dumps(payload, sort_keys=True)))
                return {'fingerprint': job, 'parsed': {'proposals': [
                    {'name': 'Pending achievement'}, {'name': 'New hypothesis'}]}}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inventory = root / 'inventory.json'
            inventory.write_text(json.dumps({'names': ['Recorded achievement'],
                'pending_candidate_names': ['Pending achievement'], 'field_counts': {}}))
            with patch.object(compare_proposals, 'Executor', FakeExecutor):
                output = json.loads(compare_proposals.run(root, inventory).read_text())
            self.assertEqual(len({c[3] for c in FakeExecutor.calls}), 1)
            self.assertEqual([(c[1], c[2]) for c in FakeExecutor.calls], [
                ('gpt-6.1-sol', 'medium'), ('gpt-6-astra', 'low'), ('gpt-6-astra', 'medium')])
            self.assertEqual(output['admitted_to_comparison'], 0)
            self.assertFalse(output['opportunity_budget']['equal_realized_spend'])
            self.assertTrue(output['models'][0]['proposals'][0]['exact_inventory_duplicate'])
            self.assertFalse(output['models'][0]['proposals'][1]['exact_inventory_duplicate'])
