"""Research observations must retain their provenance in the app bundle."""

import unittest

import build
from dataset import source_path
from tests.test_dataset import FixtureDataset, discovery


class ResearchEvidenceBuildTest(unittest.TestCase):
    def test_sources_used_only_by_observations_and_contributions_are_included(self):
        record = discovery("research-observations")
        record["measures"] = [{
            "quantity": "advertised price", "value": 12, "unit": "shillings",
            "event": "made", "status": "claimed", "currency": "shillings",
            "money_context": "Original nominal offer; no affordability conversion.",
            "evidence": [{"source": "price-only", "locator": "p. 1", "supports": "Price offered."}],
        }]
        record["research"]["basis"]["measures"] = "sourced"
        record["events"][0]["contributions"] = [{
            "person": "ada-tester", "role": "supplier", "resource": "equipment",
            "evidence": [{"source": "actor-only", "locator": "p. 2", "supports": "Equipment supplied."}],
        }]
        data = FixtureDataset.make([record])
        for key in ("price-only", "actor-only"):
            data.sources[key] = {"id": key, "title": key, "authors": [], "year": 1800, "access": "full-text"}
            data.paths["sources/" + key] = source_path(key)
        self.assertEqual(data.validate(check_files=False), [])
        bundle = build.build(data)
        compiled = bundle["discoveries"][0]
        self.assertEqual(compiled["measures"], record["measures"])
        self.assertEqual(compiled["events"][0]["contributions"], record["events"][0]["contributions"])
        self.assertEqual(set(bundle["sources"]), {"price-only", "actor-only"})


if __name__ == "__main__":
    unittest.main()
