"""Convert the public Casson 2026 certified packings to merge candidates.

The imported files are retained verbatim under data/public_external/casson_2026-09-23.
This converter keeps the source side as provenance and converts the published
degree angles to the submission format's radians.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path


SIDE_RE = re.compile(r"^s:\s*(\S+)")
SQUARE_RE = re.compile(
    r"^Square\s+(\d+):\s+x=([^,]+),\s+y=([^,]+),\s+deg=([^\s]+)"
)


def parse(path: Path):
    lines = path.read_text().splitlines()
    if not lines:
        raise ValueError("empty packing")
    side_match = SIDE_RE.match(lines[0].strip())
    if not side_match:
        raise ValueError("missing s: header")
    side = float(side_match.group(1))
    squares = []
    for line in lines[1:]:
        match = SQUARE_RE.match(line.strip())
        if not match:
            if line.strip():
                raise ValueError(f"unrecognized line: {line}")
            continue
        index, x, y, degrees = match.groups()
        squares.append((int(index), (float(x), float(y), math.radians(float(degrees)))))
    squares.sort()
    n = int(path.stem[1:])
    if len(squares) != n or [index for index, _ in squares] != list(range(1, n + 1)):
        raise ValueError(f"expected square numbering 1..{n}, got {len(squares)} rows")
    return side, [square for _, square in squares]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = {}
    for path in sorted(args.source_dir.glob("n*.txt"), key=lambda p: int(p.stem[1:])):
        n = int(path.stem[1:])
        side, squares = parse(path)
        result[str(n)] = {
            "source_file": str(path),
            "source_side": repr(side),
            "squares": [[repr(x), repr(y), repr(angle)] for x, y, angle in squares],
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"converted {len(result)} Casson packings to {args.output}")


if __name__ == "__main__":
    main()
