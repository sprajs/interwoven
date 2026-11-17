"""Export the catalogue's record-level research frontier as CSV."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import sys
from typing import TextIO

from coverage import ERAS, REGIONS
from dataset import DATA, Dataset, year_value

LAYERS = ("dependence", "transmission")
DIRECTIONS = ("incoming", "outgoing")
LINK_COUNTS = tuple(f"{direction}_established_{layer}"
                    for direction in DIRECTIONS for layer in LAYERS)
CONNECTIVITY = {
    (): "isolated",
    ("incoming",): "incoming_only",
    ("outgoing",): "outgoing_only",
    DIRECTIONS: "incoming_and_outgoing",
}
ERA_ORDER = (*(label for label, _ in ERAS), "undated")
REGION_ORDER = (*REGIONS, "multiple", "unplaced")
FIELDS = (
    "id", "name", "record_path", "era", "earliest_record_event", "earliest_record_date_label",
    "primary_region", "regions", "primary_domain", "primary_field", "established_connectivity",
    *LINK_COUNTS, "established_link_pointers", "candidate_links", "candidate_link_pointers",
    "insufficient_links", "insufficient_link_pointers", "missing_prerequisites_state",
    "missing_prerequisites", "uncertainty_pointers",
)


def encode(value: list) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def region_groups(record: dict, places: dict) -> tuple[str, list[str]]:
    """Keep overlapping audit regions, with a separate mutually exclusive grouping."""
    regions = set()
    origins = set()
    for place in record.get("places", []):
        region = places.get(place["place"], {}).get("region")
        if region:
            regions.add(region)
            if place.get("role") == "origin":
                origins.add(region)
    if not regions:
        return "unplaced", ["unplaced"]
    preferred = origins or regions
    primary = next(iter(preferred)) if len(preferred) == 1 else "multiple"
    return primary, [region for region in REGIONS if region in regions]


def uncertainty_pointers(record: dict, path: str) -> list[str]:
    research = record["research"]
    pointers = [f"/research/unresolved/{index}" for index, _ in enumerate(research.get("unresolved", []))]
    pointers.extend(f"/research/basis/{facet}" for facet, state in sorted(research["basis"].items())
                    if state == "unknown")
    if record.get("caveats"):
        pointers.append("/caveats")
    for index, event in enumerate(record["events"]):
        if event["date"]["status"] in ("approximate", "bounded"):
            pointers.append(f"/events/{index}/date")
        for field in ("caveats", "place_note", "type_provisional"):
            if event.get(field):
                pointers.append(f"/events/{index}/{field}")
    return [f"{path}#{pointer}" for pointer in pointers]


def frontier_rows(data: Dataset, data_path: Path) -> list[dict[str, str | int]]:
    records = data.discoveries
    ids = sorted(records)
    paths = {key: (Path("data") / data.paths[f"discoveries/{key}"].relative_to(data_path)).as_posix()
             for key in ids}
    layers = data.vocab["link"]["layers"]
    causal_layers = {kind: layer for layer in LAYERS for kind in layers[layer]}
    counts = defaultdict(Counter)
    pointers = defaultdict(lambda: defaultdict(list))

    for receiver in ids:
        for index, link in enumerate(records[receiver].get("links", [])):
            status, kind, sender = link["status"], link["type"], link["from"]
            layer = causal_layers.get(kind)
            if status == "established" and layer is None:
                continue
            for direction, key, other in (("incoming", receiver, sender), ("outgoing", sender, receiver)):
                if status == "established":
                    counts[key][f"{direction}_established_{layer}"] += 1
                pointers[key][status].append({
                    "direction": direction, "type": kind, "other_id": other,
                    "pointer": f"{paths[receiver]}#/links/{index}",
                })

    rows = []
    for key in ids:
        record = records[key]
        event = data.earliest_record(record)
        era = "undated"
        if event:
            latest = year_value(event["date"]["latest"])
            era = next((label for label, end in ERAS if latest < end), ERAS[-1][0])
        primary_region, regions = region_groups(record, data.registers["places"])
        counted = counts[key]
        directions = tuple(direction for direction in DIRECTIONS
                           if any(counted[f"{direction}_established_{layer}"] for layer in LAYERS))
        linked = pointers[key]
        prerequisites = record["research"].get("missing_prerequisites")
        prerequisite_state = "absent" if prerequisites is None else "listed" if prerequisites else "empty"
        rows.append({
            "id": key,
            "name": record["name"],
            "record_path": paths[key],
            "era": era,
            "earliest_record_event": event["id"] if event else "",
            "earliest_record_date_label": event["date"]["label"] if event else "",
            "primary_region": primary_region,
            "regions": encode(regions),
            "primary_domain": record["domain"].split(".")[0],
            "primary_field": record["domain"],
            "established_connectivity": CONNECTIVITY[directions],
            **{column: counted[column] for column in LINK_COUNTS},
            "established_link_pointers": encode(linked["established"]),
            "candidate_links": len(linked["candidate"]),
            "candidate_link_pointers": encode(linked["candidate"]),
            "insufficient_links": len(linked["insufficient"]),
            "insufficient_link_pointers": encode(linked["insufficient"]),
            "missing_prerequisites_state": prerequisite_state,
            "missing_prerequisites": encode(prerequisites or []),
            "uncertainty_pointers": encode(uncertainty_pointers(record, paths[key])),
        })

    return sorted(rows, key=lambda row: (ERA_ORDER.index(row["era"]), REGION_ORDER.index(row["primary_region"]),
                                         row["primary_domain"], row["id"]))


def write_csv(rows: list[dict[str, str | int]], stream: TextIO) -> None:
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA, help="dataset checkout or its data directory")
    parser.add_argument("--output", type=Path, help="CSV output path; defaults to standard output")
    args = parser.parse_args()
    data_path = args.data if (args.data / "schema.json").is_file() else args.data / "data"
    if not (data_path / "schema.json").is_file() or not (data_path / "discoveries").is_dir():
        parser.error(f"could not find a dataset at {args.data}")
    rows = frontier_rows(Dataset.load(data_path), data_path)
    if args.output is None:
        write_csv(rows, sys.stdout)
    else:
        with args.output.open("w", encoding="utf-8", newline="") as stream:
            write_csv(rows, stream)


if __name__ == "__main__":
    main()
