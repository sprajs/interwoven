#!/usr/bin/env python3
"""Build the standalone modern research reader and its evidence-date figure."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from dataset import Dataset, read_json  # noqa: E402

STATUSES = {
    "in service": "#196957",
    "commercially available": "#345e9c",
    "demonstrated": "#75518b",
    "proposed": "#94601f",
    "suspended": "#a13d25",
    "retired": "#596473",
}
DEPTH = 4
RECORD_TOKEN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)+")
DATE = re.compile(r"\d{4}(?:-\d{2}(?:-\d{2})?)?")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def read_lanes(directory: Path) -> list[dict]:
    lanes = []
    for path in sorted(directory.glob("*.json")):
        lane = read_json(path)
        for row in lane["inventory"]:
            if row["status"] not in STATUSES:
                raise ValueError(f"{path.name}: unsupported status {row['status']!r}")
            if not DATE.fullmatch(row["date"]):
                raise ValueError(f"{path.name}: unsupported evidence date {row['date']!r}")
        lanes.append(lane)
    if not lanes:
        raise ValueError(f"No lane JSON files found in {directory}")
    if len({lane["lane"] for lane in lanes}) != len(lanes):
        raise ValueError("Lane identifiers must be unique")
    return lanes


def changed_discoveries(base: str | None, manifest: Path | None) -> set[str]:
    if manifest is not None:
        paths = read_json(manifest)["paths"]
    elif base is not None:
        paths = git("diff", "--name-only", "--diff-filter=ACM", base, "--", "data/discoveries").splitlines()
    else:
        paths = []
    return {
        Path(path).stem for path in paths
        if path.startswith("data/discoveries/") and path.endswith(".json")
    }


def find_seeds(lanes: list[dict], data: Dataset, changed: set[str], overrides: list[str]) -> dict[str, list[str]]:
    seeds = {}
    for lane in lanes:
        ids = set(lane.get("records", []))
        ids.update(record for row in lane["inventory"] for record in row["records"])
        for line in lane.get("trace", []):
            ids.update(set(RECORD_TOKEN.findall(line)) & data.discoveries.keys())
        seeds[lane["lane"]] = ids
    for override in overrides:
        lane_id, separator, record_id = override.partition("=")
        if not separator or lane_id not in seeds:
            raise ValueError(f"--lane-record expects a known LANE=ID, got {override!r}")
        seeds[lane_id].add(record_id)
    missing = set().union(*seeds.values()) - data.discoveries.keys()
    if missing:
        raise ValueError(f"Unknown canonical discovery IDs: {', '.join(sorted(missing))}")
    seeds[""] = set().union(changed & data.discoveries.keys(), *seeds.values())
    return {lane_id: sorted(ids) for lane_id, ids in seeds.items()}


def evidence_details(data: Dataset, citations: list[dict]) -> list[dict]:
    details = []
    for entry in citations:
        source = data.sources[entry["source"]]
        details.append({
            "title": source["title"],
            "url": source.get("url"),
            "date": source.get("year"),
            "locator": entry.get("locator"),
            "supports": entry.get("supports"),
        })
    return details


def place_names(data: Dataset, placements: list[str | dict]) -> list[str]:
    places = data.registers["places"]
    ids = [entry["place"] if isinstance(entry, dict) else entry for entry in placements]
    return list(dict.fromkeys(places[place]["name"] for place in ids))


def canonical_detail(data: Dataset, record_id: str, incoming: list[dict], repo_url: str) -> dict:
    record = data.discoveries[record_id]
    date = data.earliest_record(record)
    return {
        "id": record_id,
        "name": record["name"],
        "description": record["description"],
        "path": repo_url + "/" + data.paths[f"discoveries/{record_id}"].relative_to(ROOT).as_posix(),
        "date": date["date"]["label"] if date else None,
        "year": date["date"]["latest"]["year"] if date else None,
        "places": place_names(data, record.get("places", [])),
        "caveats": record.get("caveats"),
        "unresolved": [
            {"about": entry["about"], "note": entry["note"],
             "evidence": evidence_details(data, entry.get("evidence", []))}
            for entry in record.get("research", {}).get("unresolved", [])
        ],
        "events": [
            {
                "id": event["id"],
                "date": event["date"]["label"],
                "type": event["type"],
                "statement": event["statement"],
                "caveats": event.get("caveats"),
                "evidence": evidence_details(data, event.get("evidence", [])),
                "places": place_names(data, event.get("places", [])),
            }
            for event in record["events"]
        ],
        "unproved": [
            {
                "name": data.discoveries[link["from"]]["name"],
                "type": link["type"],
                "status": link["status"],
                "statement": link["statement"],
                "caveats": link.get("caveats"),
                "evidence": evidence_details(data, link.get("evidence", [])),
            }
            for link in incoming
            if link["status"] in {"candidate", "insufficient"}
        ],
    }


def graph(data: Dataset, seeds: dict[str, list[str]], repo_url: str) -> tuple[dict, list[dict]]:
    relation_types = data.vocab["link"]["layers"]
    by_type = {name: layer for layer in ("dependence", "transmission") for name in relation_types[layer]}
    incoming = defaultdict(list)
    ancestors = defaultdict(list)
    for record, link in data.links():
        incoming[record["id"]].append(link)
        if link["status"] == "established" and link["type"] in by_type:
            ancestors[record["id"]].append(link)
    reached = set(seeds[""])
    frontier = reached
    for _ in range(DEPTH):
        older = {link["from"] for record_id in frontier for link in ancestors[record_id]} - reached
        reached.update(older)
        frontier = older
    nodes = {
        record_id: canonical_detail(data, record_id, incoming[record_id], repo_url)
        for record_id in sorted(reached)
    }
    edges = [
        {
            "from": link["from"],
            "to": descendant,
            "type": link["type"],
            "layer": by_type[link["type"]],
            "statement": link["statement"],
            "scope": link.get("scope"),
            "caveats": link.get("caveats"),
            "confidence": link.get("confidence"),
            "fromEvent": link.get("from_event"),
            "toEvent": link.get("to_event"),
            "evidence": evidence_details(data, link.get("evidence", [])),
        }
        for descendant in sorted(reached)
        for link in ancestors[descendant]
        if link["from"] in reached
    ]
    return nodes, edges


def timeline_svg(lanes: list[dict], fingerprint: str) -> str:
    escape = html.escape
    width, start, end, row_height = 960, 513, 914, 29
    all_dates = [row["date"] for lane in lanes for row in lane["inventory"]]
    if not all_dates:
        raise ValueError("The inventory has no dated observations")
    first_year = int(min(all_dates)[:4])
    last_year = int(max(all_dates)[:4])
    if first_year == last_year:
        first_year -= 1
    spacing = max(1, (last_year - first_year + 5) // 6)
    years = sorted(set(range(first_year, last_year, spacing)) | {last_year})

    def x(year: int) -> float:
        return start + (year - first_year) * (end - start) / (last_year - first_year)

    height = 151 + sum(40 + row_height * len(lane["inventory"]) for lane in lanes)
    fragments = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
        '<title id="title">When the modern technology observations were evidenced</title>',
        '<desc id="description">Each row describes a geographically scoped observation, with a dot '
        'at its evidence year, colored by recorded status. The status is scoped to its evidence date.</desc>',
        f'<metadata>Lane and canonical inputs SHA-256 {fingerprint}</metadata>',
        '<style>text{font-family:system-ui,sans-serif;fill:#172520}'
        '.title{font-family:Georgia,serif;font-size:30px} .sub,.year,.status{font-size:12px;fill:#52615a}'
        '.name{font-size:13px} .lane{font-size:14px;font-weight:700} .legend{font-size:12px}</style>',
        f'<rect width="{width}" height="{height}" fill="#f8faf7"/>',
        '<text class="title" x="32" y="45">When the observations were evidenced</text>',
        '<text class="sub" x="32" y="68">Evidence year for each dated observation. See the reader for exact dates, scope and sources.</text>',
    ]
    offset = 32
    for status, color in STATUSES.items():
        fragments.extend([
            f'<circle cx="{offset + 5}" cy="95" r="5" fill="{color}"/>',
            f'<text class="legend" x="{offset + 15}" y="99">{escape(status.capitalize())}</text>',
        ])
        offset += 42 + int(len(status) * 6.6)
    for year in years:
        position = x(year)
        fragments.extend([
            f'<line x1="{position:.1f}" x2="{position:.1f}" y1="130" y2="{height - 25}" stroke="#dfe6df"/>',
            f'<text class="year" x="{position:.1f}" y="124" text-anchor="middle">{year}</text>',
        ])

    y = 147
    for lane in lanes:
        fragments.extend([
            f'<line x1="32" x2="{end}" y1="{y}" y2="{y}" stroke="#d5ded6"/>',
            f'<text class="lane" x="32" y="{y + 20}">{escape(lane["title"])}</text>',
        ])
        y += 40
        for row in sorted(lane["inventory"], key=lambda item: (item["date"], item["name"])):
            label = row["name"]
            if len(label) > 59:
                label = label[:58].rstrip() + "…"
            relevance = f'{row["name"]} · {row["region"]} · {row["date"]} · {row["status"]}'
            fragments.extend([
                f'<g><title>{escape(relevance)}</title>',
                f'<text class="name" x="32" y="{y}">{escape(label)}</text>',
                f'<text class="status" x="419" y="{y}">{row["date"]}</text>',
                f'<circle cx="{x(int(row["date"][:4])):.1f}" cy="{y - 4}" r="5.5" '
                f'fill="{STATUSES[row["status"]]}" stroke="#f8faf7" stroke-width="1.2"/>',
                '</g>',
            ])
            y += row_height
    fragments.append('</svg>')
    return "\n".join(fragments) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="Include discoveries changed from this Git revision as wave records")
    parser.add_argument("--changes", type=Path,
                        help="Use a wave manifest with a paths array in place of the Git diff")
    parser.add_argument("--lanes-dir", type=Path, default=HERE / "lanes")
    parser.add_argument("--output-dir", type=Path, default=HERE)
    parser.add_argument("--repo-url", default="https://github.com/sprajs/interwoven/blob/main",
                        help="Browser path to the canonical repository tree")
    parser.add_argument("--lane-record", action="append", default=[], metavar="LANE=ID",
                        help="Assign an additional canonical discovery to a lane (repeatable)")
    args = parser.parse_args()

    data = Dataset.load()
    lanes = read_lanes(args.lanes_dir)
    changed = changed_discoveries(args.base, args.changes) & data.discoveries.keys()
    # The review files identify wave-owned discoveries even when a second investigation
    # pushed to main between the baseline and publication.
    review_dir = args.lanes_dir.parent / "reviews"
    record_assignments = list(args.lane_record)
    if review_dir.is_dir() and not args.changes:
        reviewed_ids = set()
        for lane in lanes:
            review = read_json(review_dir / (lane["lane"] + ".json"))
            for path in review["files"]:
                if path.startswith("data/discoveries/"):
                    record_id = Path(path).stem
                    reviewed_ids.add(record_id)
                    record_assignments.append(f'{lane["lane"]}={record_id}')
        changed = reviewed_ids
    seeds = find_seeds(lanes, data, changed, record_assignments)
    nodes, edges = graph(data, seeds, args.repo_url.rstrip("/"))
    payload = {
        "lanes": lanes,
        "seeds": seeds,
        "nodes": nodes,
        "edges": edges,
        "changed": sorted(changed),
        "statuses": STATUSES,
        "depth": DEPTH,
        "base": git("rev-parse", args.base) if args.base else None,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    fingerprint = hashlib.sha256(encoded.encode()).hexdigest()
    payload["fingerprint"] = fingerprint
    embedded = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    template = (HERE / "reader.html").read_text(encoding="utf-8")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "view.html").write_text(template.replace("/* REVIEW_DATA */", embedded), encoding="utf-8")
    (args.output_dir / "snapshot.svg").write_text(timeline_svg(lanes, fingerprint), encoding="utf-8")
    print(f"{len(lanes)} lanes, {len(nodes)} canonical records, {len(edges)} established relationships")


if __name__ == "__main__":
    main()
