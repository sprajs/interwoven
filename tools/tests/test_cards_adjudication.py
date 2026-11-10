"""Offline blind-adjudication masking, schema and coverage tests."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cards'))
import adjudicate_comparison as adjudicate


def case(case_id='case-1', split='calibration'):
    return {'id': case_id, 'split': split, 'candidate': {'name': 'Local workshop engine'},
            'dataset_snapshot': 'frozen', 'screen': {'matched_records': []},
            'evidence': [{'id': 'source', 'original_context': 'The workshop made its own engine in 1800.'}],
            'source_access_status': 'saved_evidence', 'provenance': {'private_path': '/must/not/leak'},
            'reference': {'decision': 'SECRET_REFERENCE_ANSWER'}}


def answer():
    return {'decision': 'admit_minimal', 'claims': [{'facet': 'achievement', 'statement': 'A local workshop made an engine.'}],
            'rationale': 'Scoped achievement.', 'unresolved': [], 'corrections': []}


def inputs():
    return {arm: {'extract': answer(), 'review': answer()} for arm in ('A', 'B')}


def judgment(case_id='case-1'):
    return {'case_id': case_id, 'reference': {'resolved': True, 'reference_admit': True,
             'decision': 'admit_minimal', 'notes': 'Original source supports local achievement.'},
            'variants': [{'label': label, 'false_admission': False, 'false_reject': False,
                          'useful_reviewed_record': True, 'substantive_corrections': 0,
                          'claims': [{'index': 0, 'verdict': 'supported', 'error_types': [],
                                      'rationale': 'Supported by the original passage.'}],
                          'notes': 'The bounded source claim is supported.'} for label in ('X', 'Y')]}


class AdjudicationTest(unittest.TestCase):
    def setUp(self):
        self.mapping = adjudicate.label_map('case-1', 'seed')
        self.payload = adjudicate.build_payload(case(), inputs(), self.mapping)

    def test_masking_omits_reference_answers_models_arms_and_private_paths(self):
        answers = inputs()
        answers['A']['extract'].update(model='gpt-6-luna', arm='A', usage={'tokens': 10})
        answers['A']['review']['rationale'] = 'Arm A: gpt-6.1-terra from A-extract; Terra.'
        encoded = json.dumps(adjudicate.build_payload(case(), answers, self.mapping))
        for forbidden in ('SECRET_REFERENCE_ANSWER', '/must/not/leak', 'gpt-6-luna', 'gpt-6.1-terra', 'A-extract', 'Arm A'):
            self.assertNotIn(forbidden, encoded)
        self.assertIn('original_context', encoded)
        self.assertIn('output_schema', self.payload)

    def test_sha_mapping_is_deterministic_and_balanced_over_cases(self):
        self.assertEqual(self.mapping, adjudicate.label_map('case-1', 'seed'))
        self.assertEqual(set(self.mapping), {'X', 'Y'})
        self.assertEqual(set(self.mapping.values()), {'A', 'B'})
        self.assertEqual({adjudicate.label_map(str(i), 'seed')['X'] for i in range(50)}, {'A', 'B'})

    def test_complete_output_normalizes_to_explicit_model_only_metrics(self):
        rows = adjudicate.normalize(case(), judgment(), self.mapping, self.payload)
        self.assertEqual({row['arm'] for row in rows}, {'A', 'B'})
        for row in rows:
            self.assertEqual(row['supported_claims'], 1)
            self.assertEqual(row['unresolved_admitted_claims'], 0)
            self.assertEqual(row['unsupported_facets'], 0)
            self.assertEqual(row['substantive_corrections'], 0)
            self.assertEqual(len(row['claim_judgments']), 1)

    def test_missing_boolean_or_counter_never_defaults_to_false(self):
        for key in ('false_admission', 'false_reject', 'useful_reviewed_record', 'substantive_corrections'):
            value = judgment()
            del value['variants'][0][key]
            with self.subTest(field=key), self.assertRaises(ValueError):
                adjudicate.validate_judgment(value, 'case-1', self.payload)
        value = judgment()
        del value['reference']['resolved']
        with self.assertRaises(ValueError):
            adjudicate.validate_judgment(value, 'case-1', self.payload)

    def test_exact_claim_indices_reject_missing_duplicate_extra_and_boolean(self):
        for indices in ([], [0, 0], [0, 1], [True], [-1]):
            value = judgment()
            value['variants'][0]['claims'] = [dict(value['variants'][0]['claims'][0], index=index) for index in indices]
            with self.subTest(indices=indices), self.assertRaises(ValueError):
                adjudicate.validate_judgment(value, 'case-1', self.payload)

    def test_two_unique_variants_and_valid_claim_errors_required(self):
        value = judgment()
        value['variants'][1]['label'] = 'X'
        with self.assertRaises(ValueError):
            adjudicate.validate_judgment(value, 'case-1', self.payload)
        value = judgment()
        value['variants'][0]['claims'][0]['error_types'] = ['unknown']
        with self.assertRaises(ValueError):
            adjudicate.validate_judgment(value, 'case-1', self.payload)

    def test_unresolved_admission_is_counted_without_historical_rejection(self):
        value = judgment()
        value['reference'] = {'resolved': False, 'reference_admit': False, 'decision': 'defer_source', 'notes': 'Missing source context.'}
        value['variants'][0]['claims'][0].update(verdict='unresolved', error_types=['date'], rationale='Publication date cannot date the invention.')
        value['variants'][0]['useful_reviewed_record'] = False
        row = next(row for row in adjudicate.normalize(case(), value, self.mapping, self.payload) if row['arm'] == self.mapping['X'])
        self.assertFalse(row['resolved'])
        self.assertFalse(row['false_reject'])
        self.assertEqual(row['unresolved_admitted_claims'], 1)
        self.assertEqual(row['unresolved_source_access'], 1)
        self.assertEqual(row['date_errors'], 1)

    def test_unsupported_admission_cannot_hide_behind_agreement(self):
        value = judgment()
        for variant in value['variants']:
            variant['claims'][0].update(verdict='unsupported', error_types=['scope'])
        with self.assertRaises(ValueError):
            adjudicate.validate_judgment(value, 'case-1', self.payload)
        for variant in value['variants']:
            variant.update(false_admission=True, useful_reviewed_record=False)
        rows = adjudicate.normalize(case(), value, self.mapping, self.payload)
        self.assertEqual(sum(row['unsupported_facets'] for row in rows), 2)

    def test_preflight_requires_every_reference_before_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            cases = [case(), case('case-2')]
            (state / 'calls').mkdir()
            (state / 'calls/case-1-reference.json').write_text(json.dumps({'status': 'success', 'parsed': {'secret': 'do not use'}}))
            executor = Mock()
            with self.assertRaisesRegex(ValueError, 'all 100'):
                adjudicate.run(cases, state, executor=executor)
            executor.call.assert_not_called()

    def test_fake_executor_produces_private_mapping_and_model_only_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            calls = state / 'calls'
            calls.mkdir()
            (calls / 'case-1-reference.json').write_text(json.dumps({'status': 'success', 'parsed': {'secret': 'never show reference'}}))
            for arm in ('A', 'B'):
                for stage in ('extract', 'review'):
                    (calls / f'case-1-{arm}-{stage}.json').write_text(json.dumps({'status': 'success', 'parsed': answer()}))
            executor = Mock()
            executor.call.return_value = {'status': 'success', 'parsed': judgment()}
            result = adjudicate.run([case()], state, executor=executor, workers=1, seed='seed')
            self.assertEqual(result['reference_standard'], 'model_only')
            self.assertIs(result['adequate_independent_reference'], False)
            self.assertEqual(len(result['judgments']), 2)
            self.assertTrue((state / 'adjudication-blinding.json').exists())
            args = executor.call.call_args.args
            self.assertEqual(args[1:3], ('gpt-6-astra', 'low'))
            self.assertNotIn('never show reference', json.dumps(args[3]))
            with self.assertRaisesRegex(ValueError, 'seed'):
                adjudicate.run([case()], state, executor=executor, workers=1, seed='changed')

    def test_service_failure_stops_dispatch_without_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            calls = state / 'calls'
            calls.mkdir()
            cases = [case('case-' + str(i)) for i in range(1, 4)]
            for fixture in cases:
                for label in ('reference', 'A-extract', 'A-review', 'B-extract', 'B-review'):
                    (calls / f"{fixture['id']}-{label}.json").write_text(json.dumps({'status': 'success', 'parsed': answer()}))
            executor = Mock()
            executor.call.side_effect = RuntimeError('service exhausted')
            with self.assertRaisesRegex(RuntimeError, 'service exhausted'):
                adjudicate.run(cases, state, executor=executor, workers=1)
            self.assertEqual(executor.call.call_count, 1)

    def test_wrong_schema_has_one_versioned_repair_and_no_retry_loop(self):
        for valid_repair in (True, False):
            with self.subTest(valid_repair=valid_repair), tempfile.TemporaryDirectory() as tmp:
                state = Path(tmp)
                calls = state / 'calls'
                calls.mkdir()
                for label in ('reference', 'A-extract', 'A-review', 'B-extract', 'B-review'):
                    (calls / ('case-1-' + label + '.json')).write_text(json.dumps({'status': 'success', 'parsed': answer()}))
                original, repair = Mock(), Mock()
                original.call.return_value = {'status': 'success', 'parsed': answer(), 'fingerprint': 'original-unchanged'}
                repair.call.return_value = {'status': 'success', 'parsed': judgment() if valid_repair else answer(), 'fingerprint': 'repair'}
                with patch.object(adjudicate.compare, 'Executor', return_value=repair):
                    if valid_repair:
                        result = adjudicate.run([case()], state, executor=original, workers=1)
                        self.assertEqual(len(result['judgments']), 2)
                    else:
                        with self.assertRaisesRegex(ValueError, 'case ID'):
                            adjudicate.run([case()], state, executor=original, workers=1)
                self.assertEqual(original.call.call_count, 1)
                self.assertEqual(repair.call.call_count, 1)
                note = json.loads((state / 'schema-repairs/case-1.json').read_text())
                self.assertEqual(note['repair_limit'], 1)
                self.assertEqual(note['original_fingerprint'], 'original-unchanged')


if __name__ == '__main__':
    unittest.main()
