#!/usr/bin/env python3
"""Validate review provenance and sampling; this does not validate source truth."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(path.read_text())


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_files(root, manifest):
    for relative, expected in manifest.items():
        path = (root / relative).resolve()
        assert path.is_relative_to(root.resolve()), relative
        assert sha256(path) == expected, relative


audit = read_json(ROOT / "SKILLS_BEHAVIOUR_SOURCE_AUDIT.json")
pre_path = ROOT / "SKILLS_BEHAVIOUR_PREREGISTRATION.json"
pre = read_json(pre_path)
snapshot = ROOT / "skills-behaviour-snapshot"
manifest_path = snapshot / "MANIFEST.json"
manifest = read_json(manifest_path)
assert sha256(manifest_path) == pre["manifest_sha256"] == audit["target"]["manifest_sha256"]
assert sha256(pre_path) == audit["selection"]["preregistration_sha256"]
check_files(snapshot, manifest["files"])

claims = {}
sources = {}
edges = {}
counts = {"cases": 0, "claims": 0, "source_records": 0, "edges": 0}
for domain in ("SKL", "PSY"):
    folder = snapshot / "contributions" / domain
    domain_claims = read_json(folder / "claims.json")
    domain_sources = read_json(folder / "sources.json")
    domain_edges = read_json(folder / "graph.json")["edges"]
    claims.update({item["id"]: item for item in domain_claims})
    sources.update({item["id"]: item for item in domain_sources})
    edges.update({item["id"]: item for item in domain_edges})
    counts["cases"] += len(read_json(folder / "cases.json"))
    counts["claims"] += len(domain_claims)
    counts["source_records"] += len(domain_sources)
    counts["edges"] += len(domain_edges)

risk_ids = {item["id"] for item in pre["risk"]}
for ordinary in pre["ordinary"]:
    eligible = [
        item["id"] for item in claims.values()
        if item["id"].startswith(ordinary["domain"] + "-")
        and item["causal_status"] == "descriptive" and item["id"] not in risk_ids
    ]
    ranking = sorted(
        (hashlib.sha256((pre["ordinary_seed"] + claim_id).encode()).hexdigest(), claim_id)
        for claim_id in eligible
    )
    assert ranking[0] == (ordinary["hash"], ordinary["id"])

selected_ids = {item["id"] for item in pre["claims"]}
assert selected_ids == {item["id"] for item in audit["claims"]}
for claim in pre["claims"]:
    assert claim == claims[claim["id"]], claim["id"]
selected_sources = {
    source["source_id"] for claim_id in selected_ids for source in claims[claim_id]["sources"]
}
assert selected_sources == {item["id"] for item in audit["sources"]}
for source in pre["sources"]:
    assert source == sources[source["id"]], source["id"]
assert all(item["id"] in edges for item in audit["edges"] + audit["context_edges"])
for key, value in counts.items():
    assert value == audit["denominator"][key], key

provenance = read_json(ROOT / "SKILLS_BEHAVIOUR_SOURCE_PROVENANCE.json")
for item in provenance:
    assert sha256(ROOT / item["evidence_file"]) == item["sha256"]
    assert sha256(ROOT / item["text_file"]) == item["text_sha256"]
evidence = read_json(ROOT / "SKILLS_BEHAVIOUR_EVIDENCE_MANIFEST.json")
check_files(ROOT, evidence["files"])
assert len(selected_ids) == audit["denominator"]["selected_claims"] == 8
assert len(selected_sources) == audit["denominator"]["selected_source_records"] == 9
assert len(audit["edges"]) == audit["denominator"]["directly_linked_edges_audited"] == 8
assert len(audit["context_edges"]) == audit["denominator"]["additional_edges_context_only"] == 3
assert {item["id"] for item in audit["findings"]} == {"SB01", "SB02", "SB03"}
print(json.dumps({
    "status": "pass",
    "target_files": len(manifest["files"]),
    "selected_claims": len(selected_ids),
    "source_records": len(selected_sources),
    "evidence_files": len(evidence["files"]),
    "ordinary_sample_reproduced": True,
    "factual_truth_validation": False,
}, indent=2))
