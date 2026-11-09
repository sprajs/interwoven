#!/usr/bin/env python3
"""Extract explicitly selected CHAT telephone cells from a verified local CSV.

The source file is never fetched by this tool. Output is a JSON observation array.
"""
import argparse
import csv
import json
from pathlib import Path

from dataset import DATA, read_json, sha256, telephone_value


def extract(path: Path, selection: list[tuple[str, str]], expected_hash: str) -> list[dict]:
    if sha256(path) != expected_hash:
        raise ValueError("input SHA-256 does not match the documented release")
    if not selection or len(set(selection)) != len(selection):
        raise ValueError("selection must be nonempty and contain no duplicate country/year")
    wanted = set(selection)
    found = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not {"country_name", "year", "telephone"}.issubset(reader.fieldnames or []):
            raise ValueError("missing CHAT CSV columns")
        previous_line = reader.line_num
        for row in reader:
            if reader.line_num != previous_line + 1:
                raise ValueError("multiline CSV rows cannot use physical line locators")
            previous_line = reader.line_num
            key = (row["country_name"], row["year"])
            if key not in wanted:
                continue
            if key in found:
                raise ValueError(f"duplicate source row: {key}")
            value = telephone_value(row["telephone"])
            found[key] = {"country": key[0], "year_token": key[1], "raw_value": row["telephone"],
                          "value": value, "status": "missing" if value is None else "reported", "row": reader.line_num}
    if wanted - found.keys():
        raise ValueError(f"selected rows absent from source: {sorted(wanted - found.keys())}")
    return [found[key] for key in selection]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--select", action="append", required=True, metavar="COUNTRY:YEAR")
    args = parser.parse_args()
    try:
        selection = []
        for value in args.select:
            country, year = value.rsplit(":", 1)
            if not country or len(year) != 4 or not year.isascii() or not year.isdigit():
                raise ValueError("selection must be COUNTRY:YYYY")
            selection.append((country, year))
        panel = read_json(DATA / "reference/adoption/chat-telephone-pilot.json")
        print(json.dumps(extract(args.input, selection, panel["release"]["sha256"]), indent=2, ensure_ascii=False))
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
