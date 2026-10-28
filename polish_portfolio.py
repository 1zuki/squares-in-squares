"""Multi-start SLP from structurally different public layouts.

This isolates the value of start diversity: each candidate gets the same
bounded SLP budget, then only independently validated improvements over the
incumbent are assembled into a complete output.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from geometry import validate_packing
from slp_submission import polish_one
from topology_search import read_submission, write_submission


def load_seeds(paths: list[Path], targets: set[int], incumbent, *, seeds_per_n: int):
    seeds = defaultdict(list)
    seen = defaultdict(set)
    for n in sorted(targets):
        values = incumbent[n]
        digest = hashlib.sha256(np.asarray(values, dtype=np.float64).tobytes()).hexdigest()
        seen[n].add(digest)
        seeds[n].append(("incumbent", values))
    for path in paths:
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        for key, record in data.items():
            try:
                n = int(str(key).rstrip("_"))
                if n not in targets:
                    continue
                values = [tuple(float(value) for value in square) for square in record["squares"]]
                if len(values) != n:
                    continue
                valid, _, side = validate_packing(values)
                if not valid:
                    continue
                digest = hashlib.sha256(np.asarray(values, dtype=np.float64).tobytes()).hexdigest()
                if digest in seen[n]:
                    continue
                seen[n].add(digest)
                seeds[n].append((str(path), values))
            except (KeyError, TypeError, ValueError):
                continue
    for n in seeds:
        seeds[n].sort(key=lambda item: (validate_packing(item[1])[2], item[0]))
        # Keep candidate loading and final runs bounded, while retaining the
        # lowest-side structurally distinct donors gathered from every source.
        seeds[n] = seeds[n][:seeds_per_n]
    return seeds


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("base", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--candidates", nargs="+", type=Path, required=True)
    parser.add_argument("--ns", required=True)
    parser.add_argument("--seeds-per-n", type=int, default=6)
    parser.add_argument("--budget", type=float, default=4.0)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--rotate-axis", action="store_true")
    args = parser.parse_args()
    targets = sorted({int(value) for value in args.ns.split(",")})
    if args.seeds_per_n < 1 or args.budget <= 0 or args.workers < 1:
        raise ValueError("seeds-per-n, budget, and workers must be positive")

    started = time.monotonic()
    layouts = read_submission(args.base)
    seed_map = load_seeds(args.candidates, set(targets), layouts, seeds_per_n=args.seeds_per_n)
    jobs = []
    job_meta = []
    for n in targets:
        for seed_rank, (source, squares) in enumerate(seed_map.get(n, [])[: args.seeds_per_n]):
            jobs.append((n, np.asarray(squares, dtype=float), args.budget, args.rotate_axis))
            job_meta.append({"n": n, "rank": seed_rank, "source": source})
    results = []
    with Pool(args.workers) as pool:
        for meta, record in zip(job_meta, pool.imap(polish_one, jobs)):
            record.update(meta)
            results.append(record)

    sources = {str(n): f"incumbent<-{args.base}" for n in range(1, 1001)}
    improvements = []
    for n in targets:
        incumbent_valid, _, incumbent_side = validate_packing(layouts[n])
        if not incumbent_valid:
            raise ValueError(f"incumbent n={n} is invalid")
        best_side = incumbent_side
        best_layout = layouts[n]
        for record in results:
            if record["n"] != n or record.get("squares") is None:
                continue
            candidate = [tuple(float(value) for value in square) for square in record["squares"]]
            valid, message, side = validate_packing(candidate)
            record["final_audit"] = {"valid": valid, "message": message, "side": side}
            if valid and side < best_side - 1e-11:
                best_side = side
                best_layout = candidate
                improvements.append({
                    "n": n,
                    "source": record["source"],
                    "seed_rank": record["rank"],
                    "input_side": record["input_side"],
                    "output_side": side,
                    "incumbent_side": incumbent_side,
                    "gain": incumbent_side - side,
                })
        if best_side < incumbent_side - 1e-11:
            layouts[n] = best_layout
            sources[str(n)] = f"multi-start-slp<-{next(item['source'] for item in improvements[::-1] if item['n'] == n)}"

    metadata = {
        "method": "multi-start bounded oriented-square SLP",
        "base": str(args.base),
        "candidate_files": [str(path) for path in args.candidates],
        "targets": targets,
        "seeds_per_n": args.seeds_per_n,
        "budget_seconds_per_seed": args.budget,
        "workers": args.workers,
        "rotate_axis_aligned": args.rotate_axis,
        "attempted_seeds": len(jobs),
        "results": results,
        "improvements": improvements,
        "changed_puzzles": len({item["n"] for item in improvements}),
        "elapsed_seconds": time.monotonic() - started,
    }
    write_submission(args.output, layouts, sources, metadata)
    print(
        f"wrote {args.output}; attempted={len(jobs)} changed={metadata['changed_puzzles']} "
        f"elapsed={metadata['elapsed_seconds']:.1f}s"
    )


if __name__ == "__main__":
    main()
