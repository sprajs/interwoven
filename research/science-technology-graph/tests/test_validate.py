"""Regression tests for graph semantics, independent of the research dataset."""
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("graph_validate", ROOT / "tools" / "validate.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def evidence(source_id="source-1"):
    return {"source_id": source_id, "locator": "fixture, p. 1", "supports": "Synthetic historical claim."}


def review():
    return {"historical_claim": "accepted", "lifecycle_classification": "needs_review", "records": []}


def provenance():
    return {"method": "source-evidence", "source_ids": ["source-1"], "note": "Synthetic source evidence."}


def historical_date(year=1900):
    return {"status": "known", "precision": "year", "calendar": "historical-BCE-CE", "label": str(year),
            "basis": "Synthetic year supplied by a fixture.", "earliest": {"year": year}, "latest": {"year": year}}


def event(event_id="event-1", node_id="node-1", event_type="invention", year=1900):
    return {"schema_version": 1, "id": event_id, "node_id": node_id, "event_type": event_type,
            "date": historical_date(year), "scope": {"regions": ["Fixture region"], "configuration": "Fixture apparatus",
            "applications": ["Fixture application"], "market": {"status": "unknown"}, "population": {"status": "unknown"}},
            "statement": "A synthetic scoped event occurred.", "evidence": [evidence()], "uncertainty": "Fixture only.",
            "review": review()}


def node(events, node_id="node-1", kind="technology"):
    lifecycle = {stage: {"status": "not_yet_researched", "event_ids": [], "rationale": "Not researched in this fixture.",
                        "evidence": []} for stage in validator.LIFECYCLE}
    for record in events:
        if record["event_type"] in lifecycle:
            entry = lifecycle[record["event_type"]]
            entry.update(status="documented", rationale="This event is documented by the fixture.", evidence=[evidence()])
            entry["event_ids"].append(record["id"])
    return {"schema_version": 1, "id": node_id, "label": "Synthetic apparatus", "kind": kind,
            "configuration": "Fixture apparatus", "regions": ["Fixture region"], "event_ids": [e["id"] for e in events],
            "lifecycle": lifecycle, "commercial_applicability": {"status": "not_applicable" if kind == "science" else "applicable",
            "rationale": "Scientific claim." if kind == "science" else "A possible commercial apparatus.", "evidence": []},
            "graph_anchor": {"status": "not_yet_researched", "policy": "scientific_event" if kind == "science" else "first_commercial_availability",
            "rationale": "No anchor has been researched."}, "review": review(), "provenance": provenance(), "uncertainty": "Fixture only."}


def source():
    return {"schema_version": 1, "id": "source-1", "title": "Synthetic test source", "url": "https://example.org/source",
            "authors": ["Fixture Author"], "year": "1900", "version": "fixture", "access": "full-text",
            "inspected_passages": [{"locator": "p. 1", "text": "Synthetic inspected passage."}],
            "accessed": "2026-11-06", "evidence_lineage": "Synthetic, not a research source."}


def fixture():
    record = event()
    return {"nodes": [node([record])], "events": [record], "relationships": [], "sources": [source()]}


def select_anchor(record, event_id, policy="first_commercial_availability"):
    record["graph_anchor"] = {"status": "selected", "policy": policy, "event_id": event_id,
                              "rationale": "The inspected fixture supports this anchor policy."}


def relationship(from_node="node-1", from_event="event-1", to_node="node-2", to_event="event-2"):
    return {"schema_version": 1, "id": "relationship-1", "from": {"node_id": from_node, "event_id": from_event},
            "to": {"node_id": to_node, "event_id": to_event}, "relation": "documented-development",
            "statement": "One synthetic historical event informed another.", "scope": "Only the specified fixture configurations.",
            "evidence": [evidence()], "confidence": "high", "necessity": "Not asserted.", "alternatives": "Not researched.",
            "uncertainty": "Fixture only.", "temporal_note": "The relationship concerns events, not commercial display anchors.",
            "review": review(), "provenance": provenance()}


def linked_fixture():
    a = [event("a-demonstration", "node-a", "demonstration", 1900),
         event("a-commercial", "node-a", "first_commercial_availability", 1980)]
    b = [event("b-prototype", "node-b", "prototype", 1920),
         event("b-commercial", "node-b", "first_commercial_availability", 1950)]
    na, nb = node(a, "node-a"), node(b, "node-b")
    select_anchor(na, "a-commercial")
    select_anchor(nb, "b-commercial")
    return {"nodes": [na, nb], "events": a + b,
            "relationships": [relationship("node-a", "a-demonstration", "node-b", "b-prototype")], "sources": [source()]}


class GraphValidationTests(unittest.TestCase):
    def check(self, records):
        return validator.validate_records(records, optional_jsonschema=False)

    def assertValid(self, records):
        result = self.check(records)
        self.assertTrue(result["valid"], result["errors"])
        return result

    def assertInvalid(self, records, code=None):
        result = self.check(records)
        self.assertFalse(result["valid"], result)
        if code:
            self.assertIn(code, {e["code"] for e in result["errors"]}, result["errors"])
        return result

    def test_unresearched_commercial_anchor_stays_unresolved_without_mutation(self):
        records = fixture()
        before = deepcopy(records)
        result = self.assertValid(records)
        self.assertEqual(before, records)
        self.assertEqual(1, result["counts"]["technology_commercial_dates_unresearched"])
        self.assertEqual(1, result["counts"]["anchors_unresolved"])
        self.assertNotIn("event_id", records["nodes"][0]["graph_anchor"])

    def test_disconnected_abandoned_and_extinct_branch_is_valid(self):
        events = [event(), event("abandoned", event_type="abandonment", year=1910),
                  event("ended", event_type="end_of_use", year=1920)]
        records = fixture()
        records.update(nodes=[node(events)], events=events)
        self.assertValid(records)
        self.assertEqual([], records["relationships"])
        self.assertEqual(["Fixture application"], records["events"][2]["scope"]["applications"])
        self.assertEqual("not_yet_researched", records["nodes"][0]["lifecycle"]["revival"]["status"])

    def test_commercial_anchor_uses_actual_commercial_event(self):
        records = fixture()
        records["events"][0]["event_type"] = "first_commercial_availability"
        records["nodes"] = [node(records["events"])]
        select_anchor(records["nodes"][0], "event-1")
        self.assertValid(records)

    def test_invention_adoption_and_other_stages_are_not_commercial_anchors(self):
        for event_type in ("invention", "adoption", "prototype", "production", "dated_assertion", "launch", "commercial_offer", "support_end", "presentation"):
            with self.subTest(event_type=event_type):
                records = fixture()
                records["events"][0]["event_type"] = event_type
                records["nodes"] = [node(records["events"])]
                select_anchor(records["nodes"][0], "event-1")
                self.assertInvalid(records, "anchor_type")

    def test_justified_nonmarket_deployment_anchor_is_valid(self):
        for applicability in ("nonmarket", "not_applicable"):
            with self.subTest(applicability=applicability):
                records = fixture()
                records["events"][0]["event_type"] = "practical_deployment"
                records["nodes"] = [node(records["events"])]
                records["nodes"][0]["commercial_applicability"].update(
                    status=applicability, rationale="The inspected fixture describes public nonmarket use.", evidence=[evidence()])
                select_anchor(records["nodes"][0], "event-1", "practical_deployment")
                self.assertValid(records)

    def test_deployment_anchor_requires_applicability_decision_and_evidence(self):
        for applicability, supported in (("applicable", True), ("not_yet_assessed", True), ("not_applicable", False)):
            with self.subTest(applicability=applicability, supported=supported):
                records = fixture()
                records["events"][0]["event_type"] = "practical_deployment"
                records["nodes"] = [node(records["events"])]
                records["nodes"][0]["commercial_applicability"].update(status=applicability, evidence=[evidence()] if supported else [])
                select_anchor(records["nodes"][0], "event-1", "practical_deployment")
                self.assertInvalid(records, "anchor_applicability")

    def test_scientific_anchor_uses_an_appropriate_scientific_milestone(self):
        for milestone in sorted(validator.SCIENTIFIC):
            with self.subTest(milestone=milestone):
                records = fixture()
                records["events"][0]["event_type"] = milestone
                records["nodes"] = [node(records["events"], kind="science")]
                select_anchor(records["nodes"][0], "event-1", "scientific_event")
                self.assertValid(records)

    def test_science_rejects_invention_anchor_and_commercial_applicability(self):
        records = fixture()
        records["nodes"] = [node(records["events"], kind="science")]
        select_anchor(records["nodes"][0], "event-1", "scientific_event")
        self.assertInvalid(records, "anchor_type")
        records["nodes"][0]["commercial_applicability"]["status"] = "applicable"
        self.assertInvalid(records, "schema")

    def test_anchor_policy_must_match_node_kind(self):
        records = fixture()
        records["nodes"][0]["graph_anchor"]["policy"] = "scientific_event"
        self.assertInvalid(records, "schema")

    def test_unselected_anchor_must_omit_event_id(self):
        records = fixture()
        records["nodes"][0]["graph_anchor"]["event_id"] = "event-1"
        self.assertInvalid(records, "schema")

    def test_ongoing_status_requires_valid_as_of_and_evidence(self):
        records = fixture()
        entry = records["nodes"][0]["lifecycle"]["adoption"]
        entry.update(status="ongoing", as_of="2026-11-06", evidence=[evidence()])
        self.assertValid(records)
        for missing in ("as_of", "evidence"):
            with self.subTest(missing=missing):
                bad = deepcopy(records)
                del bad["nodes"][0]["lifecycle"]["adoption"][missing]
                self.assertInvalid(bad, "required")
        entry["as_of"] = "2026-02-30"
        self.assertInvalid(records, "date")

    def test_all_lifecycle_statuses_are_explicit_and_documented_requires_event(self):
        for change in ("missing", "null", "undocumented"):
            with self.subTest(change=change):
                records = fixture()
                if change == "missing":
                    del records["nodes"][0]["lifecycle"]["end_of_use"]
                elif change == "null":
                    records["nodes"][0]["lifecycle"]["end_of_use"] = None
                else:
                    records["nodes"][0]["lifecycle"]["end_of_use"]["status"] = "documented"
                self.assertInvalid(records)

    def test_historical_acceptance_does_not_upgrade_lifecycle_review(self):
        result = self.assertValid(fixture())
        for kind in ("nodes", "events"):
            self.assertEqual({"accepted": 1}, result["counts"]["review"][kind]["historical_claim"])
            self.assertEqual({"needs_review": 1}, result["counts"]["review"][kind]["lifecycle_classification"])

    def test_reversed_commercial_display_order_accepts_valid_historical_events(self):
        result = self.assertValid(linked_fixture())
        self.assertEqual([], result["concerns"])

    def test_reversed_relationship_event_dates_are_a_review_concern(self):
        records = linked_fixture()
        records["events"][0]["date"] = historical_date(1930)
        result = self.assertValid(records)
        self.assertEqual(["event_chronology"], [e["code"] for e in result["concerns"]])

    def test_unknown_dates_have_explicit_status_and_no_bounds(self):
        records = fixture()
        records["events"][0]["date"] = {"status": "unknown", "precision": "unknown", "calendar": "historical-BCE-CE",
            "label": "Date unresolved", "basis": "The inspected source does not resolve the date."}
        self.assertValid(records)
        for key, value in (("earliest", {"year": 1900}), ("latest", {"year": 1900}), ("precision", "year")):
            with self.subTest(key=key):
                bad = deepcopy(records)
                bad["events"][0]["date"][key] = value
                self.assertInvalid(bad, "schema")

    def test_year_zero_impossible_month_and_reversed_dates_are_rejected(self):
        dates = [historical_date(0), historical_date(1900), historical_date(1900), historical_date(1900)]
        dates[1].update(precision="day", earliest={"year": 1900, "month": 4, "day": 31}, latest={"year": 1900, "month": 4, "day": 31})
        dates[2].update(earliest={"year": 1901}, latest={"year": 1900})
        dates[3].update(precision="month", earliest={"year": 1900, "month": 13}, latest={"year": 1900, "month": 13})
        for invalid_date in dates:
            with self.subTest(date=invalid_date):
                records = fixture()
                records["events"][0]["date"] = invalid_date
                self.assertInvalid(records)

    def test_date_precision_requires_the_declared_components(self):
        for precision, bound in (("day", {"year": 1900, "month": 1}), ("month", {"year": 1900}), ("year", {"year": 1900, "day": 1})):
            with self.subTest(precision=precision, bound=bound):
                records = fixture()
                records["events"][0]["date"].update(precision=precision, earliest=bound, latest=bound)
                self.assertInvalid(records)

    def test_bce_ce_interval_is_valid_without_year_zero(self):
        records = fixture()
        records["events"][0]["date"].update(status="bounded", precision="range", earliest={"year": -1}, latest={"year": 1})
        self.assertValid(records)

    def test_unequal_known_bounds_are_only_a_review_concern(self):
        records = fixture()
        records["events"][0]["date"]["latest"] = {"year": 1901}
        result = self.assertValid(records)
        self.assertEqual(["known_range"], [c["code"] for c in result["concerns"]])

    def test_null_is_rejected_in_optional_metadata(self):
        for kind, field in (("nodes", "classification"), ("events", "provenance"), ("sources", "inspected_passages")):
            with self.subTest(kind=kind, field=field):
                records = fixture()
                records[kind][0][field] = {"nested": [None]}
                self.assertInvalid(records, "null")

    def test_dangling_sources_and_nodes_are_rejected(self):
        records = fixture()
        records["sources"] = []
        self.assertInvalid(records, "dangling_source")
        records = fixture()
        records["events"][0]["node_id"] = "missing-node"
        self.assertInvalid(records, "dangling_node")

    def test_node_event_membership_must_match_owned_events_exactly(self):
        for ids in (["missing-event"], ["event-1", "missing-event"]):
            with self.subTest(ids=ids):
                records = fixture()
                records["nodes"][0]["event_ids"] = ids
                self.assertInvalid(records, "event_membership")

    def test_lifecycle_event_type_and_node_ownership_are_checked(self):
        records = fixture()
        entry = records["nodes"][0]["lifecycle"]["end_of_use"]
        entry.update(status="documented", event_ids=["event-1"])
        self.assertInvalid(records, "lifecycle_type")
        entry["event_ids"] = ["missing-event"]
        self.assertInvalid(records, "event_membership")

    def test_anchor_and_relationship_events_belong_to_their_endpoint_node(self):
        records = linked_fixture()
        records["nodes"][0]["graph_anchor"]["event_id"] = "b-commercial"
        self.assertInvalid(records, "anchor_membership")
        records = linked_fixture()
        records["relationships"][0]["from"]["event_id"] = "b-commercial"
        self.assertInvalid(records, "event_membership")
        records["relationships"][0]["from"]["event_id"] = "missing-event"
        self.assertInvalid(records, "dangling_event")

    def test_duplicate_ids_and_references_are_rejected(self):
        for kind in validator.KINDS:
            with self.subTest(kind=kind):
                records = linked_fixture()
                records[kind].append(deepcopy(records[kind][0]))
                self.assertInvalid(records, "duplicate_id")
        records = fixture()
        records["nodes"][0]["event_ids"].append("event-1")
        self.assertInvalid(records, "duplicate_reference")
        records = fixture()
        records["events"][0]["evidence"].append(evidence())
        self.assertInvalid(records, "duplicate_reference")

    def test_evidence_less_events_are_rejected(self):
        records = fixture()
        records["events"][0]["evidence"] = []
        self.assertInvalid(records, "schema")

    def test_new_relation_requires_inspected_source_passages(self):
        records = linked_fixture()
        records["relationships"][0]["relation"] = "revival-of"
        self.assertValid(records)
        records["sources"][0]["inspected_passages"] = []
        self.assertInvalid(records, "uninspected_relation")

    def test_provenance_uses_current_source_references(self):
        records = fixture()
        records["nodes"][0]["provenance"]["source_ids"] = ["missing-source"]
        self.assertInvalid(records, "dangling_source")
        records["nodes"][0]["provenance"]["source_ids"] = ["source-1", "source-1"]
        self.assertInvalid(records, "duplicate_reference")
        records["nodes"][0]["provenance"] = {"method": "source-evidence", "source_ids": []}
        self.assertInvalid(records, "required")

    def test_source_urls_have_valid_shapes(self):
        for url in ("ftp://example.org/source", "https://example.org/a b"):
            with self.subTest(url=url):
                records = fixture()
                records["sources"][0]["url"] = url
                self.assertInvalid(records, "schema")

    def test_initial_schema_number_is_required_as_an_integer(self):
        for value in ("1", True, 1.5):
            with self.subTest(value=value):
                records = fixture()
                records["nodes"][0]["schema_version"] = value
                self.assertInvalid(records, "schema")

    def test_in_memory_non_finite_numbers_are_rejected(self):
        records = fixture()
        records["nodes"][0]["classification"] = {"value": float("inf")}
        self.assertInvalid(records, "non_json_number")

    def test_source_author_and_year_forms_preserve_source_metadata(self):
        for authors, year in (("Author", 1900), (["Author"], [1900, "c. 1901"]), ([], "unknown")):
            with self.subTest(authors=authors, year=year):
                records = fixture()
                records["sources"][0].update(authors=authors, year=year)
                self.assertValid(records)

    def test_malformed_records_report_errors_without_crashing(self):
        for kind in validator.KINDS:
            for malformed in (None, [], "record", 7, {"id": "bad", "review": {"historical_claim": [], "lifecycle_classification": {}}}):
                with self.subTest(kind=kind, malformed=malformed):
                    records = fixture()
                    records[kind].append(malformed)
                    self.assertInvalid(records)

    def test_unsupported_schema_keywords_fail_closed(self):
        errors = validator.schema_errors("anything", {"type": "string", "unsupportedKeyword": True})
        self.assertEqual(["schema_configuration"], [e["code"] for e in errors])


class RepositoryValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copyfile(ROOT / "schema.json", self.root / "schema.json")
        (self.root / "data").mkdir()
        self.records = fixture()
        self.write_records()

    def write_records(self):
        for kind, rows in self.records.items():
            (self.root / "data" / (kind + ".jsonl")).write_text("".join(json.dumps(row) + "\n" for row in rows))

    def local_copy(self, path="evidence/source.txt", content=b"Inspected original source.\n"):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return {"path": path, "sha256": hashlib.sha256(content).hexdigest()}

    def check(self):
        return validator.validate_repository(self.root, optional_jsonschema=False)

    def test_repository_uses_one_schema_with_reusable_record_definitions(self):
        schema = json.loads((self.root / "schema.json").read_text())
        self.assertEqual(4, len(schema["oneOf"]))
        for kind in validator.KINDS.values():
            self.assertIn(kind, schema["$defs"])
            self.assertEqual({"const": 1, "type": "integer"}, schema["$defs"][kind]["properties"]["schema_version"])
            self.assertNotIn("$defs", schema["$defs"][kind])
        result = self.check()
        self.assertTrue(result["valid"], result["errors"])

    def test_local_source_copy_hash_is_verified(self):
        self.records["sources"][0]["local_copy"] = self.local_copy()
        self.write_records()
        result = self.check()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(1, result["counts"]["source_copies_verified"])

    def test_shared_source_copies_are_hashed_once(self):
        self.records["sources"][0]["local_copy"] = self.local_copy()
        self.records["sources"].append(dict(deepcopy(self.records["sources"][0]), id="source-2"))
        self.write_records()
        result = self.check()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(1, result["counts"]["source_copies_verified"])

    def test_copy_hash_mismatch_and_missing_file_are_rejected(self):
        copy = self.local_copy()
        self.records["sources"][0]["local_copy"] = copy
        self.write_records()
        (self.root / copy["path"]).write_bytes(b"altered evidence")
        self.assertIn("local_copy_hash", {e["code"] for e in self.check()["errors"]})
        (self.root / copy["path"]).unlink()
        self.assertIn("local_copy_hash", {e["code"] for e in self.check()["errors"]})

    def test_local_copy_cannot_escape_repository(self):
        for path in ("../outside.txt", "/etc/hosts", "evidence/../../outside.txt", "evidence/invalid\x00name.txt"):
            with self.subTest(path=path):
                self.records["sources"][0]["local_copy"] = {"path": path, "sha256": "0" * 64}
                self.write_records()
                self.assertIn("local_path", {e["code"] for e in self.check()["errors"]})

    def test_local_copy_symlink_escape_is_rejected(self):
        outside = self.root.parent / (self.root.name + "-outside.txt")
        outside.write_text("outside")
        self.addCleanup(outside.unlink)
        (self.root / "evidence").mkdir()
        (self.root / "evidence/link.txt").symlink_to(outside)
        self.records["sources"][0]["local_copy"] = {"path": "evidence/link.txt", "sha256": "0" * 64}
        self.write_records()
        self.assertIn("local_path", {e["code"] for e in self.check()["errors"]})

    def test_local_copy_shape_requires_path_and_sha256(self):
        for copy in ({}, {"path": "missing"}, {"path": "evidence/source.txt", "sha256": "bad-hash"}):
            with self.subTest(copy=copy):
                self.records["sources"][0]["local_copy"] = copy
                self.write_records()
                self.assertFalse(self.check()["valid"])

    def test_current_review_paths_are_checked(self):
        review_path = self.root / "reviews/fixture.json"
        review_path.parent.mkdir()
        review_path.write_text('{"decision":"candidate"}')
        for kind in ("nodes", "events"):
            self.records[kind][0]["review"]["records"] = ["reviews/fixture.json"]
        self.write_records()
        result = self.check()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(1, result["counts"]["review_files_verified"])
        review_path.unlink()
        self.assertIn("review_file", {e["code"] for e in self.check()["errors"]})
        self.records["nodes"][0]["review"]["records"] = ["../outside.json"]
        self.write_records()
        self.assertIn("local_path", {e["code"] for e in self.check()["errors"]})

    def test_malformed_json_blank_lines_duplicate_keys_and_non_json_numbers_are_rejected(self):
        for text in ('{"id":', '{"id":"a","id":"b"}\n', '{"id":"a","classification":{"number":NaN}}\n', "\n", "[]\n"):
            with self.subTest(text=text):
                (self.root / "data/nodes.jsonl").write_text(text)
                result = self.check()
                self.assertFalse(result["valid"])
                self.assertTrue(result["errors"])

    def test_jsonl_error_line_numbers_are_preserved(self):
        self.records["nodes"][0]["event_ids"] = ["missing-event"]
        (self.root / "data/nodes.jsonl").write_text("\n" + json.dumps(self.records["nodes"][0]) + "\n")
        result = self.check()
        self.assertTrue(any(e["path"].startswith("nodes.jsonl:2") and e["code"] == "event_membership" for e in result["errors"]))

    def test_missing_canonical_file_reports_error(self):
        (self.root / "data/events.jsonl").unlink()
        self.assertIn("read", {e["code"] for e in self.check()["errors"]})

    def test_cli_json_and_strict_concerns_exit_status(self):
        self.records["events"][0]["date"]["latest"] = {"year": 1901}
        self.write_records()
        for strict, expected in ((False, 0), (True, 1)):
            with self.subTest(strict=strict), redirect_stdout(io.StringIO()) as output:
                args = ["--root", str(self.root), "--json", "--stdlib-only"]
                if strict:
                    args.append("--strict-concerns")
                self.assertEqual(expected, validator.main(args))
                result = json.loads(output.getvalue())
                self.assertTrue(result["valid"])
                self.assertEqual("known_range", result["concerns"][0]["code"])


if __name__ == "__main__":
    unittest.main()
