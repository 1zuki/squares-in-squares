# Kaggle submission audit and score ledger

Competition: `squares-in-squares`
Quota history: 10 submissions were used on 2026-10-27. On 2026-10-29, the
submission form showed 10 remaining before the new upload; that candidate then
completed successfully. The strict per-`N` candidate was submitted for external
validation. On 2026-10-30, the form showed 9 remaining immediately before the
N=344 certificate refresh upload, then 8 before the combined N=182 + N=344
candidate.

| Submission | Variant | Local audit | Public score | Status |
|---:|---|---:|---:|---|
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

The combined N=182 + N=344 candidate is the best completed result at
`22.2868418214` (local audit `22.28684182148117`), improving the prior best by
`0.0002352931`. It is `0.0004239439` better than submission `57700036`
(`22.2872657654`). Kaggle marked it Complete. Its SHA-256 is
`7af0e96af7f9f5cafeb9db05ff7afc3775ec10cd8c72d7b7c00e9744d976b7cc`.

## Latest completed candidate

The combined N=182 + N=344 candidate passed the complete local audit with score
`22.28684182148117`, zero invalid puzzles, and zero errors. Kaggle returned
public score `22.2868418214`, matching the local audit to displayed precision.
The candidate uses Evan Daniel's N=182 certificate from
[issue #806](https://github.com/jlevy/squares/issues/806), plus the completed
N=344 refresh. The submitted file hash is
`7af0e96af7f9f5cafeb9db05ff7afc3775ec10cd8c72d7b7c00e9744d976b7cc`.

## Audit record

All five new source portfolios were generated from the public certificate control with imported complete layouts, then serialized and checked by `audit_submission.py`. Each contains all 1,000 puzzle sizes and reports zero invalid puzzles. The source CSVs, converted candidate JSON, merge logs, `.sources.json`, SHA-256 values, and individual JSON audit reports are retained in `data/public_external/` and `data/variants/.`

Public source artifacts were used with attribution in the submission descriptions.
