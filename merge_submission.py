"""Merge validated candidate packings and propagate layouts across sizes."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import mpmath

from geometry import bounding_side, validate_packing

MAX_N = 1000
MAX_SOURCE_N = 1100
EPS = mpmath.mpf("1e-12")


def normalize(squares):
    values = [tuple(mpmath.mpf(str(value)) for value in square) for square in squares]
    x0 = min(x - (abs(mpmath.cos(angle)) + abs(mpmath.sin(angle))) / 2 for x, _, angle in values)
    y0 = min(y - (abs(mpmath.cos(angle)) + abs(mpmath.sin(angle))) / 2 for _, y, angle in values)
    return [((x - x0) * (1 + EPS), (y - y0) * (1 + EPS), angle) for x, y, angle in values]


def candidate_frame(n, squares):
    squares = normalize(squares)
    return [(n, index, tuple(float(value) for value in square)) for index, square in enumerate(squares)]


def write_csv(path, best):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("id", "n", "square_id", "x", "y", "angle"))
        row_id = 0
        sources = {}
        for n in sorted(best):
            source, squares = best[n]
            sources[str(n)] = source
            for square_id, (x, y, angle) in enumerate(squares):
                writer.writerow((row_id, n, square_id, repr(x), repr(y), repr(angle)))
                row_id += 1
    path.with_suffix(path.suffix + ".sources.json").write_text(json.dumps(sources, indent=2) + "\n")


def load_csv(path):
    best = {}
    with Path(path).open(newline="") as handle:
        for row in csv.DictReader(handle):
            n = int(row["n"])
            best.setdefault(n, []).append((int(row["square_id"]), (float(row["x"]), float(row["y"]), float(row["angle"]))))
    result = {}
    for n, rows in best.items():
        rows.sort()
        squares = [square for _, square in rows]
        valid, message, side = validate_packing(squares)
        if valid:
            result[n] = ("base", squares, side)
        else:
            print(f"base n={n} rejected: {message}")
    return result


def load_candidates(paths):
    for path in paths:
        data = json.loads(Path(path).read_text())
        for key, record in data.items():
            n = int(str(key).rstrip("_"))
            squares = record["squares"]
            if n <= MAX_SOURCE_N and len(squares) == n:
                yield n, str(path), squares


def consider(best, n, source, squares):
    if n > MAX_SOURCE_N or len(squares) != n:
        return False
    normalized = [tuple(float(value) for value in square) for square in normalize(squares)]
    valid, message, side = validate_packing(normalized)
    if not valid:
        return False
    old = best.get(n)
    if old is None or side < old[2] - 1e-12:
        best[n] = (source, normalized, side)
        return True
    return False


def drop_pass(best):
    changed = 0
    for n in range(MAX_SOURCE_N - 1, 0, -1):
        if n + 1 not in best:
            continue
        squares = best[n + 1][1][:n]
        if consider(best, n, f"drop<-{n + 1}", squares):
            changed += 1
    return changed


def extend_pass(best):
    changed = 0
    for n in range(1, MAX_SOURCE_N):
        if n not in best:
            continue
        source_squares = best[n][1]
        side = best[n][2]
        for extra in range(1, 8):
            width = math.floor(side + 1e-9)
            n2 = n + extra * (math.floor(side + extra + 1e-9) + width)
            if n2 > MAX_SOURCE_N or n2 in best:
                continue
            new = list(source_squares)
            half = 0.5
            new.extend((side + i + half, j + half, 0.0) for i in range(extra) for j in range(math.floor(side + extra)))
            new.extend((i + half, side + j + half, 0.0) for i in range(width) for j in range(extra))
            if len(new) >= n2 and consider(best, n2, f"extend{extra}<-{n}", new[:n2]):
                changed += 1
    return changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base")
    parser.add_argument("output")
    parser.add_argument("candidates", nargs="*")
    args = parser.parse_args()
    best = load_csv(args.base)
    for path in args.candidates:
        wins = sum(consider(best, n, path, squares) for n, _, squares in load_candidates([path]))
        print(f"{path}: accepted {wins} candidates")
    for _ in range(4):
        changed = extend_pass(best) + drop_pass(best)
        print(f"transfer pass: {changed} changes")
        if not changed:
            break
    best = {n: value for n, value in best.items() if n <= MAX_N}
    write_csv(args.output, {n: (source, squares) for n, (source, squares, _) in best.items()})
    score = sum(side / math.sqrt(n) - 1 for n, (_, _, side) in best.items())
    score += sum(math.ceil(math.sqrt(n)) / math.sqrt(n) - 1 for n in range(1, MAX_N + 1) if n not in best)
    print(f"wrote {len(best)}/{MAX_N} puzzles; expected score={score:.9f}")


if __name__ == "__main__":
    main()
