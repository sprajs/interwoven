"""Regenerate the wave counts and source reader from the three published reviews."""
import argparse
from collections import Counter
from functools import cache
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from dataset import point_key, source_path, write_json
from prehistory_wave import blob, discovery_records, git, graph, require, reviewed_bytes
from render_research_round import DOCUMENT, SCRIPT, STYLE, esc, evidence

BASE = "c626bdb6cd241a7b6a4889a88ab25b4f9b576432"
SNAPSHOT = "19cb29356f68ba7a244c9bf266a283ef7ffd34fc"
TITLES = {"dry": "Dry to immersion lithography", "kirin": "TSMC 16FF+ in the Kirin 950",
          "ccd": "Early CCD imaging"}
HIGHLIGHTS = {
    "dry": {"at750-production-unit-shipment", "at1150-product-listing", "prototype-imaging"},
    "kirin": {"16ff-risk-production", "16ff-plus-volume-production", "mate-8-china-availability"},
    "ccd": {"eight-bit-ccd-report-1970", "line-imaging-report-1971", "area-imager-symposium-1972"},
}


@cache
def source(key):
    return json.loads(blob(SNAPSHOT, str(source_path(key).relative_to(ROOT))))


def passages(item):
    citations = item.get("evidence", [])
    return evidence(citations, {c["source"]: source(c["source"]) for c in citations})


def inspect(lane, before, after):
    directory = HERE.relative_to(ROOT)
    review = json.loads(blob(SNAPSHOT, f"{directory}/reviews/{lane}.json"))
    require((review["base"], review["decision"], review["reviewer"], review["effort"]) ==
            (BASE, "accept", "gpt-6.1-terra", "high"), f"Unaccepted review for {lane}")
    proposal = review["proposal"]
    for earlier, later in ((BASE, proposal), (proposal, SNAPSHOT)):
        git("merge-base", "--is-ancestor", earlier, later)
    proposed = git("diff", "--name-only", "-z", BASE, proposal).decode().split("\0")[:-1]
    reviewed = reviewed_bytes(review, SNAPSHOT)
    require(set(proposed) == set(reviewed), f"Incomplete review for {lane}")
    for path, contents in reviewed.items():
        require(blob(proposal, path) == contents, f"Proposal differs from publication at {path}")
    report = json.loads(reviewed[f"{directory}/lanes/{lane}.json"])
    require((report["lane"], report["baseline"], report["researcher"], report["effort"]) ==
            (lane, BASE, "gpt-6.2-sol", "high"), f"Unexpected researcher or baseline for {lane}")
    added = set(git("diff", "--diff-filter=A", "--name-only", "-z", BASE, proposal).decode().split("\0"))
    counts = Counter(reviewed_files=len(reviewed))
    changed = {}
    for path, raw in reviewed.items():
        if path.startswith("data/sources/"):
            counts["new_sources" if path in added else "updated_sources"] += 1
        if path.startswith("data/discoveries/"):
            rec = json.loads(raw)
            previous = before.get(rec["id"], {})
            changed[rec["id"]] = rec
            counts["updated_discoveries" if previous else "new_discoveries"] += 1
            old = {e["id"]: e for e in previous.get("events", [])}
            new = {e["id"]: e for e in rec["events"]}
            counts["new_events"] += len(new.keys() - old.keys())
            counts["updated_events"] += sum(new[k] != old[k] for k in old.keys() & new.keys())
            require(old.keys() <= new.keys(), f"Event removal in {path}")
    old_edges = graph({key: before[key] for key in changed if key in before})
    new_edges = graph(changed)
    require(all(new_edges.get(k) == v for k, v in old_edges.items()), "Existing link changed")
    links = []
    for key in sorted(new_edges.keys() - old_edges.keys()):
        link = new_edges[key]
        counts["new_" + link["status"] + "_links"] += 1
        links.append((after[key[0]]["name"], after[key[1]]["name"], link))
    events = [e for key in report["records"] for e in after[key]["events"]]
    events.sort(key=lambda event: point_key(event["date"]["earliest"] or event["date"]["latest"]))
    return report, counts, events, links


def panels(reports, compact):
    options, sections = [], []
    for lane, (report, _, events, links) in reports.items():
        title = TITLES[lane]
        options.append(f'<option value="lane-{lane}">{esc(title)}</option>')
        rows = []
        for e in events:
            if compact and e["id"] not in HIGHLIGHTS[lane]:
                continue
            rows.append(f'<li><b>{esc(e["date"]["label"])}</b> · {esc(e["statement"])}'
                        f'{passages(e)}</li>')
        groups = []
        for status, label in (("established", "Established links"), ("candidate", "Candidate links")):
            decisions = []
            for first, second, link in links:
                if link["status"] == status:
                    decisions.append(f'<li><b>{esc(first)} · {esc(second)}</b><div>{esc(link["statement"])}</div>'
                                     f'<div>{esc(link.get("caveats", ""))}</div>{passages(link)}</li>')
            if decisions:
                groups.append(f'<details><summary>{label} ({len(decisions)})</summary><ul>'
                              + "".join(decisions) + "</ul></details>")
        hidden = "" if lane == "dry" else " hidden"
        sections.append(f'<section class="lane" id="lane-{lane}"{hidden}><p>{esc(report["outcome"])}</p><ol>'
                        + "".join(rows) + "</ol>" + "".join(groups) + "</section>")
    return (STYLE + '<h2>Chip fabrication and early CCD imaging</h2><div class="viz-controls">'
            '<label class="form-label">Technology<select class="form-select">' + "".join(options)
            + '</select></label></div><div aria-live="polite">' + "".join(sections) + "</div>" + SCRIPT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fragment", type=Path, help="Also write the compact interactive chronology")
    args = parser.parse_args()
    before, after = discovery_records(BASE), discovery_records(SNAPSHOT)
    reports = {lane: inspect(lane, before, after) for lane in TITLES}
    counts = {lane: result[1] for lane, result in reports.items()}
    write_json(HERE / "metrics.json", {"base": BASE, "snapshot": SNAPSHOT, "lanes": counts,
                                      "totals": sum(counts.values(), Counter())})
    (HERE / "view.html").write_text(DOCUMENT + panels(reports, False) + "</body></html>\n")
    if args.fragment:
        args.fragment.write_text(panels(reports, True) + "\n")


if __name__ == "__main__":
    main()
