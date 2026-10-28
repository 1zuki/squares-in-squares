"""Convert public exact-rational certificate files into candidate JSON.

Certificate format:
    n side
    x y tan(theta / 2)
"""

from __future__ import annotations

import argparse
import json
import re
from fractions import Fraction
from pathlib import Path

import mpmath

mpmath.mp.dps = 80


def rational(value: str) -> mpmath.mpf:
    fraction = Fraction(value)
    return mpmath.mpf(fraction.numerator) / mpmath.mpf(fraction.denominator)


def parse(path: Path):
    rows = [line.split() for line in path.read_text().splitlines() if line.strip() and not line.startswith("#")]
    if not rows or len(rows[0]) != 2:
        raise ValueError("missing n/side header")
    n = int(rows[0][0])
    side = rational(rows[0][1])
    squares = []
    for row in rows[1 : n + 1]:
        if len(row) != 3:
            raise ValueError("expected x y tan(theta/2)")
        x, y, tangent = (rational(value) for value in row)
        squares.append((x, y, 2 * mpmath.atan(tangent)))
    if len(squares) != n:
        raise ValueError(f"expected {n} squares, found {len(squares)}")
    return n, side, squares


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("certificate_dir")
    parser.add_argument("output")
    parser.add_argument("--max-n", type=int, default=1000)
    args = parser.parse_args()

    result = {}
    errors = []
    for path in sorted(Path(args.certificate_dir).glob("n*.cert")):
        match = re.fullmatch(r"n(\d+)", path.stem)
        if not match:
            continue
        try:
            n, side, squares = parse(path)
            if n > args.max_n:
                continue
            result[str(n)] = {
                "source_file": str(path),
                "declared_side": mpmath.nstr(side, 70),
                "squares": [[mpmath.nstr(value, 70) for value in square] for square in squares],
            }
        except Exception as exc:  # noqa: BLE001 - report bad public inputs without hiding them
            errors.append(f"{path}: {exc}")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"parsed {len(result)} certificates; {len(errors)} errors")
    for error in errors:
        print(error)


if __name__ == "__main__":
    main()
