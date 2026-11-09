#!/usr/bin/env python3
"""Fetch and check the saved copies of sources that are too large to keep in git.

Text evidence (HTML, text, XML) is committed. PDFs and images are not: each has a small
descriptor beside it, ``<file>.cache.json``, that records its checksum, its size and how to get
it again. A machine without the files can still validate everything else.

    python tools/evidence.py status                 # what is present, missing or needs a person
    python tools/evidence.py verify --all           # re-hash the files that are present
    python tools/evidence.py fetch <source-id>      # download one, checked against its checksum
    python tools/evidence.py fetch --all
    python tools/evidence.py capture --path evidence/x/x-2020-title.pdf --url https://... --source x-2020-title

A download is kept only if its bytes match the recorded SHA-256. An existing file is never replaced.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from dataset import ROOT, sha256

EVIDENCE = ROOT / "evidence"
SUFFIX = ".cache.json"
BINARY = {".pdf", ".jpg", ".png"}
#: What the first bytes of each kind of file must contain, so that an error page is never kept as evidence.
SIGNATURES = {".pdf": b"%PDF-", ".png": b"\x89PNG\r\n\x1a\n", ".jpg": b"\xff\xd8\xff"}


def descriptors() -> list[dict]:
    """Every descriptor, checked for shape and for sitting beside the file it describes."""
    entries = []
    for path in sorted(EVIDENCE.rglob("*" + SUFFIX)):
        entry = json.loads(path.read_text(encoding="utf-8"))
        target = ROOT / entry["path"]
        if path != Path(str(target) + SUFFIX):
            raise ValueError(f"{path.relative_to(ROOT)} does not sit beside {entry['path']}")
        if target.suffix.lower() not in BINARY:
            raise ValueError(f"{entry['path']} is not a PDF, JPG or PNG")
        if not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) or not isinstance(entry["bytes"], int) or entry["bytes"] <= 0:
            raise ValueError(f"{entry['path']} has a bad checksum or size")
        entries.append(entry)
    return entries


def present(entry: dict) -> bool:
    target = ROOT / entry["path"]
    return target.is_file() and target.stat().st_size == entry["bytes"] and sha256(target) == entry["sha256"]


def download(urls: list[str], destination: Path, expected: str | None = None, size: int | None = None) -> Path:
    """Save the first response whose bytes match. The file appears only once it is complete and checked."""
    if destination.exists():
        if expected and sha256(destination) == expected:
            return destination
        raise ValueError(f"{destination.relative_to(ROOT)} exists and differs. Move it aside before retrying.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    problems = []
    for url in urls:
        parts = urlsplit(url)
        if parts.scheme not in {"https", "http"} or not parts.netloc or parts.username or parts.password:
            problems.append(f"{url}: not a plain web address")
            continue
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".download-", delete=False) as output:
                temporary = Path(output.name)
                with urlopen(Request(url, headers={"User-Agent": "InterwovenEvidence/1.0"}), timeout=60) as response:
                    shutil.copyfileobj(response, output)
            if not temporary.stat().st_size:
                raise ValueError("empty response")
            if size is not None and temporary.stat().st_size != size:
                raise ValueError("size differs from the recorded copy")
            if expected and sha256(temporary) != expected:
                raise ValueError("checksum differs from the recorded copy")
            with temporary.open("rb") as stream:
                if SIGNATURES[destination.suffix.lower()] not in stream.read(1024):
                    raise ValueError(f"not a {destination.suffix[1:].upper()} file")
            os.link(temporary, destination)
            return destination
        except (OSError, ValueError) as error:
            problems.append(f"{url}: {error}")
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    raise ValueError("No address gave a matching file. " + "; ".join(problems or ["none is recorded"]))


def fetch(entry: dict, original: bool = False) -> Path:
    """Get one file. An excerpt is rebuilt from its original with Poppler, page by page."""
    target = ROOT / entry["path"]
    recipe = entry["retrieval"]
    if not original and present(entry):
        return target
    if recipe["kind"] == "manual":
        raise ValueError(recipe["reason"])
    if recipe["kind"] == "download":
        return download(recipe["urls"], target, entry["sha256"], entry["bytes"])
    if recipe["kind"] != "pdf_excerpt":
        raise ValueError(f"unknown way of retrieving: {recipe['kind']}")
    source = EVIDENCE / ".cache" / "originals" / f"{recipe['original_sha256']}.pdf"
    download(recipe["urls"], source, recipe["original_sha256"])
    if original:
        return source
    if target.exists():
        raise ValueError(f"{entry['path']} exists and differs. Move it aside before retrying.")
    pages = sorted(recipe["page_mapping"], key=lambda row: row["excerpt_page"])
    with tempfile.TemporaryDirectory(dir=source.parent) as directory:
        parts = []
        for index, row in enumerate(pages):
            number = str(row["source_page"])
            subprocess.run(["pdfseparate", "-f", number, "-l", number, str(source), f"{directory}/{index}-%d.pdf"], check=True, capture_output=True)
            parts.append(f"{directory}/{index}-{number}.pdf")
        result = Path(directory) / "excerpt.pdf"
        subprocess.run(["pdfunite", *parts, str(result)], check=True, capture_output=True)
        if sha256(result) != entry["sha256"]:
            raise ValueError(f"the rebuilt excerpt differs from the recorded one. The checked original is at {source.relative_to(ROOT)}")
        target.parent.mkdir(parents=True, exist_ok=True)
        os.link(result, target)
    return target


def chosen(entries: list[dict], selectors: list[str], everything: bool) -> list[dict]:
    if everything:
        return entries
    out = []
    for selector in selectors:
        found = [e for e in entries if selector in (e["path"], Path(e["path"]).name, *e["sources"])]
        if len(found) != 1:
            raise ValueError(f"'{selector}' matches {len(found)} files. Give one source id or one path.")
        out.extend(e for e in found if e not in out)
    if not out:
        raise ValueError("Name the sources or paths to act on, or pass --all.")
    return out


def capture(path: str, url: str, source: str | None) -> None:
    target = ROOT / path
    if target.suffix.lower() not in BINARY or not target.resolve().is_relative_to(EVIDENCE):
        raise ValueError("Give a PDF, JPG or PNG path inside evidence/.")
    if Path(str(target) + SUFFIX).exists():
        raise ValueError(f"{path} is already recorded. Use fetch to restore it.")
    download([url], target)
    entry = {"path": path, "sha256": sha256(target), "bytes": target.stat().st_size, "sources": [source] if source else [], "retrieval": {"kind": "download", "urls": [url]}}
    Path(str(target) + SUFFIX).write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"path": path, "sha256": entry["sha256"]}, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="count what is present, missing and needing a person; no network")
    for name in ("verify", "fetch"):
        command = commands.add_parser(name)
        command.add_argument("selectors", nargs="*", help="source ids or paths")
        command.add_argument("--all", action="store_true")
        if name == "fetch":
            command.add_argument("--original", action="store_true", help="for an excerpt, fetch the full original and stop")
    command = commands.add_parser("capture", help="download a new file and record its address and checksum")
    command.add_argument("--path", required=True)
    command.add_argument("--url", required=True)
    command.add_argument("--source")
    args = parser.parse_args()

    try:
        entries = descriptors()
        if args.command == "capture":
            capture(args.path, args.url, args.source)
            return 0
        if args.command == "status":
            counts: Counter[str] = Counter()
            for entry in entries:
                if present(entry):
                    counts["present"] += 1
                elif entry["retrieval"]["kind"] == "manual":
                    counts["missing, and must be found by hand"] += 1
                    print(f"by hand   {entry['path']}")
                else:
                    counts["missing, and can be fetched"] += 1
                    print(f"fetchable {entry['path']}")
            print(f"{len(entries)} files: " + ", ".join(f"{n} {what}" for what, n in sorted(counts.items())))
            return 0
        failed = 0
        for entry in chosen(entries, args.selectors, args.all):
            try:
                if args.command == "verify":
                    if not (ROOT / entry["path"]).exists():
                        print(f"absent  {entry['path']}")
                    elif present(entry):
                        print(f"ok      {entry['path']}")
                    else:
                        raise ValueError("does not match its recorded checksum")
                else:
                    print(f"ok      {fetch(entry, args.original).relative_to(ROOT)}")
            except (OSError, ValueError, subprocess.CalledProcessError) as error:
                failed += 1
                print(f"FAILED  {entry['path']}: {error}")
        return 1 if failed else 0
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
