"""Verify the reviewed wave at a checkout and summarize only its owned records."""
import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

ROUND = Path("docs/reviews/2026-11-17-modern")
BASE = "71326e01a105da21decb1587195a81bd5b596b8c"
LANES = "agriculture chips communications computing energy grid health instruments land manufacturing transport water".split()
GRAPH_TYPES = {"requires", "builds_on", "uses_instrument", "uses_process", "uses_theory", "adapts", "supersedes", "part_of", "transmitted_from"}
STATUSES = {"in service", "commercially available", "demonstrated", "proposed", "retired", "suspended"}


def git(*args):
    return subprocess.check_output(["git", *args])


def check(condition, detail):
    if not condition:
        raise ValueError(detail)


def changes(before, after, key):
    old = {key(item): item for item in before}
    new = {key(item): item for item in after}
    return len(new.keys() - old.keys()), sum(old[k] != new[k] for k in new.keys() & old.keys())


def audit():
    totals = Counter()
    statuses = Counter()
    lanes = {}
    owners = {}
    bound = set()
    for lane in LANES:
        review = json.loads((ROUND / "reviews" / f"{lane}.json").read_bytes())
        check((review["decision"], review["reviewer"], review["effort"], review["base"]) ==
              ("accept", "gpt-6.1-terra", "high", BASE), f"Review gate: {lane}")
        proposal, files = review["proposal"], review["files"]
        status_paths = git("diff", "--name-status", "-z", "--no-renames", BASE, proposal).decode().split("\0")[:-1]
        changed = dict(zip(status_paths[1::2], status_paths[::2]))
        check(set(changed) == set(files) and all(v in {"A", "M"} for v in changed.values()), f"Review file coverage: {lane}")
        lane_path = ROUND / "lanes" / f"{lane}.json"
        check(str(lane_path) in files and review["claims"], f"Missing evidence review: {lane}")
        rows = json.loads(lane_path.read_bytes())
        check(rows["researcher"] == "gpt-6.2-sol" and rows["effort"] == "high" and rows["as_of"] == "2026-11-17", lane)
        for item in rows["inventory"]:
            check(item["status"] in STATUSES and item["date"] <= rows["as_of"] and item["limit"] and item["sources"], item["name"])
            statuses[item["status"]] += 1
        counts = Counter(observations=len(rows["inventory"]))
        record_ids = []
        for name, digest in files.items():
            path = Path(name)
            check(name not in owners, f"Overlapping ownership of {name}")
            owners[name] = lane
            check(hashlib.sha256(path.read_bytes()).hexdigest() == digest, f"Working files differ: {name}")
            proposed = git("show", f"{proposal}:{name}")
            check(hashlib.sha256(proposed).hexdigest() == digest, f"Proposal differs: {name}")
            if name.startswith("data/sources/"):
                counts["new_sources" if changed[name] == "A" else "extended_sources"] += 1
            if not name.startswith("data/discoveries/"):
                continue
            after = json.loads(proposed)
            before = {} if changed[name] == "A" else json.loads(git("show", f"{BASE}:{name}"))
            counts["new_records" if not before else "extended_records"] += 1
            record_ids.append(after["id"])
            new, revised = changes(before.get("events", []), after["events"], lambda e: e["id"])
            counts.update(new_events=new, revised_events=revised)
            for link in after.get("links", []):
                prior = before.get("links", [])
                if not any((l["from"], l["type"], l["status"]) ==
                           (link["from"], link["type"], link["status"]) for l in prior):
                    counts[f'{link["status"]}_links'] += 1
                    if link["status"] == "established" and link["type"] in GRAPH_TYPES:
                        bound.add((link["from"], after["id"], link["type"]))
        counts["review_bound_files"] = len(files)
        totals.update(counts)
        lanes[lane] = {"counts": dict(counts), "records": sorted(record_ids), "proposal": proposal}
    records = {p.stem: p for p in Path("data/discoveries").glob("*/*.json")}
    for lane in LANES:
        for item in json.loads((ROUND / "lanes" / f"{lane}.json").read_bytes())["inventory"]:
            check(set(item["records"]) <= records.keys(), f"Unknown record in {item['name']}")
    return {"base": BASE, "as_of": "2026-11-17", "counts": dict(totals), "status_counts": dict(statuses),
            "lanes": lanes, "new_graph_edges": [list(edge) for edge in sorted(bound)]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    target = parser.parse_args().output
    result = audit()
    if target:
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result["counts"], sort_keys=True))
