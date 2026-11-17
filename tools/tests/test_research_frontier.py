"""Checks for record-level frontier filters and their audit totals."""

import csv
from collections import Counter
import io
import json
import unittest

from dataset import DATA, Dataset
from research_frontier import FIELDS, frontier_rows, write_csv
from tech_tree_gaps import measure
from tests.test_dataset import FixtureDataset, discovery, event


class ResearchFrontierTest(unittest.TestCase):
    def test_directions_regions_question_pointers_and_prerequisite_states(self):
        outside = discovery("outside")
        outside.pop("places")
        outside["earliest_record"] = {"event": None}
        origin = discovery("origin")
        middle = discovery("middle")
        receiver = discovery("receiver")
        origin["places"] = [{"place": "testtown"}, {"place": "elsewhere"}]
        middle["places"] = [{"place": "testtown"}, {"place": "elsewhere", "role": "origin"}]
        middle["events"] = [event("made", 1700, 1850)]
        middle["events"][0]["date"]["status"] = "bounded"
        middle["research"]["unresolved"] = [{"about": "date", "note": "Still uncertain."}]
        middle["research"]["missing_prerequisites"] = ["A lead, with punctuation."]
        middle["links"] = [{"type": "transmitted_from", "status": "established", "from": "origin"}]
        receiver["research"]["missing_prerequisites"] = []
        receiver["links"] = [
            {"type": "uses_process", "status": "established", "from": "middle"},
            {"type": "same_family", "status": "established", "from": "outside"},
            {"type": "transmitted_from", "status": "candidate", "from": "outside"},
            {"type": "requires", "status": "insufficient", "from": "origin"},
        ]
        data = FixtureDataset.make([outside, middle, receiver, origin], [
            {"id": "testtown", "region": "europe"}, {"id": "elsewhere", "region": "asia"},
        ])
        result = frontier_rows(data, DATA)
        self.assertEqual([r["id"] for r in result], ["receiver", "origin", "middle", "outside"])
        rows = {r["id"]: r for r in result}
        self.assertEqual({key: row["established_connectivity"] for key, row in rows.items()}, {
            "outside": "isolated", "origin": "outgoing_only", "middle": "incoming_and_outgoing",
            "receiver": "incoming_only",
        })
        self.assertEqual(rows["outside"]["primary_region"], "unplaced")
        self.assertEqual(rows["outside"]["era"], "undated")
        self.assertEqual(rows["origin"]["primary_region"], "multiple")
        self.assertEqual(rows["middle"]["primary_region"], "asia")
        self.assertEqual(json.loads(rows["middle"]["regions"]), ["asia", "europe"])
        self.assertEqual(rows["middle"]["era"], "to 1950")
        self.assertEqual(rows["middle"]["incoming_established_transmission"], 1)
        self.assertEqual(rows["middle"]["outgoing_established_dependence"], 1)
        self.assertEqual(rows["origin"]["insufficient_links"], 1)
        candidate = json.loads(rows["outside"]["candidate_link_pointers"])[0]
        self.assertEqual(candidate, {
            "direction": "outgoing", "type": "transmitted_from", "other_id": "receiver",
            "pointer": "data/discoveries/energy/receiver.json#/links/2",
        })
        middle_path = rows["middle"]["record_path"]
        self.assertEqual(json.loads(rows["middle"]["uncertainty_pointers"]), [
            f"{middle_path}#/research/unresolved/0", f"{middle_path}#/events/0/date",
        ])
        self.assertEqual({key: row["missing_prerequisites_state"] for key, row in rows.items()}, {
            "outside": "absent", "origin": "absent", "middle": "listed", "receiver": "empty",
        })

        output = io.StringIO(newline="")
        write_csv(result, output)
        output.seek(0)
        reader = csv.DictReader(output)
        parsed = {row["id"]: row for row in reader}
        self.assertEqual(reader.fieldnames, list(FIELDS))
        self.assertEqual(json.loads(parsed["middle"]["missing_prerequisites"]), ["A lead, with punctuation."])

    def test_current_catalogue_reconciles_to_coverage_audit(self):
        data = Dataset.load()
        rows = frontier_rows(data, DATA)
        audit = measure(data, "working dataset")
        self.assertEqual(len(rows), audit["overall"]["total"])
        self.assertEqual({row["id"] for row in rows}, set(data.discoveries))
        by_era = Counter(row["era"] for row in rows)
        by_region = Counter(region for row in rows for region in json.loads(row["regions"]))
        by_domain = Counter(data.domains[row["primary_domain"]]["name"] for row in rows)
        for actual, group in [(by_era, "eras"), (by_region, "regions"), (by_domain, "domains")]:
            self.assertEqual(dict(actual), {key: count["total"] for key, count in audit[group].items() if count["total"]})
        connectivity = Counter(row["established_connectivity"] for row in rows)
        self.assertEqual(connectivity["isolated"], audit["overall"]["without_link"])
        self.assertEqual(connectivity["isolated"] + connectivity["outgoing_only"], audit["overall"]["without_incoming"])
        for layer in ("dependence", "transmission"):
            for direction in ("incoming", "outgoing"):
                self.assertEqual(sum(row[f"{direction}_established_{layer}"] for row in rows),
                                 audit["established_layers"][layer]["links"])
        for status in ("candidate", "insufficient"):
            self.assertEqual(sum(row[f"{status}_links"] for row in rows), 2 * audit["link_status"][status])
        prerequisite_states = Counter(row["missing_prerequisites_state"] for row in rows)
        prerequisites = audit["missing_prerequisites"]
        self.assertEqual(prerequisite_states, Counter({
            "listed": prerequisites["count"], "absent": prerequisites["absent"], "empty": prerequisites["empty"],
        }))


if __name__ == "__main__":
    unittest.main()
