# Historical Evaluation Failure Analysis

This note preserves the cause of an earlier evaluation mismatch. It is historical; current acceptance is reported in [`../evidence/index.md`](../evidence/index.md).

## What this checkout confirms

- The current golden case POL-04 expects both POL-RW and POL-SEC and two policy-search calls; the production route returns both families.
- The current retrieval comparison measures actual route behavior over 15 labeled queries and documents the limitations of the six-case read-only policy slice.
- The current full suite and 30-case transport evaluations are summarized in `../evidence/index.md` and `results*.md`.

## What remains unverified

The old 0.84 score is not the current result for this checkout. Current reports establish fixture alignment and deterministic behavior; they do not prove independent semantic groundedness or hosted behavior.

The earlier status disagreements came from fixtures that did not match the current MSAIE workflow contract. Query-level coverage, MMR, and routing results are in [`retrieval-comparison.md`](retrieval-comparison.md).
# Historical retrieval figures in this report predate the 2026-09-26 corpus expansion. See `retrieval-comparison.md` and `ablation-results.md` for current results.
