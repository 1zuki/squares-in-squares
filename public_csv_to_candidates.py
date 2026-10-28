"""Convert a public Kaggle submission CSV into complete-layout candidates."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def convert(path: Path):
    groups = defaultdict(list)
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        expected = {"id", "n", "square_id", "x", "y", "angle"}
        if set(reader.fieldnames or ()) != expected:
            raise ValueError(f"unexpected columns in {path}: {reader.fieldnames}")
        for row in reader:
            n = int(row["n"])
            groups[n].append((int(row["square_id"]), [row["x"], row["y"], row["angle"]]))
    result = {}
    rejected = {}
    for n, rows in groups.items():
        rows.sort()
        if len(rows) != n or [sid for sid, _ in rows] != list(range(n)):
            rejected[str(n)] = f"incomplete or duplicate square ids: {len(rows)} rows"
            continue
        result[str(n)] = {
            "source_file": str(path),
            "squares": [values for _, values in rows],
        }
    return result, rejected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("submission", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--rejected")
    args = parser.parse_args()
    result, rejected = convert(args.submission)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    if args.rejected:
        Path(args.rejected).write_text(json.dumps(rejected, indent=2) + "\n")
    print(f"converted {len(result)} complete layouts; rejected {len(rejected)} partial layouts")


if __name__ == "__main__":
    main()
