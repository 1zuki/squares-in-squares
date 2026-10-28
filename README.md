# Squares in Squares solver

This repository contains a reproducible, attribution-aware baseline for the
Kaggle **Squares in Squares** competition.

The first implementation follows the highest-confidence path from `IDEAS.md`:

1. generate deterministic grid and Göbel-style seeds;
2. fetch and parse public catalogue SVG records;
3. independently validate candidate packings with oriented-square SAT;
4. merge the best complete packing per `N`;
5. propagate useful layouts with drop-a-square and L-extension passes;
6. audit the exact serialized CSV before any upload.

The public catalogue is maintained by David Ellsworth:
<https://kingbird.myphotos.cc/packing/squares_in_squares.html>.
The parser uses only the public SVG geometry and records its source URL and
hashes in `data/public_records/manifest.json`.

## Local run

```bash
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python build_submission.py data/submission.base.csv
./.venv/bin/python fetch_public_records.py
./.venv/bin/python parse_public_records.py data/public_records/svg data/public_records/records.json
./.venv/bin/python merge_submission.py data/submission.base.csv data/submission.records.csv data/public_records/records.json
./.venv/bin/python audit_submission.py data/submission.records.csv --report data/submission.records.audit.json
```

The audit must report zero invalid puzzles before an upload is considered.
The current environment may still lack Kaggle authentication; the project does
not store or print credentials.
