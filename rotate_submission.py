"""Search rigid rotations of complete packings and keep the best envelope.

The operation preserves every pairwise distance and relative orientation.  It
only changes the orientation of the whole packing relative to the submission's
axis-aligned enclosing square.  A coarse deterministic angle grid followed by
a local refinement is used so the experiment is reproducible and cheap to
audit.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

from geometry import corners, validate_packing

MAX_N = 1000
TURN = math.pi / 2.0
STRETCH = 1.0 + 1e-11


def read_submission(path: Path):
    groups: dict[int, list[tuple[int, tuple[float, float, float]]]] = defaultdict(list)
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            groups[int(row["n"])].append(
                (
                    int(row["square_id"]),
                    (float(row["x"]), float(row["y"]), float(row["angle"])),
                )
            )
    result = {}
    for n, rows in groups.items():
        rows.sort()
        result[n] = [square for _, square in rows]
    if set(result) != set(range(1, MAX_N + 1)):
        raise ValueError("input must contain every n=1..1000")
    if any(len(result[n]) != n for n in result):
        raise ValueError("input has an incorrect square count")
    return result


def rotated_square(square, alpha: float):
    x, y, angle = square
    c, s = math.cos(alpha), math.sin(alpha)
    return (c * x - s * y, s * x + c * y, angle + alpha)


def rotated_side(points: np.ndarray, alpha: float) -> float:
    c, s = math.cos(alpha), math.sin(alpha)
    x = points[:, 0] * c - points[:, 1] * s
    y = points[:, 0] * s + points[:, 1] * c
    return float(max(np.ptp(x), np.ptp(y)))


def best_rotation(squares, coarse: int, refine: int):
    points = np.asarray([point for square in squares for point in corners(square)], dtype=float)
    base = rotated_side(points, 0.0)
    coarse_angles = np.arange(coarse, dtype=float) * TURN / coarse
    coarse_sides = np.asarray([rotated_side(points, float(alpha)) for alpha in coarse_angles])
    best_index = int(np.argmin(coarse_sides))
    best_alpha = float(coarse_angles[best_index])
    best_side = float(coarse_sides[best_index])

    step = TURN / coarse
    fine_angles = (best_alpha + np.linspace(-step, step, refine)) % TURN
    fine_sides = np.asarray([rotated_side(points, float(alpha)) for alpha in fine_angles])
    fine_index = int(np.argmin(fine_sides))
    if float(fine_sides[fine_index]) < best_side:
        best_alpha = float(fine_angles[fine_index])
        best_side = float(fine_sides[fine_index])

    if best_side >= base - 1e-12:
        return [tuple(square) for square in squares], 0.0, base

    rotated = [rotated_square(square, best_alpha) for square in squares]
    # Stretch the center configuration by a tiny reproducible amount.  This
    # leaves a small numerical clearance margin without changing the search
    # decision or materially affecting the score.
    cx = sum(square[0] for square in rotated) / len(rotated)
    cy = sum(square[1] for square in rotated) / len(rotated)
    rotated = [
        (cx + (x - cx) * STRETCH, cy + (y - cy) * STRETCH, angle)
        for x, y, angle in rotated
    ]
    return rotated, best_alpha, best_side


def write_submission(path: Path, best, sources, metadata):
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("id", "n", "square_id", "x", "y", "angle"))
        row_id = 0
        for n in range(1, MAX_N + 1):
            for square_id, (x, y, angle) in enumerate(best[n]):
                writer.writerow((row_id, n, square_id, f"{x:.45g}", f"{y:.45g}", f"{angle:.45g}"))
                row_id += 1
    path.with_suffix(path.suffix + ".sources.json").write_text(json.dumps(sources, indent=2) + "\n")
    path.with_suffix(path.suffix + ".rotation.json").write_text(json.dumps(metadata, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--coarse", type=int, default=360)
    parser.add_argument("--refine", type=int, default=41)
    args = parser.parse_args()
    if args.coarse < 4 or args.refine < 3:
        raise ValueError("coarse and refine grids are too small")

    source = read_submission(args.input)
    best = {}
    sources = {}
    metadata = {"input": str(args.input), "coarse": args.coarse, "refine": args.refine, "stretch": STRETCH}
    changed = 0
    for n in range(1, MAX_N + 1):
        original = source[n]
        valid, message, original_side = validate_packing(original)
        if not valid:
            raise ValueError(f"input n={n} invalid: {message}")
        candidate, alpha, searched_side = best_rotation(original, args.coarse, args.refine)
        candidate_valid, candidate_message, candidate_side = validate_packing(candidate)
        if not candidate_valid:
            candidate = [tuple(square) for square in original]
            alpha = 0.0
            candidate_side = original_side
            candidate_message = "fallback to valid input"
        if candidate_side < original_side - 1e-12:
            changed += 1
            sources[str(n)] = f"rigid_rotation(alpha={alpha:.17g})<-{args.input}"
        else:
            sources[str(n)] = f"unchanged<-{args.input}"
            candidate = [tuple(square) for square in original]
            candidate_side = original_side
        best[n] = candidate
        metadata[str(n)] = {
            "alpha": alpha,
            "input_side": original_side,
            "searched_side": searched_side,
            "output_side": candidate_side,
            "valid_message": candidate_message,
        }
        if n % 50 == 0:
            print(f"rotated n={n} changed={changed}", flush=True)
    metadata["changed_puzzles"] = changed
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_submission(args.output, best, sources, metadata)
    print(f"wrote {args.output}; changed_puzzles={changed}")


if __name__ == "__main__":
    main()
