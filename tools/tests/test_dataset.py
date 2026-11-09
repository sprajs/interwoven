"""Tests for reading, checking and compiling the dataset.

Run from the repository root:

    python3 -m unittest discover -s tools/tests -t tools
"""

from __future__ import annotations

import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build  # noqa: E402
from dataset import DATA, Dataset, REGISTERS, discovery_path, read_json, year_value  # noqa: E402


def point(year: int) -> dict:
    return {"year": year}


def event(event_id: str, earliest: int | None, latest: int) -> dict:
    return {
        "id": event_id,
        "type": "invention",
        "date": {
            "earliest": point(earliest) if earliest is not None else None,
            "latest": point(latest),
            "precision": "year",
            "status": "known",
            "label": str(latest),
            "basis": "Fixture date.",
        },
        "statement": "Something happened.",
        "evidence": [],
    }


def discovery(record_id: str, domain: str = "energy.steam") -> dict:
    """A minimal record that passes every check on its own."""
    return {
        "id": record_id,
        "name": record_id.replace("-", " ").title(),
        "description": "A fixture discovery.",
        "kind": "technology",
        "domain": domain,
        "places": [{"place": "testtown"}],
        "people": [{"person": "ada-tester", "role": "originator"}],
        "events": [event("made", 1800, 1800)],
        "earliest_record": {"event": "made"},
        "research": {"status": "draft", "basis": {"domain": "recalled", "places": "recalled", "people": "recalled", "events": "recalled"}},
    }


class FixtureDataset:
    """Builds a small Dataset in memory using the real schema, vocabulary and taxonomy."""

    schema = read_json(DATA / "schema.json")
    vocab = read_json(DATA / "vocab.json")
    taxonomy = read_json(DATA / "taxonomy.json")

    @classmethod
    def make(cls, records: list[dict], places: list[dict] | None = None) -> Dataset:
        data = Dataset(schema=cls.schema, vocab=cls.vocab, taxonomy=cls.taxonomy)
        data.registers = {name: {} for name in REGISTERS}
        if places is None:
            places = [
                {"id": "testland", "name": "Testland", "kind": "country", "lat": 50.0, "lon": 10.0, "region": "europe", "within": None, "basis": "recalled"},
                {"id": "testtown", "name": "Testtown", "kind": "settlement", "lat": 50.1, "lon": 10.1, "region": "europe", "within": "testland", "basis": "recalled"},
            ]
        data.registers["places"] = {p["id"]: p for p in places}
        data.registers["people"] = {"ada-tester": {"id": "ada-tester", "name": "Ada Tester", "basis": "recalled"}}
        for record in records:
            data.discoveries[record["id"]] = record
            # Filed where the record says it belongs, as `load` would find it on disk.
            data.paths["discoveries/" + record["id"]] = discovery_path(record)
        return data


def valid_pair() -> list[dict]:
    """Two sound records, the second holding a link to the first."""
    earlier = discovery("earlier-engine")
    later = discovery("later-engine")
    later["events"] = [event("made", 1820, 1825)]
    later["links"] = [{"type": "builds_on", "from": "earlier-engine", "status": "candidate", "statement": "Perhaps built on it."}]
    later["research"]["basis"]["links"] = "recalled"
    return [earlier, later]


class RealDatasetTest(unittest.TestCase):
    """The committed data must always be sound."""

    def test_real_dataset_validates(self):
        data = Dataset.load()
        self.assertGreater(len(data.discoveries), 0)
        self.assertEqual(data.validate(check_files=False), [])


class ValidationTest(unittest.TestCase):
    """Each kind of broken record is reported, and a sound one is not."""

    def problems(self, records: list[dict], places: list[dict] | None = None) -> list[str]:
        return FixtureDataset.make(records, places).validate(check_files=False)

    def assertReported(self, records: list[dict], fragment: str, places: list[dict] | None = None):
        problems = self.problems(records, places)
        self.assertTrue(any(fragment in p for p in problems), f"expected a problem containing {fragment!r}, got {problems}")

    def test_valid_fixture_has_no_problems(self):
        self.assertEqual(self.problems(valid_pair()), [])

    def test_unknown_vocabulary_value(self):
        records = valid_pair()
        records[0]["kind"] = "sorcery"
        self.assertReported(records, "'sorcery' is not in vocabulary 'kind'")

    def test_reference_to_missing_place(self):
        records = valid_pair()
        records[0]["places"] = [{"place": "atlantis"}]
        self.assertReported(records, "'atlantis' is not in places")

    def test_facet_value_without_basis(self):
        records = valid_pair()
        records[0]["scale"] = "modular"
        self.assertReported(records, "'scale' has a value and no basis")

    def test_earliest_record_points_at_missing_event(self):
        records = valid_pair()
        records[0]["earliest_record"] = {"event": "never-happened"}
        self.assertReported(records, "earliest_record: no event 'never-happened'")

    def test_event_earliest_after_latest(self):
        records = valid_pair()
        records[0]["events"] = [event("made", 1900, 1800)]
        self.assertReported(records, "earliest is after latest")

    def test_year_zero(self):
        records = valid_pair()
        records[0]["events"] = [event("made", -5, 0)]
        self.assertReported(records, "there is no year 0")

    def test_established_link_without_evidence(self):
        records = valid_pair()
        records[1]["links"][0]["status"] = "established"
        self.assertReported(records, "an established link needs evidence")

    def test_discovery_in_wrong_domain_folder(self):
        records = valid_pair()
        data = FixtureDataset.make(records)
        data.paths["discoveries/earlier-engine"] = DATA / "discoveries" / "food" / "earlier-engine.json"
        problems = data.validate(check_files=False)
        self.assertTrue(any("earlier-engine: belongs at data/discoveries/energy/" in p for p in problems), problems)

    def test_places_within_loop(self):
        places = [
            {"id": "testland", "name": "Testland", "kind": "country", "lat": 50.0, "lon": 10.0, "region": "europe", "within": "testtown", "basis": "recalled"},
            {"id": "testtown", "name": "Testtown", "kind": "settlement", "lat": 50.1, "lon": 10.1, "region": "europe", "within": "testland", "basis": "recalled"},
        ]
        self.assertReported(valid_pair(), "'within' loops back on itself", places)


class YearValueTest(unittest.TestCase):
    """Dates become a continuous number of years with no gap between the eras."""

    def test_era_boundary_has_no_gap(self):
        self.assertEqual(year_value(point(-1)), 0)
        self.assertEqual(year_value(point(1)), 1)
        self.assertEqual(year_value(point(1)) - year_value(point(-1)), 1)

    def test_bce_years_are_one_apart(self):
        self.assertEqual(year_value(point(-1)) - year_value(point(-2)), 1)

    def test_month_and_day_move_forward(self):
        start = year_value({"year": 1850})
        july = year_value({"year": 1850, "month": 7})
        july_15 = year_value({"year": 1850, "month": 7, "day": 15})
        self.assertLess(start, july)
        self.assertLess(july, july_15)
        self.assertLess(july_15, year_value({"year": 1851}))


class PersonYearsTest(unittest.TestCase):
    """The area under the population curve is integrated exactly between estimates."""

    def test_constant_population(self):
        series = build.cumulative_person_years([[0, 1000], [100, 1000]])
        self.assertEqual(series[-1][0], 100)
        self.assertAlmostEqual(series[-1][1], 1000 * 100, places=6)

    def test_doubling_population_matches_closed_form(self):
        p0, p1, dt = 1_000_000, 2_000_000, 500
        series = build.cumulative_person_years([[1000, p0], [1000 + dt, p1]])
        expected = (p1 - p0) * dt / math.log(p1 / p0)
        self.assertAlmostEqual(series[-1][1], expected, delta=expected * 1e-9)

    def test_series_strictly_increasing(self):
        series = build.cumulative_person_years([[-10000, 4_000_000], [0, 190_000_000], [1000, 275_000_000], [1900, 1_600_000_000]])
        for (y0, v0), (y1, v1) in zip(series, series[1:]):
            self.assertLess(y0, y1)
            self.assertLess(v0, v1)


class BuildTest(unittest.TestCase):
    """The compiled bundle is internally consistent and reproducible."""

    @classmethod
    def setUpClass(cls):
        cls.data = Dataset.load()
        cls.bundle = build.build(cls.data)

    def test_dated_discoveries_have_a_position(self):
        compiled = {d["id"]: d for d in self.bundle["discoveries"]}
        for record in self.data.discoveries.values():
            if record["earliest_record"].get("event"):
                t = compiled[record["id"]].get("t")
                self.assertIsInstance(t, (int, float), record["id"])
                self.assertTrue(math.isfinite(t), record["id"])

    def test_links_join_real_discoveries(self):
        ids = {d["id"] for d in self.bundle["discoveries"]}
        for link in self.bundle["links"]:
            self.assertIn(link["from"], ids)
            self.assertIn(link["to"], ids)

    def test_drawn_places_exist(self):
        for d in self.bundle["discoveries"]:
            if "at" in d:
                self.assertIn(d["at"]["place"], self.bundle["places"], d["id"])

    def test_build_is_deterministic(self):
        again = build.build(Dataset.load())
        self.assertEqual(json.dumps(self.bundle, ensure_ascii=False), json.dumps(again, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
