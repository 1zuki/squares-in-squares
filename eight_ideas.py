"""Run eight bounded square-packing research branches.

The branches share the incumbent reader/writer and the exact independent
validator. They differ only in candidate generation and local repair:

1. fixed-container feasibility;
2. buffered large-neighborhood repair;
3. near-tied separator flips;
4. low-dimensional strip construction search;
5. multi-descendant beam repair;
6. island diversity and patch transplantation;
7. soft-to-rigid continuation plus replica-style temperatures;
8. accelerated broadphase multi-start SLP.

The default invocation is intentionally bounded and targets a curated set of
hard sizes. Each branch writes a complete 1,000-size CSV, retaining the
incumbent everywhere it did not produce an audited strict improvement.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path

import numpy as np

from build_submission import diagonal_strip, min_strip_side, strip_rows
from geometry import separating_gap, validate_packing
from search_kernels import (
    broadphase_pairs,
    contact_groups,
    near_tied_separators,
    placement_penalty,
    relax_fixed_l,
    verify_broadphase,
)
from slp_submission import linear_step, normalize, side, vertices
from topology_search import read_submission, write_submission

MAX_N = 1000
EPS = 1e-11


def parse_targets(raw: str | None) -> list[int]:
    if raw:
        targets = sorted({int(value) for value in raw.split(",")})
    else:
        targets = [5, 11, 17, 26, 37, 50, 65, 86, 103, 123, 131, 152, 180, 232, 268, 299, 303, 307, 416, 457, 500, 545, 598, 649, 699, 748, 802, 857, 919, 983]
    if any(n < 1 or n > MAX_N for n in targets):
        raise ValueError("targets must be in 1..1000")
    return targets


def load_layouts(path: Path):
    return read_submission(path)


def fixed_container(p: np.ndarray, rng: np.random.Generator, trials: int, repair_steps: int):
    base = normalize(p)
    base_side = side(base)
    best = base.copy()
    best_side = base_side
    records = []
    for trial in range(trials):
        shrink = 0.0025 * (1 + trial % 5)
        L = base_side - shrink
        candidate = base.copy()
        if trial:
            candidate[:, 0] += rng.normal(0, 0.02 + 0.01 * trial, len(candidate))
            candidate[:, 1] += rng.normal(0, 0.02 + 0.01 * trial, len(candidate))
            candidate[:, 2] += rng.normal(0, 0.015 + 0.005 * trial, len(candidate))
        repaired, repair_record = relax_fixed_l(candidate, L, steps=repair_steps, rho=0.06)
        valid, message, checked = validate_packing(repaired.tolist(), gap=1e-12)
        record = {"trial": trial, "container": L, **repair_record, "valid": valid, "message": message, "side": checked}
        if valid and checked < best_side - EPS:
            best, best_side = repaired, checked
            record["accepted"] = True
        else:
            record["accepted"] = False
        records.append(record)
    return best, {"input_side": base_side, "output_side": best_side, "records": records}


def buffered_lns(p: np.ndarray, rng: np.random.Generator, trials: int, repair_steps: int):
    base = normalize(p)
    base_side = side(base)
    best = base.copy()
    best_side = base_side
    records = []
    for trial in range(trials):
        center = int(rng.integers(0, len(base)))
        dist = ((base[:, :2] - base[center, :2]) ** 2).sum(axis=1)
        patch = np.argsort(dist, kind="stable")[: min(len(base), 3 + trial % 7)]
        dist_patch = np.argsort(dist, kind="stable")[: min(len(base), len(patch) + 8)]
        q = best.copy()
        angle = float(rng.uniform(-0.18, 0.18))
        c, s = math.cos(angle), math.sin(angle)
        pivot = q[patch, :2].mean(axis=0)
        for i in dist_patch:
            dx, dy = q[i, :2] - pivot
            weight = 1.0 if i in patch else 0.35
            q[i, 0] = pivot[0] + dx * (1 - weight * 0.06) - dy * (weight * s)
            q[i, 1] = pivot[1] + dx * (weight * s) + dy * (1 - weight * 0.06)
            if i in patch:
                q[i, 2] += angle
        q[:, 0] += rng.normal(0, 0.01, len(q))
        q[:, 1] += rng.normal(0, 0.01, len(q))
        repaired, repair_record = relax_fixed_l(q, best_side, steps=repair_steps, rho=0.04)
        valid, message, checked = validate_packing(repaired.tolist(), gap=1e-12)
        record = {"trial": trial, "patch_size": len(patch), "buffer_size": len(dist_patch), **repair_record, "valid": valid, "message": message, "side": checked}
        if valid and checked < best_side - EPS:
            best, best_side = repaired, checked
            record["accepted"] = True
        else:
            record["accepted"] = False
        records.append(record)
    return best, {"input_side": base_side, "output_side": best_side, "records": records}


def separator_flip(p: np.ndarray, rng: np.random.Generator, trials: int, repair_steps: int):
    base = normalize(p)
    base_side = side(base)
    best = base.copy()
    best_side = base_side
    tied = near_tied_separators(base, tolerance=0.04)
    records = []
    for trial in range(min(trials, max(1, len(tied)))):
        i, j, _first, _second = tied[trial]
        q = best.copy()
        sign = -1.0 if trial % 2 else 1.0
        q[i, 2] += sign * (0.04 + 0.01 * (trial % 4))
        q[j, 2] -= sign * (0.03 + 0.01 * (trial % 3))
        direction = rng.normal(size=2)
        direction /= max(np.linalg.norm(direction), 1e-12)
        q[i, :2] += direction * 0.04
        q[j, :2] -= direction * 0.04
        repaired, repair_record = relax_fixed_l(q, best_side, steps=repair_steps, rho=0.05)
        valid, message, checked = validate_packing(repaired.tolist(), gap=1e-12)
        record = {"trial": trial, "pair": [i, j], "tied_count": len(tied), **repair_record, "valid": valid, "message": message, "side": checked}
        if valid and checked < best_side - EPS:
            best, best_side = repaired, checked
            record["accepted"] = True
        else:
            record["accepted"] = False
        records.append(record)
    return best, {"input_side": base_side, "output_side": best_side, "tied_pairs": len(tied), "records": records}


def strip_construction(p: np.ndarray, n: int, trials: int, repair_steps: int):
    base = normalize(p)
    base_side = side(base)
    best = base.copy()
    best_side = base_side
    records = []
    lower = math.sqrt(n)
    upper = math.ceil(math.sqrt(n))
    for width in range(1, min(8, max(1, int(math.sqrt(n) // 2) + 1)) + 1):
        candidate_side = min_strip_side(n, width, lower, upper)
        if candidate_side is None:
            continue
        count = 0
        lower_offset = None
        for probe in np.linspace(-1.0, 1.0, max(3, trials)):
            side_probe = float(candidate_side) + 3e-9
            # build_submission's strip search already chooses the best lower
            # offset; perturbing the side is enough to test neighboring counts
            # without inventing a new construction family.
            del probe
            from build_submission import best_strip
            count, lower_offset = best_strip(side_probe, width)
            if count >= n:
                candidate = np.asarray([(float(x), float(y), float(a)) for x, y, a in diagonal_strip(side_probe, float(lower_offset), width)[:n]], dtype=float)
                if len(candidate) != n:
                    continue
                valid, message, checked = validate_packing(candidate.tolist(), gap=1e-12)
                records.append({"width": width, "declared_count": count, "valid": valid, "message": message, "side": checked})
                if valid and checked < best_side - EPS:
                    best, best_side = candidate, checked
                break
    # A construction can be valid but have a side slightly above the baseline;
    # it is still retained in metadata as a tested branch, not as a promotion.
    return best, {"input_side": base_side, "output_side": best_side, "records": records}


def beam_repair(p: np.ndarray, rng: np.random.Generator, width: int, depth: int, repair_steps: int):
    base = normalize(p)
    base_side = side(base)
    beam = [(base, base_side, "root")]
    records = []
    for level in range(depth):
        expanded = []
        for parent, parent_side, label in beam:
            for branch in range(width):
                q = parent.copy()
                center = int(rng.integers(0, len(q)))
                dist = ((q[:, :2] - q[center, :2]) ** 2).sum(axis=1)
                patch = np.argsort(dist, kind="stable")[: min(len(q), 2 + (branch % 6))]
                q[patch, 0] += rng.normal(0, 0.08, len(patch))
                q[patch, 1] += rng.normal(0, 0.08, len(patch))
                q[patch, 2] += rng.normal(0, 0.06, len(patch))
                repaired, repair_record = relax_fixed_l(q, parent_side, steps=repair_steps, rho=0.05)
                valid, message, checked = validate_packing(repaired.tolist(), gap=1e-12)
                if valid:
                    expanded.append((repaired, checked, f"{label}/b{branch}"))
                records.append({"level": level, "branch": branch, "parent": label, **repair_record, "valid": valid, "message": message, "side": checked})
        expanded.sort(key=lambda item: (item[1], item[2]))
        beam = expanded[:width]
        if not beam:
            break
    if not beam:
        return base, {"input_side": base_side, "output_side": base_side, "records": records}
    best, best_side, _ = min(beam, key=lambda item: (item[1], item[2]))
    return best, {"input_side": base_side, "output_side": best_side, "records": records, "beam_size": len(beam)}


def island_search(p: np.ndarray, rng: np.random.Generator, islands: int, generations: int, repair_steps: int):
    base = normalize(p)
    base_valid, base_message, base_side = validate_packing(base.tolist(), gap=1e-12)
    if not base_valid:
        raise ValueError(f"island search requires a valid seed: {base_message}")
    population = [(base.copy(), base_side, "incumbent")]
    records = []
    for island in range(max(0, islands - 1)):
        q = base.copy()
        q[:, :2] += rng.normal(0, 0.03 + 0.015 * island, q[:, :2].shape)
        q[:, 2] += rng.normal(0, 0.025 + 0.01 * island, len(q))
        repaired, repair_record = relax_fixed_l(q, base_side, steps=repair_steps, rho=0.04)
        valid, message, checked = validate_packing(repaired.tolist(), gap=1e-12)
        records.append({"stage": "initial", "island": island, **repair_record, "valid": valid, "message": message, "side": checked})
        if valid:
            population.append((repaired, checked, f"island-{island}"))
    for generation in range(generations):
        population.sort(key=lambda item: (item[1], item[2]))
        elites = population[: max(1, islands // 2)]
        next_pop = list(elites)
        for island in range(max(0, islands - len(next_pop))):
            parent, parent_side, label = elites[island % len(elites)]
            q = parent.copy()
            group = np.argsort(((q[:, :2] - q[:, :2].mean(axis=0)) ** 2).sum(axis=1), kind="stable")[: min(len(q), 4 + generation % 8)]
            q[group, :2] += rng.normal(0, 0.06, (len(group), 2))
            q[group, 2] += rng.normal(0, 0.05, len(group))
            repaired, repair_record = relax_fixed_l(q, parent_side, steps=repair_steps, rho=0.04)
            valid, message, checked = validate_packing(repaired.tolist(), gap=1e-12)
            if valid:
                next_pop.append((repaired, checked, f"{label}/g{generation}/i{island}"))
            records.append({"generation": generation, "parent": label, **repair_record, "valid": valid, "message": message, "side": checked})
        population = next_pop
    best, best_side, _ = min(population, key=lambda item: (item[1], item[2]))
    returned_valid, returned_message, returned_side = validate_packing(best.tolist(), gap=1e-12)
    if not returned_valid:
        best, returned_side = base.copy(), base_side
        returned_valid, returned_message, _ = validate_packing(best.tolist(), gap=1e-12)
    return best, {
        "input_side": base_side,
        "output_side": returned_side,
        "records": records,
        "population": len(population),
        "returned_valid": returned_valid,
        "returned_message": returned_message,
    }


def soft_replica(p: np.ndarray, rng: np.random.Generator, replicas: int, generations: int, repair_steps: int):
    base = normalize(p)
    base_valid, base_message, base_side = validate_packing(base.tolist(), gap=1e-12)
    if not base_valid:
        raise ValueError(f"soft replica search requires a valid seed: {base_message}")
    best = base.copy()
    best_side = base_side
    # Every replica begins at a certified state; infeasible proposals never
    # replace a replica state or become eligible for the returned candidate.
    states = [(base.copy(), base_side + 0.03 * replica) for replica in range(replicas)]
    records = []
    for generation in range(generations):
        temperature = 1.0 - generation / max(1, generations)
        for replica, (q, container) in enumerate(states):
            prior = (0.12 * temperature) if replica == 0 else (0.02 * temperature)
            target = (replica % 2) * math.pi / 4
            q = q.copy()
            q[:, 2] += rng.normal(0, 0.03 * (temperature + 0.1), len(q))
            repaired, repair_record = relax_fixed_l(q, container, steps=repair_steps, rho=0.05)
            value = placement_penalty(repaired, container=container, target_angle=target) + prior * placement_penalty(repaired, container=container)
            valid, message, checked = validate_packing(repaired.tolist(), gap=1e-12)
            state_updated = False
            best_updated = False
            if valid:
                states[replica] = (repaired, max(base_side, checked))
                state_updated = True
                if checked < best_side - EPS:
                    best, best_side = repaired.copy(), checked
                    best_updated = True
            records.append({"generation": generation, "replica": replica, "temperature": temperature, "value": value, **repair_record, "valid": valid, "message": message, "side": checked, "state_updated": state_updated, "best_updated": best_updated})
        if len(states) >= 2 and generation % 2 == 1:
            states[0], states[1] = states[1], states[0]
    returned_valid, returned_message, returned_side = validate_packing(best.tolist(), gap=1e-12)
    if not returned_valid:
        best, returned_side = base.copy(), base_side
        returned_valid, returned_message, _ = validate_packing(best.tolist(), gap=1e-12)
    return best, {
        "input_side": base_side,
        "output_side": returned_side,
        "records": records,
        "replicas": replicas,
        "returned_valid": returned_valid,
        "returned_message": returned_message,
    }


def fast_slp(p: np.ndarray, trials: int, repair_steps: int):
    base = normalize(p)
    base_side = side(base)
    best = base.copy()
    best_side = base_side
    records = []
    pair_provider = lambda q, radius: broadphase_pairs(q, radius=radius)
    for trial in range(trials):
        q = base.copy()
        rng = np.random.default_rng(100003 + len(base) * 17 + trial)
        q[:, :2] += rng.normal(0, 0.02 + 0.01 * trial, q[:, :2].shape)
        q[:, 2] += rng.normal(0, 0.02 + 0.005 * trial, len(q))
        L = base_side
        accepted = 0
        for step_index in range(repair_steps):
            rho = max(0.004, 0.05 * (0.75**step_index))
            step = linear_step(q, L, rho, np.ones(len(q), dtype=bool), pair_provider=pair_provider)
            if step is None:
                continue
            candidate, candidate_L = step
            candidate = normalize(candidate)
            valid, message, checked = validate_packing(candidate.tolist(), gap=1e-12)
            if valid and checked < best_side - EPS:
                best, best_side = candidate.copy(), checked
                accepted += 1
            if valid and checked <= L + 1e-9:
                q, L = candidate, checked
        records.append({"trial": trial, "accepted": accepted, "valid": validate_packing(q.tolist())[0], "side": side(q)})
    return best, {"input_side": base_side, "output_side": best_side, "records": records, "broadphase": verify_broadphase(base)}


def run_method(method: str, p: np.ndarray, n: int, rng: np.random.Generator, args):
    if method == "fixed_container":
        return fixed_container(p, rng, args.trials, args.repair_steps)
    if method == "buffered_lns":
        return buffered_lns(p, rng, args.trials, args.repair_steps)
    if method == "separator_flip":
        return separator_flip(p, rng, args.trials, args.repair_steps)
    if method == "strip_construction":
        return strip_construction(p, n, args.trials, args.repair_steps)
    if method == "beam_repair":
        return beam_repair(p, rng, args.beam_width, args.beam_depth, args.repair_steps)
    if method == "island":
        return island_search(p, rng, args.islands, args.generations, args.repair_steps)
    if method == "soft_replica":
        return soft_replica(p, rng, args.replicas, args.generations, args.repair_steps)
    if method == "fast_slp":
        return fast_slp(p, args.trials, args.repair_steps)
    raise ValueError(method)


def json_args(args):
    """Serialize CLI metadata without leaking non-JSON Path/numpy objects."""
    result = {}
    for key, value in vars(args).items():
        if isinstance(value, Path):
            result[key] = str(value)
        elif isinstance(value, (str, int, float, bool)) or value is None:
            result[key] = value
        else:
            result[key] = str(value)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("method", choices=("fixed_container", "buffered_lns", "separator_flip", "strip_construction", "beam_repair", "island", "soft_replica", "fast_slp"))
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--ns")
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--repair-steps", type=int, default=5)
    parser.add_argument("--beam-width", type=int, default=3)
    parser.add_argument("--beam-depth", type=int, default=2)
    parser.add_argument("--islands", type=int, default=3)
    parser.add_argument("--generations", type=int, default=2)
    parser.add_argument("--replicas", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20261027)
    args = parser.parse_args()
    if min(args.trials, args.repair_steps, args.beam_width, args.beam_depth, args.islands, args.generations, args.replicas) < 1:
        raise ValueError("all budgets must be positive")
    targets = parse_targets(args.ns)
    started = time.monotonic()
    layouts = load_layouts(args.input)
    sources = {str(n): f"incumbent<-{args.input}" for n in range(1, MAX_N + 1)}
    metadata = {"method": args.method, "input": str(args.input), "targets": targets, "args": json_args(args), "results": {}, "accepted": []}
    for n in targets:
        original = np.asarray(layouts[n], dtype=float)
        rng = np.random.default_rng(args.seed + n * 1009)
        candidate, record = run_method(args.method, original, n, rng, args)
        valid, message, checked = validate_packing(candidate.tolist(), gap=1e-12)
        record["final_valid"] = valid
        record["final_message"] = message
        record["final_side"] = checked
        metadata["results"][str(n)] = record
        if valid and checked < record["input_side"] - EPS:
            layouts[n] = candidate.tolist()
            sources[str(n)] = f"eight-ideas:{args.method}:seed={args.seed}:n={n}"
            metadata["accepted"].append({"n": n, "old_side": record["input_side"], "new_side": checked, "gain": record["input_side"] - checked})
        print(f"method={args.method} n={n} in={record['input_side']:.12f} out={checked:.12f} valid={valid}", flush=True)
    metadata["changed_puzzles"] = len(metadata["accepted"])
    metadata["elapsed_seconds"] = time.monotonic() - started
    write_submission(args.output, layouts, sources, metadata)
    print(f"wrote {args.output}; changed={metadata['changed_puzzles']} elapsed={metadata['elapsed_seconds']:.1f}s")


if __name__ == "__main__":
    main()
