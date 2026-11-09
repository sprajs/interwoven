"""Tests for the machine-readable catalogue coverage audit."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import coverage  # noqa: E402
from tests.test_dataset import FixtureDataset, discovery  # noqa: E402


class CoverageAuditTest(unittest.TestCase):
    def setUp(self):
        first = discovery("first")
        first["fields"] = ["energy.steam", "food.crops", "food.crops"]
        first["grain"] = "capability"
        first["places"].append({"place": "elsewhere"})
        first["links"] = [
            {"status": "candidate", "carrier": ["text"], "contribution": []},
            {"status": "established", "contribution": ["method"]},
        ]
        first["research"]["basis"]["funding"] = "unknown"
        second = discovery("second")
        second.pop("places")
        second["earliest_record"] = {"event": None}
        places = [
            {"id": "testtown", "region": "europe"},
            {"id": "elsewhere", "region": "asia"},
        ]
        self.data = FixtureDataset.make([first, second], places)
        self.result = coverage.audit(self.data)

    def test_fields_domains_and_grain_count_each_record_once(self):
        a = self.result
        self.assertEqual(a["schema_version"], 1)
        self.assertEqual(a["fields"]["energy.steam"]["records"], 2)
        self.assertEqual(a["fields"]["food.crops"]["records"], 1)
        self.assertEqual(a["domains"]["energy"]["records"], 2)
        self.assertEqual(a["domains"]["food"]["grain"]["capability"], 1)
        self.assertEqual(a["overall"]["grain"]["unassessed"], 1)
        self.assertEqual(a["fields"]["food.fishing"]["records"], 0)

    def test_unplaced_undated_and_overlap(self):
        overall = self.result["overall"]
        self.assertEqual(overall["regions"]["europe"], 1)
        self.assertEqual(overall["regions"]["asia"], 1)
        self.assertEqual(overall["regions"]["unplaced"], 1)
        self.assertEqual(overall["eras"]["to 1800"], 1)
        self.assertEqual(overall["eras"]["undated"], 1)

    def test_era_uses_latest_evidence_endpoint(self):
        self.data.discoveries["first"]["events"][0]["date"]["earliest"] = {"year": 1700}
        self.data.discoveries["first"]["events"][0]["date"]["latest"] = {"year": 1900}
        eras = coverage.audit(self.data)["overall"]["eras"]
        self.assertEqual(eras["to 1800"], 0)
        self.assertEqual(eras["to 1950"], 1)

    def test_lead_statuses_are_grouped_by_explicit_field_or_unclassified(self):
        self.data.registers["leads"] = {
            "one": {"id": "one", "title": "One", "status": "open", "field": "food.crops"},
            "two": {"id": "two", "title": "Two", "status": "insufficient", "field": "food.crops"},
            "three": {"id": "three", "title": "Three", "status": "open"},
        }
        result = coverage.audit(self.data)
        self.assertEqual(result["counts"]["leads"], 3)
        self.assertEqual(result["leads"]["fields"]["food.crops"]["total"], 2)
        self.assertEqual(result["leads"]["fields"]["food.crops"]["status"]["insufficient"], 1)
        self.assertEqual(result["leads"]["unclassified"]["total"], 1)
        self.assertEqual(result["leads"]["unclassified"]["status"]["open"], 1)
        self.assertFalse(any("leads/three" in problem for problem in self.data.validate(check_files=False)))

    def test_lead_field_must_reference_taxonomy(self):
        self.data.registers["leads"] = {"bad": {"id": "bad", "title": "Bad", "status": "open", "field": "made.up"}}
        problems = self.data.validate(check_files=False)
        self.assertTrue(any("'made.up' is not in fields" in problem for problem in problems), problems)

    def test_missing_basis_differs_from_unknown_and_link_coverage(self):
        self.assertEqual(self.result["facet_basis"]["funding"]["unknown"], 1)
        self.assertEqual(self.result["facet_basis"]["funding"]["missing"], 1)
        self.assertEqual(self.result["links"]["status"]["candidate"], 1)
        self.assertEqual(self.result["links"]["status"]["established"], 1)
        self.assertEqual(self.result["links"]["carrier"], {"present": 1, "missing": 1})
        self.assertEqual(self.result["links"]["contribution"], {"present": 1, "missing": 1})

    def test_cli_emits_json_and_existing_text_report_remains_text(self):
        script = str(Path(coverage.__file__))
        output = subprocess.check_output([sys.executable, script, "--json"], text=True)
        self.assertEqual(json.loads(output)["schema_version"], 1)
        output = subprocess.check_output([sys.executable, script], text=True)
        self.assertIn("facet", output)
        self.assertIn("missing", output)


if __name__ == "__main__":
    unittest.main()
