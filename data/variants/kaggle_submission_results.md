# Kaggle submission audit and score ledger

Competition: `squares-in-squares`
Quota history: 10 submissions were used on 2026-10-27. On 2026-10-29, the
submission form showed 10 remaining before the new upload; that candidate then
completed successfully. The strict per-N candidate was submitted for external
validation. On 2026-10-30, the form showed 9 remaining immediately before the
N=344 certificate refresh upload, then 8 before the combined N=182 + N=344
candidate, 7 after the issue #845 upload, 6 after the issue #844 upload, 4
after the issue #846 upload, 3 after the first Mishapolk portfolio, and 2
after the N=507/N=654 refresh. The form showed 2 remaining before the Couzo
refresh upload, leaving 1 remaining. The final slot was used for the clearance
tightening candidate; Kaggle completed it with a materially worse public score.
The Couzo refresh remains the auto-selection incumbent.

| Submission | Variant | Local audit | Public score | Status |
|---:|---|---:|---:|---|
| — | Couzo clearance tightening (SHA-256 5117c9682675) | 22.28605090173753 | 26.1695943166 | COMPLETE, rejected for promotion (2026-10-30; exact download SHA matched) |
| — | Couzo full-catalogue refresh (SHA-256 a45f2c5da138) | 22.28605099922317 | 22.2860509992 | COMPLETE (2026-10-30; displayed tie) |
| — | Mishapolk N=507/N=654 refresh (SHA-256 1b07f3159185) | 22.286050999280988 | 22.2860509992 | COMPLETE (2026-10-30; displayed tie) |
| — | Mishapolk 125-certificate portfolio (SHA-256 9dbf43f6d7a0) | 22.286050999282253 | 22.2860509992 | COMPLETE (2026-10-30; displayed tie with issue #846) |
| — | Issue #846 N=299 certificate (SHA-256 f75e108be03d) | 22.28605099928466 | 22.2860509992 | COMPLETE (2026-10-30) |
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

The Couzo full-catalogue refresh is the best local-audit and completed public
result at 22.28605099922317 / 22.2860509992. It improves the completed
Mishapolk N=507/N=654 portfolio by 5.781686240879935e-11 while tying its
displayed public score. Its SHA-256 is
a45f2c5da138a7316921576f75068a6dbcd325f3950e89d40530f4bc909f4114.
## Latest submitted candidate

The clearance-tightened CSV passed two local audits with score
22.28605090173753, zero invalid puzzles, and zero errors. The uploaded file is
data/variants/couzo_clearance_tighten_20261030/submission.csv, with SHA-256
5117c9682675b181c4da645e2e1f56c264101ba59f229cffcff02ad900f20119. Kaggle
downloaded the exact same bytes and marked it Complete at public score
26.1695943166, so it was rejected for promotion.

## Latest completed candidate

The Couzo full-catalogue refresh passed the complete local audit with score
22.28605099922317, zero invalid puzzles, and zero errors. Kaggle returned
public score 22.2860509992, tying the prior certificate portfolios at
displayed precision. It strictly improves 60 serialized per-N layouts over the
Mishapolk N=507/N=654 incumbent. The submitted file hash is
a45f2c5da138a7316921576f75068a6dbcd325f3950e89d40530f4bc909f4114.
## Final slot decision

The post-Couzo audit-corpus screen found only an older neighbour-transfer
`N=147` replacement. Its complete merge score was `22.286050999222418`, a
`7.531752999057062e-13` gain over the Couzo incumbent, so it was not uploaded.
The final daily slot was spent on clearance tightening, which Kaggle rejected
by returning 26.1695943166. A positive-clearance re-dilation is prepared locally
at `data/variants/couzo_clearance_redilate_20261030/submission.csv` with
score 22.286050902697255 and SHA-256
359c422da0ed93998647661d630e18323939554449c2a08588e6a28bcd72eb7d. Keep the
Couzo refresh as the final auto-selected incumbent and submit the prepared file
only after the next slot is available.

## Audit record

All seven new source portfolios were generated from the public certificate control with imported complete layouts, then serialized and checked by `audit_submission.py`. Each contains all 1,000 puzzle sizes and reports zero invalid puzzles. The source CSVs, converted candidate JSON, merge logs, `.sources.json`, SHA-256 values, and individual JSON audit reports are retained in `data/public_external/` and `data/variants/.`

Public source artifacts were used with attribution in the submission descriptions.
