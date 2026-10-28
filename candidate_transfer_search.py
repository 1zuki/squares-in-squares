"""Screen all retained public layouts as larger-N transfer donors.

The normal merger keeps the best exact-N layout and then applies deterministic
transfers to that incumbent.  This experiment asks a different question:
could a slightly worse layout at N+k contain a better N-square descendant?

Every generated candidate is a subset of a validated donor, so deletion never
creates an overlap.  The candidate is still independently validated after
normalization and the complete output is audited with ``audit_submission.py``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

from geometry import validate_packing
from transfer_beam import (
    MAX_N,
    beam_reduce,
    materialize,
    read_submission,
    write_submission,
)


def load_json_candidates(paths: list[Path], max_n: int) -> list[tuple[int, str, list[tuple[float, float, float]]]]:
    result = []
    seen: set[tuple[int, str]] = set()
    for path in paths:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            continue
        for key, record in data.items():
            try:
                n = int(str(key).rstrip("_"))
                raw = record["squares"]
                squares = [tuple(float(value) for value in square) for square in raw]
            except (KeyError, TypeError, ValueError):
                continue
            if not 1 <= n <= max_n or len(squares) != n:
                continue
            digest = hashlib.sha256(json.dumps(raw, separators=(",", ":")).encode()).hexdigest()
            key = (n, digest)
            if key in seen:
                continue
            seen.add(key)
            valid, _, _ = validate_packing(squares)
            if valid:
                result.append((n, str(path), squares))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("base", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("candidates", nargs="+", type=Path)
    parser.add_argument("--max-offset", type=int, default=12)
    parser.add_argument("--beam-width", type=int, default=8)
    parser.add_argument("--pool-limit", type=int, default=96)
    parser.add_argument("--max-donors-per-n", type=int, default=0, help="0 means all donors")
    parser.add_argument("--ns", help="optional comma-separated target sizes")
    args = parser.parse_args()
    if args.max_offset < 1 or args.beam_width < 1 or args.pool_limit < 8:
        raise ValueError("search limits must be positive")

    started = time.monotonic()
    layouts = read_submission(args.base)
    imported = load_json_candidates(args.candidates, MAX_N)
    donors_by_n: dict[int, list[tuple[str, list[tuple[float, float, float]]]]] = {}
    for n, source, squares in imported:
        donors_by_n.setdefault(n, []).append((source, squares))
    for n, squares in layouts.items():
        donors_by_n.setdefault(n, []).append((f"incumbent:{args.base}", squares))

    targets = sorted({int(value) for value in args.ns.split(",")}) if args.ns else list(range(1, MAX_N + 1))
    if any(n < 1 or n > MAX_N for n in targets):
        raise ValueError("target sizes must be in 1..1000")

    sources = {str(n): f"incumbent<-{args.base}" for n in range(1, MAX_N + 1)}
    metadata = {
        "method": "all-public-donors boundary-aware deletion beam",
        "base": str(args.base),
        "candidate_files": [str(path) for path in args.candidates],
        "max_offset": args.max_offset,
        "beam_width": args.beam_width,
        "pool_limit": args.pool_limit,
        "max_donors_per_n": args.max_donors_per_n,
        "targets": targets,
        "candidate_layout_count": len(imported),
        "results": {},
        "improvements": [],
    }

    for target in targets:
        incumbent = layouts[target]
        valid, message, incumbent_side = validate_packing(incumbent)
        if not valid:
            raise ValueError(f"base n={target} invalid: {message}")
        best_side = incumbent_side
        best_layout = incumbent
        best_source = sources[str(target)]
        candidates = []
        for donor_n in range(target + 1, min(MAX_N, target + args.max_offset) + 1):
            for source, donor in donors_by_n.get(donor_n, []):
                candidates.append((donor_n, source, donor))
        candidates.sort(key=lambda item: (item[0], item[1]))
        if args.max_donors_per_n:
            candidates = candidates[: args.max_donors_per_n]
        records = []
        for donor_n, source, donor in candidates:
            state, record = beam_reduce(donor, target, args.max_offset, args.beam_width, args.pool_limit)
            record.update({"donor_source": source, "donor_n": donor_n})
            if state is None:
                records.append(record)
                continue
            candidate = materialize(donor, state.removed)
            valid, candidate_message, candidate_side = validate_packing(candidate)
            record["audit"] = {"valid": valid, "message": candidate_message, "side": candidate_side}
            if valid and candidate_side < best_side - 1e-12:
                gain = best_side - candidate_side
                best_side = candidate_side
                best_layout = candidate
                best_source = f"all-donor-transfer:donor_n={donor_n}:source={source}:removed={list(state.removed)}"
                metadata["improvements"].append({
                    "n": target,
                    "donor_n": donor_n,
                    "donor_source": source,
                    "removed": list(state.removed),
                    "old_side": best_side + gain,
                    "new_side": candidate_side,
                    "gain": gain,
                })
            records.append(record)
        layouts[target] = best_layout
        sources[str(target)] = best_source
        metadata["results"][str(target)] = {
            "incumbent_side": incumbent_side,
            "selected_side": best_side,
            "selected_source": best_source,
            "donor_count": len(candidates),
            "records": records,
        }
        if target % 25 == 0 or target == targets[-1]:
            print(
                f"target={target} improved={sum(1 for item in metadata['improvements'] if item['n'] == target)} "
                f"total={len(metadata['improvements'])} elapsed={time.monotonic() - started:.1f}s",
                flush=True,
            )

    metadata["changed_puzzles"] = len({item["n"] for item in metadata["improvements"]})
    metadata["improvement_events"] = len(metadata["improvements"])
    metadata["elapsed_seconds"] = time.monotonic() - started
    write_submission(args.output, layouts, sources, metadata)
    print(
        f"wrote {args.output}; changed_puzzles={metadata['changed_puzzles']} "
        f"improvement_events={metadata['improvement_events']} elapsed={metadata['elapsed_seconds']:.1f}s"
    )


if __name__ == "__main__":
    main()
