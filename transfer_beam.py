"""Search larger layouts for better smaller-N descendants.

This is a deterministic, geometry-safe large-neighborhood transfer operator.
It keeps a bounded beam of subsets obtained by deleting boundary-sensitive
squares from a donor layout.  Any subset of a valid packing is valid, so the
search never needs to repair overlaps; the serialized candidate still passes
the independent audit before it can replace the incumbent.

The operator tests three ideas from ``IDEAS.md`` in a cheap form:

* N+K -> N transfer rather than only one-square prefix deletion;
* boundary-aware deletion rather than relying on source square order;
* beam retention of structurally different deletion histories.

It intentionally does not claim to solve the full packing problem.  It is a
reproducible candidate generator for complete-submission comparison.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from geometry import corners, validate_packing

MAX_N = 1000
EPS = 1e-12


@dataclass(frozen=True)
class State:
    removed: tuple[int, ...]
    side: float


@dataclass(frozen=True)
class Extremes:
    """Sorted extrema sufficient for deletion sets up to the beam budget."""

    xlo: tuple[tuple[float, int], ...]
    xhi: tuple[tuple[float, int], ...]
    ylo: tuple[tuple[float, int], ...]
    yhi: tuple[tuple[float, int], ...]


def read_submission(path: Path) -> dict[int, list[tuple[float, float, float]]]:
    groups: dict[int, list[tuple[int, tuple[float, float, float]]]] = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            n = int(row["n"])
            groups.setdefault(n, []).append(
                (int(row["square_id"]), (float(row["x"]), float(row["y"]), float(row["angle"])))
            )
    result = {}
    for n, rows in groups.items():
        rows.sort()
        if [square_id for square_id, _ in rows] != list(range(n)):
            raise ValueError(f"n={n}: square ids are not 0..{n - 1}")
        result[n] = [square for _, square in rows]
    if set(result) != set(range(1, MAX_N + 1)):
        raise ValueError("input must contain every n=1..1000")
    return result


def write_submission(
    path: Path,
    layouts: dict[int, list[tuple[float, float, float]]],
    sources: dict[str, str],
    metadata: dict,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("id", "n", "square_id", "x", "y", "angle"))
        row_id = 0
        for n in range(1, MAX_N + 1):
            for square_id, (x, y, angle) in enumerate(layouts[n]):
                writer.writerow((row_id, n, square_id, f"{x:.45g}", f"{y:.45g}", f"{angle:.45g}"))
                row_id += 1
    path.with_suffix(path.suffix + ".sources.json").write_text(json.dumps(sources, indent=2) + "\n")
    path.with_suffix(path.suffix + ".transfer.json").write_text(json.dumps(metadata, indent=2) + "\n")


def bounds(squares: list[tuple[float, float, float]]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    points = np.asarray([corners(square) for square in squares], dtype=float)
    return (
        points[:, :, 0].min(axis=1),
        points[:, :, 0].max(axis=1),
        points[:, :, 1].min(axis=1),
        points[:, :, 1].max(axis=1),
    )


def _remaining_extreme(values: tuple[tuple[float, int], ...], removed: set[int]) -> float:
    for value, index in values:
        if index not in removed:
            return value
    return math.inf


def make_extremes(
    xlo: np.ndarray, xhi: np.ndarray, ylo: np.ndarray, yhi: np.ndarray
) -> Extremes:
    # Keep a generous prefix.  A deletion branch removes at most max_offset
    # squares, so the first 32 extrema are enough for the default search and
    # still leave a safe fallback for larger user-selected offsets.
    keep = min(len(xlo), 128)
    return Extremes(
        xlo=tuple(sorted((float(value), int(index)) for index, value in enumerate(xlo))[:keep]),
        xhi=tuple(sorted(((float(value), int(index)) for index, value in enumerate(xhi)), reverse=True)[:keep]),
        ylo=tuple(sorted((float(value), int(index)) for index, value in enumerate(ylo))[:keep]),
        yhi=tuple(sorted(((float(value), int(index)) for index, value in enumerate(yhi)), reverse=True)[:keep]),
    )


def subset_side(extremes: Extremes, removed: tuple[int, ...]) -> float:
    removed_set = set(removed)
    x_min = _remaining_extreme(extremes.xlo, removed_set)
    x_max = _remaining_extreme(extremes.xhi, removed_set)
    y_min = _remaining_extreme(extremes.ylo, removed_set)
    y_max = _remaining_extreme(extremes.yhi, removed_set)
    if not math.isfinite(x_min + x_max + y_min + y_max):
        return math.inf
    return max(x_max - x_min, y_max - y_min)


def candidate_pool(
    xlo: np.ndarray,
    xhi: np.ndarray,
    ylo: np.ndarray,
    yhi: np.ndarray,
    limit: int,
) -> list[int]:
    """Return deterministic boundary/extreme candidates for deletion."""
    n = len(xlo)
    if n <= limit:
        return list(range(n))
    each = max(4, limit // 4)
    selected: set[int] = set()
    for values, reverse in ((xlo, False), (xhi, True), (ylo, False), (yhi, True)):
        order = np.argsort(values, kind="stable")
        if reverse:
            order = order[::-1]
        selected.update(int(value) for value in order[:each])
    # Include the largest normalized boundary scores to catch non-unique
    # extrema whose removal becomes useful after an earlier deletion.
    side = max(float(xhi.max() - xlo.min()), float(yhi.max() - ylo.min()))
    score = np.maximum.reduce(
        (
            (xhi - xlo.min()) / max(side, 1.0),
            (xhi.max() - xlo) / max(side, 1.0),
            (yhi - ylo.min()) / max(side, 1.0),
            (yhi.max() - ylo) / max(side, 1.0),
        )
    )
    order = np.argsort(-score, kind="stable")
    selected.update(int(value) for value in order[: max(0, limit - len(selected))])
    return sorted(selected)


def normalize(squares: list[tuple[float, float, float]]) -> list[tuple[float, float, float]]:
    points = np.asarray([corners(square) for square in squares], dtype=float)
    x0 = float(points[:, :, 0].min())
    y0 = float(points[:, :, 1].min())
    return [(x - x0, y - y0, angle) for x, y, angle in squares]


def materialize(
    squares: list[tuple[float, float, float]], removed: tuple[int, ...]
) -> list[tuple[float, float, float]]:
    removed_set = set(removed)
    return normalize([square for index, square in enumerate(squares) if index not in removed_set])


def beam_reduce(
    squares: list[tuple[float, float, float]],
    target: int,
    max_offset: int,
    beam_width: int,
    pool_limit: int,
) -> tuple[State | None, dict]:
    donor_n = len(squares)
    deletions = donor_n - target
    if deletions < 1 or deletions > max_offset:
        return None, {"status": "skipped", "reason": "offset outside budget"}
    xlo, xhi, ylo, yhi = bounds(squares)
    extremes = make_extremes(xlo, xhi, ylo, yhi)
    pool = candidate_pool(xlo, xhi, ylo, yhi, pool_limit)
    beam = [State(removed=(), side=subset_side(extremes, ())) ]
    states_seen = {()}
    expansions = 0
    for _ in range(deletions):
        expanded: list[State] = []
        for state in beam:
            removed_set = set(state.removed)
            for index in pool:
                if index in removed_set:
                    continue
                removed = tuple(sorted((*state.removed, index)))
                if removed in states_seen:
                    continue
                states_seen.add(removed)
                expanded.append(State(removed=removed, side=subset_side(extremes, removed)))
                expansions += 1
        if not expanded:
            return None, {"status": "failed", "reason": "empty beam", "expansions": expansions}
        # Keep the lowest-side states, but retain distinct first deletions so
        # that the beam does not collapse onto one boundary choice.
        expanded.sort(key=lambda state: (state.side, state.removed))
        retained: list[State] = []
        first_seen: set[int] = set()
        for state in expanded:
            first = state.removed[0]
            if first not in first_seen or len(retained) < beam_width:
                retained.append(state)
                first_seen.add(first)
            if len(retained) >= beam_width:
                break
        beam = retained
    best = min(beam, key=lambda state: (state.side, state.removed))
    return best, {
        "status": "complete",
        "donor_n": donor_n,
        "target_n": target,
        "deletions": deletions,
        "pool_size": len(pool),
        "beam_width": beam_width,
        "expansions": expansions,
        "removed": list(best.removed),
        "side": best.side,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--max-offset", type=int, default=8)
    parser.add_argument("--beam-width", type=int, default=6)
    parser.add_argument("--pool-limit", type=int, default=64)
    parser.add_argument("--ns", help="optional comma-separated target sizes")
    args = parser.parse_args()
    if args.max_offset < 1 or args.beam_width < 1 or args.pool_limit < 8:
        raise ValueError("search limits must be positive")

    start = time.monotonic()
    layouts = read_submission(args.input)
    targets = sorted({int(value) for value in args.ns.split(",")}) if args.ns else list(range(1, MAX_N + 1))
    if any(n < 1 or n > MAX_N for n in targets):
        raise ValueError("target sizes must be in 1..1000")

    sources = {str(n): f"incumbent<-{args.input}" for n in range(1, MAX_N + 1)}
    metadata = {
        "method": "boundary-aware N+K deletion beam",
        "input": str(args.input),
        "max_offset": args.max_offset,
        "beam_width": args.beam_width,
        "pool_limit": args.pool_limit,
        "targets": targets,
        "results": {},
    }
    improvements = []
    for target in targets:
        incumbent = layouts[target]
        incumbent_valid, message, incumbent_side = validate_packing(incumbent)
        if not incumbent_valid:
            raise ValueError(f"incumbent n={target} invalid: {message}")
        best_side = incumbent_side
        best_layout = incumbent
        best_record = {"status": "no improvement", "incumbent_side": incumbent_side}
        for offset in range(1, args.max_offset + 1):
            donor_n = target + offset
            if donor_n > MAX_N:
                break
            state, record = beam_reduce(layouts[donor_n], target, args.max_offset, args.beam_width, args.pool_limit)
            metadata["results"].setdefault(str(target), []).append(record)
            if state is None:
                continue
            candidate = materialize(layouts[donor_n], state.removed)
            valid, candidate_message, candidate_side = validate_packing(candidate)
            if not valid:
                record["audit"] = {"valid": False, "message": candidate_message}
                continue
            record["audit"] = {"valid": True, "message": candidate_message, "side": candidate_side}
            if candidate_side < best_side - EPS:
                gain = best_side - candidate_side
                best_side = candidate_side
                best_layout = candidate
                best_record = {
                    "status": "improved",
                    "donor_n": donor_n,
                    "offset": offset,
                    "removed": list(state.removed),
                    "incumbent_side": incumbent_side,
                    "output_side": candidate_side,
                    "gain": gain,
                }
        layouts[target] = best_layout
        if best_record["status"] == "improved":
            sources[str(target)] = f"transfer-beam:donor={best_record['donor_n']}:removed={best_record['removed']}"
            improvements.append({"n": target, **best_record})
        metadata["results"].setdefault(str(target), []).append({"selected": best_record})
        if target % 25 == 0 or target == targets[-1]:
            print(f"target={target} improvements={len(improvements)} elapsed={time.monotonic() - start:.1f}s", flush=True)

    metadata["improvements"] = improvements
    metadata["changed_puzzles"] = len(improvements)
    metadata["elapsed_seconds"] = time.monotonic() - start
    write_submission(args.output, layouts, sources, metadata)
    improvement_path = args.output.with_suffix(args.output.suffix + ".improvements.csv")
    with improvement_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["n", "donor_n", "offset", "incumbent_side", "output_side", "gain", "removed"])
        writer.writeheader()
        for row in improvements:
            writer.writerow({key: row.get(key) for key in writer.fieldnames})
    print(f"wrote {args.output}; changed_puzzles={len(improvements)} elapsed={metadata['elapsed_seconds']:.1f}s")


if __name__ == "__main__":
    main()
