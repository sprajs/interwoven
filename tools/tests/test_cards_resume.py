"""Restoration retains old successes without dispatch or semantic acceptance."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cards'))
import resume_retained


class RetainedResume(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source.txt'
        self.source.write_text('preserved source')
        self.card = self.root / 'cards.json'
        self.card.write_text('{"cards":[{"name":"Example"}]}')
        self.manifest = self.root / 'resume-manifest.json'
        self.manifest.write_text(json.dumps({'candidates': [{
            'candidate_id': 'candidate-example', 'retained_title': 'Example',
            'source_snapshots': [{'path': 'source.txt', 'sha256': hashlib.sha256(self.source.read_bytes()).hexdigest()}],
            'artifacts': [{'path': 'cards.json', 'stage': 'extraction', 'card_index': 0,
                           'sha256': hashlib.sha256(self.card.read_bytes()).hexdigest()}]}]}))

    def restore(self):
        queue = MagicMock()
        queue.enqueue.return_value = 'stable-queue-id'
        with patch.object(resume_retained, 'Queue', return_value=queue), patch.object(
                resume_retained, 'committed_snapshot', return_value={'commit': 'frozen', 'data_hash': 'hash'}):
            rows = resume_retained.restore(self.manifest, self.root / 'queue.sqlite', self.root)
        return queue, rows

    def test_imports_only_retained_stages_and_never_dispatches(self):
        queue, rows = self.restore()
        self.assertEqual(rows[0]['adopted'], ['acquire', 'extract'])
        self.assertEqual([c.args[1] for c in queue.adopt_artifact.call_args_list], ['acquire', 'extract'])
        queue.claim.assert_not_called()
        queue.screen.assert_not_called()
        self.assertIn('review', rows[0]['next_required'])

    def test_missing_source_keeps_pending_instead_of_relabeling_success(self):
        self.source.unlink()
        queue, rows = self.restore()
        queue.adopt_artifact.assert_not_called()
        queue.defer_pending.assert_called_once()
        self.assertEqual(rows[0]['adopted'], [])
        self.assertIn('source', rows[0]['reason'])

    def test_changed_source_stops_before_adoption(self):
        self.source.write_text('changed source')
        with self.assertRaisesRegex(ValueError, 'source changed'):
            self.restore()
