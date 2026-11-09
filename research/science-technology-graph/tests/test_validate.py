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
    return {"historical_claim": "accepted", "lifecycle_classification": "needs_review", "records": ["reviews/current-evidence.json"]}


def provenance():
    return {"method": "source-evidence", "source_ids": ["source-1"], "note": "Synthetic source evidence."}


def historical_date(year=1900):
    return {"status": "known", "precision": "year", "calendar": "historical-BCE-CE", "label": str(year),
            "basis": "Synthetic year supplied by a fixture.", "earliest": {"year": year}, "latest": {"year": year}}


def one_sided_date(supplied, bound, missing_status="unknown", precision="day"):
    missing = "earliest" if supplied == "latest" else "latest"
    return {"status": "bounded", "precision": precision, "calendar": "historical-BCE-CE",
            "label": "By the supplied date" if supplied == "latest" else "From the supplied date",
            "basis": "The fixture supports one limit only.", supplied: bound, missing + "_status": missing_status}


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
    return {"schema_version": 1, "id": node_id, "label": "Synthetic apparatus", "kind": kind, "labels":["mathematics"],
            "configuration": "Fixture apparatus", "regions": ["Fixture region"], "event_ids": [e["id"] for e in events],
            "lifecycle": lifecycle, "commercial_applicability": {"status": "not_applicable" if kind == "science" else "applicable",
            "rationale": "Scientific claim." if kind == "science" else "A possible commercial apparatus.", "evidence": []},
            "graph_anchor": {"status":"not_yet_researched", "policy":"earliest_record", "rationale":"Fixture earliest record unresolved."},
            "community_entry": {"status": "not_yet_researched", "policy": "community_entry",
            "rationale": "No anchor has been researched."}, "review": review(), "provenance": provenance(), "uncertainty": "Fixture only."}


def source():
    return {"schema_version": 1, "id": "source-1", "title": "Synthetic test source", "url": "https://example.org/source",
            "authors": ["Fixture Author"], "year": "1900", "version": "fixture", "access": "full-text",
            "inspected_passages": [{"locator": "p. 1", "text": "Synthetic inspected passage."}],
            "accessed": "2026-11-06", "evidence_lineage": "Synthetic, not a research source."}


def fixture():
    record = event()
    return {"nodes": [node([record])], "events": [record], "relationships": [], "sources": [source()]}


def select_anchor(record, event_id, entry_basis="first_commercial_availability", strength=None, interpretation="event_date"):
    strength = strength or ("awareness_proxy" if entry_basis == "public_awareness" else "direct")
    record["community_entry"] = {"status": "selected", "policy": "community_entry", "event_id": event_id,
        "entry_basis": entry_basis, "evidence_strength": strength, "date_interpretation": interpretation,
        "community": "Named fixture community", "scope": {"regions": ["Fixture region"], "configuration": record["configuration"],
        "applications": ["Fixture application"], "market": {"status": "unknown"}, "population": {"status": "specified", "value": "Named fixture community"}},
        "evidence": [evidence()], "rationale": "The inspected fixture supports this deliberate community-entry choice.",
        "uncertainty": "No broader uptake or earlier entry is asserted."}
    if strength != "direct":
        record["community_entry"]["proxy_justification"] = "The fixture supports only this expressly limited community inference or awareness opportunity."


def relationship(from_node="node-1", from_event="event-1", to_node="node-2", to_event="event-2"):
    return {"schema_version": 1, "id": "relationship-1", "from": {"node_id": from_node, "event_id": from_event},
            "to": {"node_id": to_node, "event_id": to_event}, "relation": "documented-development",
            "statement": "One synthetic historical event informed another.", "scope": "Only the specified fixture configurations.",
            "evidence": [evidence()], "confidence": "high", "influence": "not_assessed", "alternatives": "Not researched.",
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
    def test_earliest_record_can_precede_community_entry(self):
        records = fixture()
        earlier = records['events'][0]
        later = event('later-use', event_type='practical_use', year=1910)
        records['events'].append(later)
        records['nodes'][0] = node(records['events'])
        select_anchor(records['nodes'][0], later['id'], 'practical_use')
        records['nodes'][0]['graph_anchor'] = {'status':'selected', 'policy':'earliest_record',
            'event_id':earlier['id'], 'date_interpretation':'event_date', 'scope':earlier['scope'],
            'evidence':earlier['evidence'], 'rationale':'Earlier scoped record, independently selected.',
            'uncertainty':'No absolute priority asserted.'}
        self.assertTrue(validator.validate_records(records, optional_jsonschema=False)['valid'])
        records['nodes'][0]['witnesses'] = [{'event_id':earlier['id'], 'limitation':'Only a surviving copy.'}]
        result = validator.validate_records(records, optional_jsonschema=False)
        self.assertTrue(any(e['code'] == 'witness_anchor' for e in result['errors']))

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
        self.assertNotIn("event_id", records["nodes"][0]["community_entry"])

    def test_dated_offer_supports_available_by_without_changing_unknown_first_sale(self):
        offer = event(event_type="commercial_offer", year=1910)
        records = fixture()
        records.update(nodes=[node([offer])], events=[offer])
        current = records["nodes"][0]
        current["lifecycle"]["first_commercial_availability"].update(status="unknown", evidence=[evidence()],
            rationale="The dated offer establishes availability by 1910; its first sale remains unresolved.")
        select_anchor(current, offer["id"], "commercial_availability", interpretation="known_by")
        before = deepcopy(records)
        self.assertValid(records)
        self.assertEqual(before, records)
        self.assertEqual("unknown", current["lifecycle"]["first_commercial_availability"]["status"])
        self.assertEqual("known", offer["date"]["status"])

    def test_scientific_observation_cannot_displace_selected_later_acceptance(self):
        events = [event("observed", event_type="observation", year=1800), event("accepted", event_type="acceptance", year=1850)]
        records = fixture()
        records.update(nodes=[node(events, kind="science")], events=events)
        select_anchor(records["nodes"][0], "accepted", "recognition")
        self.assertValid(records)
        records["nodes"][0]["community_entry"]["event_id"] = "observed"
        self.assertInvalid(records, "anchor_type")

    def test_public_disclosure_proxy_is_justified_and_never_called_adoption(self):
        disclosure = event(event_type="public_disclosure")
        records = fixture()
        records.update(nodes=[node([disclosure], kind="science")], events=[disclosure])
        select_anchor(records["nodes"][0], disclosure["id"], "public_awareness")
        self.assertValid(records)
        anchor = records["nodes"][0]["community_entry"]
        anchor["entry_basis"] = "adoption"
        self.assertInvalid(records, "anchor_strength")
        anchor["entry_basis"] = "public_awareness"
        anchor["evidence_strength"] = "direct"
        self.assertInvalid(records, "anchor_strength")
        anchor["evidence_strength"] = "awareness_proxy"
        del anchor["proxy_justification"]
        self.assertInvalid(records, "required")

    def test_direct_scientific_data_release_is_eligible_public_availability(self):
        release = event(event_type="public_availability", year=2000)
        release["statement"] = "The working scientific dataset was released for public web access on the stated date."
        release["date"].update(precision="day", earliest={"year": 2000, "month": 7, "day": 7}, latest={"year": 2000, "month": 7, "day": 7})
        records = fixture()
        records.update(nodes=[node([release], kind="science")], events=[release])
        select_anchor(records["nodes"][0], release["id"], "public_availability")
        self.assertValid(records)
        release["event_type"] = "publication"
        self.assertInvalid(records, "anchor_type")

    def test_scoped_ancient_use_inference_remains_explicit_and_typed(self):
        use = event(event_type="practical_use", year=-900)
        use["statement"] = "Practical availability to this workshop community is contextually inferred from the dated working assemblage."
        use["date"].update(status="bounded", precision="range", earliest={"year": -1250}, latest={"year": -900})
        records = fixture()
        records.update(nodes=[node([use])], events=[use])
        select_anchor(records["nodes"][0], use["id"], "practical_use", strength="scoped_inference", interpretation="known_by")
        records["nodes"][0]["community_entry"].update(community="The named workshop context", uncertainty="Contextual availability is inferred; the layer interval is not the start of manufacture or universal uptake.")
        self.assertValid(records)
        use["event_type"] = "archaeological_evidence"
        self.assertInvalid(records, "anchor_type")
        use["event_type"] = "practical_use"
        records["nodes"][0]["community_entry"]["entry_basis"] = "adoption"
        self.assertInvalid(records, "anchor_strength")

    def test_selected_community_entry_requires_explicit_scope_evidence_and_uncertainty(self):
        use = event(event_type="practical_use")
        records = fixture()
        records.update(nodes=[node([use])], events=[use])
        select_anchor(records["nodes"][0], use["id"], "practical_use")
        for field in ("community", "scope", "evidence", "uncertainty", "date_interpretation"):
            with self.subTest(field=field):
                bad = deepcopy(records)
                del bad["nodes"][0]["community_entry"][field]
                self.assertInvalid(bad, "required")

    def test_entry_bound_interpretation_requires_the_corresponding_supplied_limit(self):
        use = event(event_type="practical_use")
        records = fixture()
        records.update(nodes=[node([use])], events=[use])
        for supplied, interpretation in (("earliest", "known_by"), ("latest", "known_from")):
            with self.subTest(interpretation=interpretation):
                use["date"] = one_sided_date(supplied, {"year": 1900}, precision="year")
                select_anchor(records["nodes"][0], use["id"], "practical_use", interpretation=interpretation)
                self.assertInvalid(records, "anchor_date")

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
                select_anchor(records["nodes"][0], "event-1", "practical_use")
                self.assertValid(records)

    def test_science_rejects_invention_anchor_and_commercial_applicability(self):
        records = fixture()
        records["nodes"] = [node(records["events"], kind="science")]
        select_anchor(records["nodes"][0], "event-1", "public_awareness")
        self.assertInvalid(records, "anchor_type")
        records["nodes"][0]["commercial_applicability"]["status"] = "applicable"
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

    def test_non_documented_lifecycle_states_do_not_claim_events(self):
        for status in ("unknown", "not_yet_researched", "not_applicable"):
            with self.subTest(status=status):
                records = fixture()
                entry = records["nodes"][0]["lifecycle"]["invention"]
                entry.update(status=status, evidence=[evidence()])
                self.assertInvalid(records, "schema")
                entry["event_ids"] = []
                self.assertValid(records)

    def test_unknown_lifecycle_requires_evidence_of_researched_uncertainty(self):
        records = fixture()
        entry = records["nodes"][0]["lifecycle"]["first_commercial_availability"]
        entry.update(status="unknown", rationale="The inspected source leaves the first sale unresolved.")
        self.assertInvalid(records, "schema")
        entry["evidence"] = [evidence()]
        self.assertValid(records)

    def test_selected_technology_anchor_requires_documented_lifecycle_membership(self):
        for policy in ("first_commercial_availability", "practical_deployment"):
            for status in ("unknown", "not_yet_researched", "not_applicable", "ongoing"):
                with self.subTest(policy=policy, status=status):
                    events = [event(event_type=policy)]
                    records = fixture()
                    records.update(nodes=[node(events)], events=events)
                    current = records["nodes"][0]
                    if policy == "practical_deployment":
                        current["commercial_applicability"].update(status="nonmarket", evidence=[evidence()])
                    select_anchor(current, "event-1", "practical_use" if policy == "practical_deployment" else policy)
                    current["lifecycle"][policy].update(status=status, event_ids=[], evidence=[evidence()])
                    if status == "ongoing":
                        current["lifecycle"][policy]["as_of"] = "2026-11-06"
                    self.assertInvalid(records, "anchor_lifecycle")

    def test_selected_anchor_id_must_occur_in_its_documented_lifecycle_entry(self):
        events = [event("first", event_type="first_commercial_availability"),
                  event("other", event_type="first_commercial_availability", year=1901)]
        records = fixture()
        records.update(nodes=[node(events)], events=events)
        current = records["nodes"][0]
        select_anchor(current, "first")
        current["lifecycle"]["first_commercial_availability"]["event_ids"] = ["other"]
        self.assertInvalid(records, "anchor_lifecycle")

    def test_science_entry_agrees_with_existing_lifecycle_keys(self):
        for milestone, basis in (("acceptance", "recognition"), ("presentation", "public_awareness")):
            with self.subTest(milestone=milestone):
                events = [event(event_type=milestone)]
                records = fixture()
                records.update(nodes=[node(events, kind="science")], events=events)
                select_anchor(records["nodes"][0], "event-1", basis)
                if milestone == "acceptance":
                    records["nodes"][0]["lifecycle"][milestone].update(status="unknown", event_ids=[], evidence=[evidence()])
                    self.assertInvalid(records, "anchor_lifecycle")
                else:
                    self.assertValid(records)

    def test_all_selected_entries_require_a_usable_event_date(self):
        for stage, kind, basis in (("first_commercial_availability", "technology", "first_commercial_availability"),
                ("practical_deployment", "technology", "practical_use"),
                ("acceptance", "science", "recognition"), ("presentation", "science", "public_awareness")):
            for status in ("unknown", "not_yet_researched", "not_applicable"):
                with self.subTest(stage=stage, status=status):
                    events = [event(event_type=stage)]
                    records = fixture()
                    records.update(nodes=[node(events, kind=kind)], events=events)
                    select_anchor(records["nodes"][0], "event-1", basis)
                    events[0]["date"] = {"status": status, "precision": "unknown", "calendar": "historical-BCE-CE",
                        "label": "Unresolved date", "basis": "The fixture supplies no usable limit."}
                    self.assertInvalid(records, "anchor_date")

    def test_historical_acceptance_does_not_upgrade_lifecycle_review(self):
        result = self.assertValid(fixture())
        for kind in ("nodes", "events"):
            self.assertEqual({"accepted": 1}, result["counts"]["review"][kind]["historical_claim"])
            self.assertEqual({"needs_review": 1}, result["counts"]["review"][kind]["lifecycle_classification"])

    def test_proposition_hash_is_compact_utf8_and_excludes_only_top_level_review(self):
        record = {"id": "é", "review": {"historical_claim": "candidate"}, "configuration": {"review": "kept"}}
        encoded = '{"configuration":{"review":"kept"},"id":"é"}'.encode("utf-8")
        expected = hashlib.sha256(encoded).hexdigest()
        self.assertEqual(expected, validator.proposition_sha256(record))
        record["review"] = {"historical_claim": "accepted", "records": ["different-file.json"]}
        self.assertEqual(expected, validator.proposition_sha256(record))
        record["configuration"]["review"] = "changed"
        self.assertNotEqual(expected, validator.proposition_sha256(record))

    def test_reversed_commercial_display_order_accepts_valid_historical_events(self):
        result = self.assertValid(linked_fixture())
        self.assertEqual([], result["concerns"])

    def test_reversed_relationship_event_dates_are_a_review_concern(self):
        records = linked_fixture()
        records["events"][0]["date"] = historical_date(1930)
        result = self.assertValid(records)
        self.assertEqual(["event_chronology"], [e["code"] for e in result["concerns"]])

    def test_approximate_relationship_limits_do_not_establish_definite_reversal(self):
        for approximate_index in (0, 2):
            with self.subTest(approximate_endpoint=approximate_index):
                records = linked_fixture()
                records["events"][0]["date"] = one_sided_date("earliest", {"year": 1921}, precision="year")
                records["events"][2]["date"] = one_sided_date("latest", {"year": 1920}, precision="year")
                records["events"][approximate_index]["date"]["status"] = "approximate"
                before = deepcopy(records)
                result = self.assertValid(records)
                self.assertEqual([], result["concerns"])
                self.assertEqual(before, records)

    def test_unknown_dates_have_explicit_status_and_no_bounds(self):
        records = fixture()
        records["events"][0]["date"] = {"status": "unknown", "precision": "unknown", "calendar": "historical-BCE-CE",
            "label": "Date unresolved", "basis": "The inspected source does not resolve the date."}
        self.assertValid(records)
        for key, value in (("earliest", {"year": 1900}), ("latest", {"year": 1900}), ("precision", "year"),
                           ("earliest_status", "unknown"), ("latest_status", "not_yet_researched")):
            with self.subTest(key=key):
                bad = deepcopy(records)
                bad["events"][0]["date"][key] = value
                self.assertInvalid(bad, "schema")

    def test_one_sided_date_requires_the_correct_explicit_missing_limit_status(self):
        for supplied in ("earliest", "latest"):
            missing = "latest" if supplied == "earliest" else "earliest"
            for change in ("omitted", "wrong_side", "not_applicable", "null"):
                with self.subTest(supplied=supplied, change=change):
                    records = fixture()
                    date = one_sided_date(supplied, {"year": 2023}, precision="year")
                    if change == "omitted":
                        del date[missing + "_status"]
                    elif change == "wrong_side":
                        date[supplied + "_status"] = date.pop(missing + "_status")
                    else:
                        date[missing + "_status"] = None if change == "null" else change
                    records["events"][0]["date"] = date
                    self.assertInvalid(records)

    def test_supplied_bounds_do_not_allow_missing_limit_statuses(self):
        for name in ("earliest", "latest"):
            with self.subTest(name=name):
                records = fixture()
                records["events"][0]["date"]["status"] = "bounded"
                self.assertValid(records)
                records["events"][0]["date"][name + "_status"] = "unknown"
                self.assertInvalid(records, "schema")

    def test_bounded_date_requires_at_least_one_real_limit(self):
        records = fixture()
        records["events"][0]["date"] = {"status": "bounded", "precision": "year", "calendar": "historical-BCE-CE",
            "label": "No supported limit", "basis": "Neither endpoint is established.",
            "earliest_status": "unknown", "latest_status": "not_yet_researched"}
        self.assertInvalid(records, "schema")

    def test_known_dates_still_require_both_limits(self):
        for supplied in ("earliest", "latest"):
            with self.subTest(supplied=supplied):
                records = fixture()
                records["events"][0]["date"] = one_sided_date(supplied, {"year": 2023}, precision="year")
                records["events"][0]["date"]["status"] = "known"
                self.assertInvalid(records)

    def test_approximate_one_sided_dates_preserve_uncertainty_without_inventing_a_limit(self):
        for supplied in ("earliest", "latest"):
            for missing_status in ("unknown", "not_yet_researched"):
                with self.subTest(supplied=supplied, missing_status=missing_status):
                    records = fixture()
                    missing = "earliest" if supplied == "latest" else "latest"
                    date = one_sided_date(supplied, {"year": 325}, missing_status, precision="year")
                    date.update(status="approximate", label="Approximately the supplied date")
                    records["events"][0]["date"] = date
                    before = deepcopy(records)
                    self.assertValid(records)
                    self.assertEqual(before, records)
                    self.assertNotIn(missing, date)
                    del date[missing + "_status"]
                    self.assertInvalid(records, "required")

    def test_each_supplied_one_sided_limit_checks_precision_and_possible_days(self):
        for supplied in ("earliest", "latest"):
            for precision, bound in (("day", {"year": 2023, "month": 4, "day": 31}),
                    ("day", {"year": 2023, "month": 3}), ("month", {"year": 2023}),
                    ("year", {"year": 0}), ("month", {"year": 2023, "month": 13})):
                with self.subTest(supplied=supplied, precision=precision, bound=bound):
                    records = fixture()
                    records["events"][0]["date"] = one_sided_date(supplied, bound, precision=precision)
                    self.assertInvalid(records)

    def test_one_sided_chronology_uses_only_supplied_decisive_limits(self):
        cases = [
            (one_sided_date("latest", {"year": 1930}, precision="year"), historical_date(1920), False),
            (historical_date(1930), one_sided_date("earliest", {"year": 1920}, precision="year"), False),
            (one_sided_date("earliest", {"year": 1930}, precision="year"),
             one_sided_date("latest", {"year": 1920}, precision="year"), True),
        ]
        for source_date, receiving_date, reversed_events in cases:
            with self.subTest(source=source_date, receiving=receiving_date):
                records = linked_fixture()
                records["events"][0]["date"] = source_date
                records["events"][2]["date"] = receiving_date
                before = deepcopy(records)
                result = self.assertValid(records)
                self.assertEqual(before, records)
                self.assertEqual(["event_chronology"] if reversed_events else [], [c["code"] for c in result["concerns"]])

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
        records["nodes"][0]["community_entry"]["event_id"] = "b-commercial"
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

    def test_in_memory_non_finite_numbers_are_rejected(self):
        records = fixture()
        records["nodes"][0]["classification"] = {"value": float("inf")}
        self.assertInvalid(records, "non_json_number")

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
        self.write_ledger()

    def write_records(self):
        for kind, rows in self.records.items():
            (self.root / "data" / (kind + ".jsonl")).write_text("".join(json.dumps(row) + "\n" for row in rows))

    def write_ledger(self):
        rows = []
        for kind in ("nodes", "events", "relationships"):
            for record in self.records[kind]:
                proposition = {key: value for key, value in record.items() if key != "review"}
                digest = hashlib.sha256(json.dumps(proposition, ensure_ascii=False, sort_keys=True,
                    separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()
                rows.append({"id": record["id"], "type": validator.KINDS[kind],
                    "historical_claim": record["review"]["historical_claim"],
                    "lifecycle_classification": record["review"]["lifecycle_classification"], "proposition_sha256": digest})
        path = self.root / "reviews/current-evidence.json"
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps({"records": rows}, ensure_ascii=False), encoding="utf-8")

    def change_ledger(self, modify):
        path = self.root / "reviews/current-evidence.json"
        document = json.loads(path.read_text())
        modify(document["records"])
        path.write_text(json.dumps(document), encoding="utf-8")

    def local_copy(self, path="evidence/source.txt", content=b"Inspected original source.\n"):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return {"path": path, "sha256": hashlib.sha256(content).hexdigest()}

    def check(self):
        return validator.validate_repository(self.root, optional_jsonschema=False)

    def test_local_source_copy_hash_is_verified(self):
        self.records["sources"][0]["local_copy"] = self.local_copy()
        self.write_records()
        result = self.check()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(1, result["counts"]["source_copies_verified"])

    def test_metadata_only_defers_missing_binary_hashes_but_still_checks_current_reviews(self):
        self.records["sources"][0]["local_copy"] = self.local_copy(path="evidence/source.pdf")
        self.write_records()
        (self.root / "evidence/source.pdf").unlink()
        self.assertFalse(self.check()["valid"])
        result = validator.validate_repository(self.root, optional_jsonschema=False, defer_binary_copies=True)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(0, result["counts"]["source_copies_verified"])
        self.assertEqual(1, result["counts"]["binary_source_copies_deferred"])
        self.records["nodes"][0]["configuration"] = "A changed, unreviewed proposition"
        self.write_records()
        result = validator.validate_repository(self.root, optional_jsonschema=False, defer_binary_copies=True)
        self.assertIn("review_proposition", {error["code"] for error in result["errors"]})

    def test_empty_source_copy_is_rejected_even_with_its_matching_hash(self):
        self.records["sources"][0]["local_copy"] = self.local_copy(content=b"")
        self.write_records()
        result = self.check()
        self.assertFalse(result["valid"])
        self.assertIn("local_copy_empty", {error["code"] for error in result["errors"]})
        self.assertEqual(0, result["counts"]["source_copies_verified"])

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

    def test_excerpt_copy_requires_explicit_original_identity_and_page_mapping(self):
        self.records["sources"][0]["local_copy"] = dict(self.local_copy(), representation="excerpt",
            original_sha256="a" * 64, original_page_count=40,
            page_mapping=[{"source_page": 12, "excerpt_page": 1}], extraction_method="Selected page copied without resizing.")
        self.write_records()
        result = self.check()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(1, result["counts"]["source_copies_verified"])
        del self.records["sources"][0]["local_copy"]["page_mapping"]
        self.write_records()
        self.assertFalse(self.check()["valid"])

    def test_current_review_paths_are_checked(self):
        review_path = self.root / "reviews/fixture.json"
        review_path.write_text('{"decision":"candidate"}')
        for kind in ("nodes", "events"):
            self.records[kind][0]["review"]["records"].append("reviews/fixture.json")
        self.write_records()
        result = self.check()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(2, result["counts"]["review_files_verified"])
        review_path.unlink()
        self.assertIn("review_file", {e["code"] for e in self.check()["errors"]})
        self.records["nodes"][0]["review"]["records"] = ["../outside.json"]
        self.write_records()
        self.assertIn("local_path", {e["code"] for e in self.check()["errors"]})

    def test_normalized_review_covers_each_node_event_and_relationship(self):
        self.records = linked_fixture()
        self.write_records()
        self.write_ledger()
        result = self.check()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(7, result["counts"]["current_review_records_verified"])
        self.change_ledger(lambda rows: rows.pop())
        self.assertIn("review_membership", {e["code"] for e in self.check()["errors"]})

    def test_review_ledger_must_contain_the_referring_id_and_type(self):
        for field, value in (("id", "different-node"), ("type", "event")):
            with self.subTest(field=field):
                self.write_ledger()
                self.change_ledger(lambda rows: rows[0].update({field: value}))
                codes = {e["code"] for e in self.check()["errors"]}
                self.assertIn("review_membership", codes)
                self.assertIn("review_coverage", codes)

    def test_review_ledger_rejects_a_stale_proposition_hash(self):
        self.records["nodes"][0]["configuration"] = "The current proposition changed."
        self.write_records()
        self.assertIn("review_proposition", {e["code"] for e in self.check()["errors"]})

    def test_review_axes_must_agree_even_though_the_hash_excludes_review(self):
        for axis, value in (("historical_claim", "candidate"), ("lifecycle_classification", "accepted")):
            with self.subTest(axis=axis):
                self.records = fixture()
                self.records["nodes"][0]["review"][axis] = value
                self.write_records()
                codes = {e["code"] for e in self.check()["errors"]}
                self.assertIn("review_status", codes)
                self.assertNotIn("review_proposition", codes)

    def test_auxiliary_human_reviews_do_not_replace_current_normalized_decisions(self):
        path = self.root / "reviews/human.json"
        path.write_text(json.dumps({"records": [{"id": "node-1", "verdict": "repair", "proposition_sha256": "0" * 64}]}))
        for kind in ("nodes", "events"):
            self.records[kind][0]["review"]["records"] = ["reviews/human.json"]
        self.write_records()
        result = self.check()
        self.assertIn("review_coverage", {e["code"] for e in result["errors"]})
        self.assertNotIn("review_ledger", {e["code"] for e in result["errors"]})

    def test_current_ledger_rejects_incomplete_and_duplicate_normalized_decisions(self):
        self.change_ledger(lambda rows: rows[0].pop("proposition_sha256"))
        self.assertIn("review_ledger", {e["code"] for e in self.check()["errors"]})
        self.write_ledger()
        self.change_ledger(lambda rows: rows.append(deepcopy(rows[0])))
        self.assertIn("review_ledger", {e["code"] for e in self.check()["errors"]})

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
        self.write_ledger()
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
