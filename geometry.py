"""Independent float64 geometry checks for unit-square packings."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Iterable, Sequence


def corners(square: Sequence[float]) -> tuple[tuple[float, float], ...]:
    x, y, angle = map(float, square)
    c, s = math.cos(angle), math.sin(angle)
    return tuple(
        (x + dx * c - dy * s, y + dx * s + dy * c)
        for dx, dy in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5))
    )


def half_extent(angle: float) -> float:
    c, s = math.cos(float(angle)), math.sin(float(angle))
    return 0.5 * (abs(c) + abs(s))


def bounding_side(squares: Sequence[Sequence[float]]) -> float:
    if not squares:
        raise ValueError("packing is empty")
    xs: list[float] = []
    ys: list[float] = []
    for square in squares:
        for x, y in corners(square):
            xs.append(x)
            ys.append(y)
    return max(max(xs) - min(xs), max(ys) - min(ys))


def _projection_gap(a: Sequence[tuple[float, float]], b: Sequence[tuple[float, float]], axis: tuple[float, float]) -> float:
    pa = [x * axis[0] + y * axis[1] for x, y in a]
    pb = [x * axis[0] + y * axis[1] for x, y in b]
    return max(min(pb) - max(pa), min(pa) - max(pb))


def separating_gap(a: Sequence[float], b: Sequence[float]) -> float:
    """Return the largest SAT separation gap over the eight candidate axes."""
    ca, cb = corners(a), corners(b)
    axes: list[tuple[float, float]] = []
    for square in (a, b):
        c, s = math.cos(float(square[2])), math.sin(float(square[2]))
        axes.extend(((c, s), (-s, c)))
    return max(_projection_gap(ca, cb, axis) for axis in axes)


def _candidate_pairs(squares: Sequence[Sequence[float]], cell_size: float = 1.5) -> Iterable[tuple[int, int]]:
    """Broad-phase pairs; every possible overlap shares at least one bin."""
    bins: defaultdict[tuple[int, int], list[int]] = defaultdict(list)
    boxes: list[tuple[float, float, float, float]] = []
    for index, square in enumerate(squares):
        h = half_extent(float(square[2]))
        x, y = float(square[0]), float(square[1])
        box = (x - h, x + h, y - h, y + h)
        boxes.append(box)
        ix0, ix1 = math.floor(box[0] / cell_size), math.floor(box[1] / cell_size)
        iy0, iy1 = math.floor(box[2] / cell_size), math.floor(box[3] / cell_size)
        for ix in range(ix0, ix1 + 1):
            for iy in range(iy0, iy1 + 1):
                bins[(ix, iy)].append(index)
    seen: set[tuple[int, int]] = set()
    for members in bins.values():
        for offset, i in enumerate(members):
            for j in members[offset + 1 :]:
                pair = (i, j) if i < j else (j, i)
                if pair in seen:
                    continue
                seen.add(pair)
                ax0, ax1, ay0, ay1 = boxes[i]
                bx0, bx1, by0, by1 = boxes[j]
                if ax1 < bx0 or bx1 < ax0 or ay1 < by0 or by1 < ay0:
                    continue
                yield pair


def validate_packing(squares: Sequence[Sequence[float]], *, gap: float = 1e-12) -> tuple[bool, str, float]:
    """Validate walls and all possible overlaps inside the packing's own box."""
    if not squares:
        return False, "empty packing", math.inf
    all_corners = [point for square in squares for point in corners(square)]
    min_x = min(point[0] for point in all_corners)
    min_y = min(point[1] for point in all_corners)
    max_x = max(point[0] for point in all_corners)
    max_y = max(point[1] for point in all_corners)
    side = max(max_x - min_x, max_y - min_y)
    min_wall = math.inf
    for x, y in all_corners:
        x, y = x - min_x, y - min_y
        min_wall = min(min_wall, x, y, side - x, side - y)
    if min_wall < -gap:
        return False, f"wall violation {min_wall:.3e}", side
    min_pair = math.inf
    for i, j in _candidate_pairs(squares):
        sep = separating_gap(squares[i], squares[j])
        min_pair = min(min_pair, sep)
        if sep < -gap:
            return False, f"pair {i},{j} separation {sep:.3e}", side
    return True, f"ok; wall={min_wall:.3e}; pair={min_pair:.3e}", side

