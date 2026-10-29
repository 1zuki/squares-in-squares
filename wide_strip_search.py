"""Search diagonal-strip constructions wider than the baseline width cap."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path

from build_submission import best_strip, diagonal_strip, min_strip_side
from geometry import bounding_side, validate_packing
from topology_search import MAX_N, read_submission, write_submission

EPS = 1e-12
CONSTRUCTION_MARGIN = 3e-9
OFFSET_MARGIN = 1.5e-9


def maximum_geometric_width(n: int) -> int:
    """Largest strip width that can fit within ceil(sqrt(n)) by this family."""
    if not 1 <= n <= MAX_N:
        raise ValueError(f"n must be in 1..{MAX_N}")
    side_ceiling = math.ceil(math.sqrt(n))
    return max(0, math.floor(side_ceiling - math.sqrt(2.0) + 1e-12))


def candidate_widths(n: int, start_width: int = 9, max_width: int | None = None) -> range:
    if start_width < 1:
        raise ValueError("start_width must be positive")
    cap = maximum_geometric_width(n)
    if max_width is not None:
        if max_width < 1:
            raise ValueError("max_width must be positive")
        cap = min(cap, max_width)
    return range(start_width, cap + 1)


def candidate_for_width(n: int, width: int):
    """Build and independently check the N-square prefix of one strip family."""
    side_guess = min_strip_side(n, width, math.sqrt(n), math.ceil(math.sqrt(n)))
    if side_guess is None:
        return None, {"width": width, "built": False, "reason": "capacity below N"}

    side_probe = float(side_guess) + CONSTRUCTION_MARGIN
    count, lower_offset = best_strip(side_probe, width)
    if count < n:
        return None, {
            "width": width,
            "built": False,
            "reason": "capacity changed at construction margin",
            "declared_count": count,
        }

    squares = [
        (float(x), float(y), float(angle))
        for x, y, angle in diagonal_strip(
            side_probe, float(lower_offset) + OFFSET_MARGIN, width
        )[:n]
    ]
    if len(squares) != n:
        return None, {
            "width": width,
            "built": False,
            "reason": "construction emitted too few squares",
            "declared_count": count,
            "emitted_count": len(squares),
        }

    measured_side = bounding_side(squares)
    valid, message, checked_side = validate_packing(squares, gap=1e-12)
    if valid:
        return (squares, checked_side), {
            "width": width,
            "built": True,
            "valid": True,
            "declared_count": count,
            "measured_side": measured_side,
            "checked_side": checked_side,
        }
    return None, {
        "width": width,
        "built": True,
        "valid": False,
        "message": message,
        "measured_side": measured_side,
        "declared_count": count,
    }


def run(input_path: Path, output_path: Path, start_width: int, max_width: int | None) -> dict:
    if input_path.resolve() == output_path.resolve():
        raise ValueError("output must be a separate file from the input incumbent")
    for path in (output_path, output_path.with_suffix(output_path.suffix + ".sources.json"),
                 output_path.with_suffix(output_path.suffix + ".topology.json")):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite experiment artifact: {path}")

    layouts = read_submission(input_path)
    sources_path = input_path.with_suffix(input_path.suffix + ".sources.json")
    if sources_path.is_file():
        sources = json.loads(sources_path.read_text())
    else:
        sources = {str(n): f"incumbent<-{input_path}" for n in layouts}

    started = time.monotonic()
    records = {}
    wins = []
    checked_targets = 0
    for n in range(1, MAX_N + 1):
        valid, message, base_side = validate_packing(layouts[n], gap=1e-12)
        if not valid:
            raise ValueError(f"input n={n} failed exact geometry check: {message}")
        widths = candidate_widths(n, start_width, max_width)
        if not widths:
            continue

        checked_targets += 1
        best_side = base_side
        best = None
        best_width = None
        attempts = []
        for width in widths:
            candidate, record = candidate_for_width(n, width)
            attempts.append(record)
            if candidate is None:
                continue
            squares, checked_side = candidate
            if checked_side < best_side - EPS:
                best, best_side, best_width = squares, checked_side, width

        if best is not None:
            layouts[n] = best
            sources[str(n)] = f"wide_diagonal_strip(width={best_width})"
            win = {
                "n": n,
                "width": best_width,
                "input_side": base_side,
                "output_side": best_side,
                "score_gain": (base_side - best_side) / math.sqrt(n),
            }
            wins.append(win)
            records[str(n)] = {"attempts": attempts, "winner": win}

    metadata = {
        "experiment": "wide diagonal-strip construction search",
        "input": str(input_path),
        "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "start_width": start_width,
        "max_width": max_width,
        "geometric_width_cap": "floor(ceil(sqrt(N)) - sqrt(2))",
        "construction_margin": CONSTRUCTION_MARGIN,
        "offset_margin": OFFSET_MARGIN,
        "targets_with_wide_widths": checked_targets,
        "strict_improvement_count": len(wins),
        "estimated_total_score_gain": sum(item["score_gain"] for item in wins),
        "wins": wins,
        "records_for_winning_targets": records,
        "elapsed_seconds": time.monotonic() - started,
    }
    write_submission(output_path, layouts, sources, metadata)
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--start-width", type=int, default=9)
    parser.add_argument("--max-width", type=int)
    args = parser.parse_args()
    if args.max_width is not None and args.max_width < args.start_width:
        raise ValueError("max_width must be at least start_width")
    result = run(args.input, args.output, args.start_width, args.max_width)
    print(
        f"wrote {args.output}; tested_N={result['targets_with_wide_widths']} "
        f"strict_gains={result['strict_improvement_count']} "
        f"score_gain={result['estimated_total_score_gain']:.12g} "
        f"elapsed={result['elapsed_seconds']:.1f}s",
        flush=True,
    )


if __name__ == "__main__":
    main()
