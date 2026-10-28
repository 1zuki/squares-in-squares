"""Bounded topology-changing search around a certified packing portfolio.

The driver compares three square-specific hypotheses from ``IDEAS.md``:

``group``
    Coherent translation/rotation of a contact-like center neighborhood.
``seam``
    A fault-line/shear move that shifts the two sides of a cut in opposite
    directions.
``destroy``
    Remove a compact group, reinsert it at deterministic alternative poses,
    then repair the whole layout with the existing oriented-square SLP.

The search is deliberately conservative.  It can explore temporarily
overlapping states, but only an independently validated and strictly smaller
serialized packing can replace the incumbent.  This is an experiment adapter,
not a claim of global optimality.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path

import numpy as np

from geometry import validate_packing
from slp_submission import linear_step, normalize, side

MAX_N = 1000
EPS = 1e-11


def read_submission(path: Path) -> dict[int, list[tuple[float, float, float]]]:
    groups: dict[int, list[tuple[int, tuple[float, float, float]]]] = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            groups.setdefault(int(row["n"]), []).append(
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


def write_submission(path: Path, layouts, sources, metadata) -> None:
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
    path.with_suffix(path.suffix + ".topology.json").write_text(json.dumps(metadata, indent=2) + "\n")


def valid_side(p: np.ndarray) -> tuple[bool, float, str]:
    q = normalize(p)
    valid, message, checked_side = validate_packing(q.tolist(), gap=1e-12)
    return valid, checked_side, message


def repair(p: np.ndarray, *, steps: int, seed: int) -> tuple[np.ndarray | None, dict]:
    """Repair a kicked state with SLP while tolerating invalid intermediates."""
    del seed  # Kept in the record/API so runs remain easy to reproduce.
    p = normalize(np.asarray(p, dtype=float))
    L = side(p)
    free_angles = np.ones(len(p), dtype=bool)
    best: np.ndarray | None = None
    best_side = math.inf
    accepted = 0
    for iteration in range(steps):
        rho = max(0.003, 0.22 * (0.93 ** iteration))
        step = linear_step(p, L, rho, free_angles)
        if step is None:
            # A fixed-L correction often succeeds after the shrinking step
            # becomes too constrained.
            step = linear_step(p, L, max(rho * 2.0, 0.01), free_angles, fixed_L=True)
        if step is None:
            continue
        q, Lq = step
        q = normalize(q)
        Lq = side(q)
        valid, checked_side, message = valid_side(q)
        if valid and checked_side < best_side - EPS:
            best, best_side = q.copy(), checked_side
        if valid:
            # A valid state is safe to continue from. Avoid expanding the
            # search envelope unless the prior state was also invalid.
            if Lq <= L + 1e-9:
                p, L = q, Lq
                accepted += 1
        else:
            # SLP itself only guarantees its local linearized constraints.
            # Keep the kicked state and progressively shrink rho; invalid
            # candidates are not chained unless a cheaper exact penalty is
            # available, so fail closed here.
            pass
    if best is None:
        return None, {"valid": False, "accepted_steps": accepted}
    return best, {
        "valid": True,
        "side": best_side,
        "accepted_steps": accepted,
    }


def nearby_group(p: np.ndarray, rng: np.random.Generator, size: int) -> np.ndarray:
    n = len(p)
    seed = int(rng.integers(0, n))
    distances = ((p[:, :2] - p[seed, :2]) ** 2).sum(axis=1)
    order = np.argsort(distances, kind="stable")
    group_size = min(n, max(2, size))
    return order[:group_size]


def group_kick(p: np.ndarray, rng: np.random.Generator, trial: int) -> np.ndarray:
    q = p.copy()
    group = nearby_group(q, rng, 2 + trial % 7)
    center = q[group, :2].mean(axis=0)
    direction = float(rng.uniform(0.0, 2.0 * math.pi))
    translation = np.array([math.cos(direction), math.sin(direction)]) * (0.08 + 0.06 * (trial % 5))
    alpha = float(((-1) ** trial) * (0.05 + 0.025 * (trial % 6)))
    c, s = math.cos(alpha), math.sin(alpha)
    for index in group:
        dx, dy = q[index, :2] - center
        q[index, 0] = center[0] + c * dx - s * dy + translation[0]
        q[index, 1] = center[1] + s * dx + c * dy + translation[1]
        q[index, 2] += alpha
    return q


def seam_kick(p: np.ndarray, rng: np.random.Generator, trial: int) -> np.ndarray:
    q = p.copy()
    axis = trial % 2
    values = q[:, axis]
    threshold = float(np.median(values) + rng.normal(0.0, 0.12))
    side_sign = np.where(values >= threshold, 1.0, -1.0)
    tangent = np.array([0.0, 1.0]) if axis == 0 else np.array([1.0, 0.0])
    normal = np.array([1.0, 0.0]) if axis == 0 else np.array([0.0, 1.0])
    shift = (0.07 + 0.025 * (trial % 7)) * side_sign[:, None] * tangent[None, :]
    q[:, :2] += shift
    q[:, :2] += (0.012 + 0.005 * (trial % 3)) * side_sign[:, None] * normal[None, :]
    q[:, 2] += side_sign * (0.02 + 0.01 * (trial % 4))
    return q


def local_penalty_with(square: np.ndarray, others: np.ndarray) -> float:
    if len(others) == 0:
        return 0.0
    score = 0.0
    for other in others:
        gap = separating_gap(square, other)
        if gap < 0.0:
            score += float((-gap) ** 2)
    return score


def destroy_reinsert(p: np.ndarray, rng: np.random.Generator, trial: int) -> np.ndarray:
    q = p.copy()
    group = nearby_group(q, rng, min(len(q), 2 + trial % 5))
    removed = q[group].copy()
    keep_mask = np.ones(len(q), dtype=bool)
    keep_mask[group] = False
    working = [row.copy() for row in q[keep_mask]]
    for local_index, original in enumerate(removed):
        angle = float(rng.uniform(0.0, 2.0 * math.pi))
        distance = 0.35 + 0.16 * ((trial + local_index) % 6)
        candidates = [original.copy()]
        for sign in (-1.0, 1.0):
            for dx, dy in ((1.0, 0.0), (0.0, 1.0), (math.cos(angle), math.sin(angle))):
                candidate = original.copy()
                candidate[0] += sign * distance * dx
                candidate[1] += sign * distance * dy
                candidate[2] += sign * (0.08 + 0.02 * ((trial + local_index) % 4))
                candidates.append(candidate)
        others = np.asarray(working, dtype=float)
        chosen = min(candidates, key=lambda candidate: local_penalty_with(candidate, others))
        working.append(chosen)
    return np.asarray(working, dtype=float)


def make_kick(method: str, p: np.ndarray, rng: np.random.Generator, trial: int) -> np.ndarray:
    if method == "group":
        return group_kick(p, rng, trial)
    if method == "seam":
        return seam_kick(p, rng, trial)
    if method == "destroy":
        return destroy_reinsert(p, rng, trial)
    raise ValueError(f"unknown method: {method}")


def run_target(original, n: int, method: str, trials: int, repair_steps: int, seed: int) -> tuple[list, dict]:
    base = np.asarray(original, dtype=float)
    valid, message, base_side = validate_packing(base.tolist())
    if not valid:
        raise ValueError(f"input n={n} invalid: {message}")
    best = normalize(base)
    best_side = base_side
    records = []
    for trial in range(trials):
        trial_seed = seed + 1009 * n + 7919 * trial
        rng = np.random.default_rng(trial_seed)
        kicked = make_kick(method, best, rng, trial)
        candidate, repair_record = repair(kicked, steps=repair_steps, seed=trial_seed)
        record = {"trial": trial, "seed": trial_seed, **repair_record}
        if candidate is not None:
            valid, candidate_message, candidate_side = validate_packing(candidate.tolist())
            record["audit_message"] = candidate_message
            record["audit_valid"] = valid
            record["candidate_side"] = candidate_side
            if valid and candidate_side < best_side - EPS:
                record["accepted"] = True
                record["gain"] = best_side - candidate_side
                best, best_side = candidate, candidate_side
            else:
                record["accepted"] = False
        else:
            record["accepted"] = False
        records.append(record)
    return best.tolist(), {"input_side": base_side, "output_side": best_side, "records": records}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--method", choices=("group", "seam", "destroy"), required=True)
    parser.add_argument("--ns", required=True, help="comma-separated target sizes")
    parser.add_argument("--trials", type=int, default=4)
    parser.add_argument("--repair-steps", type=int, default=24)
    parser.add_argument("--seed", type=int, default=20261027)
    args = parser.parse_args()
    if args.trials < 1 or args.repair_steps < 1:
        raise ValueError("trials and repair-steps must be positive")
    targets = sorted({int(value) for value in args.ns.split(",")})
    if any(n < 1 or n > MAX_N for n in targets):
        raise ValueError("target sizes must be in 1..1000")

    started = time.monotonic()
    layouts = read_submission(args.input)
    sources = {str(n): f"incumbent<-{args.input}" for n in range(1, MAX_N + 1)}
    metadata = {
        "method": args.method,
        "input": str(args.input),
        "targets": targets,
        "trials": args.trials,
        "repair_steps": args.repair_steps,
        "seed": args.seed,
        "results": {},
    }
    changed = []
    for n in targets:
        result, record = run_target(layouts[n], n, args.method, args.trials, args.repair_steps, args.seed)
        layouts[n] = result
        metadata["results"][str(n)] = record
        if record["output_side"] < record["input_side"] - EPS:
            sources[str(n)] = f"topology:{args.method}:seed={args.seed}:n={n}"
            changed.append({"n": n, **record})
        print(f"method={args.method} n={n} input={record['input_side']:.12f} output={record['output_side']:.12f}", flush=True)
    metadata["changed_puzzles"] = len(changed)
    metadata["accepted"] = changed
    metadata["elapsed_seconds"] = time.monotonic() - started
    write_submission(args.output, layouts, sources, metadata)
    print(f"wrote {args.output}; changed_puzzles={len(changed)} elapsed={metadata['elapsed_seconds']:.1f}s")


if __name__ == "__main__":
    main()
