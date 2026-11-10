import json
import tempfile
import unittest
from pathlib import Path

from research_efficiency_audit import parse_claude, parse_codex


class UsageAccountingTests(unittest.TestCase):
    def test_codex_counts_response_deltas_once_and_separates_descendants(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'session.jsonl'
            usage = dict(input_tokens=100, cached_input_tokens=80, output_tokens=10,
                         reasoning_output_tokens=4)
            events = [
                dict(type='session_meta', payload=dict(id='child', cwd='/tmp/big_idea',
                     source=dict(subagent=dict(thread_spawn=dict(parent_thread_id='root', agent_path='/root/research'))))),
                dict(type='turn_context', payload=dict(model='model', effort='low')),
                dict(type='token_usage_record', payload=dict(response_id='a', usage=usage)),
                dict(type='token_usage_record', payload=dict(response_id='a', usage=usage)),
                dict(type='event_msg', payload=dict(type='token_count', info=dict(total_token_usage=dict(input_tokens=9999)))),
            ]
            path.write_text('\n'.join(json.dumps(dict(timestamp='2026-11-09T21:00:00Z', **event)) for event in events))
            calls, _, _, signals, _ = parse_codex([path], 'root', '2026-11-09', '2026-11-10')
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0]['input_tokens'], 100)
            self.assertEqual(calls[0]['output_tokens'], 10)
            self.assertEqual(calls[0]['scope'], 'campaign')
            self.assertEqual(signals['duplicate_usage_records_skipped'], 1)

    def test_claude_repeated_blocks_are_one_response_with_disjoint_input_classes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'agent.jsonl'
            row = dict(type='assistant', timestamp='2026-11-09T21:00:00Z', requestId='request',
                       message=dict(id='message', model='model', content=[], usage=dict(
                           input_tokens=2, cache_creation_input_tokens=20,
                           cache_read_input_tokens=80, output_tokens=10)))
            later = json.loads(json.dumps(row))
            later['message']['usage']['output_tokens'] = 12
            outside = dict(row, timestamp='2026-11-10T21:00:00Z', requestId='outside')
            path.write_text('\n'.join(json.dumps(r) for r in (row, row, later, outside)))
            calls, _, _, signals, _ = parse_claude([path], '2026-11-09', '2026-11-10')
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0]['input_tokens'], 102)
            self.assertEqual(calls[0]['cached_input_tokens'], 80)
            self.assertEqual(calls[0]['cache_write_input_tokens'], 20)
            self.assertEqual(calls[0]['output_tokens'], 12)
            self.assertEqual(signals['repeated_assistant_content_blocks'], 2)
