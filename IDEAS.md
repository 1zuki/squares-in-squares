# Squares-in-Square: Ideas and Findings

This document consolidates the ideas, observations, and research directions in the project-root notes `a.md`, `b.md`, `c.md`, and `d.md`. Repeated proposals are combined; distinct methods and caveats are retained. It is a research/engineering backlog, not a claim that the methods have been implemented or benchmarked in this repository.

## Executive summary

The competition is primarily a geometric search and optimization problem, not a conventional model-training task. For each size `N`, place `N` congruent unit squares—each with free translation and rotation—in the smallest enclosing square. Most instances do not have known proven optima, and a single general-purpose optimizer is unlikely to be best across all sizes.

The central working hypothesis is a hybrid:

> Preserve strong layouts, deliberately change their structure/contact topology, repair or restore feasibility, then apply a strong continuous local optimizer and independently certify the serialized result.

The most immediately actionable opportunity in the source notes is to polish existing solutions with fixed-angle LP and free-angle sequential linear programming (SLP). Transfer between nearby sizes is another high-value, reusable source of seeds. More expensive search should focus on moves that change which squares touch—not merely on more random starts or a different annealing schedule.

Three complementary tracks should share one layout archive, evaluator, and independent verifier:

1. **Precision and transfer:** select whole layouts, refine them, and propagate useful geometry across `N`.
2. **Arrangement exploration:** use annealing, basin hopping, patch rebuilding, and contact/fault-line moves to find different basins.
3. **Construction research:** search parameterized strips, blocks, frames, subdivisions, and other reusable geometric families.

Every track should end in the same refinement and certification path. Judge results by certified score gain per unit of total compute, including discovery, repair, and verification.

## Problem and score implications

The source notes report the competition metric as

\[
S=\sum_{n=1}^{1000}\left(\frac{L_n}{\sqrt n}-1\right),
\]

where `L_n` is the larger span of all square corners for the packing at size `n`. Invalid or missing instances receive a grid-ceiling penalty. Submission angles are in radians; the competition verifier may escalate difficult overlap checks to interval arithmetic. Confirm these details against the current official metric before relying on them in a submission pipeline.

Consequences for search strategy:

- Each `N` can use a different seed family and algorithm; do not force one method across all 1,000 sizes.
- An improvement `ΔL_n` contributes a score change proportional to `ΔL_n / sqrt(n)`.
- A discovery can have value beyond its original size if it can be cropped, extended, subdivided, or recombined and then refined.
- Optimize the actual submission objective, not only local packing density or a proxy loss.
- Compare candidates against one pinned baseline and report certified whole-submission score changes, not incomparable local metrics.

## Evidence and source findings

### What the public Kaggle activity suggests

The source research found several strong public notebooks with reported scores clustered around 22.30 and a dependency graph combining certified packings, research witnesses, transfer methods, and fault-line constructions. The exact notebook scores quoted in `a.md` are crawl-time snapshots, not verified live leaderboard results; they should not be treated as current rankings.

The broader finding is more durable than those numbers: competitive notebooks appear to assemble a **portfolio of complete layouts and transformations**, rather than solve each `N` independently from random initialization. The useful extension is to keep multiple structurally distinct layouts per `N`, not only the shortest known one. A slightly worse layout may be a better seed for another size or a different search basin.

Source-level notebook observations recorded in `d.md`:

| Notebook / family | Reported contribution | Caveat or use |
|---|---|---|
| Neighbour Transfer + Squeeze | Whole-layout merging, deletion/expansion transfer, contact LP, CUDA search with square-specific penalties | Default execution reportedly replays saved discoveries; separate inherited results from fresh search. |
| CUDA Packing Search | LP restoration of overlapping proposals, rigid-block compaction, seam profiles, staircase composition | Useful ideas for coordinated motion and reusable pieces. |
| CPU/CUDA/MPS ProjUnion | Sparse contact LP, tensor penalties, seam kicks, CPU repair | CUDA had a small smoke test; MPS was explicitly hardware-untested in the inspected source. |
| THINK / SELECT / RECLOSE | Delete boundary squares from larger donors, perturb placement/angle, run fixed-angle separating-axis LP | Concrete transfer and local-search pattern. |
| A Square Deal | Research witnesses, strips/blocks, frame extension, subdivision, cropping, backfilling, coupled SLP | Bridge from mathematical constructions to a competition pipeline. |
| Top LB Blending + Visualization | Select whole layouts from input submissions and visualize them | “Blend” means choose a complete packing per `N`; coordinate averaging is generally invalid. |
| SAT & Dynamics | Catalogue/grid assembly plus a centre-distance repulsion objective | The inspected overlap proxy ignored square orientation; do not use disk-like centre-distance loss as the square collision test. “SAT” in geometry sources can mean separating axis theorem, not Boolean SAT. |

Important notebook-audit cautions:

- A notebook may contain a search engine while default execution only replays frozen outputs. Runtime of a replay is not the cost of discovering its coordinates.
- Inspect code and inputs rather than inferring methods from notebook titles or scores.
- Public Kaggle rendering did not expose every cell during the source research. Some findings therefore rely on indexed content and inspected external implementations, not a complete audit of every notebook or discussion.
- Reported algorithm results in papers and repositories are author-reported; the search campaigns were not rerun for these notes.

### Why SLP is a high-priority first optimizer

The strongest concrete lead in the research notes is Griffin Casson’s square-packing work. It reports 39 new record packings for `N=103..307`; 37 were attributed to applying SLP to published layouts, while two required GPU global search to find new arrangements. These are author-reported results against that work’s catalogue snapshot—not a guarantee of gains over the current Kaggle baseline.

The reported SLP jointly optimizes square centres `(x_i, y_i)`, orientations `θ_i`, and container side `L`. For each nearby pair it considers the eight candidate separating faces (four for each square), selects the current best separator, linearizes pair and wall constraints, and solves an LP. Trust regions and elastic slack limit risky steps; correction and final dilation/verification address nonlinear feasibility. The important lesson is not merely “call an LP solver”: SLP is a carefully structured local method for the continuous variables under a currently selected contact/separator structure.

The geometry has both continuous and discrete structure:

- **Continuous:** centres, angles, and container size.
- **Combinatorial:** which face/separator keeps each nearby pair apart; equivalently, much of the contact topology.

Within a fixed separator/contact neighborhood, local refinement can be effective. Escaping to a different neighborhood is the hard part. This motivates the recurring pattern **structural/topology-changing search → SLP**.

### Other literature findings

- Gensane–Ryckelynck’s square-packing work uses a fixed-container **maximal inflation** formulation: maximize how far all pieces can grow before a pair collision or wall contact, with `ω(C) = min(ψ(C), φ(C))`. Their stochastic billiard/perturbation search provides direct precedent for square-in-square exploration.
- That work warns that ordinary local billiard search can drift toward all-axis-aligned configurations. Perturbations are needed to escape. Free orientations matter: cited packings include several distinct angles, so restricting all squares permanently to `0°/45°` is not justified.
- Friedman’s survey supplies reusable structural motifs—diagonal/tilted strips, off-centre blocks, multiple-angle families, and L-shaped border extensions. Its historical table is not a current leaderboard; use the constructions, not stale record rankings.
- Arslanov–Mustafin–Shangitbayev motivate squeezable rectangular packings, tilted stacks, and composition into square-container candidates.
- Bui and McClenagan give asymptotic tilted-stack/trapezoid construction ideas. Their asymptotic bounds are not direct Kaggle-score promises: at finite sizes, constants, integer rounding, and boundary losses can dominate.
- Nakajima’s soft-to-rigid continuation starts from rounded pieces and gradually hardens them into polygons. The cited work found distinct square packings but does not establish that a fixed compute budget split between softening and rigid search beats rigid search alone.
- Related hard-particle literature motivates replica exchange/parallel tempering as a high-upside experiment. Its transfer to square packing remains unproven here.

## Method portfolio

The priorities below summarize the research notes’ engineering judgment, not measured results from this repository.

### A. Build a certified per-size layout portfolio

Maintain a canonical archive for `N=1..1000` containing legal/imported public and research layouts, validated local discoveries, provenance, score, and derivation history. For each size:

- Normalize coordinates and units consistently.
- Independently validate every imported witness.
- Keep the best complete packing for submission, but retain several structurally different alternatives for search and transfer.
- Select a whole packing per size. Do not average coordinates across layouts.
- Track whether an improvement came from an imported witness, a transformation, or new search.

This is low-cost and establishes a trustworthy baseline before expensive search. Preserve provenance and licensing constraints when importing external solutions.

### B. Fixed-angle LP and free-angle SLP polishing

Implement two related but distinct refiners:

1. **Fixed-angle LP:** hold orientations fixed, select a separating direction and sign for each relevant pair, then optimize centres/container size under linear separation and wall constraints. It is useful for cheap compaction and feasibility restoration within chosen branches; it does not make the whole problem convex.
2. **Free-angle SLP:** repeatedly linearize the oriented-square separation and wall constraints while allowing centres, angles, and `L` to move. Use sparse nearby-pair constraints, bounded trust regions, special handling around absolute-value kinks, elastic slack/correction as appropriate, nonlinear checks after each step, and a final feasibility/clearance pass.

Run refinement on every promising seed source: public layouts, historical witnesses, `N±k` transfers, construction outputs, and stochastic-search candidates. Record gains, failures, runtime, and whether topology changed. A local optimizer stopping at a minimum is not evidence of global optimality.

### C. Transfer and propagation across sizes

Use a good `N+d` packing as a donor for `N`, and a good `N` packing as a base for `N+d`:

- Delete one or more squares, then compact/refine the remainder.
- Rank deletion candidates using boundary/extreme status, contact degree/centrality, stress or SLP slack/duals when available, and the void geometry exposed by removal.
- Test directional hull peeling and exact outer-edge trimming, not just random deletion or the square nearest an edge.
- Insert a square into a cavity after locally loosening the layout; also remove `k` and reinsert `k+1` when growing.
- Try `N±2`, `N±3`, and other useful offsets; the best structural donor need not be the nearest size.
- Crop a compact window from a larger layout, extend rows/borders/L-shaped frames, transplant corners/bands, or compose blocks and then optimize the joins.

Configuration families vary smoothly with `N` in some ranges but can jump between structural regimes. Keep transfer candidates diverse and polish every descendant. A good donor is not automatically a good target-size packing.

### D. Fixed-container global feasibility search

Avoid relying only on raw bounding-box side as the search objective: most single-square moves may not affect the extreme corners, giving poor guidance. Instead choose a fixed container side `L`, search for non-overlap and wall feasibility, then shrink `L` when feasible and expand/restart when jammed.

Candidate engines include:

- GPU simulated annealing with many independent chains, adaptive translation/rotation amplitudes, occasional angle snapping, and shrink/grow control.
- Square-specific overlap and wall penalties using true oriented-square geometry—not centre-distance/disk approximations.
- LP restoration or SLP polishing of promising overlapping or nearly feasible candidates. Do not discard all overlap proposals immediately if a repair step can rescue useful structure.
- Float32 for high-throughput exploration if validated; use float64 or higher precision for final refinement/certification.

The source inspected one GPU annealer with roughly 45% translation, 35% rotation, some `0°/45°` snapping, and the remainder joint moves; move sizes were adapted around a target acceptance rate, and feasible/infeasible episodes shrank/expanded the container. Treat these values as a reference implementation’s settings, not universal defaults.

### E. Basin hopping, iterated local search, and annealing variants

Wrap a strong local solver in a cycle:

`stored local optimum → deliberate structural perturbation → repair/refine → accept/archive candidate`.

Useful perturbations include:

- Rotate or translate a contact-connected group.
- Push or shear a fault line/seam; apply opposite tangential shifts on its sides.
- Remove/reinsert 1–4 squares for small kicks or a larger connected patch for large-neighborhood search.
- Flip an ambiguous separating-face branch.
- Expand the container slightly, scramble a stressed region, then compress again.
- Temporarily soften pieces and re-harden them (a controlled experiment).
- Perturb all squares simultaneously before relaxation.

Tiny Gaussian noise often remains in the same contact basin. Deliberate topology changes are the intended mechanism. Keep multiple minima; use basin hopping or iterated local search to decide which perturbed minima remain in the archive.

Test threshold accepting against Metropolis SA only as a controlled A/B variant. The notes’ literature reading suggests move/neighborhood design is likely more important than the exact acceptance formula.

### F. Large-neighborhood destroy-and-repair

Select a compact contact-graph neighborhood or difficult seam/corner, remove a patch (from a few squares up to tens, depending on `N`), loosen/push a surrounding buffer, generate candidate positions/orientations for reinsertion, choose a mutually compatible subset, then release and tighten the full layout with SLP.

The movable buffer matters: freezing a rigid boundary immediately around the patch can make a useful rearrangement impossible. Variants include:

- Delete a connected boundary patch.
- Crop/rebuild a compact window.
- Remove several squares and reinsert in a different order.
- Open a cavity and insert one more square than removed.
- Repair only a small region with discrete angle/placement choices, then continuously refine the full solution.

This is a promising extension from irregular-packing large-neighborhood methods, but no particular patch size or selection policy is established as best in these notes.

### G. Contact groups, separator branches, seams, and fault lines

Treat the contact graph and separating-face choices as explicit search objects:

- Detect near-zero clearances and connected contact clusters; move a group coherently rather than nudging one blocked square.
- Find pairs with nearly tied best/second-best separating faces. Flip a small number of branches, slightly expand `L`, and rerun SLP to enter a neighboring combinatorial region.
- Select a stressed contact edge or connected subgraph and relax its neighborhood.
- Move a whole strip, fault line, diagonal band, or tilted block; repair contacts along the cut.
- Build seam profiles and compose blocks with explicit interface optimization.

This targets the key failure mode of local continuous refinement: a good local minimum may require changing which objects touch. Branch combinations grow rapidly, so search only a small, selected set of ambiguous contacts or local patches.

### H. Low-dimensional parametric construction search

For large `N`, avoid searching all `3N` pose variables as the only global representation. Parameterize families with perhaps a small number of variables:

- Lattice vectors, strip/band angle, width, and offsets.
- Number of rows/stacks and boundary shifts.
- Relative placement of aligned and tilted blocks.
- Fault-line positions, gap widths, corner patterns, and boundary profiles.
- A small number of exceptional/missing squares or angle classes.

Search macro parameters using grid/random search, CMA-ES, or differential evolution; instantiate a full packing, then release individual poses into SLP. This is especially attractive for several hundred to 1,000 squares, where interiors may be periodic and boundary/fault structure dominates. Avoid permanent symmetry or a small fixed angle set: use constraints only to generate candidates, then break them and polish freely.

### I. Subdivision, scaling, and reusable construction families

- **Subdivision:** scale a packing by integer `k`, subdivide each enlarged square into `k²` unit squares, then free the internal motions and refine. Scaling/subdivision alone preserves normalized quality; improvement can only come from the added freedom and subsequent relaxation. Reported experiments include both successes and jammed/failing examples, so this is a seed operator, not a theorem.
- **Frames and borders:** extend a seed with rows or L-shaped layers, optimize the joins, and propagate to larger sizes.
- **Rectangular modules:** search for squeezable rectangular packings and compose them into square-container candidates.
- **Tilted stacks and trapezoid/quadrilateral constructions:** extract finite-size integer parameter choices from asymptotic papers, explicitly measure boundary losses, then refine. Do not infer finite Kaggle performance from asymptotic exponents.
- **Symmetry-assisted discovery:** temporarily tie mirrored/repeated groups to reduce dimension, then remove constraints before final refinement so asymmetric improvements remain possible.

### J. Soft-to-rigid continuation

Test a path from rounded pieces to squares, for example an inradius-preserving interpolation between the square `P` and a disk of radius `1/2`:

\[
P_\tau=(1-\tau)P\oplus\tau\left(\tfrac12D\right),
\]

with `τ` decreasing from 1 to 0. Run two distinct experiments:

1. Random soft-to-rigid starts versus random rigid starts.
2. Temporarily soften and re-harden incumbent layouts versus ordinary rigid perturbations.

Compare at equal compute budgets, with repeated seeds and the same final verifier. The literature notes report that hardening can find different square layouts, but do not prove it improves a fixed total budget over rigid search.

### K. Replica exchange / parallel tempering

Run replicas at different temperatures or, more naturally for hard packing, different container sizes/pressures. Loose replicas can rearrange; dense replicas exploit. Attempt swaps of whole configurations under a correctly derived acceptance rule. Compare against the same total compute spent on independent restarts. This is high-cost and high-upside but unvalidated for this square-packing workflow.

### L. Restricted discrete and exact subproblems

Do not prioritize a full exact global model for `N≈1000`; free rotations plus pairwise separation disjunctions create a large nonlinear mixed discrete-continuous problem. More plausible uses:

- Restrict orientations to a finite set for a small patch.
- Freeze most of the packing/contact graph and branch on a few separator choices.
- Use MILP/CP/SMT/MINLP/interval methods for small instances, local repair, or proof-oriented special cases.
- Infer a rigid contact pattern from a promising numerical layout, solve its contact equations at high precision or symbolically, then independently verify it.

Exact algebra can tighten or explain a chosen small arrangement; it is not a general discovery method for all sizes.

### M. Borrowed packing engines and guided search

Sparrow and other irregular-packing/nesting engines may offer separator optimization, adaptive penalties, focused sampling, warm starts, or parallel workers. A custom square-specific solver may be simpler and faster, so adapt ideas selectively rather than adopting a large system wholesale. Guided local search is another candidate, but should be measured against the simpler local-search portfolio.

### N. Lessons from the Santa 2025 medalists

The Santa 2025 competition packed one fixed, irregular, concave tree polygon for `N=1..200` inside the smallest square. Its geometry differs from this problem, but the search problem has the same core shape: many pose variables, hard non-overlap constraints, and a square-container objective. The medalist solutions provide evidence about search organization and candidate-generation operators. Their exact parameters and collision code do not transfer automatically to unit squares.

| Santa result | Main method | Transferable lesson for unit squares | What does not transfer directly |
|---|---|---|---|
| 1st, Jeroen Cottaar | Island genetic search, diversity control, structured seeds, GPU physical relaxation and L-BFGS | Keep competing populations, exchange layouts without allowing one basin to dominate, and follow structural exploration with fast continuous relaxation | Tree-specific polygon losses, raw genotype crossover, and tree lookup tables |
| 2nd, KiRaRe | Periodic seeds, large-neighborhood remove/loosen/place/tighten, SA, ILS, beam search, geometric deduplication | Treat destroy-and-repair as a first-class operator; retain a beam of structurally different candidates | Tree edge-intersection kernels and tree-specific placement |
| 3rd, Jingle Bins | Customized Sparrow, warm starts, rectangle composition, symmetry, center-aware orientation bias, global kicks, `N` up/down sampling | Use structured seeds, temporary orientation priors, warm starts across sizes, and deliberate global rotate/scale kicks | The observed tree angle range is not a square-packing constant |
| 4th, bowwowplusa | Sparrow plus manual/compositional structure, restricted orientation families, repeated region replacement from other `N` values, SA cleanup | Automate cross-`N` region transplantation and screen many cheap replacements before expensive refinement | A fixed eight-angle restriction may exclude useful square contact geometries |

#### N1. Diversity-preserving island search

The first-place implementation is more specific than “run a genetic algorithm.” It uses multiple subpopulations, configurable island connectivity, diversity-based selection, mutation and crossover operators, batched evaluation, and a relaxation stage. A square version should encode a layout as structured pieces rather than blindly crossing all `3N` pose coordinates:

- Keep islands for grid/periodic, diagonal-band, fault-line, public-record, and stochastic layouts.
- Exchange whole patches, contact-connected groups, or aligned boundary bands after geometric alignment and repair.
- Select a few elites, then retain deliberately different candidates using normalized pose matching and contact-graph distance.
- Reset or reseed an island when its candidates become too similar, while preserving its best audited layouts.
- Run fast overlap-penalty or fixed-`L` feasibility relaxation on offspring before SAT/SLP certification.

This is a stronger interpretation of evolutionary search than a giant population over unconstrained coordinates. The square-specific final gate remains the independent separating-axis verifier.

#### N2. Large-neighborhood search with beam retention

The second-place solution gives a concrete version of the destroy-and-repair idea already proposed above:

1. Select a target point, emphasizing disordered regions and occasionally corners.
2. Remove a compact contact-graph neighborhood of `k` squares.
3. Expand or loosen the surrounding layout to create a cavity.
4. Generate many candidate poses for the removed squares.
5. Select a mutually compatible subset using a conflict graph or compatibility search.
6. Tighten the entire layout with SA, fixed-angle LP, or SLP.
7. Keep several non-duplicate descendants in a beam and continue from each for a bounded depth.

For squares, the conflict graph can use exact SAT checks after broadphase filtering. Compare random targets, high-contact regions, ambiguous-separator regions, corners, and high-void regions. Deduplicate by normalized pose matching and contact structure so the beam does not become many copies of one basin.

#### N3. Periodic and compositional seed libraries

The second-, third-, and fourth-place solutions all used structured starting layouts. Their common pattern was:

```text
periodic or compositional seed
        -> warm start / N-transfer
        -> structural kick or region replacement
        -> local relaxation
        -> final exact audit
```

For this project, build a reusable library of rectangular unit-square modules, periodic interiors with several lattice angles and offsets, diagonal strips, tilted bands, frames, fault-line seams, cropped regions from strong `N'` layouts, and small exact contact motifs. Combine modules for a target `N`, then release the interface and individual square poses. Store parent layouts, cut lines, transforms, and target sizes.

#### N4. Soft orientation priors, global kicks, and warm starts

The third-place method used an adaptive, center-aware orientation bias: it encouraged a dominant lattice orientation in the regular interior while allowing more freedom near walls and boundaries. A square analogue is worth testing as a temporary search prior:

- Penalize deviation from one or more target angle classes in the interior.
- Reduce the penalty near walls, seams, and deliberately irregular patches.
- Increase the prior when the layout is noisy, then decay it when progress stalls.
- Remove the prior before final SLP and certification.

Use a mixture of target classes rather than a permanent fixed-angle restriction. Before each restart, apply a small global rotation, reflection, or scale-up kick, then re-tighten. The tree angle values themselves should not be copied to square packing.

#### N5. Geometry throughput as an algorithmic advantage

The medalists invested heavily in collision throughput: broadphase bounding boxes, compact structure-of-arrays layouts, vectorized or GPU evaluation, and precomputed geometry. For unit squares, exact SAT is simpler than concave polygon intersection, so the useful adaptation is to maintain a broadphase spatial grid or swept-AABB neighbor list, batch SAT clearance and wall penalties, use smooth overlap energy only during exploration, and use exact SAT plus the serialized-file audit for acceptance. The saved geometry time should fund more structurally distinct candidates.

#### N6. Practical priority from the cross-competition comparison

The best next square-specific experiment is a **beam large-neighborhood solver**:

1. Seed each target `N` from the current portfolio and nearby `N` values.
2. Generate 8–32 destroy-and-repair branches using contact-aware and corner-aware targets.
3. Use a compact conflict graph to place removed squares.
4. Run a short fixed-`L` repair followed by SLP on survivors.
5. Deduplicate by pose matching and contact structure.
6. Keep the best few branches and repeat for a small depth.

This combines the strongest independent idea shared by the medalists with the square-specific methods already in this document. Add an island population after the beam version has a measured correctness and throughput baseline.

## What not to prioritize

- **Pure random multistart plus generic local optimization:** likely spends compute rediscovering many local minima. Improve topology-changing moves before merely multiplying starts.
- **Generic global optimization as the main engine at large `N`:** full disjunctive geometry scales poorly relative to specialized constructions and local refiners.
- **A giant evolutionary algorithm over all `3N` pose parameters:** feasible regions are thin and dimensionality is large. Use evolutionary search on compressed structural variables instead.
- **Permanent `0°/45°` restriction:** literature examples include several unrelated orientations; such a restriction can exclude good packings.
- **Disk-like centre-distance repulsion as the collision predicate:** it ignores square orientation and can miss true overlaps. Use square separating-axis geometry.
- **Coordinate crossover/averaging between parent packings:** usually destroys non-overlap. Prefer aligned patch transplantation followed by repair.
- **Changing SA acceptance rules before improving move design:** threshold accepting is an A/B option, not a standalone research program.
- **Treating notebook score/runtime as proof of search strength:** the notebook may simply replay stored candidates.
- **Treating asymptotic bounds or author-reported records as current competition guarantees.**

## Solver architecture and size regimes

Candidate pipeline:

```text
provenance-aware seed archive
        ↓
whole-layout selection and N-transfer
        ↓
structural mutations / construction generators
        ↓
fixed-L feasibility search and/or local repair
        ↓
fixed-angle LP → free-angle SLP
        ↓
independent validation of serialized output
        ↓
certified archive update and propagation to other N
```

Possible size-dependent allocation, explicitly a starting hypothesis rather than a universal cutoff:

- **Smaller `N` (roughly below 80–150 in the notes):** afford more unrestricted orientation search, GPU annealing/inflation, contact-group moves, and exact/local-branch experiments.
- **Middle `N` (roughly 100–350):** prioritize strong seeds, SLP, transfer, and carefully selected structural mutations; the reported recent SLP improvements were concentrated in this range.
- **Large `N` (several hundred to 1,000):** emphasize periodic/banded constructions, low-dimensional search, fault lines, block/seam composition, subdivision, and transfers; use unrestricted global search as a complementary source of discoveries.

These ranges overlap intentionally. Select by measured runtime and success rate, not by a hard-coded boundary.

## Verification, provenance, and promotion gates

Treat verification as an independent subsystem. The search collision kernel and final validator should not be identical implementations, so a shared bug is less likely to certify itself.

Recommended gates:

1. Validate geometry with the search kernel during exploration.
2. Refine in float64 or higher precision and preserve a small, explicit clearance margin.
3. Serialize the exact candidate in the competition’s required format and units (angles in radians per the source notes).
4. Re-read and validate the written file, including every pair and wall constraint, with an independent float64/long-double/multiprecision SAT implementation where practical.
5. Run the official verifier/metric when available; difficult cases may require its interval-arithmetic path.
6. Promote only the exact serialized artifact that passed validation. LP success or low penalty energy alone is insufficient.
7. Store provenance: source witness or parent layout, transformations, optimizer settings, seed, precision, validation result, and score.

Maintain a fast float32/64 exploration kernel and a separate final checker. The source notes cite a recent project that used an independent checker and a 50-digit separating-axis implementation; a tiny shrink caused verification failure, illustrating why boundary rounding and safety margins matter.

## Experimental protocol and metrics

For each experiment, pin the same baseline, per-size input archive, total compute budget, precision policy, and verifier. Use repeated seeds for stochastic methods. Record:

- Certified score gain over the pinned baseline.
- Per-`N` change in `L_n` and total metric change.
- Compute spent on discovery, feasibility repair, SLP, and verification separately.
- Success frequency and variance across repeated runs.
- Number of structurally distinct candidates found, not just the best one.
- Additional gains after transferring each discovery to other sizes.
- Whether the gain came from an imported witness, deterministic construction, transfer, or fresh search.
- Invalid candidates, numerical failures, and serialization-induced regressions.

Use ablations to distinguish mechanisms. Examples: fixed-angle LP vs free-angle SLP; ordinary SA vs SA plus topology moves; transfer with random deletion vs ranked deletion; rigid vs soft-to-rigid at equal compute; replica exchange vs independent restarts. A short smoke test verifies functionality only—it is not evidence of competitive quality. The source notes explicitly correct an `N=5` demonstration with side `2.76777`: the known optimum is `2 + 1/√2 ≈ 2.70711`, so that demo was not competitive evidence.

## Suggested implementation and research sequence

This is an order of information value and reuse, not a commitment to implement every branch.

### Phase 1 — establish trusted evidence

- Build a canonical per-`N` archive and whole-layout selector.
- Import available witnesses with provenance and legal-use checks.
- Implement an independent geometry validator and submission round-trip check.
- Recompute the baseline using the official metric/verifier.

### Phase 2 — harvest cheap refinement and transfer gains

- Implement fixed-angle LP compaction/restoration.
- Implement free-angle SLP and run it on the full candidate archive.
- Add deletion/insertion and `N±k` transfers; keep multiple descendants and polish all.
- Measure certified score gain per compute before starting a large GPU search project.

### Phase 3 — change contact topology deliberately

- Add basin hopping around SLP.
- Add contact-group, separator-flip, fault-line/seam, and small destroy/reinsert moves.
- Use patch buffers and repair rather than freezing an overly rigid neighborhood.
- Preserve structurally distinct local minima in the archive.

### Phase 4 — pursue large-scale and exploratory branches

- Add fixed-`L` GPU feasibility search and compare it with inflation/billiard search.
- Add low-dimensional strip/block/fault construction search for large `N`.
- Test subdivision, frame extension, and rectangular-module composition.
- Implement beam large-neighborhood destroy/loosen/reinsert/tighten with contact-graph deletion, candidate conflict graphs, and structural deduplication.
- Build diverse island populations over construction families and use warm-started cross-`N` transfer instead of raw coordinate crossover.
- Add batched SAT/clearance evaluation and measure valid structural discoveries per unit compute.
- Run equal-budget soft-to-rigid experiments.
- Only then consider pressure replica exchange, Sparrow adaptation, or restricted MINLP/interval subsolvers.

## Research questions worth keeping open

- Which contact-graph deletion score best predicts useful `N+d → N` descendants?
- Do separator flips at near-tied contacts outperform generic basin perturbations per unit compute?
- How large should the movable buffer be around a destroy-and-repair patch?
- Does beam retention with contact-aware deduplication outperform a single incumbent under the same SLP and geometry budget?
- Which island connectivity and diversity criterion preserves useful square-packing basins without slowing convergence?
- Do temporary center-aware orientation priors improve discovery after the prior is removed before SLP?
- Which cross-`N` region transplantation policy produces valid improvements most often: corner, boundary, contact, or high-void regions?
- Which structural move families scale best from hundreds to 1,000 squares?
- Does retaining a diverse archive improve downstream transfer enough to justify its storage/search overhead?
- Does softening an incumbent create new basins more efficiently than ordinary rigid perturbation?
- Does pressure exchange outperform independent multi-start search at equal GPU time?
- Which finite-size strip/stack parameters matter most after exact boundary losses are included?
- Which improvements propagate to many `N` and therefore maximize certified total-score gain?

## Source notes and limits

The detailed source discussions and links are preserved in `a.md`, `b.md`, `c.md`, and `d.md`. Those notes reference, among others, Griffin Casson’s square-packing source, Gensane–Ryckelynck, Friedman’s survey, Kaggle notebooks, soft-to-rigid packing research, and asymptotic tilted-stack constructions. The Santa 2025 comparison uses the [1st-place genetic/GPU-relaxation writeup](https://www.kaggle.com/competitions/santa-2025/writeups/1st-place-genetic-algorithm-and-gpu-relaxation), the [2nd-place SA/ILS/beam-search writeup](https://www.kaggle.com/competitions/santa-2025/writeups/2nd-place-simulated-annealing-iterated-local-sea), the [3rd-place customized Sparrow writeup](https://www.kaggle.com/competitions/santa-2025/writeups/third-place-solution-a-customized-sparrow-algorit), the [4th-place region-replacement writeup](https://www.kaggle.com/competitions/santa-2025/writeups/4th-place-hybrid-packing-with-sparrow-manual-str), and [Cottaar’s released implementation](https://github.com/jcottaar/packing). The released implementation states that it is under CC BY-SA 4.0; direct code reuse should preserve attribution and license obligations. Use the original papers/code for implementation details and verify that links, competition rules, notebook versions, and leaderboard figures are still current before acting on them.

The source research is not a fresh benchmark of this repository. Kaggle crawl-time scores may be stale; some notebooks/discussions were only partially accessible; author-reported experiments were not rerun; and recommendations are explicitly hypotheses until validated under a pinned, reproducible, independently checked experiment.

## O. Implemented remainder audit (2026-10-27)

The first bounded implementations of the remaining low-cost ideas are now
recorded in `EXPERIMENT_RANKING.md`. The N=344 certificate refresh is now the
best completed and Kaggle-validated candidate: local score
`22.287077114539976`, public score `22.2870771145`. It adds one strict
improvement to the previous public-union portfolio using the CC0 certificate
in [issue #819](https://github.com/jlevy/squares/issues/819). The earlier
N=130 refresh and 59 public-union improvements remain in that portfolio.

#### N=182 certificate refresh submitted for evaluation (2026-10-30)

The pinned N=182 certificate from Evan Daniel's
[issue #806](https://github.com/jlevy/squares/issues/806) matches the published
SHA-256 and passes local parsing and geometry validation. Merging it over the
N=344 candidate changed only N=182 and produced an audited score of
`22.28684182148117`, with zero invalid puzzles and zero errors. Kaggle has the
combined candidate pending evaluation. The submitted SHA-256 is
`7af0e96af7f9f5cafeb9db05ff7afc3775ec10cd8c72d7b7c00e9744d976b7cc`.

The eight-branch expansion is now implemented in `eight_ideas.py` with shared
spatial-hash and fixed-container helpers in `search_kernels.py`. It tested
fixed-container feasibility, buffered LNS, separator flips, strip
construction, multi-descendant beam repair, island diversity, soft/replica
search, and accelerated broadphase SLP on the same 30 hard target sizes.
Every complete output passed the independent audit; no branch accepted a
strict improvement. The island and soft/replica branches generated invalid
intermediate states and were correctly rejected before serialization.

#### Island and replica validity-guard follow-up (2026-10-29)

The first per-`N` pilot showed that the final candidate selectors in these two
branches did not consistently require exact validity: an infeasible relaxed
state could replace a valid population member or be selected as the final
output. `eight_ideas.py` now starts from a certified incumbent, admits only
exact-valid repaired candidates, and validates the selected layout again
before return. Regression tests cover both branches. On the fresh seed
`20261030`, the repaired island and soft/replica methods each returned valid
layouts for all 30 targets, with zero strict improvements. The complete
eight-method output remained identical to the incumbent and passed the full
submission audit; see `EXPERIMENT_RANKING.md` for timings and artifact path.

Completed negative-result experiments:

- boundary-aware `N+K -> N` deletion beam over 89 hard target sizes and 5,666
  deduplicated public donor layouts;
- contact-group kick followed by oriented-square SLP repair;
- seam/fault-line kick followed by oriented-square SLP repair;
- compact destroy/reinsert followed by oriented-square SLP repair;
- rigid whole-layout rotation over all 1,000 sizes.

The listed negative-result submissions passed the independent audit with zero
invalid puzzles and tied the incumbent because no strict improvement was
accepted.
The earlier bounded SLP run on selected certificate layouts also produced no
accepted improvements. These results rule out simple safe cropping, rigid
rotation, and small one-trial kicks as sufficient improvements under the
tested budgets; they do not rule out buffered repair, separator flips,
fixed-container feasibility search, or full beam/island search.

#### Wider-strip screen and refreshed public record (2026-10-29)

The diagonal-strip search covered widths 9 through 30 where geometrically
eligible, across 900 target sizes. It took 767.8 seconds, found no strict
improvement, preserved all 1,000 incumbent layouts, and passed the full audit
at `22.287265765` with zero invalid puzzles or errors.

A newer rational `n=130` certificate from the pinned [Couzo repository
commit](https://github.com/franciscouzo/square-packing/tree/3a4d95c72083da3c3fd5acc4b1d0e94479c5422d)
was parsed and independently validated. Replacing only `n=130` lowered the
full-file score to `22.28708575920191`, a gain of `0.00018000620661`; the
complete audit reported zero invalid puzzles and zero errors. The candidate
and source provenance are retained under
`data/variants/public_record_refresh_20261029/`. This n=130-only candidate was
kept local; the merged portfolio below was the candidate submitted to Kaggle.

The audited `data/submission.public_union.csv` was then merged through the
strict per-`N` candidate gate with the same n=130 record. It contributed 59
additional layouts, with no per-`N` regression; 60 sizes now improve over the
public incumbent. The complete 500,500-row candidate scores
`22.287085755423853` and passes the full audit with zero invalid puzzles or
errors. It is saved at
`data/variants/public_union_refresh_20261029/submission.csv`. Kaggle marked
the matching uploaded file Complete with public score `22.2870857554`, a
`0.00018000998467` gain over the previous public best.

#### CPU repair-kernel crossover (2026-10-29)

On actual incumbent layouts at `N=300, 600, 700, 800, 900, 983, 1000`, dense
and spatial-hash pair lists and LP outputs matched exactly across five
alternating runs per path. The spatial-to-dense median time ratio ranged from
`0.910` to `1.012`; it was consistently useful only at the tested sizes from
`N=800` upward. `slp_submission.py` now dispatches to the shared spatial hash
at that threshold, keeping the vectorized provider for smaller layouts. The
repair step is faster at large `N`, but the complete search has not been
measured end-to-end, so no full-search speed gain is claimed. Raw repair-step
timings are in `data/variants/repair_kernel_benchmark_20261029/benchmark.json`.

A subsequent higher-budget eight-method tournament on `N=802, 857, 919, 983,
1000` returned exact-valid layouts for every method and size, but accepted no
strict gain. The full file remained numerically identical to the n=130-start
portfolio and passed the complete audit; detailed timings and provenance are
in `EXPERIMENT_RANKING.md` and `data/variants/per_n_tournament_large_20261029/`.

#### Current certified-row screen (2026-10-29)

The 77 current report-order certificates in
[the issue #742 intake](https://github.com/jlevy/squares/pull/742) were
screened by declared exact side length against the current best local CSV.
None could clear the strict `1e-12` per-size merge threshold, so no packing
was imported or changed. The source manifest/census digests and per-size
comparisons are recorded in
`data/variants/mishapolk_registry_screen_20261029/registry_screen.json`.
This was a bounds screen; it did not independently re-verify certificates
that could not improve the current candidate.
