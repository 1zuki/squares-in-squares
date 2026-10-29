# Remaining idea experiments and ranking

Date: 2026-10-27

## Baseline and interpretation

The current incumbent is:

data/variants/couzo_full_refresh_20261030/submission.csv

Its independently audited score is **22.28605099922317**, with zero invalid
puzzles and zero audit errors. Kaggle marked the upload Complete at
22.2860509992, tied at displayed precision with the prior certificate
portfolios while improving the local audit by `5.781686240879935e-11`. Local
audit ranking is a valid screen for these deterministic, complete-file
experiments, but it is not proof that every future search candidate will
reproduce on Kaggle.

## Ranking

Lower is better.

| Rank | Experiment | Scope | Local score | Delta vs incumbent | Valid | Result |
|---:|---|---|---:|---:|---:|---|
| 1 | Couzo full-catalogue refresh | 60 strict serialized per-N replacements over the Mishapolk N=507/N=654 incumbent | 22.28605099922317 | -0.00000000005782 | yes | Kaggle Complete: 22.2860509992 (tie at displayed precision) |
| 2 | Mishapolk N=507/N=654 refresh | Two serialized certificate improvements over the 125-certificate portfolio | 22.286050999280988 | 0 | yes | Kaggle Complete: 22.2860509992 (tie at displayed precision) |
| 3 | Mishapolk 125-certificate portfolio | 125 public certificates merged over the issue #846 incumbent | 22.286050999282253 | +0.00000000000126 | yes | Kaggle Complete: 22.2860509992 |
| 4 | Issue #846 N=299 certificate | 69 sizes improve; issue #844 portfolio plus the N=299 replacement | 22.28605099928466 | +0.00000000000367 | yes | Kaggle Complete: 22.2860509992 |
| 5 | Issue #844 N=232/N=307 refresh | 68 sizes improve; public union plus N=182, N=344, N=172, N=204, N=260, N=293, N=232, and N=307 replacements | 22.286193084713283 | +0.00014208543229 | yes | Kaggle Complete: 22.2861930847 |
| 6 | Issue #845 certificates | 66 sizes improve; public union plus N=182, N=344, N=172, N=204, N=260, and N=293 replacements | 22.28639795912737 | +0.00034695984638 | yes | Kaggle Complete: 22.2863979591 |
| 7 | N=182 + N=344 certificate portfolio | 62 sizes improve; public union plus two certificate replacements | 22.28684182148117 | +0.00079082220018 | yes | Kaggle Complete: 22.2868418214 |
| 8 | CC0 N=344 certificate refresh | 61 sizes improve; adds N=344 to the previous portfolio | 22.287077114539976 | +0.00102611525899 | yes | Kaggle Complete: 22.2870771145 |
| 9 | Strict per-N union plus refreshed record | 60 sizes improve; 59 union layouts plus N=130 | 22.287085755423853 | +0.00103475614286 | yes | Kaggle Complete: 22.2870857554 |
| 9 | Incumbent neighbour-transfer portfolio | 1,000 sizes | 22.287265765408524 | +0.00121476612754 | yes | Previous public incumbent |
| 9 | Boundary-aware deletion beam | 89 hard target sizes, 5,666 deduplicated public donors | 22.287265765408524 | +0.00121476612754 | yes | No accepted improvements |
| 9 | Contact-group kick + SLP repair | 11 target sizes, 1 deterministic trial each | 22.287265765408524 | +0.00121476612754 | yes | No accepted improvements |
| 9 | Seam/fault-line kick + SLP repair | 11 target sizes, 1 deterministic trial each | 22.287265765408524 | +0.00121476612754 | yes | No accepted improvements |
| 9 | Destroy/reinsert kick + SLP repair | 11 target sizes, 1 deterministic trial each | 22.287265765408524 | +0.00121476612754 | yes | No accepted improvements |
| 9 | Rigid whole-layout rotation | All 1,000 sizes, 360 coarse + 41 fine angles | 22.287265765408524 | +0.00121476612754 | yes | No envelope improvements |

The negative-result experiments tie the previous public incumbent because
their candidates were rejected and their complete outputs retained its layouts.
The Couzo refresh is now the local-audit and Kaggle-completed leader, with a
strict gain of 5.781686e-11 over the Mishapolk N=507/N=654 portfolio. Kaggle
returned 22.2860509992, a displayed-precision tie with the completed
certificate portfolios.
The serialized bytes differ for some files because experiment writers use
different decimal formatting; audits and layout comparisons, rather than byte
identity, are the comparison gate.

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

### New CC0 N=344 certificate (2026-10-30)

Public [issue #819](https://github.com/jlevy/squares/issues/819) reports an
Amund Kristiansen CC0 certificate for `N=344`, with exact side
`9496283772422138783772412642309/500000000000000000000000000000`
(`18.99256754484427`). The pinned certificate at
`data/variants/issue819_n344_20261030/s344_amund.cert` matches the published
SHA-256 `4e2c6880812a688a64c8f378f5feb27a8a1a362f0d9161c0cda201f444526e21`
and passed local parsing and geometry validation. The current `N=344` layout
had side `18.992727809382128`; the imported layout measures
`18.992567544843062` in float64.

The strict per-`N` merge accepted only `N=344`. The complete 1,000-layout
candidate at `data/variants/issue819_n344_20261030/submission.csv` passed
`audit_submission.py` with score `22.287077114539976`, zero invalid puzzles,
and zero errors, improving the previous local best by
`0.000008640883877`. Its SHA-256 is
`f424eb8c2637a344403d608a4447949b9b6b299d49cef4b5b1dabc36e5eda726`.
Kaggle marked the upload Complete at public score `22.2870771145`, matching
the local audit.

### New N=182 certificate (2026-10-30)

Public [issue #806](https://github.com/jlevy/squares/issues/806) reports Evan
Daniel's N=182 certificate at exact side
`13970916436214678735385725854133/10^30`
(`13.970916436214678735385725854133`). The pinned file from
[`evand/square-packing` commit `d99925d`](https://github.com/evand/square-packing/blob/d99925d1298262c4ddb81c95abbb6f45adca8d3d/search/packer/candidates/s182-1024.cert)
matches the issue's SHA-256
`9e12e0a42b05c4fcd2181c5255a4a19ab1aeb9a9f8c95f9943a20998a415fe97`. The
issue records two exact verifiers and an independent clean-room review; the
pinned source repository is [MIT licensed](https://github.com/evand/square-packing/blob/d99925d1298262c4ddb81c95abbb6f45adca8d3d/LICENSE).
Evan Daniel credits the start as Francisco Couzo's N=211 arrangement, designed
by Daniil Ostashev.

Local parsing and geometry validation passed. The incumbent side was
`13.974090713134416`; the imported side measures `13.97091643621468` from the
certificate and `13.97091643622765` after CSV serialization. The combined
strict merge changed only N=182 relative to the N=344 candidate. Its complete
1,000-layout audit passed at `22.28684182148117`, with zero invalid puzzles
and zero errors, a gain of `0.000235293058807` over the N=344 candidate. The
CSV at `data/variants/issue806_n182_20261030/submission.csv` has SHA-256
`7af0e96af7f9f5cafeb9db05ff7afc3775ec10cd8c72d7b7c00e9744d976b7cc`.
Kaggle marked it Complete at public score `22.2868418214`, matching the local
audit to the displayed precision.

### Issue #845 certificate portfolio (2026-10-30)

Public [issue #845](https://github.com/jlevy/squares/issues/845) reports four
new certificate packings at N=172, 204, 260, and 293. The pinned files from
[`evand/square-packing` commit `d2d5dd96`](https://github.com/evand/square-packing/commit/d2d5dd96cfdbded476050f8ba8577773a91c6ac1)
match the published hashes:

| N | Certificate side | SHA-256 |
|---:|---:|---|
| 172 | 13.6179356983814154 | `1e16ad2789538610a42ebec7f735d932fdbe8125a7c991801e644b6f072352b9` |
| 204 | 14.8076274718815796 | `2b371e81d568ad5c4490257dcfdb87cd1e238232bb60bd1ece4844340af0a2c3` |
| 260 | 16.633982502121884 | `d6d6f45f600f6552416ea3708d8ee04416cfe88820ee4c3c422d8e131d7cdf87` |
| 293 | 17.633982502122782 | `236bc05f057a28df402c09453f4ccce35d63b518f4f0305419889612f07c42bc` |

All four certificates parsed and passed local geometry validation. A targeted
strict merge changed only those four sizes relative to the N=182 + N=344
portfolio; the 500,500-row output passed `audit_submission.py` at
`22.28639795912737`, with zero invalid puzzles and zero errors. The local gain
over the previous Kaggle-complete candidate is `0.00044386235380`. The
candidate is `data/variants/issue845_n172_204_260_293_20261030/submission.csv`
with SHA-256
`cf726c180a8e7886ecd94a26fb5a0dd0ffacccc2fb37547764df32e5321c3f49`.
The source repository is MIT licensed; the Kaggle description records Evan
Daniel and issue #845 attribution. Kaggle marked the upload Complete at public
score `22.2863979591`, matching the local audit to displayed precision.

### Issue #844 N=232 and N=307 certificate refresh (2026-10-30)

Public [issue #844](https://github.com/jlevy/squares/issues/844) reports
independently checked certificates at N=232, N=260, and N=307. The N=260
record is weaker than the issue #845 N=260 certificate, so only N=232 and
N=307 were screened further. The pinned files from
[`franciscouzo/square-packing` commit `712c6a6`](https://github.com/franciscouzo/square-packing/commit/712c6a6e9ef58a9521784e6b7e236af813422de7)
match the published hashes:

| N | Certificate side | SHA-256 |
|---:|---:|---|
| 232 | 15.7616617594813299 | `23b035c34a5a93a3bf23eccaddc49e8d6e5e4003ec5e97c036153b2ca5ddbe54` |
| 307 | 17.9792512836880252 | `1fd01ff42e7679f1e5b2c8eb8af59e51d3cca0392772b81bb4d78d67a26214e9` |

Both certificates parsed and passed local geometry validation. A targeted
strict merge changed only N=232 and N=307 relative to the issue #845
portfolio; the complete audit passed at `22.286193084713283`, with zero
invalid puzzles and zero errors. This is a local gain of `0.00020487441409`
over the previous Kaggle-complete candidate. The candidate is
`data/variants/issue844_n232_n307_20261030/submission.csv` with SHA-256
`b1e3a375de54e5b69c27b94570fb9603fcdd1c52a80f1e6c481589579d0cfc0a`.
Kaggle marked the upload Complete at public score `22.2861930847`, matching the
local audit to displayed precision. The source repository has no repository-
wide LICENSE file at the pinned commit; its verifier license is MIT, and the
candidate record preserves the issue's Francisco Couzo and starting-source
credits.

### Issue #846 N=299 certificate (2026-10-30)

The latest public candidate commit in [`evand/square-packing`](https://github.com/evand/square-packing/commit/0e76d9fe5e48fc2a614e3c132a0a3fd67e0a6a8d)
adds `s299_1028.cert` with declared side
`17.801238549388584085`; its commit message identifies it as an update to
`jlevy#824` with a KKT certificate. The published certificate hash is
`ccb323dd6d69bee141d59cae4c605f45136b998dfecce1248e200b678b253db5`, and the
source repository is MIT licensed.

The certificate parsed and passed local geometry validation. A targeted strict
merge changed only N=299 relative to the issue #844 portfolio; the serialized
side is `17.801238549405387`. The complete 500,500-row audit passed at
`22.28605099928466`, with zero invalid puzzles and zero errors, a local gain of
`0.00014208542862` over the previous Kaggle-complete candidate. The candidate
is `data/variants/issue846_n299_20261030/submission.csv` with SHA-256
`f75e108be03d7d248618a868feaa2817f74678c94af93cdda5690b733afae109`. Kaggle
marked the upload Complete at public score `22.2860509992`, matching the local
audit to displayed precision.

### Mishapolk 125-certificate portfolio (2026-10-30)

The public [`Mishapolk/square-packing-records`](https://github.com/Mishapolk/square-packing-records/tree/ab8e8337cb91ac24254fe4dc09514ce4bfee2862) registry was screened against the issue #846 audit. I selected 125 certificates whose declared exact side was strictly smaller by more than `1e-12`, independently validated every imported geometry, and merged only valid replacements.

The complete 500,500-row audit passed at `22.286050999282253`, with zero invalid puzzles and zero errors. The local gain over issue #846 is `2.407407e-12`; only a handful of the selected rows contribute above serialization noise. The candidate is `data/variants/mishapolk_20261030/submission.csv` with SHA-256 `9dbf43f6d7a0750d5a82f7caef482892cefd88621a8060427db5bb86088408a6`. Kaggle marked the upload Complete at public score `22.2860509992`, tied with issue #846 at displayed precision. The source repository is MIT licensed, and its manifest records the certificate checksums and attribution.

### Mishapolk N=507/N=654 certificate refresh (2026-10-30)

After the first 125-certificate portfolio, the complete 531-record public registry was screened again. 178 declarations were strictly below the current measured sides; after independent geometry validation and serialization, only N=507 and N=654 produced strict measured improvements. Replacing those two layouts lowered the complete 500,500-row audit to 22.286050999280988, with zero invalid puzzles and zero errors.

The local gain over the 125-certificate portfolio is 1.264766e-12. The candidate is data/variants/mishapolk_n507_n654_20261030/submission.csv with SHA-256 1b07f3159185f05b275f857dcc587212ae23277d6ab623f5acf74bc8c8417336a. Kaggle marked the upload Complete at public score 22.2860509992, tied with the prior certificate portfolios at displayed precision. The source certificates and their hashes are retained in the candidate manifest.

### Couzo full-catalogue refresh (2026-10-30)

The parsed best-certificate catalogue from the public [Francisco Couzo
square-packing repository](https://github.com/franciscouzo/square-packing/tree/712c6a6e9ef58a9521784e6b7e236af813422de7), pinned at commit
`712c6a6e9ef58a9521784e6b7e236af813422de7` (MIT), was compared against the
Mishapolk N=507/N=654 incumbent. After independent geometry validation and
CSV serialization, 60 sizes had a measured side strictly smaller by more than
`1e-12`; every other size retained the incumbent layout.

The complete 500,500-row candidate passed `audit_submission.py` twice at
`22.28605099922317`, with zero invalid puzzles and zero errors. This is a
strict local gain of `5.781686240879935e-11`. The candidate is
`data/variants/couzo_full_refresh_20261030/submission.csv` with SHA-256
`a45f2c5da138a7316921576f75068a6dbcd325f3950e89d40530f4bc909f4114`. It was
submitted to Kaggle and marked Complete at public score `22.2860509992`, tied
at displayed precision with the completed certificate portfolios. The selected
records, side-by-side comparison, source catalogue digest, and audit are
retained in the variant directory.

### Final audited-corpus screen (2026-10-30)

After the Couzo refresh completed, I compared every complete zero-error audit
file already present in the workspace against the new incumbent. The only
distinct strict per-size replacement was an older neighbour-transfer layout at
`N=147`; it lowers that side by `9.155343150268891e-12`, but the complete
merged audit improves the total score by only `7.531752999057062e-13` to
`22.286050999222418`. This is below the prior strict score gain and produces
no displayed Kaggle-score change, so the final daily submission slot remains
unused.

### Additional certificate screen (2026-10-30)

I compared all 23 rounded-up side bounds in [issue #607](https://github.com/jlevy/squares/issues/607)
with the audited candidate's sides. Only N=342 remains a possible smaller
layout: its reported bound is `18.964706723173`, versus the current measured
side `18.964706723190364`, a difference of about `1.7e-11`. The implied score
change is below `1e-12`, far below Kaggle's displayed precision of `1e-10`, so
this certificate was not imported or submitted. The other displayed bounds
cannot clear the strict per-size merge gate.

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

