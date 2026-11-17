"""Reconcile the research ledger against reviewed bytes from real Git objects."""

import csv
from hashlib import sha256
from io import StringIO
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

from dataset import write_json
from prehistory_wave import WAVE, check_connections, compile_wave, coverage_svg, html_fragment, markdown, typed_changes


class PrehistoryWaveTest(unittest.TestCase):
    def test_projection_excludes_unreviewed_edits_and_gates_candidate_promotion(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("prehistory_wave.ROOT", root):
                self.exercise_fixture(root)

    def exercise_fixture(self, root):
        def git(*args):
            return subprocess.check_output(["git", "-C", root, *args], stderr=subprocess.PIPE).decode().strip()

        def discovery(key, links=None, events=None):
            write_json(root / f"data/discoveries/food/{key}.json", {"id": key, "name": key.upper(), "events": events or [],
                                                                 "links": links or []})

        def commit():
            git("add", ".")
            git("-c", "user.email=test@example.com", "-c", "user.name=Test", "commit", "-qm", "snapshot")
            return git("rev-parse", "HEAD")

        git("init", "-q")
        roles = {"dependence": ["uses_process"], "transmission": [], "affinity": ["companion_of"]}
        write_json(root / "data/vocab.json", {"link": {"layers": roles}})
        write_json(root / "data/sources/a/article.json", {"id": "article", "title": "Title", "url": "https://example.com/"})
        old_candidate = {"from": "older", "type": "uses_process", "status": "candidate", "to_event": "dated",
                         "evidence": [{"source": "article", "locator": "p. 2"}]}
        discovery("older")
        discovery("alpha", [old_candidate])
        discovery("beta", [old_candidate], [{"id": "duplicate-event"}])
        discovery("outside")
        base = commit()

        discovery("alpha", [{**old_candidate, "status": "established"}])
        discovery("beta", [old_candidate, {"from": "outside", "type": "companion_of", "status": "established"}])
        discovery("new", [{"from": "alpha", "type": "uses_process", "status": "candidate"}], [{"id": "new-event"}])
        # Another thread added an established edge to beta. Its file is absent from this wave's manifest.
        discovery("outside", [{"from": "beta", "type": "uses_process", "status": "established"}])
        lane_dir, review_dir = root / WAVE / "lanes", root / WAVE / "reviews"
        first = {"from": "older", "to": "alpha", "type": "uses_process", "decision": "new-established"}
        retained = {"from": "older", "to": "beta", "type": "uses_process", "decision": "existing-candidate"}
        affinity = {"from": "outside", "to": "beta", "type": "companion_of", "decision": "new-established"}
        proposed = {"from": "alpha", "to": "new", "type": "uses_process", "decision": "new-candidate"}

        def assessment(key, connections):
            return {"id": key, "outcome": "established", "finding": "A literal </script> marker.", "next": "Named follow-up",
                    "sources": [{"url": "https://example.com/", "locator": "p. 2"}], "connections": connections}

        lane = {"lane": "test", "base": base, "researcher": "gpt-6.2-sol", "effort": "high",
                "records": [assessment("alpha", [first, proposed]), assessment("beta", [retained, affinity])]}
        write_json(lane_dir / "test.json", lane)
        reviewed = [f"{WAVE}/lanes/test.json", *[f"data/discoveries/food/{key}.json" for key in ("alpha", "beta", "new")]]
        refs = {path: "SHA256:" + sha256((root / path).read_bytes()).hexdigest().upper() for path in reviewed}
        after = commit()
        review = {"lane": "test", "base_commit": base, "overall_decision": "accept", "worker_commit": after,
                  "reviewer": {"model": "gpt-6.1-terra", "effort": "high"}, "files": refs,
                  "records": [{"id": key, "verdict": "accept", "rationale": "Checked."} for key in ("alpha", "beta")],
                  "additional_records": [{"id": "new", "verdict": "accept"}]}
        write_json(review_dir / "test.json", review)
        roster = {"test": ["alpha", "beta"]}
        frontier = StringIO()
        writer = csv.writer(frontier)
        writer.writerow(["id", "era", "established_connectivity", "record_path", "primary_region", "primary_domain",
                         "earliest_record_date_label"])
        for key in roster["test"]:
            writer.writerow([key, "before 3000 BCE", "isolated", f"data/discoveries/food/{key}.json", "asia", "food", "4000 BCE"])

        result = compile_wave(base, after, roster, frontier.getvalue(), lane_dir, review_dir)
        self.assertEqual(result["summary"]["newly_reached"], 1)
        self.assertEqual(result["records"][0]["after"], {"incoming_dependence": 1})
        self.assertEqual(result["records"][1]["after"], {})
        self.assertEqual(len(result["changed_edges"]), 3)
        self.assertEqual(len(result["retained_candidates"]), 1)
        self.assertEqual([record["id"] for record in result["new_discoveries"]], ["new"])
        changed = next(edge for edge in result["changed_edges"] if edge["to"] == "alpha")
        self.assertEqual((changed["before"], changed["after"], changed["to_event"]), ("candidate", "established", "dated"))
        self.assertEqual(result["sources"]["article"]["title"], "Title")
        self.assertEqual(result["removed_events_on_existing_records"], [{"discovery": "beta", "event": {"id": "duplicate-event"}}])
        self.assertEqual(result["net_events"], 0)
        self.assertIn("1 distinct directed relationship in those layers and 1 relationship in other layers", markdown(result))
        self.assertEqual(ElementTree.fromstring(coverage_svg(result)).tag, "{http://www.w3.org/2000/svg}svg")
        fragment = html_fragment(result)
        self.assertIn(r"\u003c/script> marker", fragment)
        self.assertNotIn("literal </script>", fragment)

        # A different integrated byte sequence cannot reuse the old review.
        discovery("alpha")
        with self.assertRaisesRegex(ValueError, "differs from accepted bytes"):
            compile_wave(base, commit(), roster, frontier.getvalue(), lane_dir, review_dir)

        # A reminder about the wrong graph direction cannot stand in for an admitted edge.
        lane["records"][0]["connections"][0] = {**first, "from": "alpha", "to": "older"}
        write_json(lane_dir / "test.json", lane)
        refs[str((lane_dir / "test.json").relative_to(root))] = sha256((lane_dir / "test.json").read_bytes()).hexdigest()
        write_json(review_dir / "test.json", review)
        discovery("alpha", [{**old_candidate, "status": "established"}])
        with self.assertRaisesRegex(ValueError, "disagrees with graph snapshots"):
            compile_wave(base, commit(), roster, frontier.getvalue(), lane_dir, review_dir)

    def test_replacing_event_scope_does_not_add_a_distinct_directed_type(self):
        triple = ("one", "two", "uses_process")
        before = {(*triple, "", ""): {"status": "established"}}
        after = {(*triple, "", "new-event"): {"status": "established"}}
        self.assertEqual(typed_changes(before, after), [])
        mention = {"from": "one", "to": "two", "type": "uses_process", "decision": "existing-established"}
        resolved, keys = check_connections([mention], before, after)
        self.assertEqual(keys, set(after))
        self.assertEqual(resolved[0]["edges"][0]["to_event"], "new-event")


if __name__ == "__main__":
    unittest.main()
