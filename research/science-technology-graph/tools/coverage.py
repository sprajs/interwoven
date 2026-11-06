#!/usr/bin/env python3
"""Compare community-entry coverage using supplied date limits, not invention dates."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess

from query import entry_date

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
RELATIVE = ROOT.relative_to(REPO)
ERAS = ("Before 500 CE", "500–1499", "1500–1749", "1750–1944", "1945 onward")


def read_records(kind, revision=None):
    path = RELATIVE / "data" / f"{kind}.jsonl"
    text = subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=REPO, text=True) if revision else (REPO / path).read_text()
    return [json.loads(line) for line in text.splitlines()]


def coverage(revision=None):
    nodes = read_records("nodes", revision)
    events = {event["id"]: event for event in read_records("events", revision)}
    eras, strengths, limits = Counter(), Counter(), Counter()
    unplaced = []
    for node in nodes:
        anchor = node["graph_anchor"]
        if anchor["status"] != "selected":
            unplaced.append(node["id"])
            continue
        date = entry_date(anchor, events[anchor["event_id"]])
        bound = date.get("latest", date.get("earliest"))
        year = bound["year"]
        era = ERAS[0 if year < 500 else 1 if year < 1500 else 2 if year < 1750 else 3 if year < 1945 else 4]
        eras[era] += 1
        strengths[anchor["evidence_strength"]] += 1
        limits["upper only" if "earliest" not in date else "lower only" if "latest" not in date else "both limits"] += 1
    assert sum(eras.values()) + len(unplaced) == len(nodes)
    return {"nodes": len(nodes), "eras": {era: eras[era] for era in ERAS}, "evidence_strength": dict(strengths), "date_limits": dict(limits), "unplaced": unplaced}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default="96b3199", help="Placement checkpoint commit to compare with the current files.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = {"method": "Classify each selected community-entry date by its supplied latest year, or earliest year if it has only a lower bound. A known-by upper limit does not establish the true onset era; these are placement-coverage counts, not invention dates or evidence of continuous use.", "baseline": args.baseline, "before": coverage(args.baseline), "after": coverage()}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["method"])
        print("\n| Placement limit | Before | After | Change |\n| --- | ---: | ---: | ---: |")
        for era in ERAS:
            before, after = result["before"]["eras"][era], result["after"]["eras"][era]
            print(f"| {era} | {before} | {after} | {after-before:+d} |")
        print(f"\nTotal entries: {result['before']['nodes']} → {result['after']['nodes']}.")


if __name__ == "__main__":
    main()
