"""Generate deterministic grid and Göbel-style seed packings for n=1..1000."""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import mpmath
import numpy as np

mpmath.mp.dps = 60
MAX_N = 1000
EPS = mpmath.mpf("1e-12")


def side(squares):
    xs, ys = [], []
    for x, y, angle in squares:
        h = (abs(mpmath.cos(angle)) + abs(mpmath.sin(angle))) / 2
        xs.extend((x - h, x + h))
        ys.extend((y - h, y + h))
    return max(max(xs) - min(xs), max(ys) - min(ys))


def grid_squares(n: int):
    k = math.ceil(math.sqrt(n))
    return [(mpmath.mpf(i % k) + mpmath.mpf("0.5"), mpmath.mpf(i // k) + mpmath.mpf("0.5"), mpmath.mpf("0")) for i in range(n)]


def goebel_square(a: int, b: int):
    root2 = mpmath.sqrt(2)
    s = a + 1 + b / root2
    center = s / 2
    half = mpmath.mpf("0.5")
    squares = []
    for i in range(a):
        for j in range(a - i):
            for fx, fy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                x = i + half if fx == 0 else s - i - half
                y = j + half if fy == 0 else s - j - half
                squares.append((x, y, mpmath.mpf("0")))
    for p in range(b):
        for q in range(b):
            u = p - (b - 1) * half
            v = q - (b - 1) * half
            squares.append((center + (u - v) / root2, center + (u + v) / root2, mpmath.pi / 4))
    return s, squares


ROOT2_F = math.sqrt(2.0)


def _staircase_counts(thresholds, k):
    t = np.floor(np.asarray(thresholds) + 1e-12)
    i = np.arange(k, dtype=np.float64)
    active = np.clip(t[..., None] - i + 1, 0, k)
    return active.sum(axis=-1)


def _best_strip_float(side_length, width):
    k = math.floor(side_length + 1e-12)
    ms = np.arange(-1, int(side_length) + 2, dtype=np.float64)
    values = [ms - side_length + 2, side_length - 2 - ms - width * ROOT2_F]
    row_m = np.arange(0, int(side_length * ROOT2_F) + 2, dtype=np.float64)
    half = (side_length * ROOT2_F - 2 - row_m) / 2
    half = half[half >= 0]
    for row in range(width):
        for offset in (half, -half):
            values.append((0.5 + row - offset) * ROOT2_F - width * ROOT2_F)
    lower = np.concatenate(values)
    lower = lower[(lower >= -side_length - 1) & (lower <= side_length + 1)]
    upper = lower + width * ROOT2_F
    lower_stairs = _staircase_counts(side_length - 2 - upper, k)
    upper_stairs = _staircase_counts(side_length - 2 + lower, k)
    rows = np.zeros_like(lower)
    for row in range(width):
        offset = -upper / ROOT2_F + 0.5 + row
        span = side_length * ROOT2_F - 2 - 2 * np.abs(offset)
        rows += np.where(span >= -1e-12, np.floor(span + 1e-12) + 1, 0)
    totals = lower_stairs + upper_stairs + rows
    index = int(np.argmax(totals))
    return int(totals[index]), float(lower[index])


def row_count(side_length, offset):
    span = float(side_length) * ROOT2_F - 2 - 2 * abs(float(offset))
    return int(math.floor(span + 1e-12)) + 1 if span >= -1e-12 else 0


def strip_rows(lower, width):
    root2 = mpmath.sqrt(2)
    upper = lower + width * root2
    return [-upper / root2 + mpmath.mpf("0.5") + row for row in range(width)]


def best_strip(side_length, width):
    count, lower = _best_strip_float(float(side_length), width)
    return count, mpmath.mpf(str(lower))


def min_strip_side(n, width, lower_bound, upper_bound):
    lo, hi = float(lower_bound), float(upper_bound)
    if _best_strip_float(hi, width)[0] < n:
        return None
    for _ in range(42):
        mid = (lo + hi) / 2
        if _best_strip_float(mid, width)[0] >= n:
            hi = mid
        else:
            lo = mid
    return mpmath.mpf(repr(hi))


def diagonal_strip(side_length, lower, width):
    side_length = mpmath.mpf(side_length)
    lower = mpmath.mpf(lower)
    root2 = mpmath.sqrt(2)
    upper = lower + width * root2
    squares = []
    k = int(mpmath.floor(side_length))
    for i in range(k):
        for j in range(k):
            if i + j <= mpmath.floor(side_length - 2 - upper):
                squares.append((i + mpmath.mpf("0.5"), side_length - j - mpmath.mpf("0.5"), mpmath.mpf("0")))
            if i + j <= mpmath.floor(side_length - 2 + lower):
                squares.append((side_length - i - mpmath.mpf("0.5"), j + mpmath.mpf("0.5"), mpmath.mpf("0")))
    for row, offset in enumerate(strip_rows(lower, width)):
        count = row_count(side_length, offset)
        for index in range(count):
            distance = 1 + abs(offset) + index
            squares.append(((distance + offset) / root2, (distance - offset) / root2, mpmath.pi / 4))
    return squares


def candidates(n: int):
    best = (side(grid_squares(n)), grid_squares(n), "grid")
    root2 = mpmath.sqrt(2)
    for a in range(0, 40):
        for b in range(1, 50):
            if not (a - 1 < b / root2 < a + 1):
                continue
            if 2 * a * (a + 1) + b * b != n:
                continue
            candidate_side, squares = goebel_square(a, b)
            if candidate_side < best[0]:
                best = (candidate_side, squares, f"goebel(a={a},b={b})")
    for width in range(1, 9):
        upper_bound = mpmath.mpf(math.ceil(math.sqrt(n)))
        lower_bound = mpmath.sqrt(n)
        candidate_side = min_strip_side(n, width, lower_bound, upper_bound)
        if candidate_side is not None and candidate_side < best[0] - mpmath.mpf("1e-30"):
            count, lower = best_strip(float(candidate_side), width)
            squares = diagonal_strip(candidate_side + mpmath.mpf("3e-9"), lower + mpmath.mpf("1.5e-9"), width)
            if len(squares) >= n:
                best = (candidate_side, squares[:n], f"diagonal_strip(width={width})")
    squares = [((x + EPS) * (1 + EPS), (y + EPS) * (1 + EPS), angle) for x, y, angle in best[1]]
    return best[0], squares, best[2]


def write_submission(path: str | Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("id", "n", "square_id", "x", "y", "angle"))
        row_id = 0
        sources = {}
        for n in range(1, MAX_N + 1):
            _, squares, source = candidates(n)
            sources[str(n)] = source
            for square_id, (x, y, angle) in enumerate(squares):
                writer.writerow((row_id, n, square_id, mpmath.nstr(x, 45), mpmath.nstr(y, 45), mpmath.nstr(angle, 45)))
                row_id += 1
            if n % 25 == 0:
                print(f"generated n={n}", flush=True)
    if len(sources) != MAX_N or row_id != MAX_N * (MAX_N + 1) // 2:
        temp_path.unlink(missing_ok=True)
        raise RuntimeError(f"incomplete generation: puzzles={len(sources)} rows={row_id}")
    temp_path.replace(path)
    path.with_suffix(path.suffix + ".sources.txt").write_text("\n".join(f"{n}: {src}" for n, src in sources.items()) + "\n")


if __name__ == "__main__":
    write_submission(sys.argv[1] if len(sys.argv) > 1 else "data/submission.base.csv")
