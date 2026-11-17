"""Open a reviewed source workflow, start a worksheet, or render the evidence reader."""
from __future__ import annotations

import argparse
from hashlib import sha256
from html import escape
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from urllib.parse import urlsplit

from dataset import ROOT


ROUND = "docs/reviews/2026-11-17-provenance"
ARTIFACTS = ("eynan", "samir")
WORKFLOWS = ("computing", "electricity", "metrology", "optics", "printing", "rail", "steam", "telephony")
REVIEWER = ("gpt-6.1-terra", "high")
TEMPLATES = Path(__file__).parent


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], stderr=subprocess.PIPE)


def commit(ref: str) -> str:
    try:
        return git("rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"unknown Git revision {ref!r}") from exc


def blob(ref: str, path: str) -> bytes:
    try:
        return git("cat-file", "blob", f"{ref}:{path}")
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"missing file at {ref[:12]}: {path}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def text_fields(item: dict, fields: tuple[str, ...], label: str) -> None:
    for field in fields:
        value = item.get(field)
        require(isinstance(value, str) and bool(value.strip()), f"{label}: missing text for {field}")


def verify_case_shape(case: dict, lane: str) -> None:
    kind = "workflow" if lane in WORKFLOWS else "artifact"
    require(case["lane"] == lane and case["kind"] == kind, f"{lane}: mismatched case ID or kind")
    text_fields(case, ("title", "question", "summary", "decision", "next", "researcher", "effort", "base"), lane)
    if kind == "workflow":
        text_fields(case, ("reject_if", "stop_when", "next_anchor"), lane)
        inputs = case["inputs"]
        require(isinstance(inputs, list) and bool(inputs) and all(isinstance(x, str) and x.strip() for x in inputs),
                f"{lane}: expected workflow inputs")
    steps = case["steps"]
    require(isinstance(steps, list) and bool(steps), f"{lane}: expected an ordered sequence of steps")
    for step in steps:
        text_fields(step, ("title", "action", "result"), lane)
        sources = step["sources"]
        require(isinstance(sources, list) and bool(sources), f"{lane}: no sources for {step['title']}")
        for source in sources:
            text_fields(source, ("title", "url", "locator"), lane)
            parsed = urlsplit(source["url"])
            require(parsed.scheme in {"https", "http"} and bool(parsed.netloc), f"{lane}: invalid source URL")


def manifest_hashes(receipt: dict) -> dict[str, str]:
    hashes = {}
    for entry in receipt["files"]:
        path = entry["path"]
        parsed = PurePosixPath(path)
        require(not parsed.is_absolute() and ".." not in parsed.parts and str(parsed) == path,
                f"invalid reviewed file path {path!r}")
        require(path not in hashes, f"duplicate reviewed file {path}")
        digest = entry["sha256"].strip().lower().removeprefix("sha256:").strip()
        require(re.fullmatch(r"[0-9a-f]{64}", digest) is not None, f"invalid SHA-256 for {path}")
        hashes[path] = digest
    return hashes


def verify_bytes(raw: bytes, expected: str, path: str) -> None:
    require(sha256(raw).hexdigest() == expected, f"reviewed SHA-256 mismatch: {path}")


def reviewed_case(snapshot: str, lane: str, *, verify_history: bool = False, historical: str | None = None) -> dict:
    lane_path = f"{ROUND}/lanes/{lane}.json"
    raw = blob(snapshot, lane_path)
    case = json.loads(raw)
    receipt = json.loads(blob(snapshot, f"{ROUND}/reviews/{lane}.json"))
    require(receipt.get("lane", lane) == lane, f"{lane}: review lane ID does not match")
    require(receipt.get("overall_decision") == "accept", f"{lane}: no accepted independent review")
    reviewer = receipt["reviewer"]
    require((reviewer["model"], reviewer["effort"]) == REVIEWER, f"{lane}: expected Terra High reviewer")
    require((case["researcher"], case["effort"]) != REVIEWER, f"{lane}: reviewer and researcher identities coincide")
    require(receipt.get("base_commit", receipt.get("base", case["base"])) == case["base"], f"{lane}: review baseline mismatch")
    worker = receipt["worker_commit"]
    require(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", worker) is not None
            and receipt.get("proposal_commit", worker) == worker, f"{lane}: invalid worker commit")
    hashes = manifest_hashes(receipt)
    require(lane_path in hashes, f"{lane}: independent review omitted the ledger hash")
    verify_bytes(raw, hashes[lane_path], lane_path)
    verify_case_shape(case, lane)

    if verify_history:
        try:
            binding = commit(worker)
        except ValueError:
            # Published checkouts can have the accepted bytes without private worker Git objects.
            binding = historical or snapshot
        for path, digest in hashes.items():
            verify_bytes(blob(binding, path), digest, path)
        claims = receipt.get("claim_reviews", receipt.get("claims"))
        require(isinstance(claims, (dict, list)) and bool(claims), f"{lane}: review has no claim details")
        case["review"] = {
            **{key: receipt[key] for key in ("issues", "unknowns", "rationale", "scope") if key in receipt},
            "source_checks": receipt.get("source_checks", receipt.get("originalsourcechecks")),
            "limitations": receipt.get("limitations", receipt.get("limits")),
            "claim_reviews": claims,
            "reviewer": reviewer,
            "overall_decision": receipt["overall_decision"],
            "worker_commit": worker,
            "verified_commit": binding,
            "files_checked": len(hashes),
        }
    return case


def workflow_steps(case: dict) -> str:
    inputs = "\n".join(f"- {item}" for item in case["inputs"])
    actions = "\n\n".join(f"{number}. {step['action']}" for number, step in enumerate(case["steps"], 1))
    return (f"# {case['lane']}\n\n## Required inputs\n\n{inputs}\n\n## Steps\n\n{actions}\n\n"
            f"## Rejection criterion\n\n{case['reject_if']}\n\n## Stopping rule\n\n{case['stop_when']}\n")


def worksheet(case: dict, subject: str) -> str:
    title = re.sub(r"([\\`*_\[\]])", r"\\\1", escape(" ".join(subject.split()), quote=False))
    lines = [f"# Source research worksheet for {title}", "", f"Workflow **{case['lane']}**", "",
             "## Required inputs", "", *(f"- {item} …" for item in case["inputs"]), "",
             "## Proposed relationship", "", "- Antecedent or sender, version and event …",
             "- Dependent or recipient, version and event …", "- Proposed type and direction …",
             "- Competing explanation …", "", "## Investigation", ""]
    for number, step in enumerate(case["steps"], 1):
        lines.extend([f"### Step {number}", "", step["action"], "", "- Search or catalogue query and version …",
                      "- Original source URL and exact locator …", "- Observed result and what it supports …",
                      "- Limits, access gaps or contrary evidence …", ""])
    lines.extend(["## Evidence for the proposed direction", "", "- Observation supporting the antecedent …",
                  "- Observation supporting use or receipt by the dependent …", "- Evidence linking the exact endpoints …",
                  "- Independent corroborating source lineage, URL and locator …", "",
                  "## Rejection criterion", "", case["reject_if"], "", "## Stopping rule", "", case["stop_when"], "",
                  "## Decision", "",
                  "- Disposition and reason …", "- Unresolved evidence and next test …", ""])
    return "\n".join(lines)


def reader(cases: list[dict]) -> tuple[str, str]:
    raw = json.dumps(cases, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    fragment = (TEMPLATES / "provenance_view.html").read_text(encoding="utf-8").replace("@@CASE_DATA@@", raw)
    require(len(fragment.encode("utf-8")) < 1_000_000, "provenance reader exceeds the inline size limit")
    standalone = (TEMPLATES / "provenance_standalone.html").read_text(encoding="utf-8")
    return fragment, standalone.replace("<!--PROVENANCE_READER-->", fragment)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", default="HEAD", help="revision with the selected ledgers and independent receipts")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="list all verified reusable workflow IDs")
    show = sub.add_parser("show", help="show transferable steps for a workflow")
    show.add_argument("id", choices=WORKFLOWS)
    start = sub.add_parser("start", help="write a blank Markdown worksheet to standard output")
    start.add_argument("id", choices=WORKFLOWS)
    start.add_argument("--subject", required=True, help="new subject for the worksheet heading")
    render = sub.add_parser("render", help="render both versions of the reviewed evidence reader")
    render.add_argument("--output", type=Path, required=True, help="directory for view.html and provenance-reader.html")
    render.add_argument("--historical", help="reviewed integration revision when worker Git objects are unavailable")
    args = parser.parse_args()
    try:
        snapshot = commit(args.snapshot)
        if args.command == "list":
            entries = [reviewed_case(snapshot, key) for key in WORKFLOWS]
            print("\n".join(f"{case['lane']}\t{case['title']}" for case in entries))
        elif args.command == "show":
            print(workflow_steps(reviewed_case(snapshot, args.id)), end="")
        elif args.command == "start":
            require(bool(args.subject.strip()), "worksheet subject cannot be empty")
            print(worksheet(reviewed_case(snapshot, args.id), args.subject), end="")
        else:
            historical = commit(args.historical) if args.historical else None
            cases = [reviewed_case(snapshot, key, verify_history=True, historical=historical) for key in ARTIFACTS + WORKFLOWS]
            fragment, standalone = reader(cases)
            args.output.mkdir(parents=True, exist_ok=True)
            (args.output / "provenance-reader.html").write_text(fragment, encoding="utf-8")
            (args.output / "view.html").write_text(standalone, encoding="utf-8")
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
