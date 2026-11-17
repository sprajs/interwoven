"""Measure gaps in established dependence and transmission in a committed dataset."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from io import BytesIO
import json
from pathlib import Path
import subprocess
import tarfile
from tempfile import TemporaryDirectory
from xml.sax.saxutils import escape

from coverage import ERAS, REGIONS, audit
from dataset import ROOT, Dataset, year_value


def measure(data: Dataset, commit: str) -> dict:
    coverage = audit(data)
    network = coverage["established_network"]
    ids = set(data.discoveries)
    isolated = set(network["without_established_dependence_or_transmission"]["records"])
    layers = data.vocab["link"]["layers"]
    types = set(layers["dependence"] + layers["transmission"])
    receiving = set()
    adjacent = defaultdict(set)
    for receiver, link in data.links():
        if link["status"] == "established" and link["type"] in types:
            left, right = link["from"], receiver["id"]
            receiving.add(right)
            adjacent[left].add(right)
            adjacent[right].add(left)

    def counts(members: set[str]) -> dict:
        return {"total": len(members), "without_link": len(members & isolated),
                "without_incoming": len(members - receiving)}

    remaining = ids - isolated
    sizes = []
    while remaining:
        component = [remaining.pop()]
        for node in component:
            neighbors = adjacent[node] & remaining
            remaining.difference_update(neighbors)
            component.extend(neighbors)
        sizes.append(len(component))

    domains = {domain["name"]: set() for domain in data.taxonomy["domains"]}
    names = {domain["id"]: domain["name"] for domain in data.taxonomy["domains"]}
    regions = {region: set() for region in (*REGIONS, "unplaced")}
    eras = {label: set() for label, _ in ERAS}
    eras["undated"] = set()
    for key, record in data.discoveries.items():
        domains[names[record["domain"].split(".")[0]]].add(key)
        places = {data.registers["places"][p["place"]]["region"] for p in record.get("places", [])}
        for region in places or {"unplaced"}:
            regions[region].add(key)
        event = data.earliest_record(record)
        era = "undated"
        if event:
            year = year_value(event["date"]["latest"])
            era = next((label for label, end in ERAS if year < end), ERAS[-1][0])
        eras[era].add(key)

    assert ids - set(adjacent) == isolated
    assert sum(sizes) == len(ids - isolated)
    assert {k: len(v) for k, v in eras.items()} == coverage["overall"]["eras"]
    assert {k: len(v) for k, v in regions.items()} == coverage["overall"]["regions"]
    assert sum(map(len, domains.values())) == len(ids)
    return {
        "data_commit": commit,
        "counts": coverage["counts"], "link_status": coverage["links"]["status"],
        "established_layers": network["layers"], "overall": counts(ids),
        "connected_component_sizes_excluding_isolates": sorted(sizes, reverse=True),
        "domains": {k: counts(v) for k, v in domains.items()},
        "regions": {k: counts(v) for k, v in regions.items()},
        "eras": {k: counts(v) for k, v in eras.items()},
        "missing_prerequisites": coverage["missing_prerequisites"],
        "facet_basis": coverage["facet_basis"],
        "lead_status": dict(Counter(lead["status"] for lead in data.registers["leads"].values())),
    }


def domain_figure(result: dict) -> str:
    rows = sorted(result["domains"].items(), key=lambda item: (-item[1]["without_link"], item[0]))[:8]
    maximum = max((row["without_link"] for _, row in rows), default=0)
    # Tick intervals of ten records, including the origin and the next multiple of ten.
    limit = max(10, ((maximum + 9) // 10) * 10)
    chart_left, width = 222, 340
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 365" role="img">',
           '<title>Primary domains with the most unlinked records</title>',
           '<desc>Counts include records with no established dependence or transmission in either direction.</desc>',
           '<rect width="680" height="365" fill="#faf9f5"/>',
           '<g font-family="system-ui,sans-serif" font-size="13" fill="#272823">',
           '<text x="18" y="30" font-size="19" font-weight="600">Where the most records are unlinked</text>',
           '<text x="18" y="55">Established dependence or transmission, counted at either endpoint</text>',
           '<text x="660" y="84" text-anchor="end">Unlinked / total</text>']
    for tick in range(0, limit + 1, 10):
        x = chart_left + tick / limit * width
        svg.extend([f'<path d="M{x:g} 92 V308" stroke="#d9d9d0"/>',
                    f'<text x="{x:g}" y="326" text-anchor="middle">{tick}</text>'])
    for i, (name, row) in enumerate(rows):
        y = 98 + 27 * i
        value = row["without_link"]
        svg.extend([f'<text x="18" y="{y + 12}">{escape(name)}</text>',
                    f'<rect x="{chart_left}" y="{y}" width="{value / limit * width:.2f}" height="15" fill="#276458"/>',
                    f'<text x="660" y="{y + 12}" text-anchor="end">{value} / {row["total"]}</text>'])
    svg.extend([f'<text x="18" y="351" fill="#50564e">Catalogue {result["data_commit"][:7]}</text>',
                '<text x="390" y="351" text-anchor="middle">Unlinked discovery records</text>', '</g></svg>'])
    return "\n".join(svg) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("revision", help="Git revision of the dataset")
    parser.add_argument("output", type=Path, help="Directory for coverage.json and domain-gaps.svg")
    args = parser.parse_args()
    git = ["git", "-C", str(ROOT)]
    commit = subprocess.check_output([*git, "rev-parse", "--verify", "--end-of-options",
                                      args.revision + "^{commit}"], text=True).strip()
    raw = subprocess.check_output([*git, "archive", commit, "data"])
    with TemporaryDirectory() as directory, tarfile.open(fileobj=BytesIO(raw)) as archive:
        archive.extractall(directory, filter="data")
        result = measure(Dataset.load(Path(directory) / "data"), commit)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "coverage.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (args.output / "domain-gaps.svg").write_text(domain_figure(result), encoding="utf-8")


if __name__ == "__main__":
    main()
