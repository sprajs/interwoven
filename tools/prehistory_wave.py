"""Verify and render the independently reviewed prehistory research wave."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from hashlib import sha256
from html import escape
from io import StringIO
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess

from dataset import ROOT, read_json, write_json


WAVE = "docs/reviews/2026-11-17-prehistory"
FRONTIER = "docs/reviews/2026-11-17-all-eras/frontier/research-frontier.csv"
EARLY_ERA = "before 3000 BCE"
EDGE_FIELDS = ("from", "to", "type", "from_event", "to_event")
DECISIONS = {"new-established", "existing-established", "new-candidate", "existing-candidate", "deferred"}
CAUSAL_LAYERS = ("dependence", "transmission")
GRAPH_OUTCOMES = ("established", "candidate", "open")
LANE_NAMES = {"eastasia": "East Asia", "ferment": "Fermentation", "herds": "Herding"}


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def revision(ref: str) -> str:
    return git("rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()


def blob(commit: str, path: str) -> bytes:
    return git("cat-file", "blob", f"{commit}:{path}")


def discovery_records(commit: str) -> dict[str, dict]:
    """Read the exact baseline without checking it out or calling git per file."""
    paths = git("ls-tree", "-rz", "--name-only", commit, "data/discoveries").decode().split("\0")
    names = [path for path in paths if path.endswith(".json")]
    requests = "".join(f"{commit}:{path}\n" for path in names)
    raw = subprocess.run(["git", "-C", str(ROOT), "cat-file", "--batch"], input=requests.encode(),
                         stdout=subprocess.PIPE, check=True).stdout
    records = {}
    offset = 0
    for path in names:
        end = raw.index(b"\n", offset)
        _, kind, size = raw[offset:end].split()
        require(kind == b"blob", f"{path} is not a blob in {commit}")
        start = end + 1
        offset = start + int(size) + 1
        record = json.loads(raw[start:offset - 1])
        require(record["id"] not in records, f"duplicate baseline discovery {record['id']}")
        records[record["id"]] = record
    return records


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def exact_rows(rows: list[dict], ids: set[str], label: str) -> dict[str, dict]:
    indexed = {row["id"]: row for row in rows}
    require(len(indexed) == len(rows), f"{label}: duplicate ids")
    require(set(indexed) == ids, f"{label}: missing {sorted(ids - indexed.keys())}, extra {sorted(indexed.keys() - ids)}")
    return indexed


def reviewed_bytes(review: dict, after: str) -> dict[str, bytes]:
    entries = review["files"]
    if isinstance(entries, dict):
        entries = [{"path": path, "sha256": digest} for path, digest in entries.items()]
    contents = {}
    for entry in entries:
        path = entry["path"]
        require(not PurePosixPath(path).is_absolute() and ".." not in PurePosixPath(path).parts,
                f"invalid review path {path}")
        require(path not in contents, f"duplicate reviewed path {path}")
        digest = entry["sha256"].lower().removeprefix("sha256:").strip()
        require(re.fullmatch(r"[a-f0-9]{64}", digest) is not None, f"invalid reviewed SHA-256 for {path}")
        stored = blob(after, path)
        require(sha256(stored).hexdigest() == digest, f"integrated file differs from accepted bytes: {path}")
        contents[path] = stored
    return contents


def added_record_reviews(review: dict) -> dict[str, dict]:
    items = review.get("additional_records", [])
    if isinstance(items, dict):
        return items
    indexed = {}
    for item in items:
        key = item.get("id") or item.get("record_id")
        path = item.get("path", "")
        if not key and path.startswith("data/discoveries/"):
            key = PurePosixPath(path).stem
        require(bool(key) and key not in indexed, f"missing or duplicate additional review ID {key!r}")
        indexed[key] = item
    return indexed


def edge_key(receiver: str, link: dict) -> tuple[str, ...]:
    return (link["from"], receiver, link["type"], link.get("from_event", ""), link.get("to_event", ""))


def graph(records: dict[str, dict]) -> dict[tuple[str, ...], dict]:
    edges = {}
    for receiver, record in records.items():
        for link in record.get("links", []):
            key = edge_key(receiver, link)
            require(key not in edges, f"duplicate graph edge {key}")
            edges[key] = link
    return edges


def connection_status(edge: dict | None) -> str:
    return edge["status"] if edge is not None else "absent"


def check_connections(mentions: list[dict], old: dict, new: dict) -> tuple[list[dict], set]:
    """Resolve each ledger mention to exact stored edges, including event scope."""
    results = []
    claimed = set()
    for mention in mentions:
        prefix = tuple(mention[k] for k in EDGE_FIELDS[:3])
        decision = mention["decision"]
        require(decision in DECISIONS, f"invalid link decision {decision!r}")
        matches = sorted(key for key in old.keys() | new.keys() if key[:3] == prefix
                         and all((mention[k] or "") == key[i] for i, k in enumerate(EDGE_FIELDS[3:], 3) if k in mention))
        if decision != "deferred":
            freshness, status = decision.split("-")
            seen_before = {key for key in matches if connection_status(old.get(key)) == status}
            matches = [key for key in matches if connection_status(new.get(key)) == status
                       and (bool(seen_before) if freshness == "existing" else key not in seen_before)]
            require(bool(matches), f"ledger decision {decision} disagrees with graph snapshots for {prefix}")
            claimed.update(matches)
        results.append({**mention, "edges": [edge_transition(key, old, new) for key in matches]})
    return results, claimed


def edge_transition(key: tuple, old: dict, new: dict) -> dict:
    link = new.get(key) or old[key]
    return {**dict(zip(EDGE_FIELDS, key)), "before": connection_status(old.get(key)),
            "after": connection_status(new.get(key)),
            **{field: link[field] for field in ("statement", "scope", "caveats", "evidence") if field in link}}


def causal_incidence(edges: dict, layers: dict) -> dict[str, list[tuple]]:
    incident = defaultdict(list)
    for edge in sorted(edges):
        origin, receiver, kind, *_ = edge
        if layers[kind] in CAUSAL_LAYERS:
            incident[origin].append(edge)
            incident[receiver].append(edge)
    return incident


def graph_status(edges: list[tuple], graph: dict) -> str:
    statuses = {graph[key]["status"] for key in edges}
    return next((status for status in GRAPH_OUTCOMES[:2] if status in statuses), "open")


def established_counts(anchor: str, edges: list[tuple], graph: dict, layers: dict) -> dict:
    totals = Counter()
    for key in edges:
        origin, _, kind, *_ = key
        if graph[key]["status"] == "established":
            direction = "outgoing" if origin == anchor else "incoming"
            totals[f"{direction}_{layers[kind]}"] += 1
    return dict(totals)


def typed_changes(old: dict, new: dict) -> list[dict]:
    """Compare unique directed types independently of exact event attachments."""
    statuses = []
    for edges in (old, new):
        grouped = defaultdict(set)
        for key, edge in edges.items():
            grouped[key[:3]].add(edge["status"])
        statuses.append(grouped)
    before, after = statuses
    return [{**dict(zip(EDGE_FIELDS[:3], key)), "before": sorted(before[key]), "after": sorted(after[key])}
            for key in sorted(before.keys() | after.keys()) if before[key] != after[key]]


def summary(records: list[dict]) -> dict:
    before = Counter(row["graph_status_before"] for row in records)
    after = Counter(row["graph_status"] for row in records)
    return {"records": len(records), "graph_outcomes_before": {status: before[status] for status in GRAPH_OUTCOMES},
            "graph_outcomes": {status: after[status] for status in GRAPH_OUTCOMES},
            "researcher_outcomes": dict(Counter(r["outcome"] for r in records)),
            "with_insufficient": sum(any(edge["after"] == "insufficient" for edge in row["incident_causal_edges"])
                                     for row in records),
            "linked_before": before["established"], "linked_after": after["established"],
            "newly_reached": sum(row["graph_status_before"] != "established" and row["graph_status"] == "established"
                                 for row in records)}


def current_date_label(record: dict) -> str:
    event_id = record.get("earliest_record", {}).get("event")
    return next((event["date"]["label"] for event in record["events"] if event["id"] == event_id), "")


def compile_wave(base: str, after: str, roster: dict, frontier: str, lane_dir: Path, review_dir: Path) -> dict:
    ids = [key for members in roster.values() for key in members]
    frozen = exact_rows([row for row in csv.DictReader(StringIO(frontier)) if row["era"] == EARLY_ERA],
                        set(ids), "frozen frontier")
    require(len(ids) == len(set(ids)) and bool(ids), "roster must contain disjoint, nonempty discovery IDs")
    baseline = discovery_records(base)
    require(set(ids) <= baseline.keys(), "roster contains discoveries missing from the baseline")
    wave_records = baseline.copy()
    layers = {kind: layer for layer, kinds in json.loads(blob(base, "data/vocab.json"))["link"]["layers"].items()
              for kind in kinds}
    lanes, additions, removals, sources = {}, {}, {}, {}
    review_paths = {}
    for lane, members in roster.items():
        ledger_path = lane_dir / f"{lane}.json"
        ledger = read_json(ledger_path)
        review = read_json(review_dir / f"{lane}.json")
        require(ledger["lane"] == review["lane"] == lane, f"lane label mismatch for {lane}")
        require(ledger["base"] == review["base_commit"] == base, f"baseline mismatch for {lane}")
        require(review["overall_decision"] == "accept", f"lane {lane} lacks an accepted final review")
        identity = review["reviewer"]
        require((identity["model"], identity["effort"]) == ("gpt-6.1-terra", "high"), f"reviewer mismatch for {lane}")
        worker = review.get("worker_commit") or review.get("proposal_commit")
        require(isinstance(worker, str) and re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", worker) is not None
                and review.get("proposal_commit", worker) == worker, f"invalid proposal commit for {lane}")
        contents = reviewed_bytes(review, after)
        require(contents.get(f"{WAVE}/lanes/{lane}.json") == ledger_path.read_bytes(), f"ledger bytes unbound for {lane}")
        for entry in review.get("deleted_files", []):
            removed_path = entry if isinstance(entry, str) else entry["path"]
            require(not git("ls-tree", "-r", "--name-only", after, "--", removed_path),
                    f"reviewed deletion still present: {removed_path}")
            if removed_path.startswith("data/discoveries/") and removed_path.endswith(".json"):
                record = json.loads(blob(base, removed_path))
                key = record["id"]
                require(key not in removals and key in wave_records, f"duplicate reviewed deletion: {key}")
                removals[key] = {"id": key, "name": record["name"], "lane": lane, "path": removed_path,
                                 "events": record["events"]}
                del wave_records[key]
        extra = added_record_reviews(review)
        seen_extras = set()
        for path, data in contents.items():
            digest = sha256(data).hexdigest()
            if path in review_paths:
                require(review_paths[path] == digest, f"conflicting acceptance hashes for {path}")
            review_paths[path] = digest
            if path.startswith("data/discoveries/") and path.endswith(".json"):
                record = json.loads(data)
                key = record["id"]
                if key not in baseline:
                    require(key in extra, f"{lane}: new discovery {key} has no additional-record review")
                    seen_extras.add(key)
                    additions[key] = {"id": key, "name": record["name"], "lane": lane, "path": path,
                                      "events": record["events"], "review": extra[key]}
                wave_records[key] = record
            elif path.startswith("data/sources/") and path.endswith(".json"):
                source = json.loads(data)
                sources[source["id"]] = source
        require(seen_extras == set(extra), f"{lane}: additional-record review IDs disagree with additions")
        lanes[lane] = {"name": LANE_NAMES.get(lane, lane.title()),
                       "researcher": ledger["researcher"], "effort": ledger["effort"], "reviewer": identity,
                       "worker_commit": worker, "files_checked": len(contents),
                       "records": exact_rows(ledger["records"], set(members), f"{lane} ledger"),
                       "reviews": exact_rows(review["records"], set(members), f"{lane} review")}

    old = graph(baseline)
    new = graph(wave_records)
    old_incident, new_incident = causal_incidence(old, layers), causal_incidence(new, layers)
    changed_keys = sorted(key for key in old.keys() | new.keys()
                          if connection_status(old.get(key)) != connection_status(new.get(key)))
    changed = [edge_transition(key, old, new) for key in changed_keys]
    claimed, retained, rows = set(), set(), []
    for lane, info in lanes.items():
        ledger = info.pop("records")
        reviewed = info.pop("reviews")
        lane_rows = []
        for key in roster[lane]:
            row = ledger[key]
            require(row["outcome"] in {"established", "candidate", "deferred"}
                    and isinstance(row["sources"], list) and bool(row["sources"]),
                    f"invalid outcome or missing citations for {key}")
            before_status = graph_status(old_incident[key], old)
            require(frozen[key]["established_connectivity"] == "isolated" and before_status != "established",
                    f"{key} is not isolated in the frozen graph")
            connections, row_claimed = check_connections(row["connections"], old, new)
            claimed.update(row_claimed)
            retained.update(edge for edge in row_claimed if connection_status(old.get(edge)) == "candidate"
                            and connection_status(new.get(edge)) == "candidate")
            current_record = wave_records.get(key, baseline[key])
            lane_rows.append({**row, "lane": lane, "connections": connections,
                              "name": current_record["name"],
                              "path": frozen[key]["record_path"], "region": frozen[key]["primary_region"],
                              "domain": frozen[key]["primary_domain"], "date": current_date_label(current_record),
                              "frozen_date": frozen[key]["earliest_record_date_label"],
                              "graph_status_before": before_status, "graph_status": graph_status(new_incident[key], new),
                              "before": established_counts(key, old_incident[key], old, layers),
                              "after": established_counts(key, new_incident[key], new, layers),
                              "incident_causal_edges": [edge_transition(edge, old, new) for edge in new_incident[key]],
                              "review": reviewed[key]})
        info.update(summary(lane_rows))
        rows.extend(lane_rows)
    unreported = [key for key in changed_keys if key not in claimed
                  and connection_status(new.get(key)) in {"established", "candidate"}]
    require(not unreported, f"new stored relationships lack matching ledger decisions: {unreported}")

    new_events, revised_events, removed_events = [], [], []
    for key in sorted(baseline.keys() & wave_records.keys()):
        previous = {event["id"]: event for event in baseline[key]["events"]}
        present = {event["id"]: event for event in wave_records[key]["events"]}
        for event_id, event in present.items():
            if event_id not in previous:
                new_events.append({"discovery": key, "event": event})
            elif event != previous[event_id]:
                revised_events.append({"discovery": key, "event": event})
        for event_id in sorted(previous.keys() - present.keys()):
            removed_events.append({"discovery": key, "event": previous[event_id]})

    relevant_edges = [*changed, *(edge for row in rows for edge in row["incident_causal_edges"]),
                      *(edge for row in rows for mention in row["connections"] for edge in mention["edges"])]
    endpoints = {key for edge in relevant_edges for key in (edge["from"], edge["to"])}
    evidence_ids = {entry["source"] for edge in relevant_edges for entry in edge.get("evidence", [])}
    for source_id in sorted(evidence_ids - sources.keys()):
        path = f"data/sources/{source_id[0]}/{source_id}.json"
        sources[source_id] = json.loads(blob(base, path))
    return {"schema_version": 2, "base_commit": base, "after_commit": after, "frozen_frontier": FRONTIER,
            "summary": summary(rows), "lanes": lanes, "records": rows, "new_discoveries": list(additions.values()),
            "removed_discoveries": list(removals.values()), "removed_events_on_existing_records": removed_events,
            "new_events_on_existing_records": new_events, "revised_events_on_existing_records": revised_events,
            "net_events": sum(len(r["events"]) for r in wave_records.values()) - sum(len(r["events"]) for r in baseline.values()),
            "sources": sources, "reviewed_file_sha256": review_paths,
            "changed_edges": changed, "retained_candidates": [edge_transition(key, old, new) for key in sorted(retained)],
            "typed_direction_changes": typed_changes(old, new), "layers": layers,
            "edge_endpoints": {key: (wave_records.get(key) or baseline[key])["name"] for key in sorted(endpoints)}}


def new_status(result: dict, status: str) -> list[dict]:
    return [edge for edge in result["changed_edges"] if edge["after"] == status]


def quantity(number: int, noun: str) -> str:
    return f"{number} {noun}{'' if number == 1 else 's'}"


def markdown(result: dict) -> str:
    totals = result["summary"]
    outcomes = totals["graph_outcomes"]
    established = new_status(result, "established")
    directed = [edge for edge in result["typed_direction_changes"]
                if "established" in edge["after"] and "established" not in edge["before"]]
    layer_totals = Counter(result["layers"][e["type"]] for e in directed)
    causal = sum(layer_totals[layer] for layer in CAUSAL_LAYERS)
    promoted = sum(edge["before"] == "candidate" for edge in established)
    lines = ["# Prehistory research wave", "",
             f"{totals['newly_reached']} of {totals['records']} previously isolated discoveries gained an established "
             f"dependence or transmission relationship. After review, {outcomes['candidate']} had a candidate as their "
             f"strongest relationship in those layers and {outcomes['open']} remained open. The wave added or promoted "
             f"{quantity(causal, 'distinct directed relationship')} in those layers and "
             f"{quantity(len(directed) - causal, 'relationship')} in other layers.", "",
             "[Evidence reader](view.html) · [Machine-readable results](results.json) · [Frozen frontier]"
             "(../2026-11-17-all-eras/frontier/research-frontier.csv) · [Roster](roster.json)", "",
             "![Dependence and transmission outcomes by research lane](graph-coverage.svg)", "",
             "## Graph outcomes", "",
             f"The graph gained {quantity(len(result['new_discoveries']), 'discovery record')} and removed "
             f"{quantity(len(result['removed_discoveries']), 'record')}. On existing records, the wave added "
             f"{quantity(len(result['new_events_on_existing_records']), 'event')}, revised "
             f"{quantity(len(result['revised_events_on_existing_records']), 'event')} and removed "
             f"{quantity(len(result['removed_events_on_existing_records']), 'event')}. The net event change across all "
             f"reviewed discoveries was {result['net_events']:+d}. "
             f"The review promoted {quantity(promoted, 'scoped candidate')} to established status. "
             f"{len(new_status(result, 'candidate'))} relationships newly have candidate status, and "
             f"{len(result['retained_candidates'])} assessed candidates retained their status.", "",
             "| Research lane | Records | Established link | Candidate only | Open | With an insufficient assessment |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for lane, stats in result["lanes"].items():
        established_count, candidate_count, open_count = (stats['graph_outcomes'][key] for key in GRAPH_OUTCOMES)
        lines.append(f"| [{stats['name']}](lanes/{lane}.json) | {stats['records']} | {established_count} | {candidate_count} | "
                     f"{open_count} | {stats['with_insufficient']} |")
    lines.extend(["", "Each anchor counts once under its strongest dependence or transmission status in either direction. "
                   "Open means there is no established or candidate edge in those layers. Insufficient assessments are listed "
                   "separately and can overlap any outcome. The evidence reader also shows the researcher's original assessment, "
                   "which may concern a dated find or an affinity relationship.", "",
                  "## Established relationship changes", ""])
    if established:
        lines.extend(["| Recorded direction | Type | Layer | Previous status |", "| --- | --- | --- | --- |"])
        for edge in established:
            left, right = result["edge_endpoints"][edge["from"]], result["edge_endpoints"][edge["to"]]
            from_event, to_event = edge["from_event"], edge["to_event"]
            if from_event:
                left += f" (`{from_event}`)"
            if to_event:
                right += f" (`{to_event}`)"
            lines.append(f"| {left} → {right} | `{edge['type']}` | {result['layers'][edge['type']]} | {edge['before']} |")
    else:
        lines.append("The reviewed records added or promoted zero established edges.")
    lines.extend(["", "## Method", "",
                  f"The roster is the `{EARLY_ERA}` cohort in the frozen frontier at `{result['base_commit']}`. "
                  "The exporter checks one ledger row and one independent Terra High verdict for each roster ID. "
                  "The cohort retains its frozen membership when review revises a record's date. "
                  f"It applies only the file contents bound by those accepted reviews at `{result['after_commit']}`. "
                  "It counts distinct directed relationships by sender, receiver and type. The detailed changes also track "
                  "individual event attachments. The exporter checks every prospective "
                  "or retained candidate and established ledger decision against the snapshots. The graph excludes candidates, "
                  "insufficient links, parallel achievements and affinity from its prerequisite and transmission coverage. "
                  "A missing edge marks a catalogue research gap.", ""])
    return "\n".join(lines)


def coverage_svg(result: dict) -> str:
    lanes = result["lanes"]
    height = 140 + 32 * len(lanes)
    maximum = max(lane["records"] for lane in lanes.values())
    totals = result["summary"]
    before = totals["graph_outcomes_before"]
    after = totals["graph_outcomes"]
    labels = ("Established", "Candidate only", "Open")
    colors = ("#25695f", "#a66324", "#dbded8")
    before_text = " · ".join(f"{before[status]} {label.lower()}" for status, label in zip(GRAPH_OUTCOMES, labels))
    after_text = " · ".join(f"{after[status]} {label.lower()}" for status, label in zip(GRAPH_OUTCOMES, labels))
    description = f"Before review, {before_text}. After review, {after_text}."
    head = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 {height}" width="760" height="{height}" role="img">',
            '<title>Dependence and transmission outcomes</title>', f'<desc>{description}</desc>',
            '<rect width="100%" height="100%" fill="#f9f8f3"/>',
            '<g font-family="DejaVu Sans, sans-serif" font-size="16" fill="#25302e">',
            '<text x="24" y="36" font-size="21" font-weight="600">Dependence and transmission outcomes</text>',
            f'<text x="24" y="62">Before review · {before_text}</text>',
            f'<text x="24" y="86">After review · {after_text}</text>']
    for x, label, color in zip((175, 310, 465), labels, colors):
        head.extend([f'<rect x="{x}" y="106" width="12" height="12" fill="{color}"/>',
                     f'<text x="{x+20}" y="117" font-size="14">{label}</text>'])
    for index, (lane, values) in enumerate(lanes.items()):
        y = 136 + 32 * index
        head.append(f'<text x="24" y="{y+14}">{escape(values["name"])}</text>')
        x = 175
        outcomes = values["graph_outcomes"]
        for status, color in zip(GRAPH_OUTCOMES, colors):
            width = 420 * outcomes[status] / maximum
            head.append(f'<rect x="{x:.3f}" y="{y}" width="{width:.3f}" height="16" fill="{color}"/>')
            x += width
        values_text = " / ".join(str(outcomes[status]) for status in GRAPH_OUTCOMES)
        head.append(f'<text x="730" y="{y+14}" text-anchor="end">{values_text}</text>')
    return "\n".join([*head, '</g></svg>', ''])


def html_fragment(result: dict) -> str:
    template = (Path(__file__).with_name("prehistory_wave_view.html")).read_text(encoding="utf-8")
    records = [{key: row[key] for key in ("id", "name", "date", "frozen_date", "lane", "region", "domain", "outcome", "finding",
                                         "next", "sources", "graph_status_before", "graph_status", "after", "connections",
                                         "incident_causal_edges")}
               | {"rationale": row["review"]["rationale"], "verdict": row["review"]["verdict"]}
               for row in result["records"]]
    sources = {key: {field: value[field] for field in ("title", "url") if field in value}
               for key, value in result["sources"].items()}
    data = {"records": records, "layers": result["layers"], "names": result["edge_endpoints"], "sources": sources,
            "lanes": {key: item["name"] for key, item in result["lanes"].items()}}
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    fragment = template.replace("@@WAVE_DATA@@", payload)
    require(len(fragment.encode("utf-8")) < 1_000_000, "inline evidence reader exceeds the visualization size limit")
    return fragment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="frozen dataset revision")
    parser.add_argument("--after", required=True, help="revision containing the reviewed wave bytes")
    parser.add_argument("--roster", type=Path, required=True, help="frozen lane-to-record-ID mapping")
    parser.add_argument("--frontier", type=Path, help="override frozen frontier CSV extracted from base by default")
    parser.add_argument("--lanes", type=Path, required=True, help="directory containing final lane ledger JSON")
    parser.add_argument("--reviews", type=Path, required=True, help="directory containing accepted review JSON")
    parser.add_argument("--output", type=Path, required=True, help="output directory for reports and views")
    parser.add_argument("--png", action="store_true", help="also rasterize the coverage figure with rsvg-convert")
    args = parser.parse_args()
    if args.png and shutil.which("rsvg-convert") is None:
        parser.error("--png requires rsvg-convert (librsvg)")
    try:
        base, after = revision(args.base), revision(args.after)
        frontier = args.frontier.read_text(encoding="utf-8") if args.frontier else blob(base, FRONTIER).decode("utf-8")
        roster = read_json(args.roster)
        result = compile_wave(base, after, roster, frontier, args.lanes, args.reviews)
        fragment = html_fragment(result)
        target = args.output
        write_json(target / "results.json", result)
        write_json(target / "roster.json", roster)
        (target / "report.md").write_text(markdown(result), encoding="utf-8")
        (target / "graph-coverage.svg").write_text(coverage_svg(result), encoding="utf-8")
        (target / "prehistory-wave.html").write_text(fragment, encoding="utf-8")
        standalone = (Path(__file__).with_name("prehistory_wave_standalone.html")).read_text(encoding="utf-8")
        (target / "view.html").write_text(standalone.replace("<!--WAVE_FRAGMENT-->", fragment), encoding="utf-8")
        if args.png:
            subprocess.run(["rsvg-convert", str(target / "graph-coverage.svg"), "-o",
                            str(target / "graph-coverage.png")], check=True)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
