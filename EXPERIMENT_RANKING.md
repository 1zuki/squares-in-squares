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
| 1 | Incumbent neighbour-transfer portfolio | 1,000 sizes | 22.287265765408524 | 0 | yes | Current best |
| 1 | Boundary-aware deletion beam | 89 hard target sizes, 5,666 deduplicated public donors | 22.287265765408524 | 0 | yes | No accepted improvements |
| 1 | Contact-group kick + SLP repair | 11 target sizes, 1 deterministic trial each | 22.287265765408524 | 0 | yes | No accepted improvements |
| 1 | Seam/fault-line kick + SLP repair | 11 target sizes, 1 deterministic trial each | 22.287265765408524 | 0 | yes | No accepted improvements |
| 1 | Destroy/reinsert kick + SLP repair | 11 target sizes, 1 deterministic trial each | 22.287265765408524 | 0 | yes | No accepted improvements |
| 1 | Rigid whole-layout rotation | All 1,000 sizes, 360 coarse + 41 fine angles | 22.287265765408524 | 0 | yes | No envelope improvements |

The ties are exact at the audit score precision because every new candidate
was rejected and the complete output retained the incumbent layouts. The
serialized bytes differ for some files because the experiment writers use a
different decimal formatting path; the audits, rather than byte identity, are
the comparison gate.

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
and JSON audit report under `data/variants/`. No new candidate was promoted,
submitted, or used to overwrite the incumbent. Public submission history and
scores remain in `data/variants/kaggle_submission_results.md`.

