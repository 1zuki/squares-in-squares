"""Bounded sequential-linear-programming polish for selected submissions.

This is an experiment adapter, not the competition verifier.  It keeps the
independent audit in ``audit_submission.py`` as the promotion gate.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix

from geometry import corners, validate_packing

CORNER_OFFSETS = np.array(
    [[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5], [-0.5, 0.5]], dtype=float
)
NEAR = 0.35
RESTORE = 3
MAX_N = 1000


def read_submission(path: Path):
    groups = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            groups.setdefault(int(row["n"]), []).append(
                (int(row["square_id"]), [float(row["x"]), float(row["y"]), float(row["angle"])])
            )
    out = {}
    for n, rows in groups.items():
        rows.sort()
        out[n] = np.asarray([square for _, square in rows], dtype=float)
    return out


def normalize(p):
    p = np.asarray(p, dtype=float).copy()
    cs = np.asarray([corners(square) for square in p])
    p[:, 0] -= cs[:, :, 0].min()
    p[:, 1] -= cs[:, :, 1].min()
    return p


def side(p):
    cs = np.asarray([corners(square) for square in p])
    return float(max(np.ptp(cs[:, :, 0]), np.ptp(cs[:, :, 1])))


def vertices(p):
    c, s = np.cos(p[:, 2]), np.sin(p[:, 2])
    u, v = CORNER_OFFSETS[:, 0], CORNER_OFFSETS[:, 1]
    x = p[:, None, 0] + c[:, None] * u - s[:, None] * v
    y = p[:, None, 1] + s[:, None] * u + c[:, None] * v
    dx = -s[:, None] * u - c[:, None] * v
    dy = c[:, None] * u - s[:, None] * v
    return np.stack((x, y), axis=-1), np.stack((dx, dy), axis=-1)


def near_pairs(p, radius):
    d = p[:, None, :2] - p[None, :, :2]
    i, j = np.nonzero(np.triu((d * d).sum(axis=-1) < radius * radius, 1))
    return list(zip(i.tolist(), j.tolist()))


def broadphase_pairs(p, radius=2.2, *, cell_size=None):
    """Return center pairs within radius using a spatial hash grid."""
    n = len(p)
    if n < 2:
        return []
    if cell_size is None:
        cell_size = radius
    bins = {}
    for i, (x, y, _angle) in enumerate(p):
        key = (math.floor(float(x) / cell_size), math.floor(float(y) / cell_size))
        bins.setdefault(key, []).append(i)
    pairs = set()
    r2 = radius * radius
    reach = math.ceil(radius / cell_size)
    offsets = [(dx, dy) for dx in range(-reach, reach + 1) for dy in range(-reach, reach + 1)]
    for key, members in bins.items():
        for dx, dy in offsets:
            other = bins.get((key[0] + dx, key[1] + dy), ())
            for i in members:
                for j in other:
                    if i >= j:
                        continue
                    delta = p[i, :2] - p[j, :2]
                    if float(delta @ delta) < r2:
                        pairs.add((i, j))
    return sorted(pairs)


BROADPHASE_CROSSOVER_N = 800


def default_pair_provider(n):
    """Use vectorized dense pairs for small layouts and hashing for large ones."""
    return broadphase_pairs if n >= BROADPHASE_CROSSOVER_N else near_pairs


def pair_separator(p, i, j, verts):
    best = None
    for owner, other in ((i, j), (j, i)):
        theta = p[owner, 2]
        for face in range(4):
            angle = theta + face * math.pi / 2.0
            axis = np.array((math.cos(angle), math.sin(angle)))
            owner_support = float(axis @ p[owner, :2] + 0.5)
            gap = float(np.min(verts[other] @ axis) - owner_support)
            if best is None or gap > best[0]:
                best = (gap, owner, other, axis, angle)
    return best


def linear_step(p, L, rho, free_angles, fixed_L=False, pair_provider=None):
    n = len(p)
    verts, dverts = vertices(p)
    rows, cols, values, rhs = [], [], [], []
    row = 0

    def add(coefficients, bound):
        nonlocal row
        for col, value in coefficients:
            rows.append(row); cols.append(col); values.append(value)
        rhs.append(bound)
        row += 1

    # Active wall constraints: corner coordinates remain in [0, L].
    for i in range(n):
        for k in range(4):
            for axis in range(2):
                value = verts[i, k, axis]
                derivative = dverts[i, k, axis]
                if value < NEAR + rho:
                    add([(3 * i + axis, -1.0), (3 * i + 2, -derivative)], value)
                if value > L - NEAR - rho:
                    add([(3 * i + axis, 1.0), (3 * i + 2, derivative), (3 * n, -1.0)], L - value)

    # Keep every nearby pair separated by its currently best SAT face.
    radius = math.sqrt(2.0) + 0.2 + 2.0 * rho
    provider = pair_provider if pair_provider is not None else default_pair_provider(n)
    pairs = provider(p, radius)
    for i, j in pairs:
        gap, owner, other, axis, angle = pair_separator(p, i, j, verts)
        if gap > NEAR + 3.0 * rho:
            continue
        d_axis = np.array((-math.sin(angle), math.cos(angle)))
        for k in range(4):
            rel = verts[other, k] - p[owner, :2]
            value = float(axis @ rel - 0.5)
            d_other = dverts[other, k]
            coefficients = [
                (3 * other, -axis[0]), (3 * other + 1, -axis[1]),
                (3 * owner, axis[0]), (3 * owner + 1, axis[1]),
                (3 * owner + 2, -float(d_axis @ rel)),
                (3 * other + 2, -float(axis @ d_other)),
            ]
            if value < NEAR + 3.0 * rho:
                add(coefficients, value)

    nv = 3 * n + 1
    if not rows:
        return None
    A = csr_matrix((values, (rows, cols)), shape=(row, nv))
    objective = np.zeros(nv)
    objective[-1] = 1.0
    bounds = []
    for i in range(n):
        angle_limit = rho if free_angles[i] else 0.0
        bounds.extend([(-rho, rho), (-rho, rho), (-angle_limit, angle_limit)])
    bounds.append((0.0, 0.0) if fixed_L else (-rho, rho))
    result = linprog(objective, A_ub=A, b_ub=np.asarray(rhs), bounds=bounds, method="highs-ipm")
    if not result.success:
        return None
    delta = result.x
    q = p.copy()
    q[:, 0] += delta[0 : 3 * n : 3]
    q[:, 1] += delta[1 : 3 * n : 3]
    q[:, 2] += delta[2 : 3 * n : 3]
    return q, float(L + delta[-1])


def polish_one(job):
    n, original, budget, rotate_axis = job
    start = time.monotonic()
    p = normalize(original)
    original_side = side(p)
    L = original_side
    free_angles = np.ones(n, dtype=bool) if rotate_axis else np.abs(np.sin(p[:, 2])) > 1e-9
    rho = 0.05
    best = p.copy()
    best_side = original_side
    while time.monotonic() - start < budget and rho > 1e-7:
        step = linear_step(p, L, rho, free_angles)
        if step is None:
            rho *= 0.35
            continue
        q, Lq = step
        # Correct curvature-induced violations at fixed side before accepting.
        valid = False
        for _ in range(RESTORE + 1):
            if validate_packing(q.tolist(), gap=1e-10)[0]:
                valid = True
                break
            correction = linear_step(q, max(Lq, side(q)), max(rho / 10.0, 1e-8), free_angles, fixed_L=True)
            if correction is None:
                break
            q, _ = correction
        if valid:
            q = normalize(q)
            Lq = side(q)
            if Lq < best_side - 1e-12:
                p, L, best, best_side = q, Lq, q.copy(), Lq
                rho = min(rho * 1.5, 0.1)
                continue
        rho *= 0.35
    valid, message, checked_side = validate_packing(best.tolist(), gap=1e-12)
    if not valid or checked_side >= original_side - 1e-10:
        return {"n": n, "input_side": original_side, "output_side": original_side, "squares": None, "message": message}
    return {"n": n, "input_side": original_side, "output_side": checked_side, "squares": best.tolist(), "message": message}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--ns", required=True, help="comma-separated sizes")
    parser.add_argument("--budget", type=float, default=20.0)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--rotate-axis", action="store_true")
    args = parser.parse_args()
    data = read_submission(args.input)
    ns = sorted({int(value) for value in args.ns.split(",")})
    jobs = [(n, data[n], args.budget, args.rotate_axis) for n in ns]
    result = {
        "method": "bounded SLP with oriented-square SAT face linearization",
        "input": str(args.input),
        "budget_seconds_per_n": args.budget,
        "rotate_axis_aligned": args.rotate_axis,
        "results": {},
    }
    with Pool(args.workers) as pool:
        for record in pool.imap_unordered(polish_one, jobs):
            n = str(record.pop("n"))
            if record["squares"] is not None:
                result["results"][n] = record
            else:
                record.pop("squares", None)
                result["results"][n] = record
            print(f"n={n} input={result['results'][n]['input_side']:.12f} output={result['results'][n]['output_side']:.12f}", flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    improved = sum("squares" in item for item in result["results"].values())
    print(f"wrote {args.output}; improved={improved}/{len(ns)}")


if __name__ == "__main__":
    main()
