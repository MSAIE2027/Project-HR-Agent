# Reported Evaluation Failures: Current Diagnosis

The earlier combined-folder report described legacy status mismatches, a full-evaluation score of 0.84 against a 0.90 threshold, and a missing POL-RW citation on a multi-document case.

## What this checkout confirms

- The current golden case POL-04 expects both POL-RW and POL-SEC and two policy-search calls. The current route now returns both families.
- A 15-query read-only retrieval comparison now cited all expected families for all queries, including 5/5 multi-family probes.
- The six-item read-only policy golden slice scored 100% on status, citation-prefix, and groundedness-proxy checks.
- Runtime retrieval reported `huggingface_dense_cosine`, confirming the MiniLM dense cosine path during this run.
- Global top-five MMR λ=0.5 improved all-family coverage from 2/5 to 3/5 and family recall from 0.81 to 0.86.

## What remains unverified

The full 0.84 result was not reproduced because the full golden set includes workflow and confirmed mock-action cases, which remain outside the authorized verification scope. Therefore the failing IDs and exact numerator/denominator cannot be stated from current evidence. Pytest and transaction/action scenarios were not run.

The legacy status disagreements described in the prior report are not a reason to change current status behavior. The current golden set encodes the MSAIE status contract; reconcile any old fixture only after identifying its exact test and product requirement. Do not change the 0.90 threshold or rewrite statuses to make an obsolete suite pass.

For query-level coverage, MMR and route filters, see evaluation/retrieval-comparison.md. The read-only comparison is retrieval evidence, not a replacement for the unrun full evaluation.
