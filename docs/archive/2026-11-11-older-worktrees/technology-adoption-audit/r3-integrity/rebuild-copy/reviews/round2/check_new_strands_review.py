"""Verify target integrity, preregistered sample and review evidence transport."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "wave2-source-snapshot"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def record_sha(record):
    return hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


checks = []


def check(name, condition, detail=None):
    checks.append({"check": name, "pass": bool(condition), "detail": detail})


manifest = read(SNAP / "MANIFEST.json")
audit = read(ROOT / "NEW_STRANDS_SOURCE_AUDIT.json")
registration = read(ROOT / "NEW_STRANDS_PREREGISTRATION.json")
provenance = read(ROOT / "NEW_STRANDS_SOURCE_PROVENANCE.json")
before = read(ROOT / "NEW_STRANDS_MANIFEST_CHECK.json")

check("manifest-identity-before-and-after", sha(SNAP / "MANIFEST.json") == before["manifest_sha256"] == audit["target"]["manifest_sha256"] == registration["snapshot_manifest_sha256"])
bad_target = []
for path, expected in manifest["files"].items():
    file = (SNAP / path).resolve()
    if not file.is_relative_to(SNAP.resolve()) or not file.is_file() or sha(file) != expected:
        bad_target.append(path)
check("all-frozen-target-files-still-match", not bad_target, {"count": len(manifest["files"]), "failures": bad_target})
check("registration-identity", sha(ROOT / audit["registration"]["path"]) == audit["registration"]["sha256"])

claims = {}
sources = {}
edges = {}
cases = {}
selected = []
for strand, plan in registration["strands"].items():
    base = SNAP / "contributions" / strand
    strand_claims = read(base / "claims.json")
    claims.update({c["id"]: c for c in strand_claims})
    sources.update({s["id"]: s for s in read(base / "sources.json")})
    edges.update({e["id"]: e for e in read(base / "graph.json")["edges"]})
    cases.update({c["id"]: c for c in read(base / "cases.json")})
    selected.extend(plan["selected"])
    candidates = [{"id": c["id"], "sha256": hashlib.sha256((registration["selection_rule"]["seed"] + "|" + c["id"]).encode()).hexdigest()} for c in strand_claims if c["id"] not in plan["purposive_reasons"]]
    candidates.sort(key=lambda x: (x["sha256"], x["id"]))
    check(strand + "-ordinary-selection-reproduced", candidates == plan["ordinary_candidates_ranked"] and candidates[0]["id"] == plan["ordinary_selected"])
    check(strand + "-two-purposive-plus-one-ordinary", len(plan["purposive_reasons"]) == 2 and set(plan["selected"]) == set(plan["purposive_reasons"]) | {plan["ordinary_selected"]})

check("claim-sample-not-substituted", len(selected) == len(set(selected)) == 9 and set(selected) == {v["claim_id"] for v in audit["claim_audits"]})
check("audited-claim-records-match-target", all(record_sha(claims[v["claim_id"]]) == v["frozen_record_sha256"] for v in audit["claim_audits"]))
expected_sources = {s["source_id"] for cid in selected for s in claims[cid]["sources"]}
check("source-denominator-and-records-match", expected_sources == {s["source_id"] for s in audit["source_inspections"]} and len(expected_sources) == 9 and all(record_sha(sources[s["source_id"]]) == s["frozen_source_record_sha256"] for s in audit["source_inspections"]))
expected_edges = {e["id"] for e in edges.values() if set(e["claim_ids"]) & set(selected)}
check("all-incident-edge-propositions-accounted-for", expected_edges == {v["edge_id"] for v in audit["edge_audits"]} and len(expected_edges) == 11)
check("audited-edge-records-match-target", all(record_sha(edges[v["edge_id"]]) == v["frozen_record_sha256"] for v in audit["edge_audits"]))

bad_evidence = []
for path, info in provenance["evidence_file_manifest"].items():
    file = (ROOT / path).resolve()
    if not file.is_relative_to(ROOT.resolve()) or not file.is_file() or sha(file) != info["sha256"] or file.stat().st_size != info["bytes"]:
        bad_evidence.append(path)
check("evidence-file-hashes-and-path-safety", not bad_evidence, {"files": len(provenance["evidence_file_manifest"]), "failures": bad_evidence})
check("source-evidence-fingerprints", all(sha(ROOT / "new-strands-evidence" / path) == expected for s in audit["source_inspections"] for path, expected in s["evidence_file_hashes"].items()))
check("population-denominators", (len(cases), len(claims), len(sources), len(edges)) == (14, 56, 41, 55))
check("required-findings-target-current-frozen-values", len(audit["findings"]) == 2 and claims["OCE-K11"]["test"]["status"] == "evaluated" and claims["ENE-K01"]["statement"].startswith("For US PV"))
check("observed-telegraph-percentage-arithmetic", [round(x, 2) for x in provenance["numerical_check"]["percentage_magnitudes"]] == [4.24, 5.24, 5.50])

broken_links = []
report = ROOT / "NEW_STRANDS_SOURCE_REVIEW.md"
for match in re.finditer(r"\]\(([^)]+)\)", report.read_text()):
    target = match.group(1)
    if "://" not in target and not target.startswith("#"):
        path = (report.parent / target.split("#")[0]).resolve()
        if not path.exists():
            broken_links.append(target)
check("review-report-local-links", not broken_links, broken_links)

result = {
    "checked_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "all_pass": all(c["pass"] for c in checks),
    "checks_passed": sum(c["pass"] for c in checks),
    "checks_total": len(checks),
    "checks": checks,
    "verification_scope": "Integrity and transport only; does not mechanically validate historical or causal judgments.",
    "review_outputs": {name: sha(ROOT / name) for name in ("NEW_STRANDS_SOURCE_REVIEW.md", "NEW_STRANDS_SOURCE_AUDIT.json", "NEW_STRANDS_SOURCE_PROVENANCE.json", "NEW_STRANDS_PREREGISTRATION.json")},
}
(ROOT / "NEW_STRANDS_REVIEW_CHECKS.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: result[k] for k in ("all_pass", "checks_passed", "checks_total", "checked_utc")}, indent=2))
raise SystemExit(0 if result["all_pass"] else 1)
