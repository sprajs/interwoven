"""Verify the worksheet and reader against accepted bytes in Git snapshots."""

from contextlib import redirect_stdout
from hashlib import sha256
from io import StringIO
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from dataset import write_json
from provenance import ARTIFACTS, ROUND, WORKFLOWS, main, reviewed_case, worksheet


class ProvenanceTest(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.enterContext(patch("provenance.ROOT", self.root))
        self.git("init", "-q")
        self.datafile = "data/discoveries/measurement/fixture.json"
        write_json(self.root / self.datafile, {"historical": "baseline"})
        base = self.commit()

        for lane in ARTIFACTS + WORKFLOWS:
            kind = "workflow" if lane in WORKFLOWS else "artifact"
            data = {
                "lane": lane, "kind": kind, "title": f"{lane.title()} </script> test", "question": "Pilot question",
                "summary": "Pilot summary", "decision": "Pilot decision", "next": "Pilot next test",
                "steps": [{"title": "Pilot-specific step title", "action": "Find the agency's final report.",
                           "result": "Distinct result in the pilot", "sources": [
                               {"title": "Pilot original", "url": "https://example.com/pilot", "locator": "p. 11"},
                           ]}], "researcher": "gpt-6.2-sol", "effort": "high", "base": base,
            }
            if kind == "workflow":
                data.update(inputs=["Project and organization"], reject_if="version or date differs.",
                            stop_when="the specified archive search is exhausted.", next_anchor="Another project")
            write_json(self.root / self.ledger_path(lane), data)
        write_json(self.root / self.datafile, {"historical": "accepted"})
        self.proposal = self.commit()
        self.receipts = {}
        for lane in ARTIFACTS + WORKFLOWS:
            paths = [self.ledger_path(lane), self.datafile]
            self.receipts[lane] = {
                "lane": lane, "base_commit": base, "overall_decision": "accept", "worker_commit": self.proposal,
                "reviewer": {"model": "gpt-6.1-terra", "effort": "high"},
                "claim_reviews": {"claim": {"rationale": "Checked in the original."}},
                "files": [{"path": path, "sha256": sha256((self.root / path).read_bytes()).hexdigest()} for path in paths],
            }
            self.write_receipt(lane)
        self.accepted = self.commit()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", self.root, *args], stderr=subprocess.PIPE).decode().strip()

    def commit(self):
        self.git("add", ".")
        self.git("-c", "user.email=test@example.com", "-c", "user.name=Test", "commit", "-qm", "fixture")
        return self.git("rev-parse", "HEAD")

    def ledger_path(self, lane):
        return f"{ROUND}/lanes/{lane}.json"

    def write_receipt(self, lane):
        write_json(self.root / ROUND / "reviews" / f"{lane}.json", self.receipts[lane])

    def run_cli(self, *args):
        stream = StringIO()
        with patch("sys.argv", ["provenance.py", *map(str, args)]), redirect_stdout(stream):
            main()
        return stream.getvalue()

    def test_cli_distinguishes_worksheet_actions_from_pilot_evidence(self):
        listed = self.run_cli("list")
        self.assertEqual([row.split("\t")[0] for row in listed.splitlines()], list(WORKFLOWS))
        steps = self.run_cli("show", "metrology")
        self.assertIn("Find the agency's final report", steps)
        self.assertNotIn("Pilot decision", steps)
        blank = self.run_cli("start", "metrology", "--subject", "A fresh subject")
        self.assertIn("A fresh subject", blank)
        self.assertIn("Antecedent or sender", blank)
        self.assertIn("Independent corroborating source lineage", blank)
        for pilot_only in ("Pilot-specific step title", "Distinct result in the pilot", "https://example.com/pilot", "p. 11"):
            self.assertNotIn(pilot_only, blank)

    def test_reader_binds_historical_bytes_and_survives_later_catalogue_edits(self):
        write_json(self.root / self.datafile, {"historical": "extended after review"})
        later = self.commit()
        self.assertIn("A later subject", self.run_cli("start", "rail", "--subject", "A later subject"))
        case = reviewed_case(later, "steam", verify_history=True)
        self.assertEqual(case["review"]["verified_commit"], self.proposal)
        path = self.root / "out"
        self.run_cli("render", "--output", path)
        fragment = (path / "provenance-reader.html").read_text()
        self.assertTrue(fragment.startswith('<div id="provenance-source-reader">'))
        self.assertIn(r"\u003c/script> test", fragment)
        self.assertIn("https://example.com/pilot", fragment)
        self.assertIn("<html lang=", (path / "view.html").read_text())

    def test_fresh_clone_can_verify_against_a_pinned_integration_revision(self):
        self.receipts["rail"]["worker_commit"] = "1" * 40
        self.write_receipt("rail")
        write_json(self.root / self.datafile, {"historical": "extended after review"})
        later = self.commit()
        self.assertEqual(reviewed_case(later, "rail")["lane"], "rail")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            reviewed_case(later, "rail", verify_history=True)
        case = reviewed_case(later, "rail", verify_history=True, historical=self.accepted)
        self.assertEqual(case["review"]["verified_commit"], self.accepted)

    def test_stale_or_unaccepted_receipt_does_not_generate_a_worksheet(self):
        ledger = self.root / self.ledger_path("rail")
        ledger.write_text(ledger.read_text().replace("Pilot decision", "Changed decision"))
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            reviewed_case(self.commit(), "rail")
        self.receipts["rail"]["overall_decision"] = "changes_requested"
        self.write_receipt("rail")
        with self.assertRaisesRegex(ValueError, "no accepted independent review"):
            reviewed_case(self.commit(), "rail")
        self.assertIn("&lt;tag&gt;", worksheet(reviewed_case(self.accepted, "rail"), "<tag>"))


if __name__ == "__main__":
    unittest.main()
