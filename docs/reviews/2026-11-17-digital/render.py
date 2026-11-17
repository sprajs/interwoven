#!/usr/bin/env python3
"""Verify the digital follow-up reviews and regenerate the reader, figure and metrics."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from functools import cache
import html
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WAVE = HERE.relative_to(ROOT).as_posix()
sys.path.insert(0, str(ROOT / "tools"))

from dataset import source_path, write_json  # noqa: E402
from prehistory_wave import (  # noqa: E402
    blob, connection_status, current_date_label, discovery_records, graph, require,
    reviewed_bytes, revision,
)
from render_research_round import esc, evidence  # noqa: E402

BASE = "da459259a134eae431d4e45991dc050fa25a83d6"
REVIEW_SETTINGS = ("gpt-6.1-terra", "high")
DECISIONS = {"established", "still candidate", "insufficient", "narrowed", "extension"}
# Stored orientation is (earlier/source record, later/receiving record, type).
QUESTIONS = {
    "fugaku": ("fujitsu-tofu-interconnect-2", "riken-fujitsu-fugaku", "adapts"),
    "tofu": ("riken-fujitsu-k-computer", "fujitsu-tofu-interconnect-2", "adapts"),
    "finfet": ("tsmc-n7-immersion-finfet-process", "tsmc-n7-plus-euv-finfet-process", "builds_on"),
    "immersion": ("tsmc-193nm-immersion-lithography", "tsmc-n7-immersion-finfet-process", "uses_process"),
    "berkeley": ("berkeley-high-resistivity-pin-detector-process",
                 "berkeley-fully-depleted-back-illuminated-ccd", "builds_on"),
    "steel": ("lulea-hybrit-hydrogen-direct-reduction", "oxelosund-hybrit-trial-steel", "builds_on"),
}
LABELS = {
    "fugaku": "Tofu2 and Fugaku",
    "tofu": "Original Tofu and Tofu2",
    "finfet": "TSMC N7 and N7+",
    "immersion": "TSMC immersion lithography",
    "berkeley": "Berkeley silicon detectors",
    "steel": "HYBRIT trial steel",
    "sensor": "Charge-coupled image sensors",
}
COUNT_KEYS = (
    "new_nodes", "updated_nodes", "new_events", "updated_events", "removed_events",
    "new_sources", "updated_sources", "new_established_edges", "promoted_established_edges",
    "updated_established_edges", "removed_established_edges", "changed_open_edges",
    "original_questions", "original_questions_established",
)
EDGE_LABELS = {
    "new_established_edges": "New",
    "promoted_established_edges": "Promoted",
    "updated_established_edges": "Updated",
    "removed_established_edges": "Removed or reopened",
    "changed_open_edges": "Open or removed",
    "context": "Established in the baseline",
    "related": "Reviewed in another lane",
}
ARROW_LABELS = {
    "builds_on": "built on by",
    "requires": "required by",
    "adapts": "adapted by",
    "uses_instrument": "used as an instrument by",
    "uses_process": "used as a process by",
    "uses_theory": "used as a theory by",
    "supersedes": "succeeded by",
    "transmitted_from": "transmitted to",
}


def read_review(after: str, lane: str) -> tuple[dict, dict, dict]:
    review = json.loads(blob(after, f"{WAVE}/reviews/{lane}.json"))
    require(review["lane"] == lane and review["base"] == BASE, f"{lane}: wrong lane or base")
    require(review["decision"] == "accept", f"{lane}: proposal lacks acceptance")
    settings = review["reviewer"], review["effort"]
    require(settings == REVIEW_SETTINGS, f"{lane}: unexpected reviewer settings {settings!r}")
    proposal = revision(review["proposal"])
    require(proposal == review["proposal"], f"{lane}: proposal must be a full commit SHA")
    for ancestor, descendant in ((BASE, proposal), (proposal, after)):
        subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", ancestor, descendant], check=True)
    paths = subprocess.check_output(
        ["git", "-C", str(ROOT), "diff", "--name-only", "--no-renames", "-z", BASE, proposal]
    ).decode().split("\0")[:-1]
    require(set(paths) == review["files"].keys(), f"{lane}: proposal and review path sets differ")
    integrated = reviewed_bytes(review, after)
    for path, contents in integrated.items():
        require(blob(proposal, path) == contents, f"{lane}: proposal and integrated bytes differ for {path}")
    report_path = f"{WAVE}/lanes/{lane}.json"
    require(report_path in integrated, f"{lane}: reviewed lane report missing")
    report = json.loads(integrated[report_path])
    require(report["lane"] == lane and report["baseline"] == BASE, f"{lane}: wrong lane report or baseline")
    return report, review, integrated


def classify_edges(before: dict, after: dict) -> list[tuple[tuple, str]]:
    """Count an unambiguous event-scoped replacement of an open edge as a promotion."""
    changes = sorted(key for key in before.keys() | after.keys() if before.get(key) != after.get(key))
    additions = Counter(key[:3] for key in changes if key not in before and after[key]["status"] == "established")
    removed_open = defaultdict(list)
    for key in changes:
        if key not in after and before[key]["status"] in {"candidate", "insufficient"}:
            removed_open[key[:3]].append(key)

    replaced = set()
    results = []
    for key in changes:
        old_status = connection_status(before.get(key))
        new_status = connection_status(after.get(key))
        if new_status == "established":
            if old_status == "established":
                kind = "updated_established_edges"
            elif old_status != "absent":
                kind = "promoted_established_edges"
            elif additions[key[:3]] == 1 and len(removed_open[key[:3]]) == 1:
                kind = "promoted_established_edges"
                replaced.add(removed_open[key[:3]][0])
            else:
                kind = "new_established_edges"
        elif old_status == "established":
            kind = "removed_established_edges"
        else:
            kind = "changed_open_edges"
        results.append((key, kind))
    return [(key, kind) for key, kind in results if key not in replaced]


def event_changes(before: dict, after: dict) -> dict:
    old = {event["id"]: event for event in before.get("events", [])}
    new = {event["id"]: event for event in after["events"]}
    return {
        "new_events": [new[key] for key in sorted(new.keys() - old.keys())],
        "updated_events": [new[key] for key in sorted(old.keys() & new.keys()) if old[key] != new[key]],
        "removed_events": [old[key] for key in sorted(old.keys() - new.keys())],
    }


def compile_wave(after: str) -> tuple[list[dict], dict, dict, dict]:
    baseline = discovery_records(BASE)
    records = baseline.copy()
    all_paths = set()
    sources = {}
    wave = []
    optional_review = f"{WAVE}/reviews/sensor.json"
    review_paths = subprocess.check_output(
        ["git", "-C", str(ROOT), "ls-tree", "-r", "-z", "--name-only", after, f"{WAVE}/reviews"]
    ).decode().split("\0")
    lanes = [*QUESTIONS]
    if optional_review in review_paths:
        lanes.append("sensor")
    for lane in lanes:
        report, review, files = read_review(after, lane)
        require(not all_paths.intersection(files), f"{lane}: reviewed paths overlap another lane")
        all_paths.update(files)
        counters = Counter(dict.fromkeys(COUNT_KEYS, 0))
        nodes = []
        for path, raw in sorted(files.items()):
            if path.startswith("data/sources/"):
                source = json.loads(raw)
                old_source = subprocess.run(
                    ["git", "-C", str(ROOT), "cat-file", "-e", f"{BASE}:{path}"],
                    stderr=subprocess.DEVNULL,
                ).returncode == 0
                counters["updated_sources" if old_source else "new_sources"] += 1
                sources[source["id"]] = source
            if not path.startswith("data/discoveries/"):
                continue
            record = json.loads(raw)
            previous = baseline.get(record["id"], {})
            records[record["id"]] = record
            change = "updated_nodes" if previous else "new_nodes"
            counters[change] += 1
            events = event_changes(previous, record)
            for event_key, values in events.items():
                counters[event_key] += len(values)
            changed_fields = sorted(
                key for key in previous.keys() | record.keys()
                if key not in {"events", "links"} and previous.get(key) != record.get(key)
            ) if previous else []
            nodes.append(dict(record=record, change=change, events=events, fields=changed_fields))
        wave.append(dict(report=report, review=review, counters=counters, nodes=nodes))

    old_graph = graph(baseline)
    new_graph = graph(records)
    by_receiver = defaultdict(list)
    for key, kind in classify_edges(old_graph, new_graph):
        by_receiver[key[1]].append((key, kind))

    for item in wave:
        report = item["report"]
        lane = report["lane"]
        counters = item["counters"]
        nodes = {node["record"]["id"] for node in item["nodes"]}
        changes = sorted((key, kind) for record in nodes for key, kind in by_receiver[record])
        for _, kind in changes:
            counters[kind] += 1
        item["edges"] = [(key, kind, new_graph.get(key) or old_graph[key]) for key, kind in changes]

        original = QUESTIONS.get(lane)
        questions = report["questions"]
        if original:
            matches = [question for question in questions
                       if (question["parent"], question["child"]) == original[:2]]
            require(len(matches) == 1, f"{lane}: expected one disposition for the original question")
            original_key = next(key for key in old_graph if key[:3] == original and old_graph[key]["status"] == "candidate")
            item["original"] = original_key, old_graph[original_key]
            current = [(key, entry) for key, entry in new_graph.items() if key[:3] == original]
            item["question_edges"] = current
            counters["original_questions"] = 1
            question = matches[0]
            require(question["initial_status"] == "candidate", f"{lane}: original was candidate in the baseline")
            require(question["decision"] in DECISIONS, f"{lane}: unknown question decision {question['decision']!r}")
            if question["decision"] == "established":
                require(any(edge["status"] == "established" for _, edge in current),
                        f"{lane}: established question has no matching canonical edge")
                counters["original_questions_established"] = 1
            item["original_question"] = question
            item["original_decision"] = question["decision"]

        seeds = nodes | set(report["records"])
        seeds.update(question[side] for question in questions for side in ("parent", "child"))
        require(seeds <= records.keys(), f"{lane}: unknown record IDs {sorted(seeds - records.keys())}")
        for key, _ in changes:
            seeds.update(key[:2])
        earlier = {key[0] for key, kind in changes if kind in
                   {"new_established_edges", "promoted_established_edges", "updated_established_edges"}}
        changed = {key for key, _ in changes}
        item["context"] = [
            (key, "context" if old_graph.get(key) == edge else "related", edge)
            for key, edge in sorted(new_graph.items())
            if key not in changed and edge["status"] == "established"
            and (key[1] in earlier or (key[0] in seeds and key[1] in seeds))
        ]

    totals = Counter(dict.fromkeys(COUNT_KEYS, 0))
    for item in wave:
        totals.update(item["counters"])
    metrics = {
        "baseline": BASE,
        "reviewer": REVIEW_SETTINGS[0],
        "effort": REVIEW_SETTINGS[1],
        "aggregate": dict(totals),
        "original_question_decisions": dict(Counter(item["original_decision"] for item in wave if "original" in item)),
        "lanes": {
            item["report"]["lane"]: {
                "proposal": item["review"]["proposal"],
                "question_decision": item.get("original_decision"),
                "counts": dict(item["counters"]),
                "reviewed_files": len(item["review"]["files"]),
                "original_question": question_summary(item),
            }
            for item in wave
        },
    }
    return wave, records, sources, metrics


def question_summary(item: dict) -> dict | None:
    if "original" not in item:
        return None
    key, entry = item["original"]
    return {
        "earlier_record": key[0], "receiving_record": key[1], "type": key[2],
        "baseline_status": entry["status"],
        "current_statuses": sorted({link["status"] for _, link in item["question_edges"]}),
    }


def linked_source(title: str, url: str) -> str:
    if urlsplit(url).scheme in {"http", "https"}:
        return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(title)}</a>'
    return esc(title)


def source_list(entries: list[dict], title: str) -> str:
    if not entries:
        return ""
    rows = []
    for entry in entries:
        url = entry["url"]
        label = linked_source(entry.get("title", url), url)
        locator = f' · {esc(entry["locator"])}' if entry.get("locator") else ""
        rows.append(f"<li>{label}{locator}</li>")
    return f"<details><summary>{esc(title)}</summary><ul>{''.join(rows)}</ul></details>"


def notes(items: list) -> str:
    rows = []
    for item in items:
        if isinstance(item, dict):
            parts = [str(value) for field, value in item.items() if field not in {"paths", "decision"}]
            item = " · ".join(parts)
        rows.append(f"<li>{esc(item)}</li>")
    return "<ul>" + "".join(rows) + "</ul>" if rows else ""


def render_reader(wave: list[dict], records: dict, sources: dict, metrics: dict) -> str:
    @cache
    def load_source(source_id: str) -> dict:
        if source_id in sources:
            return sources[source_id]
        return json.loads(blob(BASE, source_path(source_id).relative_to(ROOT).as_posix()))

    def citations(items: list[dict]) -> str:
        return evidence(items, {entry["source"]: load_source(entry["source"]) for entry in items})

    def node_name(record_id: str, event_id: str = "") -> str:
        record = records[record_id]
        label = current_date_label(record)
        if event_id:
            event = next(event for event in record["events"] if event["id"] == event_id)
            label = event["date"]["label"]
        return f'<span>{esc(record["name"])}</span><small>{esc(label)}</small>'

    def edge_card(key: tuple, kind: str, edge: dict) -> str:
        upstream, downstream, relation, upstream_event, downstream_event = key
        problem = kind in {"changed_open_edges", "removed_established_edges"}
        if problem:
            pair = (f'<p>{node_name(downstream)} · {node_name(upstream)}</p>')
        else:
            label = ARROW_LABELS.get(relation, relation.replace("_", " "))
            pair = (f'<div class="dr-edge" aria-label="Earlier record to receiving record">'
                    f'<div>{node_name(upstream, upstream_event)}</div>'
                    f'<div class="dr-arrow"><b aria-hidden="true">→</b><small>{esc(label)}</small></div>'
                    f'<div>{node_name(downstream, downstream_event)}</div></div>')
        details = "".join(
            f'<p><strong>{esc(label)}</strong> {esc(edge[field])}</p>'
            for field, label in (("scope", "Scope"), ("finding", "Finding"), ("caveats", "Uncertainty"))
            if edge.get(field)
        )
        return (f'<article class="dr-card"><strong class="dr-tag">{esc(EDGE_LABELS[kind])}</strong>'
                f'{pair}<p>{esc(edge["statement"])}</p>{details}{citations(edge.get("evidence", []))}</article>')

    def question_card(question: dict, item: dict) -> str:
        original = item.get("original")
        source = question["parent"]
        target = question["child"]
        exact = original and original[0][:2] == (source, target)
        old_text = ""
        current_text = ""
        if exact:
            old_text = f'<p>{esc(original[1]["statement"])}</p>'
            scope = original[1].get("scope")
            if scope:
                old_text += f'<p><strong>Original scope</strong> {esc(scope)}</p>'
            statuses = ", ".join(sorted({entry["status"] for _, entry in item["question_edges"]})) or "absent"
            current_text = f'<p class="dr-meta">Canonical {esc(original[0][2].replace("_", " "))} status · {esc(statuses)}</p>'
        reviewed_sources = {entry["url"]: entry for entry in item["report"]["sources"]}
        entries = [reviewed_sources.get(url, {"url": url}) if isinstance(url, str) else url
                   for url in question["sources"]]
        parent = f'<p>Earlier record · {esc(records[source]["name"])}</p>' if source != target else ""
        return (
            f'<article class="dr-card"><div class="dr-meta">{esc(question["initial_status"].capitalize())}'
            f' → <strong>{esc(question["decision"].capitalize())}</strong></div>'
            f'<h4>{esc(records[target]["name"])}</h4>'
            f'{parent}'
            f'{old_text}<p>{esc(question["reason"])}</p>{current_text}'
            f'{source_list(entries, "Sources for this decision")}</article>'
        )

    def node_card(node: dict) -> str:
        record = node["record"]
        events = []
        for kind, rows in node["events"].items():
            for event in rows:
                events.append(
                    f'<li><strong>{esc(kind.removesuffix("_events").capitalize())} · '
                    f'{esc(event["date"]["label"])}</strong> {esc(event["statement"])}'
                    f'{citations(event.get("evidence", []))}</li>'
                )
        changes = f'<p>Changed fields · {esc(", ".join(node["fields"]))}</p>' if node["fields"] else ""
        return (
            f'<details class="dr-card"><summary>{esc("Added" if node["change"] == "new_nodes" else "Updated")}'
            f' · {node_name(record["id"])}</summary><p class="dr-meta">{esc(record["id"])}</p>'
            f'<p>{esc(record["description"])}</p>{changes}'
            f'{f"<ul>{''.join(events)}</ul>" if events else ""}</details>'
        )

    options = []
    panels = []
    for item in wave:
        report = item["report"]
        review = item["review"]
        lane = report["lane"]
        label = LABELS[lane]
        options.append(f'<option value="dr-{esc(lane)}">{esc(label)}</option>')
        panels.append(f'<section class="dr-panel" id="dr-{esc(lane)}"><h3>{esc(report["title"])}</h3>')
        if "original" in item:
            panels.append('<h4>Original research question</h4>')
            panels.append(question_card(item["original_question"], item))
        other_questions = [question for question in report["questions"] if question != item.get("original_question")]
        if other_questions:
            cards = "".join(question_card(question, item) for question in other_questions)
            panels.append(f'<details><summary>Other questions reviewed</summary>{cards}</details>')
        established = {"new_established_edges", "promoted_established_edges", "updated_established_edges"}
        panels.append("<h4>Established relationships in this update</h4>")
        edge_cards = "".join(edge_card(*edge) for edge in item["edges"] if edge[1] in established)
        panels.append(edge_cards or "<p>Zero established relationships added, promoted or updated.</p>")
        if item["context"]:
            panels.append('<details><summary>Established links for context</summary>'
                          + "".join(edge_card(*edge) for edge in item["context"]) + "</details>")
        open_changes = "".join(edge_card(*edge) for edge in item["edges"] if edge[1] not in established)
        if open_changes:
            panels.append(f'<details><summary>Other relationship changes</summary>{open_changes}</details>')
        if item["nodes"]:
            panels.append("<h4>Discovery records changed</h4>" + "".join(node_card(node) for node in item["nodes"]))
        if report["findings"]:
            panels.append("<h4>Findings</h4>" + notes(report["findings"]))
        if report["frontier"]:
            panels.append("<h4>What still needs evidence</h4>" + notes(report["frontier"]))
        if report["limits"]:
            limits = report["limits"] if isinstance(report["limits"], list) else [report["limits"]]
            panels.append("<h4>Evidence limits</h4>" + notes(limits))
        panels.append(source_list(report["sources"], "Sources and locators"))
        panels.append(
            f'<details><summary>Independent review and provenance</summary>'
            f'<p>Proposal · {esc(report["researcher"])} / {esc(report["effort"])}</p>'
            f'<p>Review · {esc(review["reviewer"])} / {esc(review["effort"])}</p>'
            f'<p>Accepted commit · <code>{esc(review["proposal"])}</code> '
            f'({len(review["files"])} files verified)</p>'
            f'{notes(review["claims"])}{notes(review["corrections"])}{notes(review["deferred"])}</details></section>'
        )

    totals = metrics["aggregate"]
    statistics = (
        (f'{totals["original_questions_established"]} / {totals["original_questions"]}', "Original links established"),
        (totals["new_established_edges"], "New established links"),
        (totals["promoted_established_edges"], "Promoted links"),
        (totals["new_nodes"], "New records"),
    )
    stats_html = "".join(f'<div><strong>{count}</strong><small>{label}</small></div>' for count, label in statistics)
    template = (HERE / "template.html").read_text(encoding="utf-8")
    return (template.replace("<!-- STATS -->", stats_html)
            .replace("<!-- OPTIONS -->", "".join(options))
            .replace("<!-- PANELS -->", "".join(panels)))


def snapshot(wave: list[dict], metrics: dict) -> str:
    """Compare counts on a shared scale and label each original decision."""
    width, left, size, row_height = 820, 262, 310, 48
    height = 166 + len(wave) * row_height
    maximum = max(
        max(1, item["counters"]["new_established_edges"] + item["counters"]["promoted_established_edges"])
        for item in wave
    )
    ticks = sorted({0, maximum // 2, maximum})
    scale = size / maximum
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        'role="img" aria-labelledby="title description">',
        '<title id="title">Digital follow-up evidence by lane</title>',
        '<desc id="description">Counts of new and promoted established links by lane, with dispositions for all six original questions.</desc>',
        '<rect width="100%" height="100%" rx="16" fill="#f5f4ef"/>',
        '<g fill="#172c2a" font-family="system-ui,sans-serif">',
        '<text x="26" y="41" font-size="25" font-weight="700">Digital technology evidence follow-up</text>',
        '<text x="26" y="68" font-size="13">17 November 2026 · Independently reviewed changes</text>',
        f'<text x="{left}" y="101" font-size="14" font-weight="700">Established links (count)</text>',
        '<text x="634" y="101" font-size="14" font-weight="700">Original question</text>',
    ]
    for tick in ticks:
        x = left + tick * scale
        parts.append(f'<path d="M{x:g} 121 V{height - 49}" stroke="#cbd4ce"/>'
                     f'<text x="{x:g}" y="119" text-anchor="middle" font-size="12">{tick}</text>')
    for i, item in enumerate(wave):
        y = 127 + i * row_height
        lane = item["report"]["lane"]
        counters = item["counters"]
        new = counters["new_established_edges"]
        promoted = counters["promoted_established_edges"]
        outcome = item.get("original_decision", "Supplemental").capitalize()
        parts.append(f'<text x="26" y="{y+22}" font-size="14">{html.escape(LABELS[lane])}</text>')
        for start, span, color in ((0, new, "#167266"), (new, promoted, "#4a508b")):
            if span:
                parts.append(f'<rect x="{left + start * scale:g}" y="{y+7}" width="{span*scale:g}" height="18" fill="{color}"/>'
                             f'<text x="{left + (start + span / 2) * scale:g}" y="{y+21}" text-anchor="middle" '
                             f'fill="white" font-size="12">{span}</text>')
        if not new and not promoted:
            parts.append(f'<text x="{left+9}" y="{y+21}" font-size="12">0</text>')
        parts.append(f'<text x="634" y="{y+22}" font-size="14">{html.escape(outcome)}</text>')
    parts.append(f'<rect x="26" y="{height-31}" width="12" height="12" fill="#167266"/>'
                 f'<text x="45" y="{height-20}" font-size="12">New established</text>'
                 f'<rect x="174" y="{height-31}" width="12" height="12" fill="#4a508b"/>'
                 f'<text x="193" y="{height-20}" font-size="12">Promoted from open</text>'
                 f'<text x="634" y="{height-20}" font-size="12">Base {metrics["baseline"][:12]}</text></g></svg>')
    return "\n".join(parts) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--after", required=True, help="Integrated commit containing the accepted proposals and reviews")
    parser.add_argument("--output", type=Path, default=HERE, help="Directory for view.html, snapshot.svg and metrics.json")
    parser.add_argument("--fragment", type=Path, help="Also write the interactive conversation fragment to this path")
    args = parser.parse_args()
    try:
        wave, records, sources, metrics = compile_wave(revision(args.after))
        fragment = render_reader(wave, records, sources, metrics)
    except (ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"{exc}\n")
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "view.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Digital technology evidence follow-up</title>'
        '<style>html{color-scheme:light dark}body{margin:0;background:Canvas;color:CanvasText;font:16px/1.55 system-ui,sans-serif}'
        '#digital-reader{max-width:920px;margin:auto;padding:clamp(16px,4vw,48px)}</style></head><body>'
        + fragment + "</body></html>\n",
        encoding="utf-8",
    )
    (args.output / "snapshot.svg").write_text(snapshot(wave, metrics), encoding="utf-8")
    write_json(args.output / "metrics.json", metrics)
    if args.fragment:
        args.fragment.parent.mkdir(parents=True, exist_ok=True)
        args.fragment.write_text(fragment, encoding="utf-8")


if __name__ == "__main__":
    main()
