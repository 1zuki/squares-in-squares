"""Independent schema, decimal, wall, SAT, and score audit for a submission."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

from geometry import validate_packing

DECIMAL = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$")
MAX_N = 1000


def read_submission(path: str | Path):
    rows = defaultdict(list)
    errors = []
    with Path(path).open(newline="") as handle:
        reader = csv.DictReader(handle)
        expected = {"id", "n", "square_id", "x", "y", "angle"}
        if set(reader.fieldnames or ()) != expected:
            errors.append(f"columns are {reader.fieldnames!r}, expected {sorted(expected)!r}")
        for line, row in enumerate(reader, start=2):
            try:
                n = int(row["n"]); square_id = int(row["square_id"])
                values = [row["x"].strip(), row["y"].strip(), row["angle"].strip()]
                if any(len(v) > 1000 or not DECIMAL.fullmatch(v) for v in values): raise ValueError("non-decimal coordinate")
                square = tuple(float(v) for v in values)
                if not all(math.isfinite(v) for v in square): raise ValueError("non-finite coordinate")
                rows[n].append((square_id, square))
            except Exception as exc:  # noqa: BLE001 - audit should continue
                errors.append(f"line {line}: {exc}")
    return rows, errors


def audit(path: str | Path):
    rows, errors = read_submission(path)
    details = {}
    score = 0.0
    invalid = 0
    for n in range(1, MAX_N + 1):
        group = rows.get(n, [])
        if len(group) != n or {sid for sid, _ in group} != set(range(n)):
            errors.append(f"n={n}: expected square ids 0..{n-1} exactly once, got {len(group)} rows")
            invalid += 1
            penalty = math.ceil(math.sqrt(n)) / math.sqrt(n) - 1.0
            details[str(n)] = {"valid": False, "side": None, "message": "bad count or ids", "score": penalty}
            score += penalty
            continue
        squares = [square for _, square in sorted(group)]
        valid, message, side = validate_packing(squares)
        if not valid:
            invalid += 1
            errors.append(f"n={n}: {message}")
            penalty = math.ceil(math.sqrt(n)) / math.sqrt(n) - 1.0
            details[str(n)] = {"valid": False, "side": side, "message": message, "score": penalty}
            score += penalty
        else:
            puzzle_score = side / math.sqrt(n) - 1.0
            details[str(n)] = {"valid": True, "side": side, "message": message, "score": puzzle_score}
            score += puzzle_score
    return {"path": str(path), "score": score, "invalid_puzzles": invalid, "errors": errors, "puzzles": details}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("submission")
    parser.add_argument("--report")
    args = parser.parse_args()
    report = audit(args.submission)
    if args.report: Path(args.report).parent.mkdir(parents=True, exist_ok=True); Path(args.report).write_text(json.dumps(report, indent=2) + "\n")
    print(f"score={report['score']:.9f} invalid_puzzles={report['invalid_puzzles']} errors={len(report['errors'])}")
    for error in report["errors"][:40]: print(error)
    raise SystemExit(1 if report["invalid_puzzles"] or report["errors"] else 0)


if __name__ == "__main__":
    main()
