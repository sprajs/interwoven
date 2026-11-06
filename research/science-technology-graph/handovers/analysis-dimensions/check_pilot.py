#!/usr/bin/env python3
"""Checks the pilot coding against the graph and reproduces the figures in PROPOSAL.md.

Run from research/science-technology-graph:
    python3 handovers/analysis-dimensions/check_pilot.py
Reads the graph only. Exits with status 1 if a pilot row is invalid.
"""
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GRAPH = HERE.parents[1]


def jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


nodes = jsonl(GRAPH / "data/nodes.jsonl")
links = jsonl(GRAPH / "data/relationships.jsonl")
events = jsonl(GRAPH / "data/events.jsonl")
vocab = json.loads((HERE / "vocabulary.json").read_text())
pilot_entries = jsonl(HERE / "pilot-entries.jsonl")
pilot_links = jsonl(HERE / "pilot-links.jsonl")

by_id = {n["id"]: n for n in nodes}
link_by_id = {l["id"]: l for l in links}
statuses = set(vocab["statuses"])
errors = []


def check(row, facet, allowed):
    value = row.get(facet)
    if isinstance(value, str) and value in statuses:
        return
    values = value if isinstance(value, list) else [value]
    if not values:
        errors.append(f"{row['id']}: {facet} is empty")
    for item in values:
        if item not in allowed:
            errors.append(f"{row['id']}: {facet} has unknown value {item!r}")


for row in pilot_entries:
    if row["id"] not in by_id:
        errors.append(f"unknown entry {row['id']}")
    for facet in ("advance_type", "change_scale", "prompted_by"):
        check(row, facet, vocab["entry_facets"][facet]["values"])
for row in pilot_links:
    if row["id"] not in link_by_id and not row.get("archived"):
        errors.append(f"unknown link {row['id']}")
    for facet in ("contribution", "influence", "carrier"):
        check(row, facet, vocab["link_facets"][facet]["values"])

parents = collections.defaultdict(list)
touched = collections.Counter()
for link in links:
    if link["relation"] in {"companion-of","same-principle","same-family"}:
        continue
    source, target = link["from"]["node_id"], link["to"]["node_id"]
    parents[target].append(source)
    touched[source] += 1
    touched[target] += 1

science = [n for n in nodes if n["kind"] == "science"]
technology = [n for n in nodes if n["kind"] == "technology"]
has_kind_parent = lambda n, kind: any(by_id[p]["kind"] == kind for p in parents[n["id"]])
relation_counts = collections.Counter(l["relation"] for l in links)
unit = re.compile(r"\d\s?(mm|cm|m\b|km|Å|nm|kW|hp|%|x\b|×|percent|MHz|bit|inch|horsepower)")

print("THE GRAPH TODAY")
print(f"  entries {len(nodes)}, links {len(links)}, events {len(events)}")
print(f"  entries with no link at all: {sum(not touched[n['id']] for n in nodes)}")
print(f"  science results: {len(science)}; with a technology parent: {sum(has_kind_parent(n, 'technology') for n in science)}; with no parent: {sum(not parents[n['id']] for n in science)}")
print(f"  technologies: {len(technology)}; with a science parent: {sum(has_kind_parent(n, 'science') for n in technology)}; with no parent: {sum(not parents[n['id']] for n in technology)}")
print(f"  tier 0 entries: {sum(n.get('tier') == 0 for n in nodes)}; with no parent: {sum(n.get('tier') == 0 and not parents[n['id']] for n in nodes)}")
print(f"  largest relation type: {relation_counts.most_common(1)[0]}")
print(f"  descriptions containing a number with a unit (rough match): {sum(bool(unit.search(n.get('configuration', ''))) for n in nodes)}")
print(f"  distinct free-text regions: {len({r for n in nodes for r in n['regions']})}")

undetermined = lambda rows, facet: sum(isinstance(r.get(facet), str) and r[facet] in statuses for r in rows)
print("\nTHE PILOT (one coder, from the graph's own text, no sources reopened)")
print(f"  entries {len(pilot_entries)}, links {len(pilot_links)}")
for facet in ("advance_type", "change_scale", "prompted_by"):
    print(f"  entry {facet}: undetermined from the record in {undetermined(pilot_entries, facet)}")
for facet in ("contribution", "influence", "carrier"):
    print(f"  link {facet}: undetermined from the record in {undetermined(pilot_links, facet)}")
print(f"  entries needing a prerequisite that has no entry yet: {sum(bool(r['open_dependencies']) for r in pilot_entries)}")

print("\nWHAT THE LARGEST RELATION TYPES HIDE (pilot links only)")
cross = collections.defaultdict(collections.Counter)
for row in pilot_links:
    if row["id"] not in link_by_id:
        continue
    for value in row["contribution"]:
        cross[link_by_id[row["id"]]["relation"]][value] += 1
for relation, counts in sorted(cross.items(), key=lambda item: -sum(item[1].values())):
    detail = ", ".join(f"{value} {count}" for value, count in counts.most_common())
    print(f"  {relation}: {detail}")

if errors:
    print("\nINVALID PILOT ROWS")
    print("\n".join(f"  {error}" for error in errors))
    sys.exit(1)
print("\nAll pilot rows match the graph and the vocabulary.")
