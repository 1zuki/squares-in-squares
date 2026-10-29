# Remaining idea experiments and ranking

Date: 2026-10-27

## Baseline and interpretation

The pinned incumbent is:

`data/public_external/kaggle_neighbour_transfer/submission_merged.csv`

Its independently audited score is **22.287265765408524**, with zero invalid
puzzles and zero audit errors. The completed Kaggle ledger reports the same
public score to the displayed precision, so local audit ranking is a valid
screen for these deterministic, complete-file experiments. This is evidence of
score agreement for the finished uploads, not proof that every future search
candidate will reproduce on Kaggle.

## Ranking

Lower is better.

| Rank | Experiment | Scope | Local score | Delta vs incumbent | Valid | Result |
|---:|---|---|---:|---:|---:|---|
| 1 | Strict per-`N` union plus refreshed record | 60 sizes improve; 59 union layouts plus N=130 | 22.287085755423853 | -0.00018000998467 | yes | Kaggle Complete: 22.2870857554 |
| 2 | Incumbent neighbour-transfer portfolio | 1,000 sizes | 22.287265765408524 | 0 | yes | Previous public incumbent |
| 2 | Boundary-aware deletion beam | 89 hard target sizes, 5,666 deduplicated public donors | 22.287265765408524 | 0 | yes | No accepted improvements |
| 2 | Contact-group kick + SLP repair | 11 target sizes, 1 deterministic trial each | 22.287265765408524 | 0 | yes | No accepted improvements |
| 2 | Seam/fault-line kick + SLP repair | 11 target sizes, 1 deterministic trial each | 22.287265765408524 | 0 | yes | No accepted improvements |
| 2 | Destroy/reinsert kick + SLP repair | 11 target sizes, 1 deterministic trial each | 22.287265765408524 | 0 | yes | No accepted improvements |
| 2 | Rigid whole-layout rotation | All 1,000 sizes, 360 coarse + 41 fine angles | 22.287265765408524 | 0 | yes | No envelope improvements |

The negative-result experiments tie the previous public incumbent because
their candidates were rejected and their complete outputs retained its layouts.
The refreshed portfolio passed Kaggle validation: public score `22.2870857554`,
compared with the previous best `22.2872657654` (gain `0.00018000998467`). Its
submission description carried SHA-256
`a930b7a9c82b9e8620b83287adc0d99e47813334725bd596b27f464928acd7ef`, matching
the local candidate. The serialized bytes differ for some files because
experiment writers use different decimal formatting; audits and layout
comparisons, rather than byte identity, are the comparison gate.

## Eight-branch expansion

The eight remaining ideas were implemented in `eight_ideas.py`, with shared
accelerated helpers in `search_kernels.py`. The benchmark used the same 30
representative target sizes, seed `20261027`, two trials where applicable,
four repair steps, beam width 3, beam depth 2, three islands, two generations,
and three replicas. Each branch wrote a complete file and was then checked by
`audit_submission.py`.

| Branch | Runtime | Search evidence | Accepted gains | Final audit |
|---|---:|---|---:|---|
| Fixed-container feasibility | 61.9 s | 30 valid repaired trials | 0 | 22.287265765408524, 0 invalid |
| Buffered large-neighborhood repair | 35.6 s | 0 valid repaired trials | 0 | 22.287265765408524, 0 invalid |
| Near-tied separator flips | 67.3 s | 0 valid repaired trials in the final batch | 0 | 22.287265765408524, 0 invalid |
| Low-dimensional strip construction | 13.6 s | 196 valid construction checks | 0 | 22.287265765408524, 0 invalid |
| Multi-descendant beam repair | 53.9 s | 0 valid repaired descendants in the final batch | 0 | 22.287265765408524, 0 invalid |
| Island diversity / patch transplantation | 99.2 s | exploratory states failed exact validation | 0 | 22.287265765408524, 0 invalid |
| Soft-to-rigid / replica-style search | 106.9 s | 2 valid intermediate states out of 180 records | 0 | 22.287265765408524, 0 invalid |
| Accelerated broadphase multi-start SLP | 46.5 s | broadphase matched brute force at tested sizes | 0 | 22.287265765408524, 0 invalid |

The island and soft/replica branches failed closed: their infeasible
exploratory states were never written into the submission because the exact
validator rejected them. The eight output CSVs share one SHA-256 because they
all serialize the retained incumbent through the common writer. They are
byte-different from the original incumbent due to serialization formatting,
while the selected layouts and audited score remain unchanged.

## Should the search algorithm depend on N?

Yes, the final candidate should be selected independently for each square
count `N`: the benchmark score is a sum of per-`N` terms, and for a fixed `N`
the term improves exactly when the valid layout has a smaller bounding side.
`merge_submission.py` already applies this rule in `consider()`: it validates
each candidate and replaces the current layout only when that candidate has a
smaller side. The merged submission is therefore already a per-`N` portfolio,
not one algorithm forced to supply every size.

That does not yet establish which *search method* should be run at each `N`.
The eight new methods were screened on the same 30 representative sizes, and
none accepted a strict improvement; the targeted transfer beam also found no
gains over its 89 hard sizes. Since the candidate CSVs retained the incumbent
at every size, these runs provide no method-by-`N` signal from which to learn a
routing rule. Assigning, for example, one method to small `N` and another to
large `N` would be unsupported by the current results.

### Fresh-seed per-`N` pilot (2026-10-29)

`per_n_tournament.py` ran all eight comparable branches from the same pinned
layout for each of the same 30 target sizes, using seed `20261029`, two trials,
and the prior repair/beam/island/replica settings. It selected only strictly
smaller candidates that passed exact validation. The iteration settings were
matched across branches, while wall-clock runtime varied and was recorded;
this was not an equal-time comparison.

| Method | Exact-valid outputs | Runtime | Per-`N` wins |
|---|---:|---:|---:|
| Fixed-container feasibility | 30/30 | 47.3 s | 0 |
| Buffered large-neighborhood repair | 30/30 | 26.9 s | 0 |
| Separator flips | 30/30 | 50.8 s | 0 |
| Strip construction | 30/30 | 8.2 s | 0 |
| Multi-descendant beam repair | 30/30 | 43.5 s | 0 |
| Island diversity | 0/30 | 87.7 s | 0 |
| Soft-to-rigid / replica search | 0/30 | 90.6 s | 0 |
| Accelerated broadphase SLP | 30/30 | 30.9 s | 0 |

The complete output passed `audit_submission.py` at **22.287265765**, with
zero invalid puzzles and zero errors. Its 1,000 layouts are numerically
identical to the pinned incumbent. Full per-trial metadata is retained at
`data/variants/per_n_tournament_seed20261029/submission.csv.topology.json`.
The unchanged full CSV remains local and is omitted from the repository
snapshot. No incumbent was replaced and no Kaggle upload was made. This
fresh-seed run adds no method-by-`N` winner signal. The island and replica
candidates failed the exact final check on every tested target and were
discarded.

### Validity-guard follow-up (2026-10-29, seed `20261030`)

The first pilot exposed a branch-level selection bug: island and soft/replica
search could carry infeasible exploratory states into their populations and
return the smallest one without an exact-validity gate. `eight_ideas.py` now
certifies its seed, admits only exact-valid repaired candidates to those
populations, and rechecks the selected output with a certified incumbent
fallback. `tests/test_eight_ideas.py` covers both branches. The tournament
runner also checkpoints each completed `N` atomically and can resume only when
the runner, solver, inputs, seed, methods, and budgets match the checkpoint.

The repaired branches were rerun with all eight methods on the same 30 sizes,
seed `20261030`, and two trials per method. All methods now returned exact-
valid candidates at every size, but none strictly improved the incumbent.
The completed run took 422.7 seconds; timings below are measured wall time,
so this remains a matched-settings comparison rather than an equal-time one.

| Method | Exact-valid outputs | Runtime | Per-`N` wins |
|---|---:|---:|---:|
| Fixed-container feasibility | 30/30 | 40.3 s | 0 |
| Buffered large-neighborhood repair | 30/30 | 23.5 s | 0 |
| Separator flips | 30/30 | 53.1 s | 0 |
| Strip construction | 30/30 | 8.4 s | 0 |
| Multi-descendant beam repair | 30/30 | 39.1 s | 0 |
| Island diversity | 30/30 | 72.2 s | 0 |
| Soft-to-rigid / replica search | 30/30 | 154.1 s | 0 |
| Accelerated broadphase SLP | 30/30 | 28.7 s | 0 |

The serialized submission passed `audit_submission.py` at **22.287265765**,
with zero invalid puzzles and zero errors. All 1,000 layouts are numerically
identical to the pinned incumbent. Full per-trial results are in
`data/variants/per_n_tournament_seed20261030/submission.csv.topology.json`;
the full CSV remains local. No Kaggle upload was made because this run produced
no new candidate for external validation.

### CPU repair-kernel crossover (2026-10-29)

The dense vectorized pair search and spatial-hash broadphase were compared on
actual incumbent layouts at `N=300, 600, 700, 800, 900, 983, 1000`, using
container slack `0.25`, `rho=0.04`, and five alternating `linear_step` runs per
path. Every pair list matched exactly; both paths returned the same LP result
at every size. Spatial-to-dense median time ratios were `1.011`, `0.994`,
`0.986`, `0.910`, `0.963`, `0.946`, and `0.930`, respectively. The spatial
path is slightly slower at `N=300`, effectively tied through `N=700`, and
3.7–9.0% faster at the tested sizes from `N=800` onward.

`slp_submission.py` now selects the existing dense provider below `N=800` and
the equivalent spatial hash at or above that cutoff. `search_kernels.py`
re-exports the same implementation, avoiding a second copy. All four
large-`N` targets in the repaired tournament (`802, 857, 919, 983`) also had
identical pair lists after dispatch. This is a measured single-repair-step
speedup, not a claim that a full search or submission score improved. Raw
timings and settings are in
`data/variants/repair_kernel_benchmark_20261029/benchmark.json`.

### High-budget large-`N` tournament (2026-10-29)

The size-aware repair kernel was used in an eight-method tournament starting
from the refreshed n=130 portfolio. It tested `N=802, 857, 919, 983, 1000`
with seed `202610293`, four trials per method, eight repair steps, beam width
5 and depth 3, four islands, four generations, and four replicas. The complete
run took 731.0 seconds.

| Method | Exact-valid targets | Runtime | Strict per-`N` wins |
|---|---:|---:|---:|
| Fixed-container feasibility | 5/5 | 49.9 s | 0 |
| Buffered large-neighborhood repair | 5/5 | 34.3 s | 0 |
| Separator flips | 5/5 | 45.2 s | 0 |
| Strip construction | 5/5 | 3.0 s | 0 |
| Multi-descendant beam repair | 5/5 | 45.0 s | 0 |
| Island diversity | 5/5 | 128.8 s | 0 |
| Soft-to-rigid / replica search | 5/5 | 387.2 s | 0 |
| Accelerated broadphase SLP | 5/5 | 36.3 s | 0 |

The output passed the full audit at **22.287085759**, with zero invalid
puzzles and zero errors; it is numerically identical to the starting
portfolio. Artifacts are in
`data/variants/per_n_tournament_large_20261029/`. This adds no large-`N`
method-by-size winner signal under the tested budget.

### Wider strips and refreshed public record (2026-10-29)

`wide_strip_search.py` screened diagonal-strip widths 9 through the geometric
cap (up to width 30), covering 900 target sizes in 767.8 seconds. No candidate
strictly improved its incumbent layout. The complete output was numerically
identical to the incumbent for all 1,000 sizes and passed the full audit at
**22.287265765**, with zero invalid puzzles and zero errors.

A newer rational `n130.cert` from the pinned
[Couzo repository commit](https://github.com/franciscouzo/square-packing/tree/3a4d95c72083da3c3fd5acc4b1d0e94479c5422d)
was parsed and checked with the local geometry validator. Its side length is
11.902430645984346, improving the incumbent's 11.90448303252669. Merging it
changed only `N=130` in the 1,000-layout file. The merged submission passed
`audit_submission.py` at **22.28708575920191**, with zero invalid puzzles and
zero errors, a strict score gain of **0.00018000620661**. The candidate is
`data/variants/public_record_refresh_20261029/submission.csv`. This n=130-only
candidate was retained separately; the combined public-union candidate below
was later submitted for Kaggle validation.

An additional merge compared the existing audited
`data/submission.public_union.csv` and the n=130 certificate against the
pinned public incumbent using `merge_submission.py`'s strict-validity,
strictly-smaller per-`N` rule. It accepted 59 public-union layouts and the
n=130 record. Compared with the public incumbent, 60 sizes have a smaller
side and none regresses by more than `1e-10`. The 500,500-row output passed a
fresh full audit at **22.287085755423853**, with zero invalid puzzles and zero
errors. The candidate at
`data/variants/public_union_refresh_20261029/submission.csv` was submitted to
Kaggle and completed with public score **22.2870857554**.

A stronger follow-up needs explicit wall-time caps per method and additional
seed replicates. If a routing rule by size band is proposed, hold contiguous
`N` ranges out of method selection and require repeatable gains there. Until
such a result exists, keep the incumbent as fallback at every `N` and let
audited candidate merging select any strict per-size gain independently.

## What was implemented

### Boundary-aware N+K deletion beam

`transfer_beam.py` tests deletion from larger donors using boundary/extreme
selection and bounded beam retention. `candidate_transfer_search.py` expands
this over public candidate corpora, deduplicating identical donor layouts by
content. A subset of a valid packing remains valid, so this branch isolates
cross-size cropping without introducing a repair bug.

Commands:

```bash
.venv/bin/python transfer_beam.py \
  data/public_external/kaggle_neighbour_transfer/submission_merged.csv \
  data/variants/submission.transfer_beam.smoke2.csv \
  --ns 10,50,100,232,500,983 --max-offset 4 --beam-width 4 --pool-limit 48
```

The larger targeted run used `--max-offset 12 --beam-width 8 --pool-limit 96`
over 89 hard sizes and 5,666 deduplicated public donor layouts. It found zero
improvement events in about 211 seconds.

### Topology-changing kicks

`topology_search.py` tests three branches:

- coherent contact-neighborhood translation/rotation;
- median seam/fault-line shear;
- compact destroy/reinsert followed by SLP repair.

Each branch used the same 11 target sizes, one deterministic trial, 12 repair
steps, and seed `20261027`. All three output files passed the full audit. The
branch records show only a few valid intermediate repairs and zero accepted
strict improvements.

### Rigid envelope rotation

`rotate_submission.py` searched 360 coarse angles and 41 local refinement
angles over the 90-degree symmetry interval for every size. It changed zero
layouts and passed the full audit.

## Important negative result

The existing bounded SLP adapter was also tried earlier on selected public
certificate layouts and produced no accepted improvements. A broader
multi-start SLP run was started, but the prototype's exact pairwise diagnostic
cost made the broad batch too slow; it was stopped before writing an output.
It must not be counted as a completed result.

## Remaining ideas not yet validated at competitive depth

These branches now have bounded smoke or pilot implementations, but they have
not been validated at a competitive search depth or compute budget:

1. fixed-container feasibility search with a stronger square-specific batched
   penalty and adaptive shrink/grow;
2. true buffered large-neighborhood repair that moves the surrounding shell,
   not only the deleted squares;
3. separator-branch flips at near-tied SAT faces;
4. low-dimensional diagonal-strip, block, frame, and fault-line construction
   search followed by SLP;
5. beam retention over multiple repaired descendants with a valid repair
   kernel rather than the current conservative fixed-L filter;
6. island populations with contact-graph diversity and aligned patch
   transplantation;
7. soft-to-rigid continuation and replica-exchange comparisons at equal
   compute;
8. a faster broadphase/batched SLP implementation with robust infeasible-state
   recovery so multi-start search can cover more structurally distinct seeds.

The first three are the most direct next experiments. They are more expensive
than the completed branches because they must move a surrounding feasible
buffer and solve genuine topology changes; they should be run only after a
faster repair kernel is available.

## Artifact and audit policy

Every completed output retains its CSV, sidecar provenance, method metadata,
and JSON audit report under `data/variants/`. The n=130-only candidate remains
separate at `data/variants/public_record_refresh_20261029/submission.csv`. The
combined public-union candidate was validated on Kaggle and its result is
recorded in `data/variants/kaggle_submission_results.md`.

## Current certified-row screen (2026-10-29)

The current report-order rows from Mishapolk's certificate registry were
screened against the best local candidate. The source manifest and census are
pinned by SHA-256 in
[issue #732](https://github.com/jlevy/squares/issues/732), and the later
[issue #742 intake](https://github.com/jlevy/squares/pull/742) identifies 77
current rows through `N=995`. Comparing their declared exact side lengths to
the serialized candidate's locally measured sides found no row that could
pass the merge gate's strict `1e-12` improvement threshold. No layouts were
changed. The screen details are retained at
`data/variants/mishapolk_registry_screen_20261029/registry_screen.json`.

The full candidate was freshly audited at **22.287085755423853** with zero
invalid puzzles and zero errors, then marked Complete by Kaggle at public score
**22.2870857554**. The uploaded file hash in the submission description
matched the local CSV.

