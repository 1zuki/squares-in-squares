"""Shared fast local-search kernels for square-packing experiments."""

from __future__ import annotations

import math

import numpy as np

from geometry import half_extent, separating_gap
from slp_submission import linear_step, normalize, side, vertices


def broadphase_pairs(p: np.ndarray, *, radius: float = 2.2, cell_size: float | None = None):
    """Return center pairs within a safe radius using a spatial hash grid."""
    n = len(p)
    if n < 2:
        return []
    if cell_size is None:
        cell_size = radius
    bins: dict[tuple[int, int], list[int]] = {}
    for i, (x, y, _angle) in enumerate(p):
        key = (math.floor(float(x) / cell_size), math.floor(float(y) / cell_size))
        bins.setdefault(key, []).append(i)
    offsets = [
        (dx, dy)
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
    ]
    pairs = set()
    r2 = radius * radius
    for key, members in bins.items():
        for dx, dy in offsets:
            other = bins.get((key[0] + dx, key[1] + dy), ())
            for i in members:
                for j in other:
                    if i >= j:
                        continue
                    delta = p[i, :2] - p[j, :2]
                    if float(delta @ delta) <= r2:
                        pairs.add((i, j))
    return sorted(pairs)


def verify_broadphase(p: np.ndarray, *, cell_size: float = 2.2) -> dict:
    """Compare spatial-hash pairs to a brute-force radius graph."""
    radius = 2.2
    observed = set(broadphase_pairs(p, radius=radius, cell_size=cell_size))
    centers = p[:, :2]
    expected = set()
    for i in range(len(p)):
        for j in range(i + 1, len(p)):
            delta = centers[i] - centers[j]
            if float(delta @ delta) <= radius * radius:
                expected.add((i, j))
    missing = expected - observed
    return {"valid": not missing, "expected": len(expected), "observed": len(observed), "missing": sorted(missing)[:20]}


def placement_penalty(p: np.ndarray, *, container: float | None = None, target_angle: float | None = None) -> float:
    """SAT overlap plus wall penalty, optionally with an orientation prior."""
    p = np.asarray(p, dtype=float)
    if len(p) == 0:
        return math.inf
    if container is None:
        container = side(p)
    points, _ = vertices(p)
    penalty = 0.0
    for i, j in broadphase_pairs(p):
        gap = separating_gap(p[i], p[j])
        if gap < 0.0:
            penalty += gap * gap
    outside = np.maximum(-points, 0.0) + np.maximum(points - container, 0.0)
    penalty += float(np.sum(outside * outside))
    if target_angle is not None:
        delta = (p[:, 2] - target_angle + math.pi / 2) % math.pi - math.pi / 2
        # Weak temporary center-aware prior; callers taper it to zero.
        penalty += float(np.mean(delta * delta)) * 1e-3
    return penalty


def relax_fixed_l(
    initial: np.ndarray,
    container: float,
    *,
    steps: int = 8,
    rho: float = 0.04,
    free_angles: np.ndarray | None = None,
) -> tuple[np.ndarray, dict]:
    """Fast deterministic SLP feasibility repair at a fixed container side."""
    p = normalize(np.asarray(initial, dtype=float))
    if free_angles is None:
        free_angles = np.ones(len(p), dtype=bool)
    accepted = 0
    attempts = 0
    for iteration in range(steps):
        step_rho = max(rho * (0.72**iteration), 1e-4)
        step = linear_step(p, container, step_rho, free_angles, fixed_L=True)
        if step is None:
            continue
        attempts += 1
        q, _ = step
        q = normalize(q)
        if side(q) > container + 1e-9:
            continue
        before = placement_penalty(p, container=container)
        after = placement_penalty(q, container=container)
        if after <= before + 1e-14:
            p = q
            accepted += 1
    return p, {"accepted_steps": accepted, "lp_attempts": attempts, "penalty": placement_penalty(p, container=container)}


def contact_graph(p: np.ndarray, *, threshold: float = 0.06):
    pairs = []
    degree = np.zeros(len(p), dtype=int)
    gaps = {}
    for i, j in broadphase_pairs(p, radius=2.2):
        gap = separating_gap(p[i], p[j])
        gaps[(i, j)] = gap
        if gap <= threshold:
            pairs.append((i, j, gap))
            degree[i] += 1
            degree[j] += 1
    return pairs, degree, gaps


def contact_groups(p: np.ndarray, *, threshold: float = 0.06) -> list[list[int]]:
    pairs, _degree, _gaps = contact_graph(p, threshold=threshold)
    adjacency = [[] for _ in range(len(p))]
    for i, j, _ in pairs:
        adjacency[i].append(j)
        adjacency[j].append(i)
    seen = set()
    groups = []
    for start in range(len(p)):
        if start in seen or not adjacency[start]:
            continue
        stack = [start]
        seen.add(start)
        group = []
        while stack:
            node = stack.pop()
            group.append(node)
            for neighbor in adjacency[node]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        groups.append(sorted(group))
    return groups


def near_tied_separators(p: np.ndarray, *, tolerance: float = 0.025):
    """Find pairs whose leading SAT axes are nearly tied."""
    result = []
    for i, j in broadphase_pairs(p):
        # Candidate separations by each oriented edge normal.
        axes = []
        for owner in (i, j):
            theta = float(p[owner, 2])
            axes.extend(((math.cos(theta), math.sin(theta)), (-math.sin(theta), math.cos(theta))))
        all_vertices, _ = vertices(p[[i, j]])
        ca = np.asarray(all_vertices[0])
        cb = np.asarray(all_vertices[1])
        projections = []
        for axis in axes:
            a = ca @ np.asarray(axis)
            b = cb @ np.asarray(axis)
            projections.append(max(float(b.min() - a.max()), float(a.min() - b.max())))
        ordered = sorted(projections, reverse=True)
        if len(ordered) >= 2 and ordered[0] - ordered[1] <= tolerance:
            result.append((i, j, ordered[0], ordered[1]))
    return result

