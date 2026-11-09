#!/usr/bin/env python3
"""Compile ``data/`` into independently cached browser artifacts and a research index.

    python tools/build.py              # publishes app/public/data/manifest.json
    python tools/build.py --check      # validate first and refuse to build bad data

Use --out FILE to export the full legacy JSON bundle.

The output is derived and is not committed. It is the same for the same input, so it can be
compared between machines. Everything the app shows about the research comes from here: the app
does no research logic of its own.
"""

from __future__ import annotations

from contextlib import closing
import argparse
import json
import math
import sys
from pathlib import Path

from dataset import FACETS, ROOT, Dataset, year_value
from publish import evidence_ids

OUT = ROOT / "app" / "public" / "data" / "atlas.json"

#: From most to least precise. A discovery is drawn at its most precise place.
PLACE_ORDER = ("site", "settlement", "area", "country", "region", "water")


def cumulative_person_years(series: list[list[int]], steps: int = 8) -> list[list[float]]:
    """Person-years lived since the first estimate, sampled finely enough to interpolate linearly.

    Between two estimates the population grows at a constant rate, so the area under it has a
    closed form: (p1 - p0) * dt / ln(p1 / p0).
    """
    points = [[float(series[0][0]), 0.0]]
    total = 0.0
    for (y0, p0), (y1, p1) in zip(series, series[1:]):
        rate = math.log(p1 / p0) / (y1 - y0)
        for step in range(1, steps + 1):
            dt = (y1 - y0) * step / steps
            if abs(rate) < 1e-12:
                area = p0 * dt
            else:
                area = p0 * (math.exp(rate * dt) - 1) / rate
            points.append([y0 + dt, total + area])
        total = points[-1][1]
    return points


def compile_date(event: dict) -> dict:
    date = event["date"]
    out = {"t": round(year_value(date["latest"]), 3), "label": date["label"], "status": date["status"], "precision": date["precision"]}
    if date["earliest"]:
        out["t0"] = round(year_value(date["earliest"]), 3)
    return out


def build(data: Dataset) -> dict:
    places = data.registers["places"]
    discoveries = []
    links = []
    used_sources: set[str] = set()

    def evidence(items: list[dict] | None) -> list[dict]:
        for item in items or []:
            used_sources.add(item["source"])
        return items or []

    for record in sorted(data.discoveries.values(), key=lambda r: r["id"]):
        events = []
        for event in record["events"]:
            compiled = {
                "id": event["id"],
                "type": event["type"],
                **compile_date(event),
                "basis": event["date"]["basis"],
                "statement": event["statement"],
                "evidence": evidence(event.get("evidence")),
            }
            for key in ("places", "place_note", "scope", "applications", "population", "market", "caveats", "type_provisional", "contributions"):
                if key in event:
                    compiled[key] = event[key]
            for contribution in event.get("contributions", []):
                evidence(contribution.get("evidence"))
            events.append(compiled)
        by_id = {e["id"]: e for e in events}

        out = {key: record[key] for key in (
            "id", "name", "aliases", "summary", "description", "kind", "domain", "fields", "tier", "tier_reason", "impact", "grain",
            "advance", "scale", "origin", "concept", "prompted_by", "why", "limit_removed", "setting", "funding",
            "places", "people", "organizations", "societies", "known_from", "reception", "fate", "end_reason",
            "measures", "witnesses", "caveats", "external",
        ) if key in record}
        if "market" in record:
            out["market"] = {k: v for k, v in record["market"].items() if k != "evidence"}
            evidence(record["market"].get("evidence"))
        for measure in record.get("measures", []):
            evidence(measure.get("evidence"))
        out["events"] = events

        anchor = by_id.get(record["earliest_record"].get("event"))
        out["earliest_record"] = record["earliest_record"]
        if anchor:
            out["t"] = anchor["t"]
            out["date"] = {k: anchor[k] for k in ("label", "status", "precision", "t", "t0") if k in anchor}
        if record.get("community_entry"):
            out["community_entry"] = record["community_entry"]
            entry = by_id.get(record["community_entry"]["event"])
            if entry:
                out["entered"] = {"t": entry["t"], "label": entry["label"]}

        # Where to draw it: the most precise place named on the record, else on its earliest record.
        candidates = [p["place"] for p in record.get("places", [])]
        if not candidates and anchor:
            candidates = anchor.get("places", [])
        known = [places[p] for p in candidates if p in places]
        if known:
            best = min(known, key=lambda p: PLACE_ORDER.index(p["kind"]))
            out["at"] = {"place": best["id"], "lat": best["lat"], "lon": best["lon"], "kind": best["kind"], "region": best["region"]}

        research = record["research"]
        out["research"] = {"status": research["status"], "basis": research["basis"]}
        for key in ("unresolved", "missing_prerequisites", "note"):
            if key in research:
                out["research"][key] = research[key]
        for item in research.get("unresolved", []):
            evidence(item.get("evidence"))
        out["filled"] = sum(1 for facet in FACETS if research["basis"].get(facet) in ("sourced", "recalled", "reviewed"))
        out['source_ids'] = sorted(evidence_ids(record))
        used_sources.update(out['source_ids'])
        discoveries.append(out)

        for link in record.get("links", []):
            compiled = {"to": record["id"], **link}
            compiled["layer"] = next(layer for layer, types in data.vocab["link"]["layers"].items() if link["type"] in types)
            evidence(link.get("evidence"))
            links.append(compiled)

    links.sort(key=lambda l: (l["from"], l["to"], l["type"]))
    sources = {
        key: {k: data.sources[key][k] for k in ("title", "authors", "year", "url") if data.sources[key].get(k) is not None}
        for key in sorted(used_sources)
    }

    population = None
    if data.population:
        population = {
            "sources": data.population["sources"],
            "method": data.population["method"],
            "series": data.population["series"],
            "person_years": {
                name: [[round(y, 2), round(v)] for y, v in cumulative_person_years(series)]
                for name, series in data.population["series"].items()
            },
        }

    return {
        "counts": {
            "discoveries": len(discoveries),
            "events": sum(len(d["events"]) for d in discoveries),
            "links": sum(1 for l in links if l["status"] == "established"),
            "sources": len(data.sources),
            "leads": len(data.registers["leads"]),
            "facets": len(FACETS),
        },
        "facets": list(FACETS),
        "vocab": {name: entry["values"] for name, entry in data.vocab.items()},
        "link_layers": data.vocab["link"]["layers"],
        "taxonomy": data.taxonomy,
        "discoveries": discoveries,
        "links": links,
        "places": data.registers["places"],
        "people": data.registers["people"],
        "organizations": data.registers["organizations"],
        "societies": data.registers["societies"],
        "concepts": data.registers["concepts"],
        "sources": sources,
        "population": population,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="validate first and stop on any problem")
    parser.add_argument("--out", type=Path, help="export the legacy full JSON bundle to this file")
    parser.add_argument("--output-dir", type=Path, default=OUT.parent)
    parser.add_argument("--no-research-db", action="store_true", help="browser artifacts only")
    args = parser.parse_args()

    from research import signature, connect
    from publish import digest, encoded, atomic_write
    before = signature()
    build_inputs = {**before, **{
        str(path.relative_to(ROOT)): [path.stat().st_size, path.stat().st_mtime_ns]
        for path in (Path(__file__), ROOT / 'tools/publish.py')
    }}
    stamp = ROOT / '.cache' / ('browser-build-' + digest(str(args.output_dir.resolve()).encode())[:16] + '.json')
    if not args.check and not args.out:
        try:
            saved = json.loads(stamp.read_text())
            manifest = json.loads((args.output_dir / 'manifest.json').read_text())
            core = json.loads((args.output_dir / manifest['core']).read_text())
            assets = [manifest['core'], core['population_file'], *core['details'].values()]
            if saved['inputs'] == build_inputs and all((args.output_dir / name).is_file() for name in assets):
                if not args.no_research_db:
                    with closing(connect()):
                        pass
                print(f"Dataset unchanged: {manifest['version']}")
                return 0
        except (OSError, KeyError, ValueError):
            pass
    data = Dataset.load()
    if args.check:
        errors = data.validate(check_files=False)
        if errors:
            print("\n".join(errors[:50]), file=sys.stderr)
            print(f"{len(errors)} problems. Not built.", file=sys.stderr)
            return 1
    bundle = build(data)
    if before != signature():
        print('Dataset changed during compilation; retry the build.', file=sys.stderr)
        return 1
    from publish import atomic_write, encoded, publish
    if args.out:
        atomic_write(args.out, encoded(bundle))
        print(f"Wrote {args.out}: {bundle['counts']}")
    else:
        manifest = publish(bundle, args.output_dir)
        # The previous monolithic artifact is derived, and no longer a browser dependency.
        (args.output_dir / 'atlas.json').unlink(missing_ok=True)
        if not args.no_research_db:
            with closing(connect()):
                pass
        atomic_write(stamp, encoded({'inputs': build_inputs}))
        print(f"Published {manifest['version']}: {bundle['counts']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
