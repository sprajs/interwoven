#!/usr/bin/env python3
"""Check and summarise the independent review's verdict files.

Run from anywhere:
    python3 research/science-technology-graph/handovers/independent-review/summarise_verdicts.py

The script fails with a non-zero exit if a verdict file does not cover every
relationship and entry in data/, has a duplicate or unknown id, or has a value
outside the allowed sets. It writes summary.json and summary.md beside itself,
plus verdict-summary.png when matplotlib is available, and fills
verdict-browser.html from its template. It never changes data/.

Measures describe this review's judgements and the graph's stored records. They
are not measurements of history.
"""
from __future__ import annotations

import collections
import json
import pathlib
import re
import statistics
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
GRAPH = HERE.parents[1]
REPO = GRAPH.parents[1]
REVIEWED_COMMIT = "30df3e7"

CONN_FIELDS = {"id", "verdict", "severity", "issue", "proposed_change", "basis"}
ENTRY_FIELDS = {"id", "kind_verdict", "identity_verdict", "tier_verdict", "proposed_kind", "proposed_tier", "issue", "basis"}
VERDICTS = {"agree", "change", "reject", "cannot_verify"}
SEVERITIES = {"high", "medium", "low"}
CONN_CHECKS = {"read_cited_source", "read_cited_source_partly", "could_not_read_cited_source", "read_cited_and_other_source"}
ENTRY_CHECKS = {"read_cited_source", "read_other_source", "entry_record_and_linked_edge_sources", "knowledge_only"}
KIND_VERDICTS = {"agree", "change", "third_kind"}
IDENTITY = {"agree", "bundle", "duplicate", "too_narrow", "unclear", "witness_for_broader", "wrong_witness"}
TIER = {"agree", "too_high", "too_low"}
ANCHOR = {"agree", "minor", "misleading"}
CLASSES = {"none", "historical_error", "modelling_choice", "evidence_limit", "opinion"}


def load(path: pathlib.Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def check(rows: list[dict], expected: set[str], fields: set[str], name: str) -> list[str]:
    errors = []
    ids = [row.get("id") for row in rows]
    for dup, count in collections.Counter(ids).items():
        if count > 1:
            errors.append(f"{name}: {dup} appears {count} times")
    missing, extra = expected - set(ids), set(ids) - expected
    if missing:
        errors.append(f"{name}: missing {len(missing)}: {sorted(missing)[:5]}")
    if extra:
        errors.append(f"{name}: unknown {len(extra)}: {sorted(extra)[:5]}")
    for row in rows:
        absent = fields - set(row)
        if absent:
            errors.append(f"{name}: {row.get('id')} lacks {sorted(absent)}")
        if not row.get("basis", "").strip():
            errors.append(f"{name}: {row.get('id')} has an empty basis")
    return errors


def allowed(rows: list[dict], field: str, values: set, name: str) -> list[str]:
    return [f"{name}: {row['id']} has {field}={row.get(field)!r}" for row in rows if row.get(field) not in values]


def classes_ok(rows: list[dict], name: str) -> list[str]:
    return [
        f"{name}: {row['id']} has issue_class={row.get('issue_class')!r}"
        for row in rows
        if not set(str(row.get("issue_class")).split(";")) <= CLASSES
    ]


def year(event: dict) -> int | None:
    date = event["date"]
    bound = date.get("latest") or date.get("earliest")
    return bound["year"] if bound else None


def earliest_year(event: dict) -> int | None:
    date = event["date"]
    bound = date.get("earliest") or date.get("latest")
    return bound["year"] if bound else None


def graph_measures(nodes: list[dict], events: list[dict], rels: list[dict]) -> dict:
    """Facts computed from the graph itself, so REVIEW.md can be rechecked."""
    node_by_id = {n["id"]: n for n in nodes}
    event_by_id = {e["id"]: e for e in events}
    anchor = {n["id"]: event_by_id[n["graph_anchor"]["event_id"]] for n in nodes}

    reversed_edges = []
    for rel in rels:
        a, b = year(anchor[rel["from"]["node_id"]]), year(anchor[rel["to"]["node_id"]])
        if a is not None and b is not None and a > b:
            reversed_edges.append({"id": rel["id"], "from_year": a, "to_year": b})

    gaps = []
    for node in nodes:
        starts = [earliest_year(event_by_id[i]) for i in node["event_ids"]]
        starts = [s for s in starts if s is not None]
        anchor_year = year(anchor[node["id"]])
        if starts and anchor_year is not None and anchor_year - min(starts) >= 20:
            gaps.append({"id": node["id"], "tier": node["tier"], "gap_years": anchor_year - min(starts),
                         "earliest_event": min(starts), "anchor": anchor[node["id"]]["date"]["label"]})
    gaps.sort(key=lambda g: -g["gap_years"])

    parent = {n["id"]: n["id"] for n in nodes}
    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    degree = collections.Counter()
    in_degree = collections.Counter()
    for rel in rels:
        a, b = rel["from"]["node_id"], rel["to"]["node_id"]
        parent[find(a)] = find(b)
        degree[a] += 1
        degree[b] += 1
        in_degree[b] += 1
    fragments = collections.Counter(find(n["id"]) for n in nodes)

    reasons = collections.Counter(n.get("tier_reason") for n in nodes)
    boilerplate = {r: c for r, c in reasons.items() if c > 2}
    boiler_ids = {n["id"] for n in nodes if n.get("tier_reason") in boilerplate}
    prefix_tiers = collections.defaultdict(collections.Counter)
    for node in nodes:
        for prefix in ("entry-electronics", "entry-regional"):
            if node["id"].startswith(prefix):
                prefix_tiers[prefix][node["tier"]] += 1

    tier_sources = {}
    for tier in sorted({n["tier"] for n in nodes}):
        group = [n for n in nodes if n["tier"] == tier]
        tier_sources[tier] = {
            "entries": len(group),
            "median_sources": statistics.median(len(set(n["provenance"]["source_ids"])) for n in group),
            "median_connections": statistics.median(degree[n["id"]] for n in group),
            "with_no_connections": sum(1 for n in group if not degree[n["id"]]),
        }

    necessity = collections.Counter(r.get("necessity") for r in rels)
    return {
        "display_reversed_edges": reversed_edges,
        "anchor_gaps_20y_or_more": gaps,
        "fragments": len(fragments),
        "isolated_entries": sum(1 for n in nodes if not degree[n["id"]]),
        "tier0_with_no_inbound_connection": sum(1 for n in nodes if n["tier"] == 0 and not in_degree[n["id"]]),
        "entries_with_shared_tier_reason": len(boiler_ids),
        "shared_tier_reasons": boilerplate,
        "tiers_within_batches": {k: dict(v) for k, v in prefix_tiers.items()},
        "by_tier": tier_sources,
        "known_by_placements": sum(1 for n in nodes if n["graph_anchor"].get("date_interpretation") == "known_by"),
        "repeated_necessity_text": {k: v for k, v in necessity.items() if v >= 5},
        "relation_counts": dict(collections.Counter(r["relation"] for r in rels)),
        "confidence_counts": dict(collections.Counter(r["confidence"] for r in rels)),
    }


def write_figure(conn: list[dict], entries: list[dict], path: pathlib.Path) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    # One hue, light to dark, for counts; recessive axes; numbers labelled directly.
    ink, muted = "#1f2a30", "#5c6a72"
    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={"width_ratios": [1, 1.5]})
    grid = [[0] * 4 for _ in range(4)]
    for row in entries:
        target = row["proposed_tier"] if row["proposed_tier"] is not None else row["tier"]
        grid[row["tier"]][target] += 1
    left.imshow(grid, cmap="Blues", vmin=0, vmax=max(max(r) for r in grid) * 1.25)
    for y in range(4):
        for x in range(4):
            if grid[y][x]:
                left.text(x, y, grid[y][x], ha="center", va="center", fontsize=11,
                          color="white" if grid[y][x] > 45 else ink)
    left.set_xticks(range(4), [f"Tier {i}" for i in range(4)], color=muted)
    left.set_yticks(range(4), [f"Tier {i}" for i in range(4)], color=muted)
    left.set_xlabel("Tier this review proposes (entries; judgement, not measurement)", color=muted, fontsize=9)
    left.set_ylabel("Tier in the graph", color=muted, fontsize=9)
    left.tick_params(length=0)
    for side in left.spines.values():
        side.set_visible(False)
    left.set_title("Most tier proposals move one level", loc="left", fontsize=11, color=ink)

    relation = collections.defaultdict(collections.Counter)
    for row in conn:
        relation[row["relation"]][row["verdict"]] += 1
    names = sorted(relation, key=lambda r: sum(relation[r].values()))
    colours = {"agree": "#c6d4dc", "change": "#2a78d6", "reject": "#e34948", "cannot_verify": "#8a8f94"}
    label = {"agree": "Agree", "change": "Change", "reject": "Reject", "cannot_verify": "Cannot verify"}
    for y, name in enumerate(names):
        at = 0
        for verdict in colours:
            n = relation[name][verdict]
            if n:
                right.barh(y, n, left=at, height=0.6, color=colours[verdict], edgecolor="white", linewidth=2,
                           label=label[verdict] if y == len(names) - 1 or verdict not in ("agree", "change") else None)
                at += n
        right.text(at + 0.6, y, f"{sum(relation[name].values())}", va="center", fontsize=9, color=muted)
    right.set_yticks(range(len(names)), names, color=ink, fontsize=9)
    right.set_xlabel("Connections (count)", color=muted, fontsize=9)
    right.tick_params(axis="x", colors=muted, length=0)
    right.tick_params(axis="y", length=0)
    for side in ("top", "right", "left"):
        right.spines[side].set_visible(False)
    handles, labels = right.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    right.legend([unique[k] for k in label.values() if k in unique], [k for k in label.values() if k in unique],
                 frameon=False, fontsize=9, loc="lower right")
    right.set_title("'observed-combination' needs the most retyping", loc="left", fontsize=11, color=ink)
    fig.text(0.01, 0.005, f"Independent review of graph commit {REVIEWED_COMMIT}. Generated by summarise_verdicts.py.",
             fontsize=7.5, color=muted)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


TOP_CORRECTIONS = [
    ("Re-anchor entries whose date contradicts the graph's own events: Kilby at 1964, Bi Sheng at 1400, Maxwell at 1894, the Soho trials at 1854.", "Modelling choice, some historical error"),
    ("Fix the double helix's ancestry: add Franklin and Gosling and the diffraction work, and raise them from tiers 3 and 2.", "Modelling choice"),
    ("Remove the pH to Oxford penicillin link and add Fleming to Oxford.", "Modelling choice"),
    ("Re-rank tier 0 against one written test: remove the toothbrush bristle and aluminum supply; raise Ørsted, the integrated circuit, the telegraph and the Web.", "Opinion"),
    ("Split witnesses from what they witness: recombinant DNA as 1979, PCR as 1989, CRISPR as 2015, Newcomen as 1796.", "Modelling choice"),
    ("Add the major missing breakthroughs, or state what the chart covers: Gutenberg, paper, modern physics, germ theory, agriculture, writing.", "Selection"),
    ("Replace observed-combination, split documented-development, and record influence separately from confidence.", "Modelling choice"),
    ("Reconnect broken histories using the bounded relation: oxide mask to Hoerni, Briggs to Gunter, Volta to Ampère.", "Modelling choice"),
    ("Give mathematics and practices their own kind, with a separate role field.", "Modelling choice"),
    ("Move labels out of regular expressions: 43 entries have a labelling problem.", "Modelling choice, some plain bugs"),
]


def write_browser(conn: list[dict], entries: list[dict], gaps: list[dict], summary: dict, rels: list[dict], nodes: list[dict], events: list[dict]) -> None:
    """Fill the interactive page with this data. Presentation only; no simulation or new judgement."""
    template = HERE / "verdict-browser.template.html"
    if not template.exists():
        return
    rel = {r["id"]: r for r in rels}
    event = {e["id"]: e for e in events}
    node = {n["id"]: n for n in nodes}
    data = {
        "summary": summary,
        "top": TOP_CORRECTIONS,
        "gaps": gaps,
        "connections": [{**row, "statement": rel[row["id"]]["statement"], "from": rel[row["id"]]["from"]["node_id"], "to": rel[row["id"]]["to"]["node_id"]} for row in conn],
        "entries": [{**row, "date_label": event[node[row["id"]]["graph_anchor"]["event_id"]]["date"]["label"]} for row in entries],
    }
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    (HERE / "verdict-browser.html").write_text(template.read_text(encoding="utf-8").replace("/*DATA*/null", blob), encoding="utf-8")


def main() -> int:
    nodes = load(GRAPH / "data/nodes.jsonl")
    events = load(GRAPH / "data/events.jsonl")
    rels = load(GRAPH / "data/relationships.jsonl")
    conn = load(HERE / "connection-verdicts.jsonl")
    entries = load(HERE / "entry-verdicts.jsonl")
    gaps = load(HERE / "gaps.jsonl")

    errors = check(conn, {r["id"] for r in rels}, CONN_FIELDS, "connections")
    errors += check(entries, {n["id"] for n in nodes}, ENTRY_FIELDS, "entries")
    errors += allowed(conn, "verdict", VERDICTS, "connections")
    errors += allowed(conn, "severity", SEVERITIES, "connections")
    errors += allowed(conn, "check_method", CONN_CHECKS, "connections")
    errors += allowed(entries, "kind_verdict", KIND_VERDICTS, "entries")
    errors += allowed(entries, "identity_verdict", IDENTITY, "entries")
    errors += allowed(entries, "tier_verdict", TIER, "entries")
    errors += allowed(entries, "anchor_verdict", ANCHOR, "entries")
    errors += allowed(entries, "check_method", ENTRY_CHECKS, "entries")
    errors += classes_ok(conn, "connections") + classes_ok(entries, "entries")
    errors += [f"entries: {r['id']} has tier change {r['tier_verdict']} without proposed_tier" for r in entries
               if (r["tier_verdict"] != "agree") != (r["proposed_tier"] is not None)]
    errors += [f"connections: {r['id']} cannot_verify but marks a source fully read" for r in conn
               if r["verdict"] == "cannot_verify" and r["check_method"] == "read_cited_source"]
    breakthrough = [g for g in gaps if g["type"] == "missing_breakthrough"]
    links = [g for g in gaps if g["type"] == "missing_connection"]
    known = {n["id"] for n in nodes}
    errors += [f"gaps: unknown endpoint in {g}" for g in links if g["from"] not in known or g["to"] not in known]
    if len(breakthrough) > 30 or len(links) > 30:
        errors.append("gaps: more than 30 of a type")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        print(f"FAILED with {len(errors)} problem(s)", file=sys.stderr)
        return 1

    def counts(rows: list[dict], field: str) -> dict:
        return dict(collections.Counter(str(r[field]) for r in rows).most_common())

    class_conn = collections.Counter(c for r in conn for c in r["issue_class"].split(";"))
    class_entry = collections.Counter(c for r in entries for c in r["issue_class"].split(";"))
    try:
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    except OSError:
        head = "unknown"
    summary = {
        "reviewed_commit": REVIEWED_COMMIT,
        "generated_at_commit": head,
        "coverage": {"connections": f"{len(conn)}/{len(rels)}", "entries": f"{len(entries)}/{len(nodes)}"},
        "connections": {
            "verdict": counts(conn, "verdict"),
            "severity": counts(conn, "severity"),
            "evidence_support": counts(conn, "evidence_support"),
            "check_method": counts(conn, "check_method"),
            "issue_class": dict(class_conn),
            "observed_combination_verdicts": counts([r for r in conn if r["relation"] == "observed-combination"], "verdict"),
        },
        "entries": {
            "kind_verdict": counts(entries, "kind_verdict"),
            "identity_verdict": counts(entries, "identity_verdict"),
            "tier_verdict": counts(entries, "tier_verdict"),
            "anchor_verdict": counts(entries, "anchor_verdict"),
            "check_method": counts(entries, "check_method"),
            "issue_class": dict(class_entry),
            "with_label_issue": sum(1 for r in entries if r["label_issue"]),
            "tier0_now": sum(1 for r in entries if r["tier"] == 0),
            "tier0_kept": sum(1 for r in entries if r["tier"] == 0 and r["tier_verdict"] == "agree"),
            "tier0_proposed_up": sum(1 for r in entries if r["proposed_tier"] == 0),
        },
        "gaps": {"missing_breakthroughs": len(breakthrough), "missing_connections": len(links)},
        "graph": graph_measures(nodes, events, rels),
    }
    (HERE / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    g = summary["graph"]
    lines = [
        "# Verdict summary", "",
        f"Generated by `summarise_verdicts.py` from the review of commit `{REVIEWED_COMMIT}`. Do not edit by hand.", "",
        f"Coverage: {summary['coverage']['connections']} connections and {summary['coverage']['entries']} entries.", "",
        f"- Connection verdicts: {summary['connections']['verdict']}",
        f"- Connection severity: {summary['connections']['severity']}",
        f"- Cited evidence: {summary['connections']['evidence_support']}",
        f"- How connections were checked: {summary['connections']['check_method']}",
        f"- Tier verdicts: {summary['entries']['tier_verdict']}",
        f"- Identity verdicts: {summary['entries']['identity_verdict']}",
        f"- Kind verdicts: {summary['entries']['kind_verdict']}",
        f"- Anchor verdicts: {summary['entries']['anchor_verdict']}",
        f"- How entries were checked: {summary['entries']['check_method']}",
        f"- Entries with a label issue: {summary['entries']['with_label_issue']}",
        f"- Display-reversed connections: {len(g['display_reversed_edges'])}",
        f"- Entries anchored 20 or more years after their earliest event: {len(g['anchor_gaps_20y_or_more'])}",
        f"- Fragments and isolated entries: {g['fragments']} and {g['isolated_entries']}",
        f"- Entries sharing a tier reason used by more than two entries: {g['entries_with_shared_tier_reason']}",
        f"- Placements that use an upper or lower limit (known_by): {g['known_by_placements']}", "",
    ]
    (HERE / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    figure = write_figure(conn, entries, HERE / "verdict-summary.png")
    write_browser(conn, entries, gaps, summary, rels, nodes, events)
    print("\n".join(lines))
    print("Figure written." if figure else "matplotlib is not available; no figure written.")
    print("All coverage and value checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
