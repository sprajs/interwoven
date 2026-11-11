#!/usr/bin/env python3
"""Check the bounded SB repair bytes and unchanged-scope invariants."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
OLD = ROOT / "skills-behaviour-snapshot"
NEW = ROOT / "sb-repair-snapshot"


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


manifest = read(NEW / "MANIFEST.json")
checks = []
for relative, expected in manifest["files"].items():
    path = (NEW / relative).resolve()
    assert path.is_relative_to(NEW.resolve()), relative
    actual = sha(path)
    assert actual == expected, relative
    checks.append({"file": relative, "sha256": actual, "matches": True})

expected_changes = {
    "cases.json": {"PSY-C05"},
    "claims.json": {"PSY-K20"},
    "sources.json": {"PSY-S11", "PSY-S14"},
    "comparisons.json": {"PSY-X05"},
}
changes = {}
for filename, expected in expected_changes.items():
    old = {x["id"]: x for x in read(OLD / "contributions/PSY" / filename)}
    new = {x["id"]: x for x in read(NEW / "contributions/PSY" / filename)}
    assert set(old) == set(new), filename
    changed = {key for key in old if old[key] != new[key]}
    assert changed == expected, filename
    changes[filename] = sorted(changed)

psy_old = read(OLD / "contributions/PSY/graph.json")
psy_new = read(NEW / "contributions/PSY/graph.json")
assert psy_old["nodes"] == psy_new["nodes"]
psy_old_edges = {e["id"]: e for e in psy_old["edges"]}
psy_new_edges = {e["id"]: e for e in psy_new["edges"]}
assert set(psy_old_edges) == set(psy_new_edges)
assert {key for key in psy_old_edges if psy_old_edges[key] != psy_new_edges[key]} == {"PSY-E14"}
old_e14 = dict(psy_old_edges["PSY-E14"])
new_e14 = dict(psy_new_edges["PSY-E14"])
old_e14.pop("dispute")
new_e14.pop("dispute")
assert old_e14 == new_e14
changes["graph.json"] = ["PSY-E14.dispute"]

k20 = next(c for c in read(NEW / "contributions/PSY/claims.json") if c["id"] == "PSY-K20")
assert k20["causal_status"] == "causal-identification"
assert k20["test"]["status"] == "underdetermined"
assert {s["source_id"] for s in k20["sources"]} == {"PSY-S11", "PSY-S14"}

skl_old = read(OLD / "contributions/SKL/graph.json")
skl_new = read(NEW / "contributions/SKL/graph.json")
old_nodes = {n["id"]: n for n in skl_old["nodes"]}
new_nodes = {n["id"]: n for n in skl_new["nodes"]}
assert set(new_nodes) - set(old_nodes) == {"SKL-T28", "SKL-T29", "SKL-T30"}
assert all(new_nodes[key] == value for key, value in old_nodes.items())
old_edges = {e["id"]: e for e in skl_old["edges"]}
new_edges = {e["id"]: e for e in skl_new["edges"]}
assert set(old_edges) == set(new_edges)
targets = {"SKL-E17": "SKL-T29", "SKL-E18": "SKL-T30", "SKL-E19": "SKL-T28"}
for key, old in old_edges.items():
    expected = dict(old)
    if key in targets:
        assert old["to"] == "SKL-T23"
        expected["to"] = targets[key]
    assert new_edges[key] == expected, key
assert new_edges["SKL-E16"] == old_edges["SKL-E16"]
assert all(e["from"] in new_nodes and e["to"] in new_nodes for e in new_edges.values())
assert not any(e["from"] in targets.values() for e in new_edges.values())
assert [e["id"] for e in new_edges.values() if e["to"] == "SKL-T23"] == ["SKL-E16"]

handoff_path = ROOT.parents[1] / "contributions/PSY/drafts/source-audit-repair-2026-11-05/AFTER_MANIFEST.json"
handoff = read(handoff_path)
author_hashes = {x["file"]: x["sha256"] for x in handoff["files"]}
author_matches = []
for relative in manifest["files"]:
    if relative.startswith("contributions/PSY/"):
        filename = Path(relative).name
        assert sha(NEW / relative) == author_hashes[filename], filename
        author_matches.append(filename)

evidence_manifest = read(ROOT / "SKILLS_BEHAVIOUR_EVIDENCE_MANIFEST.json")
evidence_names = [
    "PSY-S11.pdf", "PSY-S11.txt", "PSY-S14-search-primary-output.txt",
    "SKL-institutional-and-publisher-pages.txt",
]
evidence_checks = []
for name in evidence_names:
    relative = "skills-behaviour-evidence/" + name
    actual = sha(ROOT / relative)
    assert actual == evidence_manifest["files"][relative]
    evidence_checks.append({"file": relative, "sha256": actual, "matches": True})

result = {
    "status": "pass",
    "manifest_sha256": sha(NEW / "MANIFEST.json"),
    "frozen_file_checks": checks,
    "psy_changed_records": changes,
    "psy_author_handoff_matches": sorted(author_matches),
    "psy_author_handoff_manifest_sha256": sha(handoff_path),
    "skl_added_nodes": sorted(set(new_nodes) - set(old_nodes)),
    "skl_retargeted_edges": targets,
    "skl_all_other_edge_fields_unchanged": True,
    "skl_new_outcome_nodes_have_no_outgoing_edges": True,
    "original_evidence_checks": evidence_checks,
    "numeric_estimates_outside_k20_unchanged": True,
    "structural_checks_do_not_establish_historical_truth": True,
}
print(json.dumps(result, indent=2))
