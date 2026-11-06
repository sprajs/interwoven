import importlib.util
from pathlib import Path
from copy import deepcopy
from contextlib import redirect_stdout, redirect_stderr
import io
import json
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("query", Path(__file__).parents[1] / "tools/query.py")
query = importlib.util.module_from_spec(spec)
spec.loader.exec_module(query)


def chosen(node_id="tool", basis="commercial_availability", strength="direct", interpretation="known_by"):
    node = {"id": node_id, "label": node_id, "kind": "technology", "event_ids": [node_id + "-entry"],
        "lifecycle": {"first_commercial_availability": {"status": "unknown", "rationale": "First sale remains unresolved."}},
        "commercial_applicability": {"status": "applicable"},
        "graph_anchor": {"status": "selected", "policy": "community_entry", "event_id": node_id + "-entry",
            "entry_basis": basis, "evidence_strength": strength, "date_interpretation": interpretation,
            "community": "Named local specialist community", "scope": {}, "evidence": [],
            "rationale": "A deliberate choice.", "uncertainty": "No broader uptake is asserted."}}
    event = {"id": node_id + "-entry", "node_id": node_id, "event_type": "commercial_offer",
        "date": {"status": "known", "precision": "year", "calendar": "historical-BCE-CE", "label": "1910",
            "basis": "A dated offer.", "earliest": {"year": 1910}, "latest": {"year": 1910}}}
    return node, event


class QueryTests(unittest.TestCase):
    def test_commercial_question_is_independent_of_display_anchor(self):
        def node(node_id, kind, status, anchor):
            return {"id": node_id, "kind": kind, "lifecycle": {"first_commercial_availability": {"status": status}}, "graph_anchor": {"status": anchor}}
        rows = [node("state-vessel", "technology", "unknown", "selected"), node("product", "technology", "documented", "selected"),
            node("unresearched", "technology", "not_yet_researched", "not_yet_researched"), node("discovery", "science", "not_applicable", "selected")]
        self.assertEqual([row["id"] for row in query.unresolved_commercial(rows)], ["state-vessel", "unresearched"])

    def test_known_by_offer_remains_a_bound_and_does_not_change_first_unknown(self):
        node, event = chosen()
        before = deepcopy((node, event))
        result = query.community_entries([node], {event["id"]: event})[0]
        self.assertEqual("By 1910", result["entry_date"]["label"])
        self.assertEqual({"year": 1910}, result["entry_date"]["latest"])
        self.assertNotIn("earliest", result["entry_date"])
        self.assertEqual("unknown", result["entry_date"]["earliest_status"])
        self.assertEqual([node], query.unresolved_commercial([node]))
        self.assertEqual(before, (node, event))

    def test_event_date_on_a_one_sided_event_still_exposes_a_bound(self):
        node, event = chosen(interpretation="event_date")
        event["date"].update(status="bounded", earliest_status="unknown", label="The source supports one limit.")
        del event["date"]["earliest"]
        result = query.entry_date(node["graph_anchor"], event)
        self.assertEqual("By 1910", result["label"])
        self.assertNotIn("earliest", result)
        self.assertEqual("unknown", result["earliest_status"])
        event["date"]["earliest_status"] = "not_yet_researched"
        node["graph_anchor"]["date_interpretation"] = "known_by"
        self.assertEqual("not_yet_researched", query.entry_date(node["graph_anchor"], event)["earliest_status"])

    def test_known_from_exposes_no_synthetic_upper_limit(self):
        node, event = chosen(interpretation="known_from")
        result = query.entry_date(node["graph_anchor"], event)
        self.assertEqual("Not before 1910", result["label"])
        self.assertNotIn("latest", result)
        self.assertEqual("unknown", result["latest_status"])

    def test_entry_filters_expose_community_and_proxy_status(self):
        direct, used = chosen("local-tool", "practical_use", interpretation="event_date")
        proxy, published = chosen("science", "public_awareness", "awareness_proxy", "event_date")
        proxy["kind"] = "science"
        proxy["graph_anchor"]["community"] = "Readers of the named scientific journal"
        proxy["graph_anchor"]["proxy_justification"] = "Publication proves a public awareness opportunity, not adoption."
        published["event_type"] = "publication"
        events = {event["id"]: event for event in (used, published)}
        self.assertEqual(["science"], [row["id"] for row in query.community_entries([direct, proxy], events, strength="awareness_proxy")])
        self.assertEqual(["local-tool"], [row["id"] for row in query.community_entries([direct, proxy], events, community="local specialist")])
        self.assertEqual([], query.community_entries([direct, proxy], events, basis="adoption"))

    def test_invalid_selected_references_are_reported_without_earliest_event_fallback(self):
        node, event = chosen()
        for invalid in ({}, {event["id"]: dict(event, node_id="different-owner")}):
            with self.subTest(events=invalid):
                result = query.community_entries([node], invalid)[0]
                self.assertIn("anchor_error", result)
                self.assertNotIn("entry_date", result)
        self.assertEqual([], query.unresolved_commercial([None, {}, {"kind": []}]))

    def test_cli_traversal_keeps_disconnected_and_reversed_display_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            left, le = chosen("left")
            right, re = chosen("right")
            le["date"].update(earliest={"year": 1990}, latest={"year": 1990})
            re["date"].update(earliest={"year": 1950}, latest={"year": 1950})
            self.assertGreater(query.entry_date(left["graph_anchor"], le)["latest"]["year"], query.entry_date(right["graph_anchor"], re)["latest"]["year"])
            left["review"] = right["review"] = {"historical_claim": "accepted"}
            edge = {"id": "connection", "from": {"node_id": "left"}, "to": {"node_id": "right"}, "review": {"historical_claim": "accepted"}}
            rows = {"nodes": [left, right], "events": [le, re], "relationships": [edge], "sources": []}
            for name, values in rows.items():
                (root / "data" / (name + ".jsonl")).write_text("".join(json.dumps(value) + "\n" for value in values))
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(0, query.main(["--root", directory, "traverse", "left", "--depth", "0"]))
            self.assertEqual(["left"], [node["id"] for node in json.loads(output.getvalue())["nodes"]])
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(0, query.main(["--root", directory, "traverse", "right"]))
            self.assertEqual(1, len(json.loads(output.getvalue())["relationships"]))
            (root / "data/nodes.jsonl").write_text('{"id":"duplicate","id":"key"}\n')
            with redirect_stderr(io.StringIO()) as errors, self.assertRaises(SystemExit) as error:
                query.main(["--root", directory, "stats"])
            self.assertEqual(2, error.exception.code)
            self.assertIn("duplicate JSON key", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
