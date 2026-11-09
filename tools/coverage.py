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
import json
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


def audit(data: Dataset) -> dict:
    """Return catalogue coverage counts, not estimates of historical activity."""
    records = list(data.discoveries.values())
    grains = (*data.vocab["grain"]["values"], "unassessed")
    region_keys = (*REGIONS, "unplaced")
    era_keys = (*(name for name, _ in ERAS), "undated")
    domain_rows = {d: [] for d in data.domains}
    field_rows = {f: [] for f in data.fields}
    places = data.registers["places"]

    def regions(record: dict) -> set[str]:
        found = {places[p["place"]].get("region") for p in record.get("places", []) if p.get("place") in places}
        found.discard(None)
        return found or {"unplaced"}

    def era(record: dict) -> str:
        event = data.earliest_record(record)
        if event is None:
            return "undated"
        year = year_value(event["date"]["latest"])
        return next((name for name, end in ERAS if year < end), ERAS[-1][0])

    def summarize(rows: list[dict]) -> dict:
        grain_counts = Counter(r.get("grain") or "unassessed" for r in rows)
        region_counts = Counter(region for r in rows for region in regions(r))
        era_counts = Counter(era(r) for r in rows)
        return {
            "records": len(rows),
            "grain": {k: grain_counts[k] for k in grains},
            "regions": {k: region_counts[k] for k in region_keys},
            "eras": {k: era_counts[k] for k in era_keys},
        }

    for record in records:
        fields = {record["domain"], *record.get("fields", [])}
        for field in fields:
            if field in field_rows:
                field_rows[field].append(record)
        for domain in {field.split(".")[0] for field in fields}:
            if domain in domain_rows:
                domain_rows[domain].append(record)

    linked = list(data.links())
    links = [link for _, link in linked]
    layers = data.vocab["link"]["layers"]
    type_layers = {link_type: layer for layer, types in layers.items() for link_type in types}
    established_by_layer = Counter()
    touched_by_layer: dict[str, set[str]] = {layer: set() for layer in layers}
    for receiver, link in linked:
        if link.get("status") != "established":
            continue
        layer = type_layers.get(link.get("type"))
        if layer is None:
            continue
        established_by_layer[layer] += 1
        touched_by_layer[layer].add(receiver["id"])
        if link.get("from") in data.discoveries:
            touched_by_layer[layer].add(link["from"])
    causal_touch = touched_by_layer["dependence"] | touched_by_layer["transmission"]
    no_causal_touch = sorted(set(data.discoveries) - causal_touch)
    missing_prerequisites = sorted(r["id"] for r in records if r.get("research", {}).get("missing_prerequisites"))
    absent_prerequisites = sum("missing_prerequisites" not in r.get("research", {}) for r in records)
    empty_prerequisites = sum(r.get("research", {}).get("missing_prerequisites") == [] for r in records)
    statuses = (*data.vocab["link_status"]["values"], "missing")
    status_counts = Counter(link.get("status") or "missing" for link in links)
    leads = list(data.registers["leads"].values())
    lead_statuses = (*data.vocab["lead_status"]["values"], "missing")
    lead_fields = {field: Counter() for field in field_rows}
    lead_unclassified = Counter()
    for lead in leads:
        status = lead.get("status") or "missing"
        if lead.get("field"):
            lead_fields.setdefault(lead["field"], Counter())[status] += 1
        else:
            lead_unclassified[status] += 1

    def lead_counts(counts: Counter) -> dict:
        return {"total": sum(counts.values()), "status": {status: counts[status] for status in lead_statuses}}
    facets = {}
    for facet in FACETS:
        states = Counter(facet_state(r, facet) for r in records)
        facets[facet] = {state: states[state] for state in (*BASES, "missing")}
    return {
        "schema_version": 1,
        "semantics": {
            "scope": "Counts describe this catalogue, not historical activity or absence.",
            "fields_and_domains": "A record counts once in each primary or cross-listed field and domain; groups can overlap.",
            "regions": "Distinct regions of recorded places; a record can count in more than one region. Unplaced means no recorded region.",
            "eras": "The latest endpoint of the earliest-record event determines the era; undated means no such event. This is not necessarily the date of invention.",
            "grain": "Unassessed means no grain value; basis counts separately distinguish missing from unknown.",
            "link_coverage": "Carrier and contribution count links with at least one value, including candidate and insufficient links.",
            "leads": "Fields count only explicit lead.field values; unclassified leads have no field. Lead status is independent of discovery status.",
            "established_network": "A link is stored on the receiving record and from identifies the other record, usually an antecedent (for part_of, the whole). Both endpoints count as touched; dependence and transmission are distinct from affinity and parallel. Missing established links are missing catalogue evidence, not evidence of no historical dependency. Counts do not measure historical importance.",
            "missing_prerequisites": "Present means a nonempty list of recorded research leads; absent and empty do not prove no prerequisite existed.",
        },
        "counts": {
            "discoveries": len(records),
            "events": sum(len(r.get("events", [])) for r in records),
            "links": len(links),
            "sources": len(data.sources),
            "leads": len(leads),
        },
        "overall": summarize(records),
        "domains": {k: summarize(v) for k, v in domain_rows.items()},
        "fields": {k: summarize(v) for k, v in field_rows.items()},
        "established_network": {
            "layers": {layer: {"links": established_by_layer[layer], "touched_records": len(touched_by_layer[layer])} for layer in layers},
            "dependence_or_transmission": {"links": established_by_layer["dependence"] + established_by_layer["transmission"], "touched_records": len(causal_touch)},
            "without_established_dependence_or_transmission": {"count": len(no_causal_touch), "records": no_causal_touch},
        },
        "missing_prerequisites": {"count": len(missing_prerequisites), "records": missing_prerequisites, "absent": absent_prerequisites, "empty": empty_prerequisites},
        "facet_basis": facets,
        "leads": {"fields": {field: lead_counts(counts) for field, counts in lead_fields.items()}, "unclassified": lead_counts(lead_unclassified)},
        "links": {
            "status": {k: status_counts[k] for k in statuses},
            "carrier": {"present": sum(bool(link.get("carrier")) for link in links), "missing": sum(not link.get("carrier") for link in links)},
            "contribution": {"present": sum(bool(link.get("contribution")) for link in links), "missing": sum(not link.get("contribution") for link in links)},
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--by", choices=["domain", "kind", "tier"], help="split the table")
    parser.add_argument("--missing", metavar="FACET", choices=FACETS, help="list discoveries lacking this facet")
    parser.add_argument("--basis", choices=BASES, help="list discoveries with a facet on this basis")
    parser.add_argument("--facet", choices=FACETS, help="with --basis, look at one facet only")
    parser.add_argument("--grid", action="store_true", help="count discoveries per domain by region and by era")
    parser.add_argument("--json", action="store_true", help="emit the versioned catalogue coverage audit as JSON")
    args = parser.parse_args()

    data = Dataset.load()
    records = sorted(data.discoveries.values(), key=lambda r: (r["domain"], r["id"]))

    if args.json:
        if args.grid or args.by or args.missing or args.basis or args.facet:
            parser.error("--json cannot be combined with text report options")
        print(json.dumps(audit(data), indent=2, ensure_ascii=False))
        return 0

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
