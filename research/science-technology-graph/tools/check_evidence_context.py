#!/usr/bin/env python3
"""Check saved comparison captures and context-map pointers without changing files.

Canonical source copies and proposition bindings are checked by validate.py.
This additional check covers declared evidence paths in continuation comparisons
and the two portable context maps. It does not assess historical claims.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def check(root: Path) -> dict:
    root = root.resolve()
    if not (root / "data/nodes.jsonl").is_file():
        return {"valid": False, "errors": [{"error": "Not a graph directory", "path": str(root)}]}
    hashes, errors, references = {}, [], 0

    def capture(path, expected, locus):
        nonlocal references
        references += 1
        target = (root / path).resolve()
        if not target.is_relative_to(root):
            errors.append({"locus": locus, "error": "Path leaves the graph directory", "path": path})
            return
        try:
            if target not in hashes:
                raw = target.read_bytes()
                if not raw:
                    raise ValueError("Empty capture")
                hashes[target] = hashlib.sha256(raw).hexdigest()
            if hashes[target] != expected:
                raise ValueError(f"SHA-256 mismatch: actual {hashes[target]}")
        except (OSError, ValueError) as exc:
            errors.append({"locus": locus, "path": path, "error": str(exc)})

    def walk(value, locus):
        if isinstance(value, dict):
            if isinstance(value.get("path"), str) and value["path"].startswith("evidence/"):
                digest = value.get("sha256")
                if isinstance(digest, str):
                    capture(value["path"], digest, locus)
            for key, item in value.items():
                walk(item, f"{locus}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{locus}[{index}]")

    maps = [root / "reviews" / name for name in ("frontier-context.json", "continuation-context.json")]
    for file in maps:
        if file.exists():
            document = json.loads(file.read_text())
            for index, row in enumerate(document.get("retained_context_files", [])):
                capture(row["path"], row["sha256"], f"{file.name}.retained_context_files[{index}]")

    ledgers = sorted((root / "reviews").glob("continuation-[0-9][0-9].json"))
    for file in ledgers:
        document = json.loads(file.read_text())
        pointer = document.get("portable_comparison_context")
        if pointer:
            capture(pointer["path"], pointer["sha256"], f"{file.name}.portable_comparison_context")
        walk(document.get("frontier_comparisons", []), f"{file.name}.frontier_comparisons")

    return {"valid": not errors, "comparison_ledgers": len(ledgers), "declared_references_checked": references,
            "distinct_files_hashed": len(hashes), "errors": errors,
            "scope": "Declared context captures, nested comparison evidence path/hash pairs and portable-map pointers; no historical or frontier-certification claim."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = check(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["valid"] else 1)
