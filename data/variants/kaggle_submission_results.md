# Kaggle submission audit and score ledger

Competition: `squares-in-squares`
Quota history: 10 submissions were used on 2026-10-27. On 2026-10-29, the
submission form showed 10 remaining before the new upload; that candidate then
completed successfully. The strict per-`N` candidate was submitted for external
validation. On 2026-10-30, the form showed 9 remaining immediately before the
N=344 certificate refresh upload, then 8 before the combined N=182 + N=344
candidate, 7 after the issue #845 upload, and 6 after the issue #844 upload.

| Submission | Variant | Local audit | Public score | Status |
|---:|---|---:|---:|---|
| — | Issue #844 N=232/N=307 certificate refresh (SHA-256 b1e3a375de54) | 22.286193084713283 | 22.2861930847 | COMPLETE (2026-10-30) |
| — | Issue #845 N=172/204/260/293 certificate portfolio (SHA-256 cf726c180a8e) | 22.28639795912737 | 22.2863979591 | COMPLETE (2026-10-30) |
| — | N=182 + N=344 certificates (SHA-256 7af0e96af7f9) | 22.28684182148117 | 22.2868418214 | COMPLETE (2026-10-30) |
| — | CC0 N=344 certificate refresh (SHA-256 f424eb8c2637) | 22.287077114539976 | 22.2870771145 | COMPLETE (2026-10-30) |
| — | strict per-`N` public-union refresh + n=130 record (SHA-256 a930b7a9c82b) | 22.287085755423853 | 22.2870857554 | COMPLETE (2026-10-29) |
| 57700036 | public neighbour-transfer merged portfolio | 22.2872657654 | 22.2872657654 | COMPLETE |
| 57700871 | certificate control + public Kirill CPU/CUDA/MPS lab complete layouts | 22.2959148948 | 22.2959148947 | COMPLETE |
| 57700885 | certificate control + public A Square Deal verified packings | 22.2972606379 | 22.2972606378 | COMPLETE |
| 57700085 | public top-blend whole-layout portfolio | 22.2982307206 | 22.2982307205 | COMPLETE |
| 57700847 | certificate control + public CUDA packing-search complete layouts | 22.2999958177 | 22.2999958176 | COMPLETE |
| 57700275 | FTMC/MILP partial-donor portfolio over certificate control | 22.3064554966 | 22.3064554965 | COMPLETE |
| 57700902 | certificate control + public subset-transfer complete layouts | 22.3477395292 | 22.3477395291 | COMPLETE |
| 57700778 | certificate control + public Fault DP complete layouts | 22.3477395501 | 22.3477395501 | COMPLETE |
| 57697531 | public rational certificates + catalogue/control | 22.3477399461 | 22.3477399461 | COMPLETE |
| 57696917 | public catalogue SVG records + Goebel/diagonal-strip baseline | 23.2619312796 | 23.2619312796 | COMPLETE |

## Best completed public result

The issue #844 certificate portfolio is the best completed result at
`22.2861930847` (local audit `22.286193084713283`), improving the previous
Kaggle-complete result by `0.0002048744` and submission `57700036`
(`22.2872657654`) by `0.0010726807`. Its SHA-256 is
`b1e3a375de54e5b69c27b94570fb9603fcdd1c52a80f1e6c481589579d0cfc0a`.

## Latest submitted candidate

The issue #844 portfolio passed the complete local audit with score
`22.286193084713283`, zero invalid puzzles, and zero errors. It replaces only
N=232 and N=307 relative to the issue #845 candidate.
The uploaded CSV is
`data/variants/issue844_n232_n307_20261030/submission.csv`, with
SHA-256
`b1e3a375de54e5b69c27b94570fb9603fcdd1c52a80f1e6c481589579d0cfc0a`.
Kaggle marked the upload Complete at public score `22.2861930847`, matching
the local audit to displayed precision.

## Latest completed candidate

The issue #844 portfolio passed the complete local audit with score
`22.286193084713283`, zero invalid puzzles, and zero errors. Kaggle returned
public score `22.2861930847`, matching the local audit to displayed precision.
It layers Francisco Couzo's N=232 and N=307 certificates over the previously
validated issue #845 portfolio. The submitted file hash is
`b1e3a375de54e5b69c27b94570fb9603fcdd1c52a80f1e6c481589579d0cfc0a`.

## Audit record

All five new source portfolios were generated from the public certificate control with imported complete layouts, then serialized and checked by `audit_submission.py`. Each contains all 1,000 puzzle sizes and reports zero invalid puzzles. The source CSVs, converted candidate JSON, merge logs, `.sources.json`, SHA-256 values, and individual JSON audit reports are retained in `data/public_external/` and `data/variants/.`

Public source artifacts were used with attribution in the submission descriptions.
