#!/usr/bin/env python3
"""Check the dataset against its schema, its registers and its saved evidence.

    python tools/validate.py            # everything
    python tools/validate.py --fast     # skip hashing the saved copies of sources

Exits with status 1 when anything is wrong.
"""

from __future__ import annotations

import argparse
import sys

from dataset import Dataset


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fast", action="store_true", help="skip hashing saved copies of sources")
    args = parser.parse_args()

    data = Dataset.load()
    errors = data.validate(check_files=not args.fast)
    links = list(data.links())
    print(
        f"{len(data.discoveries)} discoveries, "
        f"{sum(len(d['events']) for d in data.discoveries.values())} events, "
        f"{len(links)} links, {len(data.sources)} sources, "
        + ", ".join(f"{len(rows)} {name}" for name, rows in data.registers.items())
    )
    for line in errors[:200]:
        print("  " + line)
    if len(errors) > 200:
        print(f"  ... and {len(errors) - 200} more")
    print("No problems found." if not errors else f"{len(errors)} problems.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
