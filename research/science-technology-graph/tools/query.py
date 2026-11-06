#!/usr/bin/env python3
"""Inspect community-entry choices and traverse distinct historical relationships."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import sys

R = Path(__file__).resolve().parents[1]
BASES = ("first_commercial_availability", "commercial_availability", "practical_use", "adoption", "public_availability", "recognition", "public_awareness")
STRENGTHS = ("direct", "scoped_inference", "awareness_proxy")


def _state(record, *keys):
    current = record
    for key in keys:
        current = current.get(key) if isinstance(current, dict) else None
    return current if isinstance(current, str) else "missing"


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_number(value):
    raise ValueError(f"non-JSON number {value}")


def records(name, root=R):
    path = Path(root) / "data" / f"{name}.jsonl"
    rows, ids = [], set()
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            row = json.loads(line, object_pairs_hook=_unique_object, parse_constant=_reject_number)
        except ValueError as error:
            raise ValueError(f"{path}:{number}: {error}") from error
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"]:
            raise ValueError(f"{path}:{number}: expected an object with a nonempty string ID")
        if row["id"] in ids:
            raise ValueError(f"{path}:{number}: duplicate ID {row['id']!r}")
        ids.add(row["id"])
        rows.append(row)
    return rows


def unresolved_commercial(nodes):
    return [node for node in nodes if _state(node, "kind") == "technology"
            and _state(node, "lifecycle", "first_commercial_availability", "status") in ("unknown", "not_yet_researched")]


def _bound_label(bound):
    year = bound.get("year") if isinstance(bound, dict) else None
    if not isinstance(year, int) or isinstance(year, bool) or year == 0:
        raise ValueError("selected entry has an invalid historical year")
    label = f"{-year} BCE" if year < 0 else str(year)
    month = bound.get("month")
    if month is not None:
        if not isinstance(month, int) or isinstance(month, bool) or not 1 <= month <= 12:
            raise ValueError("selected entry has an invalid month")
        label = ("January February March April May June July August September October November December".split()[month - 1] + " " + label)
        if "day" in bound:
            label = f"{bound['day']} {label}"
    return label


def entry_date(anchor, event):
    """Return the declared community-entry date without changing its event date."""
    date = event.get("date")
    if not isinstance(date, dict) or date.get("status") not in ("known", "approximate", "bounded"):
        raise ValueError("selected community-entry event has no usable date")
    interpretation = anchor.get("date_interpretation")
    result = deepcopy(date)
    qualification = "approximately " if date["status"] == "approximate" else ""
    if interpretation == "event_date":
        if not any(isinstance(date.get(key), dict) for key in ("earliest", "latest")):
            raise ValueError("selected community-entry event has no supplied limit")
        if "earliest" not in date:
            result["label"] = "By " + qualification + _bound_label(date["latest"])
        elif "latest" not in date:
            result["label"] = "Not before " + qualification + _bound_label(date["earliest"])
        return result
    if interpretation not in ("known_by", "known_from"):
        raise ValueError("community-entry date interpretation is missing or invalid")
    supplied, missing, word = ("latest", "earliest", "By") if interpretation == "known_by" else ("earliest", "latest", "Not before")
    if not isinstance(date.get(supplied), dict):
        raise ValueError(f"{interpretation} needs the selected event's supplied {supplied} limit")
    result.update(status="approximate" if date["status"] == "approximate" else "bounded",
                  label=f"{word} {qualification}{_bound_label(date[supplied])}")
    result.pop(missing, None)
    result.pop(supplied + "_status", None)
    result[missing + "_status"] = date.get(missing + "_status", "unknown") if missing not in date else "unknown"
    return result


def community_entries(nodes, events, basis=None, strength=None, community=""):
    rows = []
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("graph_anchor"), dict):
            continue
        anchor = node["graph_anchor"]
        if anchor.get("status") != "selected":
            continue
        if basis and anchor.get("entry_basis") != basis or strength and anchor.get("evidence_strength") != strength:
            continue
        if community.lower() not in str(anchor.get("community", "")).lower():
            continue
        row = {"id": node.get("id", "missing"), "label": node.get("label", ""), "kind": _state(node, "kind"), "anchor": deepcopy(anchor)}
        try:
            if anchor.get("policy") != "community_entry":
                raise ValueError("selected anchor does not declare a community-entry policy")
            event_id = anchor.get("event_id")
            event = events.get(event_id) if isinstance(event_id, str) else None
            if not isinstance(event, dict) or event.get("node_id") != node.get("id") or not isinstance(node.get("event_ids"), list) or event_id not in node["event_ids"]:
                raise ValueError("selected community-entry event is missing or not owned by this node")
            row["entry_date"] = entry_date(anchor, event)
        except ValueError as error:
            row["anchor_error"] = str(error)
        rows.append(row)
    return rows


def _evidence_ids(value):
    if isinstance(value, dict):
        evidence = value.get("evidence")
        if isinstance(evidence, list):
            for item in evidence:
                if isinstance(item, dict) and isinstance(item.get("source_id"), str):
                    yield item["source_id"]
        for item in value.values():
            yield from _evidence_ids(item)
    elif isinstance(value, list):
        for item in value:
            yield from _evidence_ids(item)


def _endpoints(edge):
    source, target = edge.get("from"), edge.get("to")
    if not isinstance(source, dict) or not isinstance(target, dict) or not isinstance(source.get("node_id"), str) or not isinstance(target.get("node_id"), str):
        raise ValueError(f"relationship {edge.get('id', '?')!r} has invalid endpoints")
    return source["node_id"], target["node_id"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=R)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("stats")
    single = commands.add_parser("node"); single.add_argument("id")
    traversal = commands.add_parser("traverse"); traversal.add_argument("id")
    traversal.add_argument("--depth", type=int, default=1)
    traversal.add_argument("--direction", choices=("incoming", "outgoing", "both"), default="both")
    traversal.add_argument("--include-candidates", action="store_true")
    commands.add_parser("unresolved-commercial")
    entries = commands.add_parser("community-entries")
    entries.add_argument("--basis", choices=BASES)
    entries.add_argument("--strength", choices=STRENGTHS)
    entries.add_argument("--community", default="")
    args = parser.parse_args(argv)
    try:
        nodes = {row["id"]: row for row in records("nodes", args.root)}
        events = {row["id"]: row for row in records("events", args.root)}
        edges = records("relationships", args.root)
        sources = {row["id"]: row for row in records("sources", args.root)}
        if args.command == "stats":
            selected = [node["graph_anchor"] for node in nodes.values() if _state(node, "graph_anchor", "status") == "selected"]
            result = {"nodes": len(nodes), "events": len(events), "relationships": len(edges), "sources": len(sources),
                "historical_review": dict(Counter(_state(node, "review", "historical_claim") for node in nodes.values())),
                "lifecycle_review": dict(Counter(_state(node, "review", "lifecycle_classification") for node in nodes.values())),
                "commercial_availability": dict(Counter(_state(node, "lifecycle", "first_commercial_availability", "status") for node in nodes.values() if node.get("kind") == "technology")),
                "graph_anchors": dict(Counter(_state(node, "graph_anchor", "status") for node in nodes.values())),
                "entry_basis": dict(Counter(_state(anchor, "entry_basis") for anchor in selected)),
                "evidence_strength": dict(Counter(_state(anchor, "evidence_strength") for anchor in selected)),
                "date_interpretation": dict(Counter(_state(anchor, "date_interpretation") for anchor in selected))}
        elif args.command == "unresolved-commercial":
            result = [{"id": node["id"], "label": node.get("label", ""), "applicability": _state(node, "commercial_applicability", "status"),
                "status": _state(node, "lifecycle", "first_commercial_availability", "status"),
                "rationale": node["lifecycle"]["first_commercial_availability"].get("rationale", "")} for node in unresolved_commercial(nodes.values())]
        elif args.command == "community-entries":
            result = community_entries(nodes.values(), events, args.basis, args.strength, args.community)
        elif args.id not in nodes:
            raise ValueError("unknown node ID: " + args.id)
        elif args.command == "node":
            related = [edge for edge in edges if args.id in _endpoints(edge)]
            owned = [events[event_id] for event_id in nodes[args.id]["event_ids"]]
            source_ids = set(_evidence_ids([nodes[args.id], owned, related]))
            result = {"node": nodes[args.id], "events": owned,
                "incoming": [edge for edge in related if edge["to"]["node_id"] == args.id],
                "outgoing": [edge for edge in related if edge["from"]["node_id"] == args.id],
                "sources": [sources[source_id] for source_id in sorted(source_ids)]}
        else:
            if not 0 <= args.depth <= 20:
                raise ValueError("depth must be 0..20")
            allowed = [edge for edge in edges if _state(edge, "review", "historical_claim") in (("accepted", "candidate") if args.include_candidates else ("accepted",))]
            seen, frontier, selected = {args.id}, {args.id}, {}
            for _ in range(args.depth):
                following = set()
                for edge in allowed:
                    source, target = _endpoints(edge)
                    if args.direction in ("outgoing", "both") and source in frontier or args.direction in ("incoming", "both") and target in frontier:
                        selected[edge["id"]] = edge; following.update((source, target))
                frontier = following - seen; seen |= following
            result = {"nodes": [nodes[node_id] for node_id in sorted(seen)], "relationships": list(selected.values()),
                "note": "Traversal follows typed historical relationships, not community-entry display chronology. Disconnected nodes remain valid."}
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
