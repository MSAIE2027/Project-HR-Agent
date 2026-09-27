# Historical Evaluation Failure Report: Reconciliation

An earlier combined-folder report described legacy status mismatches, a full-evaluation score of 0.84 against a 0.90 threshold, and a missing POL-RW citation on a multi-document case. That report is historical and has been superseded by current local test/evaluation runs.

## What this checkout confirms

- The current golden case POL-04 expects both POL-RW and POL-SEC and two policy-search calls. The current route now returns both families.
- A 15-query read-only retrieval comparison now cited all expected families for all queries, including 5/5 multi-family probes.
- The six-item read-only policy golden slice scored 100% on status, citation-prefix, and groundedness-proxy checks.
- Runtime retrieval reported `huggingface_dense_cosine`, confirming the MiniLM dense cosine path during this run.
- Global top-five MMR λ=0.5 improved all-family coverage from 2/5 to 3/5 and family recall from 0.81 to 0.86.
- At the time of the original report, the full local suite and 25-case golden set passed; those saved reports were later refreshed. The current 82-test suite and 30-case golden reports are recorded in `../evidence/index.md` and `results*.md`. The first UI test run also exposed stale demo fixture assumptions and embedding environment variables; those were corrected and are documented in `docs/implementation-slices.md`.

## What remains unverified

The old 0.84 score is not the current result for this checkout. The suite now exercises workflow and confirmed local mock-action cases. The current evaluation and test report establish fixture alignment and deterministic behavior only; they do not prove independent semantic groundedness or hosted behavior. The local run is documented in `../evidence/index.md`.

The legacy status disagreements described in the prior report were stale relative to the current MSAIE golden-set contract. Do not change the rubric threshold or rewrite status behavior just to match obsolete fixtures.

For query-level coverage, MMR and route filters, see `retrieval-comparison.md`. Keep the historical diagnosis separate from the current full evaluation report.
# Historical retrieval figures in this report predate the 2026-09-26 corpus expansion. See `retrieval-comparison.md` and `ablation-results.md` for current results.
