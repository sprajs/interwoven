#!/usr/bin/env python3
"""Fetch selected local binary evidence using per-item .cache.json descriptors."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SIDECAR_SUFFIX = ".cache.json"
BINARY_SUFFIXES = {".pdf", ".jpg", ".png"}


def local_path(root, relative):
    path = (root / relative).resolve()
    if not str(relative).startswith("evidence/") or not path.is_relative_to(root.resolve() / "evidence"):
        raise ValueError("Evidence paths must stay inside the local evidence directory")
    return path


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_catalog(root):
    entries = []
    seen = set()
    for descriptor in sorted((root / "evidence").rglob("*" + SIDECAR_SUFFIX)):
        entry = json.loads(descriptor.read_text())
        if entry.get("schema_version") != 1:
            raise ValueError("Unsupported cache descriptor: " + str(descriptor))
        path = local_path(root, entry["path"])
        if descriptor.resolve() != Path(str(path) + SIDECAR_SUFFIX):
            raise ValueError("Cache descriptor must sit beside its binary: " + str(descriptor))
        if path.suffix.lower() not in BINARY_SUFFIXES or entry["path"] in seen:
            raise ValueError("Duplicate or unsupported binary path: " + entry["path"])
        seen.add(entry["path"])
        if not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) or type(entry["bytes"]) is not int or entry["bytes"] <= 0:
            raise ValueError("Invalid checksum or byte length: " + entry["path"])
        entries.append(entry)
    return entries


def matches(path, sha256, size=None):
    return path.is_file() and (size is None or path.stat().st_size == size) and digest(path) == sha256


def download(urls, destination, expected=None, size=None):
    """Promote a complete verified response atomically; preserve existing files."""
    if destination.exists():
        if expected and matches(destination, expected, size):
            return destination
        raise ValueError("Existing file differs; preserve or move it before retrying: " + str(destination))
    destination.parent.mkdir(parents=True, exist_ok=True)
    errors = []
    for url in urls:
        parts = urlsplit(url)
        if parts.scheme not in {"https", "http"} or not parts.netloc or parts.username or parts.password:
            errors.append("Unsupported source URL")
            continue
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".download-", delete=False) as output:
                temporary = Path(output.name)
                request = Request(url, headers={"User-Agent": "BigIdeaEvidenceCache/1.0"})
                with urlopen(request, timeout=60) as response:
                    shutil.copyfileobj(response, output)
            if not temporary.stat().st_size:
                raise ValueError("Empty response")
            if size is not None and temporary.stat().st_size != size:
                raise ValueError("Response byte length differs from the recorded capture")
            if expected and digest(temporary) != expected:
                raise ValueError("Response SHA-256 differs from the recorded capture")
            with temporary.open("rb") as stream:
                header = stream.read(1024)
            if destination.suffix == ".pdf" and b"%PDF-" not in header:
                raise ValueError("Response is not a PDF")
            if destination.suffix == ".png" and not header.startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError("Response is not a PNG")
            if destination.suffix == ".jpg" and not header.startswith(b"\xff\xd8\xff"):
                raise ValueError("Response is not a JPEG")
            os.link(temporary, destination)
            return destination
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    raise ValueError("No matching source response: " + "; ".join(errors or ["No recorded source URL"]))


def fetch_entry(root, entry, original=False):
    target = local_path(root, entry["path"])
    recipe = entry["retrieval"]
    if not original and matches(target, entry["sha256"], entry["bytes"]):
        return target
    if recipe["kind"] == "manual":
        raise ValueError(recipe["reason"])
    if recipe["kind"] == "download":
        return download(recipe["urls"], target, entry["sha256"], entry["bytes"])
    if recipe["kind"] != "pdf_excerpt":
        raise ValueError("Unsupported retrieval recipe")
    original_hash = recipe["original_sha256"]
    if not re.fullmatch(r"[0-9a-f]{64}", original_hash):
        raise ValueError("Invalid original source checksum")
    source = local_path(root, "evidence/.cache/originals/" + original_hash + ".pdf")
    download(recipe["urls"], source, original_hash)
    if original:
        return source
    if target.exists():
        raise ValueError("Existing excerpt differs; preserve or move it before retrying")
    mapping = sorted(recipe["page_mapping"], key=lambda row: row["excerpt_page"])
    if [row["excerpt_page"] for row in mapping] != list(range(1, len(mapping) + 1)) or not mapping:
        raise ValueError("Page mapping must describe consecutive excerpt pages")
    for row in mapping:
        if type(row["source_page"]) is not int or not 1 <= row["source_page"] <= recipe["original_page_count"]:
            raise ValueError("Page mapping leaves the original document")
    with tempfile.TemporaryDirectory(dir=source.parent) as directory:
        directory = Path(directory)
        pages = []
        for index, row in enumerate(mapping):
            number = str(row["source_page"])
            pattern = directory / (str(index) + "-%d.pdf")
            subprocess.run(["pdfseparate", "-f", number, "-l", number, str(source), str(pattern)], check=True, capture_output=True)
            pages.append(directory / (str(index) + "-" + number + ".pdf"))
        result = directory / "excerpt.pdf"
        subprocess.run(["pdfunite", *map(str, pages), str(result)], check=True, capture_output=True)
        if not matches(result, entry["sha256"], entry["bytes"]):
            raise ValueError("Rebuilt excerpt bytes differ. The verified original is available at " + str(source)
                             + "; retain the historical excerpt locally or review a new representation explicitly.")
        target.parent.mkdir(parents=True, exist_ok=True)
        os.link(result, target)
    return target


def selected(entries, selectors, all_files):
    if all_files:
        return entries
    result = []
    for selector in selectors:
        found = [entry for entry in entries if selector in [entry["path"], Path(entry["path"]).name, *entry["source_ids"]]]
        if len(found) != 1:
            raise ValueError("Select one unambiguous source ID or evidence path: " + selector)
        if found[0] not in result:
            result.append(found[0])
    if not result:
        raise ValueError("Select evidence paths/source IDs, or explicitly use --all")
    return result


def capture(root, entries, path, url, source_id):
    target = local_path(root, path)
    if target.suffix.lower() not in BINARY_SUFFIXES:
        raise ValueError("Capture supports PDF, JPG and PNG files")
    if any(entry["path"] == path for entry in entries):
        raise ValueError("Path already catalogued; use fetch to restore it or a new path for a new version")
    download([url], target)
    entry = {"schema_version": 1, "path": path, "sha256": digest(target), "bytes": target.stat().st_size,
             "source_ids": [source_id] if source_id else [], "provenance_records": [],
             "retrieval": {"kind": "download", "urls": [url], "note": "Captured by evidence_cache.py; capture is not historical review."}}
    descriptor = Path(str(target) + SIDECAR_SUFFIX)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=descriptor.parent, prefix=".descriptor-", delete=False) as output:
        temporary = Path(output.name)
        json.dump(entry, output, indent=2, ensure_ascii=False)
        output.write("\n")
    try:
        os.link(temporary, descriptor)
    finally:
        temporary.unlink(missing_ok=True)
    print(json.dumps({"path": path, "sha256": entry["sha256"], "representation": "full_source"}, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("status", help="List cache availability and retrieval limits; no network access")
    command.add_argument("--summary", action="store_true", help="Show counts without listing individual paths")
    commands.add_parser("check-metadata", help="Check individual descriptors against canonical binary source references; no network access")
    for name in ("fetch", "verify"):
        command = commands.add_parser(name)
        command.add_argument("selectors", nargs="*")
        command.add_argument("--all", action="store_true")
        if name == "fetch":
            command.add_argument("--original", action="store_true", help="For legacy excerpts, fetch the verified full original without rebuilding")
    command = commands.add_parser("capture", help="Capture one new full source locally and record its URL and checksum")
    command.add_argument("--path", required=True)
    command.add_argument("--url", required=True)
    command.add_argument("--source-id")
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        entries = load_catalog(root)
        if args.command == "capture":
            capture(root, entries, args.path, args.url, args.source_id)
            return 0
        if args.command == "status":
            report = {"present": [], "missing": [], "mismatched": [], "manual_recovery": []}
            for entry in entries:
                target = local_path(root, entry["path"])
                state = "present" if matches(target, entry["sha256"], entry["bytes"]) else "mismatched" if target.exists() else "missing"
                report[state].append(entry["path"])
                if entry["retrieval"]["kind"] == "manual":
                    report["manual_recovery"].append(entry["path"])
            counts = {key: len(value) for key, value in report.items()}
            print(json.dumps({"counts": counts, **({} if args.summary else report)}, indent=2))
            return int(bool(report["mismatched"]))
        if args.command == "check-metadata":
            by_path = {entry["path"]: entry for entry in entries}
            count = 0
            for line in (root / "data/sources.jsonl").read_text().splitlines():
                source = json.loads(line)
                copy = source.get("local_copy", {})
                if Path(copy.get("path", "")).suffix.lower() in BINARY_SUFFIXES:
                    entry = by_path.get(copy["path"])
                    if entry is None or entry["sha256"] != copy["sha256"] or source["id"] not in entry["source_ids"]:
                        raise ValueError("Canonical binary source differs from its cache descriptor: " + source["id"])
                    count += 1
            print(f"Descriptors cover {count} canonical binary source references and {len(entries)} cache files; no local bytes certified.")
            return 0
        failed = False
        for entry in selected(entries, args.selectors, args.all):
            try:
                if args.command == "fetch":
                    print(str(fetch_entry(root, entry, args.original)))
                elif not matches(local_path(root, entry["path"]), entry["sha256"], entry["bytes"]):
                    raise ValueError("Local bytes are missing or differ from the recorded capture")
            except (OSError, ValueError, subprocess.CalledProcessError) as exc:
                failed = True
                print(entry["path"] + ": " + str(exc), file=sys.stderr)
        return int(failed)
    except (OSError, ValueError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
