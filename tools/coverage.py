#!/usr/bin/env python3
"""Show how much of each facet has been researched, and list what is left.

    python tools/coverage.py                      # one row per facet
    python tools/coverage.py --by domain          # the same, split by domain
    python tools/coverage.py --missing places     # discoveries with no value for a facet
    python tools/coverage.py --basis recalled     # discoveries with any facet entered from memory
    python tools/coverage.py --basis recalled --facet people

This is how one facet is researched across the whole dataset: list what is missing, fill it in,
and run it again.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict

from dataset import FACETS, Dataset

BASES = ("reviewed", "sourced", "recalled", "unknown", "not_applicable")


def facet_state(record: dict, facet: str) -> str:
    return record["research"]["basis"].get(facet, "missing")


def table(records: list[dict]) -> list[str]:
    lines = [f"{'facet':<16}" + "".join(f"{b:>16}" for b in BASES) + f"{'missing':>16}"]
    for facet in FACETS:
        counts = Counter(facet_state(r, facet) for r in records)
        lines.append(f"{facet:<16}" + "".join(f"{counts[b]:>16}" for b in BASES) + f"{counts['missing']:>16}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--by", choices=["domain", "kind", "tier"], help="split the table")
    parser.add_argument("--missing", metavar="FACET", choices=FACETS, help="list discoveries lacking this facet")
    parser.add_argument("--basis", choices=BASES, help="list discoveries with a facet on this basis")
    parser.add_argument("--facet", choices=FACETS, help="with --basis, look at one facet only")
    args = parser.parse_args()

    records = sorted(Dataset.load().discoveries.values(), key=lambda r: (r["domain"], r["id"]))

    if args.missing:
        rows = [r for r in records if facet_state(r, args.missing) == "missing"]
        for r in rows:
            print(f"{r['domain']:<34} {r['id']}")
        print(f"{len(rows)} of {len(records)} discoveries have no '{args.missing}'.")
        return 0

    if args.basis:
        count = 0
        for r in records:
            facets = [f for f in FACETS if facet_state(r, f) == args.basis and args.facet in (None, f)]
            if facets:
                count += 1
                print(f"{r['domain']:<34} {r['id']:<60} {', '.join(facets)}")
        print(f"{count} of {len(records)} discoveries.")
        return 0

    if args.by:
        groups: dict[str, list[dict]] = defaultdict(list)
        for r in records:
            key = r["domain"].split(".")[0] if args.by == "domain" else str(r.get(args.by))
            groups[key].append(r)
        for key in sorted(groups):
            print(f"\n{key} ({len(groups[key])})")
            print("\n".join(table(groups[key])))
        return 0

    print(f"{len(records)} discoveries")
    print("\n".join(table(records)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
