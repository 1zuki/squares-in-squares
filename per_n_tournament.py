"""Run a bounded per-N tournament over the eight comparable search branches.

Each method starts from the same pinned input layout for each target N. Only a
strictly smaller, exactly valid candidate can replace that N's current winner.
The output is a complete submission plus provenance for every method/N trial.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from eight_ideas import parse_targets, run_method
from geometry import validate_packing
from topology_search import read_submission, write_submission

METHODS = (
    "fixed_container",
    "buffered_lns",
    "separator_flip",
    "strip_construction",
    "beam_repair",
    "island",
    "soft_replica",
    "fast_slp",
)
EPS = 1e-11
DEFAULT_INPUT = Path("data/public_external/kaggle_neighbour_transfer/submission_merged.csv")


def json_safe(value):
    """Convert NumPy scalars and containers into standard JSON values."""
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_methods(raw: str) -> list[str]:
    methods = [value.strip() for value in raw.split(",") if value.strip()]
    if not methods or len(methods) != len(set(methods)):
        raise ValueError("methods must be a non-empty comma-separated list without duplicates")
    unknown = sorted(set(methods) - set(METHODS))
    if unknown:
        raise ValueError(f"unknown methods: {', '.join(unknown)}")
    return methods


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ns", help="comma-separated target sizes; default is the shared 30-size screen")
    parser.add_argument("--methods", default=",".join(METHODS))
    parser.add_argument("--seed", type=int, default=20261029)
    parser.add_argument("--trials", type=int, default=2)
    parser.add_argument("--repair-steps", type=int, default=4)
    parser.add_argument("--beam-width", type=int, default=3)
    parser.add_argument("--beam-depth", type=int, default=2)
    parser.add_argument("--islands", type=int, default=3)
    parser.add_argument("--generations", type=int, default=2)
    parser.add_argument("--replicas", type=int, default=3)
    args = parser.parse_args()

    if min(args.trials, args.repair_steps, args.beam_width, args.beam_depth,
           args.islands, args.generations, args.replicas) < 1:
        raise ValueError("all search budgets must be positive")
    if args.input.resolve() == args.output.resolve():
        raise ValueError("output must not overwrite the pinned input")

    targets = parse_targets(args.ns)
    methods = parse_methods(args.methods)
    pinned = read_submission(args.input)
    best_layouts = {n: list(layout) for n, layout in pinned.items()}
    sources = {str(n): f"incumbent<-{args.input}" for n in range(1, 1001)}
    baseline_sides: dict[int, float] = {}
    best_sides: dict[int, float] = {}
    for n in targets:
        valid, message, side = validate_packing(pinned[n], gap=1e-12)
        if not valid:
            raise ValueError(f"pinned input n={n} failed validation: {message}")
        baseline_sides[n] = side
        best_sides[n] = side

    method_args = SimpleNamespace(
        trials=args.trials,
        repair_steps=args.repair_steps,
        beam_width=args.beam_width,
        beam_depth=args.beam_depth,
        islands=args.islands,
        generations=args.generations,
        replicas=args.replicas,
    )
    started = time.monotonic()
    results: dict[str, dict] = {}
    for n in targets:
        results[str(n)] = {}
        original = np.asarray(pinned[n], dtype=float)
        for method in methods:
            rng = np.random.default_rng(args.seed + n * 1009)
            method_started = time.monotonic()
            candidate, record = run_method(method, original.copy(), n, rng, method_args)
            elapsed = time.monotonic() - method_started
            valid, message, side = validate_packing(candidate.tolist(), gap=1e-12)
            strict_gain = valid and side < baseline_sides[n] - EPS
            took_slot = valid and side < best_sides[n] - EPS
            if took_slot:
                best_layouts[n] = candidate.tolist()
                best_sides[n] = side
                sources[str(n)] = f"tournament:{method}:seed={args.seed}:n={n}"
            results[str(n)][method] = {
                "valid": valid,
                "message": message,
                "baseline_side": baseline_sides[n],
                "candidate_side": side,
                "side_gain": baseline_sides[n] - side if valid else None,
                "score_gain": (baseline_sides[n] - side) / math.sqrt(n) if valid else None,
                "strict_gain_vs_baseline": strict_gain,
                "selected_for_n": took_slot,
                "elapsed_seconds": elapsed,
                "details": json_safe(record),
            }
            print(
                f"n={n} method={method} valid={valid} side={side:.12f} "
                f"gain={baseline_sides[n] - side:.3e} elapsed={elapsed:.1f}s",
                flush=True,
            )

    winner_counts = {method: 0 for method in methods}
    for n in targets:
        source = sources[str(n)]
        if source.startswith("tournament:"):
            winner_counts[source.split(":", 2)[1]] += 1
    metadata = {
        "experiment": "per-N algorithm tournament",
        "input": str(args.input),
        "input_sha256": file_sha256(args.input),
        "targets": targets,
        "methods": methods,
        "seed": args.seed,
        "budgets": {
            "trials": args.trials,
            "repair_steps": args.repair_steps,
            "beam_width": args.beam_width,
            "beam_depth": args.beam_depth,
            "islands": args.islands,
            "generations": args.generations,
            "replicas": args.replicas,
        },
        "selection_rule": "Keep the smallest exact-valid side per N; incumbent wins ties and invalid candidates.",
        "results": results,
        "winners_by_n": {
            str(n): {
                "source": sources[str(n)],
                "side": best_sides[n],
                "side_gain_vs_incumbent": baseline_sides[n] - best_sides[n],
            }
            for n in targets
        },
        "winner_counts": winner_counts,
        "strict_improvement_count": sum(
            best_sides[n] < baseline_sides[n] - EPS for n in targets
        ),
        "elapsed_seconds": time.monotonic() - started,
    }
    write_submission(args.output, best_layouts, sources, json_safe(metadata))
    print(
        f"wrote {args.output}; targets={len(targets)} "
        f"strict per-N gains={sum(winner_counts.values())} "
        f"elapsed={metadata['elapsed_seconds']:.1f}s",
        flush=True,
    )


if __name__ == "__main__":
    main()
