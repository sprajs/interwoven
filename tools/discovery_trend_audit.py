"""Audit discovery counts in immutable Git snapshots; standard library only.

This is descriptive analysis of a selected catalogue, not a population estimate.
No simulation, random sampling, or causal model is used. All intervals are [a,b).
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import tarfile
from xml.sax.saxutils import escape

from dataset import ROOT, year_value


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def snapshot(revision: str) -> tuple[dict, list[dict], dict]:
    commit = git("rev-parse", revision + "^{commit}")
    archive = subprocess.check_output(["git", "-C", str(ROOT), "archive", commit, "data"])
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        files = {m.name: tar.extractfile(m).read() for m in tar.getmembers() if m.isfile()}
    places = {p["id"]: p for line in files["data/places.jsonl"].splitlines()
              if line.strip() for p in [json.loads(line)]}
    rank = {kind: i for i, kind in enumerate(("site", "settlement", "area", "country", "region", "water"))}
    rows = []
    undated = []
    for path, raw in sorted(files.items()):
        if not path.startswith("data/discoveries/") or not path.endswith(".json"):
            continue
        d = json.loads(raw)
        anchor = next((e for e in d["events"] if e["id"] == (d.get("earliest_record") or {}).get("event")), None)
        if anchor is None:
            undated.append(d["id"])
            continue
        date = anchor["date"]
        latest = round(year_value(date["latest"]), 3)
        earliest = round(year_value(date["earliest"]), 3) if date.get("earliest") else None
        candidates = [p["place"] for p in d.get("places", [])] or anchor.get("places", [])
        known = [places[p] for p in candidates if p in places]
        best = min(known, key=lambda p: rank[p["kind"]]) if known else None
        rows.append({
            "id": d["id"], "name": d["name"], "path": path,
            "year": latest, "earliest": earliest, "date_status": date["status"],
            "event_type": anchor["type"], "domain": d["domain"].split(".")[0],
            "field": d["domain"], "grain": d.get("grain"), "tier": d.get("tier"),
            "origin": d.get("origin"), "concept": d.get("concept"),
            "region": best["region"] if best else None,
            "event_basis": d["research"]["basis"].get("events"),
            "people_count": len(d.get("people", [])),
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
    population = json.loads(files["data/reference/population.json"])
    used_paths = [p for p in files if p.startswith("data/discoveries/") and p.endswith(".json")]
    used_paths += ["data/reference/population.json", "data/places.jsonl"]
    digest = hashlib.sha256()
    for path in sorted(used_paths):
        digest.update(path.encode() + b"\0" + files[path] + b"\0")
    meta = {"commit": commit, "committed_at": git("show", "-s", "--format=%cI", commit),
            "dated_records": len(rows), "undated_ids": undated,
            "discovery_files": len(rows) + len(undated), "input_sha256": digest.hexdigest(),
            "population_sha256": hashlib.sha256(files["data/reference/population.json"]).hexdigest()}
    return meta, rows, population


def person_years(series: list, start: float, end: float) -> float:
    """Analytical integral of log-linear population, with no extrapolation."""
    if not series[0][0] <= start < end <= series[-1][0]:
        raise ValueError("Period outside recorded population coverage")
    total = 0.0
    for (y0, p0), (y1, p1) in zip(series, series[1:]):
        lo, hi = max(start, y0), min(end, y1)
        if hi <= lo:
            continue
        k = math.log(p1 / p0) / (y1 - y0)
        total += p0 * math.exp(k * (lo-y0)) * math.expm1(k * (hi-lo)) / k if k else p0 * (hi-lo)
    return total


def period(rows: list[dict], series: list, start: int, end: int, earliest: bool = False) -> dict:
    selected = [r for r in rows if start <= (r["earliest"] if earliest and r["earliest"] is not None else r["year"]) < end]
    exposure = person_years(series, start, end)
    return {"start": start, "end": end, "count": len(selected),
            "billion_person_years": exposure / 1e9, "rate": len(selected) * 1e9 / exposure}


def comparison(rows: list[dict], series: list, start: int = 1960, split: int = 1980, end: int = 2000, earliest: bool = False) -> dict:
    pre, post = period(rows, series, start, split, earliest), period(rows, series, split, end, earliest)
    return {"pre": pre, "post": post,
            "rate_ratio": post["rate"] / pre["rate"] if pre["rate"] else None,
            "count_ratio": post["count"] / pre["count"] if pre["count"] else None}


def audit(meta: dict, rows: list[dict], pop: dict) -> dict:
    world = pop["series"]["world"]
    filters = {
        "all": rows,
        "capabilities": [r for r in rows if r["grain"] == "capability"],
        "major_scored": [r for r in rows if r["tier"] is not None and r["tier"] <= 1],
        "electronics": [r for r in rows if r["domain"] == "electronics"],
        "other_domains": [r for r in rows if r["domain"] != "electronics"],
        "known_date": [r for r in rows if r["date_status"] == "known"],
        "bounded_date_only": [r for r in rows if r["earliest"] is not None],
        "sourced_events": [r for r in rows if r["event_basis"] in ("sourced", "reviewed")],
    }
    domains = sorted({r["domain"] for r in rows})
    domain_comparisons = {d: comparison([r for r in rows if r["domain"] == d], world) for d in domains}
    # App-like single most precise location. Regional rates use the region's own population.
    regional = {region: comparison([r for r in rows if r["region"] == region], series)
                for region, series in pop["series"].items() if region != "world"}
    bins = {name: {str(width): [period(rs, world, y, y+width) for y in range(1760, 2020, width)]
                   for width in (10, 20)} for name, rs in filters.items()}
    sensitivity = {name: comparison(rs, world) for name, rs in filters.items()}
    sensitivity["earliest_where_bounded"] = comparison(filters["bounded_date_only"], world, earliest=True)
    shifted = {str(split): comparison(rows, world, split-20, split, split+20)
               for split in (1965, 1970, 1975, 1980, 1985, 1990)}
    # A two-constant-rate descriptive fit, NOT a population-level significance test.
    fits = []
    for start, end in ((1800, 2000), (1900, 2000), (1940, 2000)):
        for minimum_span in (10, 20):
            choices = []
            lo, hi = max(1945, start+minimum_span), min(1990, end-minimum_span)
            for split in range(lo, hi+1):
                c = comparison(rows, world, start, split, end)
                score = sum(p["count"] * math.log(p["rate"]) if p["count"] else 0 for p in (c["pre"], c["post"]))
                choices.append((score, split, c))
            _, split, c = max(choices, key=lambda x: x[0])
            fits.append({"start": start, "end": end, "minimum_span": minimum_span,
                         "search": [lo, hi], "at_search_boundary": split in (lo, hi), "split": split, **c})
    profiles = []
    for start, end in ((1760, 1960), (1960, 1980), (1980, 2000), (2000, 2020)):
        rs = [r for r in rows if start <= r["year"] < end]
        profiles.append({"start": start, "end": end, "count": len(rs),
                         **{key: dict(Counter(str(r[key]) for r in rs))
                            for key in ("grain", "tier", "origin", "date_status", "event_basis", "region")}})
    # Names/descriptions are checked separately from this anchor-based quantitative audit.
    return {"metadata": meta, "bins": bins, "comparison": sensitivity["all"],
            "sensitivity": sensitivity, "shifted_windows": shifted,
            "domains": domain_comparisons, "regions": regional,
            "descriptive_break_fits": fits, "profiles": profiles}


def svg_plot(result: dict) -> str:
    """Persistent, dependency-free Python-rendered figure; actual measured catalogue counts."""
    bins = result["bins"]["all"]["20"]
    w, h, left, right, top, bottom = 960, 410, 75, 25, 50, 70
    pw, ph = w-left-right, h-top-bottom
    ymax = math.ceil(max(b["rate"] for b in bins)*2)/2
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">',
           '<title>Recorded discoveries per billion person-years; twenty-year periods</title>',
           '<rect width="100%" height="100%" fill="white"/>',
           '<g font-family="system-ui,sans-serif" font-size="14" fill="#17232c">',
           '<text x="75" y="25">Recorded discoveries per billion person-years (selective catalogue)</text>']
    for i in range(5):
        value = ymax*i/4; y=top+ph*(1-value/ymax)
        out.extend([f'<line x1="{left}" x2="{w-right}" y1="{y}" y2="{y}" stroke="#dbe1e5"/>',
                    f'<text x="{left-10}" y="{y+5}" text-anchor="end">{value:g}</text>'])
    for i, b in enumerate(bins):
        x=left+pw*i/len(bins)+5; bw=pw/len(bins)-10; bh=b["rate"]/ymax*ph
        color="#b86624" if b["start"]>=1980 else "#256a87"
        out.extend([f'<rect x="{x}" y="{top+ph-bh}" width="{bw}" height="{bh}" fill="{color}"><title>{b["start"]}–{b["end"]-1}: {b["count"]} records, {b["rate"]:.3f} per billion person-years</title></rect>',
                    f'<text x="{x+bw/2}" y="{top+ph+24}" text-anchor="middle">{b["start"]}</text>',
                    f'<text x="{x+bw/2}" y="{top+ph-bh-8}" text-anchor="middle">{b["count"]}</text>'])
    out.extend([f'<text x="{left}" y="{h-20}">Period start (CE); labels above bars are record counts. Snapshot {escape(result["metadata"]["commit"][:8])}.</text>', '</g></svg>'])
    return '\n'.join(out)+'\n'


def inline_chart(result: dict) -> str:
    """Presentation of already computed Python results; no browser analysis."""
    scopes = ("all", "electronics", "other_domains", "known_date")
    payloads = []
    old = result["earlier_snapshot"]
    current_label = f'{result["metadata"]["committed_at"][:10]} snapshot'
    old_label = f'{old["metadata"]["committed_at"][:10]} snapshot'
    if current_label == old_label:
        current_label += ' ' + result["metadata"]["commit"][:7]
        old_label += ' ' + old["metadata"]["commit"][:7]
    for scope in scopes:
        for measure in ("rate", "count"):
            for width in ("20", "10"):
                key = f"{scope}-{measure}-{width}"
                rows = [{"period": f'{a["start"]}–{(a["end"]-1)%100:02}',
                         current_label: a[measure], old_label: b[measure]}
                        for a, b in zip(result["bins"][scope][width], old["bins"][scope][width])]
                config = {"id": "discovery-trend-series", "title": "Recorded discoveries",
                          "showHeader": False, "height": 320,
                          "spec": {"type": "line", "x": "period", "y": [current_label, old_label],
                                   "xLabel": "Period (CE)", "yLabel": "Records per billion person-years" if measure == "rate" else "Records",
                                   "startAtZero": True, "showLegend": True,
                                   "valueFormat": {"style": "decimal", "maximumFractionDigits": 3 if measure == "rate" else 0}},
                          "rows": rows}
                payloads.append(f'<script type="application/json" data-viz-chart data-key="{key}">' +
                                json.dumps(config, ensure_ascii=False).replace('<', '\\u003c') + '</script>')
    template = Path(__file__).with_name("discovery_trend_template.html").read_text()
    for placeholder, metadata in (("__CURRENT_SNAPSHOT__", result["metadata"]), ("__EARLIER_SNAPSHOT__", old["metadata"])):
        template = template.replace(placeholder, f'{metadata["committed_at"][:10]} ({metadata["commit"][:7]})')
    return template.replace("<!--CHART_CONFIGS-->", '\n'.join(payloads)).replace(
        "__COMPARISONS__", json.dumps({s: result["sensitivity"][s] for s in scopes}, ensure_ascii=False).replace('<', '\\u003c'))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--compare-revision")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    meta, rows, pop = snapshot(args.revision)
    result = audit(meta, rows, pop)
    if args.compare_revision:
        oldmeta, oldrows, oldpop = snapshot(args.compare_revision)
        result["earlier_snapshot"] = audit(oldmeta, oldrows, oldpop)
    result["method"] = {
        "analysis_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "presentation_template_sha256": hashlib.sha256(Path(__file__).with_name("discovery_trend_template.html").read_bytes()).hexdigest(),
        "unit": "One dated discovery record, not a paper, person, or unique world-first",
        "date": "Latest bound of earliest_record event, rounded to 0.001 year, matching app",
        "intervals": "Half-open [start,end); all plotted periods are complete",
        "denominator": "Exact integral of log-linear world population in data/reference/population.json",
        "limits": ["Selective collection with unknown inclusion probabilities", "No measured researcher denominator",
                   "Origin, grain and importance coverage vary with historical period and snapshot",
                   "Regional assignment uses the app's single most precise place; transnational collaboration not apportioned",
                   "Break fits describe this catalogue only; no significance or causal estimate is reported",
                   "Major-only filtering selects on consequences observed to date; recent achievements have less follow-up"],
    }
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=True)
    (out/"results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    with (out/"records.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    (out/"discovery-rates.svg").write_text(svg_plot(result))
    if args.compare_revision:
        (out/"interactive.html").write_text(inline_chart(result))
    print(json.dumps({"output": str(out), "metadata": meta, "comparison": result["comparison"],
                      "earlier": result.get("earlier_snapshot", {}).get("comparison"),
                      "break_fits": result["descriptive_break_fits"]}, indent=2))


if __name__ == "__main__":
    main()
