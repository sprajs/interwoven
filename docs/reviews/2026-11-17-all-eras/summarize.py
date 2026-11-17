"""Rebuild the all-eras reader from the reviewed Git snapshot specified in report.md."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
ROUND = "docs/reviews/2026-11-17-all-eras"
# Each reader selection is a dated event with its own evidence in the accepted record.
SELECTIONS = {
    "building": ("Roman volcanic aggregate and the Pantheon", [
        ("roman-lightweight-stone-in-concrete-vaults", "basilica-ulpia-aisle-vault")]),
    "textiles": ("Jacquard weaving and Babbage’s engine design", [
        ("babbage-analytical-engine-punched-card-design", "annotated-english-account-1843")]),
    "gesher": ("Fire and fish cooking at Gesher Benot Ya’aqov", [
        ("gesher-fish-cooking-inference", "documented-evidence")]),
    "nanchoc": ("Water and cultivated fields at Ñanchoc", [
        ("nanchoc-early-crop-system", "tierra-blanca-field-cultivation")]),
    "maize": ("Maize preparation in Maya and Nahua communities", [
        ("alkaline-cooking-of-maize-san-bartolo", "residues-at-grupo-zacatal")]),
    "antiquity": ("The Antikythera calendar dial", [
        ("toothed-gearing-in-the-hellenistic-greek-world", "archaeological-evidence-100bce")]),
    "credit": ("Tang remittances and the Sichuan note office", [
        ("tang-flying-money-exchange-certificates", "three-fiscal-offices-812"),
        ("sichuan-jiaozi-paper-money", "state-takeover-1024")]),
    "endowment": ("The Jerusalem hospital endowment", [
        ("1047-jerusalem-hospital-endowment", "dated-evidence")]),
    "engaruka": ("Sediment capture at Engaruka", [
        ("engaruka-terraced-irrigation-and-sediment-capture", "abandonment-of-sediment-capture")]),
    "medicine": ("The stethoscope travels from Paris to London", [
        ("laennec-monaural-stethoscope-and-mediate-auscultation", "paris-london-transmission-by-1820")]),
    "oceania": ("Marshallese navigation and teaching models", [
        ("marshallese-wave-model-instruction", "bokin-ujae-instruction-2006")]),
    "placement": ("The Barbegal mills and Radio Sutatenza", [
        ("barbegal-mill-complex", "dated-assertion-130"),
        ("radio-sutatenza-rural-radio-schools", "transmitter-inauguration-1954")]),
    "fft": ("Good’s method and the fast Fourier transform", [
        ("good-interaction-and-fourier-analysis-1958", "addendum-1960")]),
    "yoruba": ("Yoruba filmmaking and the surviving VHS edition", [
        ("1989-nigerian-yoruba-commercial-video-films", "aje-ni-iya-mi-vhs-edition")]),
}


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def load(revision: str, path: str) -> dict:
    return json.loads(git("show", f"{revision}:{path}"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", help="the integrated data commit")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    snapshot = git("rev-parse", "--verify", "--end-of-options", args.snapshot + "^{commit}").decode().strip()
    filenames = git("ls-tree", "-r", "--name-only", snapshot, "data/discoveries").decode().splitlines()
    paths = {Path(path).stem: path for path in filenames if path.endswith(".json")}
    result = {"title": "What changed across the six eras", "context_label": "selected dated events",
              "data_commit": snapshot, "lanes": {},
              "accepted_established_edges": [], "unresolved_edges": [], "supported_circumstances": [], "sources": {}}
    record_changes = []
    source_ids = set()
    verified = set()
    bases = set()
    for lane, (title, selected) in SELECTIONS.items():
        review = load(snapshot, f"{ROUND}/reviews/{lane}.json")
        if review["overall_decision"] != "accept":
            raise ValueError(f"{lane}: review is not an acceptance")
        base = review["base_commit"]
        bases.add(base)
        changed = git("diff", "--name-only", base, review["worker_commit"],
                      "--", "data", "evidence", f"{ROUND}/lanes").decode().splitlines()
        bound = {item["path"]: item["sha256"] for item in review["files"]}
        if set(changed) != set(bound):
            raise ValueError(f"{lane}: reviewed file list differs from proposal")
        for path, expected in bound.items():
            if path in verified or hashlib.sha256(git("show", f"{snapshot}:{path}")).hexdigest() != expected:
                raise ValueError(f"{lane}: overlapping or changed reviewed file {path}")
            verified.add(path)
        result["lanes"][lane] = {"title": title, "worker_commit": review["worker_commit"],
                                 "review": f"reviews/{lane}.json", "next_questions": review["unknowns"]}
        for record_id, event_id in selected:
            path = paths[record_id]
            if path not in bound:
                raise ValueError(f"Selected event is outside {lane}'s reviewed records")
            record = load(snapshot, path)
            event = next(e for e in record["events"] if e["id"] == event_id)
            result["supported_circumstances"].append({
                "lane": lane, "record_name": record["name"], "record_id": record_id, "event_id": event_id,
                "facet": event["date"]["label"], "statement": event["statement"], "review_decision": "accept",
                "qualification": event.get("caveats") or event["date"].get("basis", ""),
                "evidence": event["evidence"],
            })
            source_ids.update(item["source"] for item in event["evidence"])
        for path in bound:
            if not path.startswith("data/discoveries/"):
                continue
            record = load(snapshot, path)
            existing = git("ls-tree", base, "--", path)
            old_record = load(base, path) if existing else {}
            prior_events = {e["id"]: e for e in old_record.get("events", [])}
            events = {e["id"]: e for e in record["events"]}
            record_changes.append({
                "lane": lane, "record": record["id"], "new_record": not bool(existing),
                "events_added": sorted(events.keys() - prior_events.keys()),
                "events_removed": sorted(prior_events.keys() - events.keys()),
                "events_revised": sorted(k for k in events.keys() & prior_events.keys()
                                         if events[k] != prior_events[k]),
            })
            old_links = old_record.get("links", [])
            old_keys = {(item["from"], item["type"], item["status"]) for item in old_links}
            for edge in record.get("links", []):
                if edge in old_links:
                    continue
                if edge["status"] == "established":
                    if (edge["from"], edge["type"], edge["status"]) in old_keys:
                        continue  # A revised qualifier on an existing established relation.
                    result["accepted_established_edges"].append({
                        **edge, "lane": lane, "to": record["id"], "review_decision": "accept",
                        "from_name": load(snapshot, paths[edge["from"]])["name"], "to_name": record["name"],
                    })
                    source_ids.update(item["source"] for item in edge["evidence"])
                else:
                    result["unresolved_edges"].append({**edge, "lane": lane, "to": record["id"]})
                    source_ids.update(item["source"] for item in edge.get("evidence", []))
    if len(bases) != 1:
        raise ValueError("Research proposals used different baselines")
    base = bases.pop()
    live = set(git("diff", "--name-only", base, snapshot, "--", "data", "evidence").decode().splitlines())
    if live != {p for p in verified if p.startswith(("data/", "evidence/"))}:
        raise ValueError("Integrated data changes differ from independently reviewed changes")
    result.update(base_commit=base, verified_files=len(verified), record_changes=record_changes)
    for source in sorted(source_ids):
        meta = load(snapshot, f"data/sources/{source[0]}/{source}.json")
        result["sources"][source] = {"title": meta["title"], "url": meta.get("url", "")}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
