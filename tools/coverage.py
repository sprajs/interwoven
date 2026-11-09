#!/usr/bin/env python3
"""Show how much of each facet has been researched, and list what is left.

    python tools/coverage.py                      # one row per facet
    python tools/coverage.py --by domain          # the same, split by domain
    python tools/coverage.py --missing places     # discoveries with no value for a facet
    python tools/coverage.py --basis recalled     # discoveries with any facet entered from memory
    python tools/coverage.py --basis recalled --facet people
    python tools/coverage.py --grid               # discoveries per domain, by region and by era

This is how one facet is researched across the whole dataset: list what is missing, fill it in,
and run it again.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict

from dataset import FACETS, Dataset, year_value

BASES = ("reviewed", "sourced", "recalled", "unknown", "not_applicable")


def facet_state(record: dict, facet: str) -> str:
    return record["research"]["basis"].get(facet, "missing")


def table(records: list[dict]) -> list[str]:
    lines = [f"{'facet':<16}" + "".join(f"{b:>16}" for b in BASES) + f"{'missing':>16}"]
    for facet in FACETS:
        counts = Counter(facet_state(r, facet) for r in records)
        lines.append(f"{facet:<16}" + "".join(f"{counts[b]:>16}" for b in BASES) + f"{counts['missing']:>16}")
    return lines


REGIONS = ("africa", "asia", "europe", "north_america", "south_america", "oceania")
#: The eras of the grid: a name and the year each one ends before.
ERAS = (("before 3000 BCE", -2999), ("to 500 CE", 501), ("to 1500", 1501), ("to 1800", 1801), ("to 1950", 1951), ("since 1950", 10**9))


def grid(data: Dataset) -> list[str]:
    """Discoveries per domain, across the regions and across the eras. An empty cell is a gap to fill."""
    places = data.registers["places"]
    by_region: dict[str, Counter] = defaultdict(Counter)
    by_era: dict[str, Counter] = defaultdict(Counter)
    for record in data.discoveries.values():
        domain = record["domain"].split(".")[0]
        regions = {places[p["place"]]["region"] for p in record.get("places", []) if p["place"] in places}
        for region in regions or {"unplaced"}:
            by_region[domain][region] += 1
        event = data.earliest_record(record)
        if event is None:
            by_era[domain]["undated"] += 1
        else:
            year = year_value(event["date"]["latest"])
            by_era[domain][next(name for name, end in ERAS if year < end)] += 1
    domains = [d["id"] for d in data.taxonomy["domains"]]
    lines = ["By region", f"{'domain':<20}" + "".join(f"{r[:13]:>14}" for r in (*REGIONS, "unplaced"))]
    lines += [f"{d:<20}" + "".join(f"{by_region[d][r] or '.':>14}" for r in (*REGIONS, "unplaced")) for d in domains]
    eras = [name for name, _ in ERAS] + ["undated"]
    lines += ["", "By era", f"{'domain':<20}" + "".join(f"{e:>16}" for e in eras)]
    lines += [f"{d:<20}" + "".join(f"{by_era[d][e] or '.':>16}" for e in eras) for d in domains]
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--by", choices=["domain", "kind", "tier"], help="split the table")
    parser.add_argument("--missing", metavar="FACET", choices=FACETS, help="list discoveries lacking this facet")
    parser.add_argument("--basis", choices=BASES, help="list discoveries with a facet on this basis")
    parser.add_argument("--facet", choices=FACETS, help="with --basis, look at one facet only")
    parser.add_argument("--grid", action="store_true", help="count discoveries per domain by region and by era")
    args = parser.parse_args()

    data = Dataset.load()
    records = sorted(data.discoveries.values(), key=lambda r: (r["domain"], r["id"]))

    if args.grid:
        print("\n".join(grid(data)))
        return 0

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
