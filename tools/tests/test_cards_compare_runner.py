"""Mocked provider: meaningful accounting, immutable resume and guard contracts."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cards'))
from compare import Executor, Runner, MODELS, REFERENCE, api_cost, encoded, load_cases, mechanical, usage_records, tool_observations, audit_saved_calls, sha


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.sessions = self.root / 'sessions'
        self.runner = Runner(self.root / 'private', sessions=self.sessions)
        self.quote = 'This original source records eight meaningful words about construction methods.'
        self.case = dict(id='case-one', split='calibration', evidence=[dict(id='s1', original_context=self.quote)])
        self.answer = dict(id='case-one', decision='admit_minimal', claims=[dict(facet='achievement', statement='A bounded claim', source_id='s1', quote=self.quote, earliest_year=None, latest_year=None, uncertainty='')], rationale='Source supports it', unresolved=[])
        self.usage = dict(input_tokens=1000, cached_input_tokens=400, cache_write_input_tokens=100, output_tokens=200, reasoning_output_tokens=150)
        self.log = self.sessions / '2026/11/10/rollout-test-thread.jsonl'
        self.log.parent.mkdir(parents=True)
        self.log.write_text('\n'.join(encoded(x) for x in [
            dict(type='response_item', payload=dict(text='PRIVATE HIDDEN REASONING')),
            dict(type='event_msg', payload=dict(type='token_count', total_token_usage=dict(input_tokens=999999))),
            dict(type='token_usage_record', payload=dict(response_id='r1', usage=self.usage, thread_token_usage=dict(input_tokens=888888))),
            dict(type='token_usage_record', payload=dict(response_id='r1', usage=self.usage))]))

    def process(self, failed=False):
        answer = self.answer
        class Process:
            returncode = 1 if failed else 0
            def communicate(self, prompt=None, timeout=None):
                return '\n'.join(encoded(x) for x in [
                    dict(type='thread.started', thread_id='test-thread'),
                    dict(type='item.completed', item=dict(type='reasoning', text='PRIVATE HIDDEN REASONING')),
                    dict(type='item.completed', item=dict(type='agent_message', text=encoded(answer))),
                    dict(type='turn.failed' if failed else 'turn.completed', usage=dict(input_tokens=777777))]), ''
        return Process()

    def test_usage_unique_no_cumulative_no_reasoning_sum(self):
        records = usage_records(self.log)
        self.assertEqual(list(records), ['r1'])
        self.assertEqual(records['r1']['input_tokens'], 1000)
        expected = (500*.10 + 400*.01 + 100*.125 + 200*.50) / 1_000_000
        self.assertAlmostEqual(api_cost('gpt-6-luna', records['r1']), expected)
        self.assertGreater(api_cost('gpt-6-luna', records['r1'], 2), expected)

    def test_immutable_resume_and_no_hidden_reasoning_export(self):
        with patch('compare.subprocess.Popen', return_value=self.process()) as proc:
            first = self.runner.call(self.case, 'reference', 'gpt-6-astra', 'medium')
            second = Runner(self.runner.state, sessions=self.sessions).call(self.case, 'reference', 'gpt-6-astra', 'medium')
            self.assertEqual(first, second)
            self.assertEqual(proc.call_count, 1)
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                self.runner.call({**self.case, 'changed': True}, 'reference', 'gpt-6-astra', 'medium')
        saved = (self.runner.state / 'calls/case-one-reference.json').read_text()
        self.assertNotIn('PRIVATE HIDDEN REASONING', saved)
        self.assertIsNone(first['observed_billing'])
        for setting in ('web_search="disabled"', 'features.shell_tool=false', 'project_doc_max_bytes=0'):
            self.assertIn(setting, first['params']['command'])
        self.assertNotIn('--ephemeral', first['params']['command'])
        self.assertFalse(any('model_providers.openai' in value for value in first['params']['command']))
        self.assertIn('not disabled', first['params']['builtin_transport_retries'])

    def test_response_dedup_and_aggregate_guard(self):
        with patch('compare.subprocess.Popen', return_value=self.process()):
            self.runner.call(self.case, 'reference', 'gpt-6-astra', 'medium')
            self.runner.call(self.case, 'A-extract', 'gpt-6-luna', 'low')
        with self.runner.ledger() as ledger:
            self.assertEqual(ledger['requests'], 2)
            self.assertEqual(self.runner.totals(ledger)['input'], 1000)
            self.assertEqual(self.runner.totals(ledger)['output'], 200)
        guarded = Runner(self.runner.state, sessions=self.sessions, limits=dict(input=1000))
        with patch('compare.subprocess.Popen') as proc:
            with self.assertRaisesRegex(RuntimeError, 'budget'):
                guarded.call(self.case, 'B-extract', 'gpt-6.1-terra', 'low')
            proc.assert_not_called()

    def test_failure_stops_dispatch_and_never_retries(self):
        with patch('compare.subprocess.Popen', return_value=self.process(True)) as proc:
            with self.assertRaisesRegex(RuntimeError, 'failed request'):
                self.runner.call(self.case, 'reference', 'gpt-6-astra', 'medium')
            with self.assertRaisesRegex(RuntimeError, 'cannot retry'):
                self.runner.call(self.case, 'reference', 'gpt-6-astra', 'medium')
            with self.assertRaisesRegex(RuntimeError, 'stopped'):
                self.runner.call(self.case, 'other', 'gpt-6-luna', 'low')
            self.assertEqual(proc.call_count, 1)

    def test_inflight_crash_not_replayed(self):
        with patch('compare.subprocess.Popen', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.call(self.case, 'reference', 'gpt-6-astra', 'medium')
        with patch('compare.subprocess.Popen') as proc:
            with self.assertRaisesRegex(RuntimeError, 'inflight'):
                self.runner.call(self.case, 'reference', 'gpt-6-astra', 'medium')
            proc.assert_not_called()

    def test_mechanical_refs_whole_quotes_required_fields_years(self):
        self.assertTrue(mechanical(self.answer, self.case)['pass'])
        bad = copy.deepcopy(self.answer)
        bad['claims'][0].update(quote='Only four matching words', earliest_year=1900, latest_year=1800)
        self.assertEqual(len(mechanical(bad, self.case, review=True)['errors']), 3)
        for year in (0, True):
            bad = copy.deepcopy(self.answer)
            bad['claims'][0]['earliest_year'] = year
            self.assertFalse(mechanical(bad, self.case)['pass'])
        bad = copy.deepcopy(self.answer)
        del bad['claims'][0]['latest_year']
        self.assertFalse(mechanical(bad, self.case)['pass'])

    def test_arms_require_blinded_reference(self):
        with patch.object(self.runner, 'call') as call:
            with self.assertRaisesRegex(ValueError, 'reference first'):
                self.runner.run([self.case], 'arms')
            call.assert_not_called()

    def test_tool_observation_names_counts_only_and_deduplicates(self):
        rows = [dict(type='response_item', payload=dict(type='function_call', name='web_search', call_id='c1', arguments='PRIVATE INPUT')),
                dict(type='response_item', payload=dict(type='function_call', name='web_search', call_id='c1', arguments='PRIVATE INPUT')),
                dict(type='response_item', payload=dict(type='custom_tool_call_output', name='web_search', output='PRIVATE OUTPUT'))]
        observations = tool_observations(rows, 'test')
        self.assertEqual(observations, [dict(name='web_search', count=1, source='test')])
        self.assertNotIn('PRIVATE', encoded(observations))

    def test_unexpected_rollout_tool_stops_runner(self):
        with self.log.open('a') as stream:
            stream.write('\n' + encoded(dict(type='response_item', payload=dict(type='function_call', name='shell', call_id='call-1', arguments='PRIVATE INPUT'))))
        with patch('compare.subprocess.Popen', return_value=self.process()):
            with self.assertRaisesRegex(RuntimeError, 'failed request'):
                self.runner.call(self.case, 'reference', 'gpt-6-astra', 'medium')
        saved = json.loads((self.runner.state / 'calls/case-one-reference.json').read_text())
        self.assertEqual(saved['observed_tool_calls'][0]['name'], 'shell')
        self.assertIsNone(saved['provider_reported_tool_search_usage'])
        self.assertNotIn('PRIVATE INPUT', encoded(saved))
        with self.runner.ledger() as ledger:
            self.assertIn('Unexpected tool', ledger['stopped']['reason'])

    def test_backfill_is_separate_and_does_not_modify_immutable_calls(self):
        with patch('compare.subprocess.Popen', return_value=self.process()):
            self.runner.call(self.case, 'reference', 'gpt-6-astra', 'medium')
        path = self.runner.state / 'calls/case-one-reference.json'
        before = path.read_bytes()
        # Simulate a historical call lacking the newly added observation fields.
        old = json.loads(before)
        del old['observed_tool_calls']
        path.write_text(encoded(old))
        before = path.read_bytes()
        report = audit_saved_calls(self.runner.state, self.sessions)
        self.assertTrue(report['calls'][0]['tool_free'])
        self.assertEqual(report['calls'][0]['call_sha256'], sha(before))
        self.assertEqual(path.read_bytes(), before)
        with self.log.open('a') as stream:
            stream.write('\n' + encoded(dict(type='response_item', payload=dict(type='web_search_call', id='s1', arguments='PRIVATE QUERY'))))
        updated = audit_saved_calls(self.runner.state, self.sessions)
        self.assertTrue(updated['unexpected_tool_use'])
        self.assertNotIn('PRIVATE QUERY', encoded(updated))
        self.assertEqual(path.read_bytes(), before)

    def test_prompt_freeze_canonical_survives_json_roundtrip(self):
        # Model presets contain tuples in Python and lists after JSON loading.
        freeze = dict(models=MODELS, reference=REFERENCE, instruction_sha256='frozen')
        self.assertEqual(encoded(freeze), encoded(json.loads(encoded(freeze))))

    def test_executor_custom_schema_and_fixture_requires100(self):
        executor = Executor(self.root / 'executor', sessions=self.sessions)
        with patch('compare.subprocess.Popen', return_value=self.process()):
            result = executor.call('adjudication-one', 'gpt-6-astra', 'low', dict(output_schema=dict(result='custom')))
        self.assertIn('output_schema', result['prompt'])
        fixture = self.root / 'cases.json'
        fixture.write_text(encoded(dict(cases=[dict(id='one')]*100)))
        with self.assertRaisesRegex(ValueError, '100 unique'):
            load_cases(fixture)


if __name__ == '__main__':
    unittest.main()
