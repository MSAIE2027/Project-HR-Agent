# MiniLM Top-k, Routing, MMR, and Weight Comparison

Retrieval-only experiment. MiniLM (384 dimensions), onnxruntime-quint8-avx2 from pinned HF revision 1110a243fdf4706b3f48f1d95db1a4f5529b4d41, 120/20 chunks, corpus, and query labels are fixed. No pytest, LLM generation, employee lookups, or action tools are used.

Queries: 15 total; 5 multi-family. Index chunks: 182.

Independent scoring matched production top-5 order on 15/15 queries and matched its top-10 candidate set on 15/15.

## Global top-k and ranking weights

| Ranker | k | Hit@k | Family recall@k | All-family coverage@k | Multi-family all-family@k | Unique docs | Unique sections |
|---|---:|---:|---:|---:|---:|---:|---:|
| Current | 1 | 1.00 | 0.71 | 0.67 | 0.00 | 1.00 | 1.00 |
| Current | 3 | 1.00 | 0.76 | 0.73 | 0.20 | 1.13 | 3.00 |
| Current | 5 | 1.00 | 0.76 | 0.73 | 0.20 | 1.27 | 5.00 |
| Current | 8 | 1.00 | 0.81 | 0.80 | 0.40 | 1.93 | 8.00 |
| Dense only | 1 | 1.00 | 0.71 | 0.67 | 0.00 | 1.00 | 1.00 |
| Dense only | 3 | 1.00 | 0.76 | 0.73 | 0.20 | 1.27 | 3.00 |
| Dense only | 5 | 1.00 | 0.76 | 0.73 | 0.20 | 1.33 | 5.00 |
| Dense only | 8 | 1.00 | 0.81 | 0.73 | 0.20 | 2.13 | 8.00 |
| Cosine 0.5x | 1 | 1.00 | 0.71 | 0.67 | 0.00 | 1.00 | 1.00 |
| Cosine 0.5x | 3 | 1.00 | 0.76 | 0.73 | 0.20 | 1.13 | 3.00 |
| Cosine 0.5x | 5 | 1.00 | 0.76 | 0.73 | 0.20 | 1.27 | 5.00 |
| Cosine 0.5x | 8 | 1.00 | 0.81 | 0.80 | 0.40 | 1.73 | 8.00 |
| Cosine 2x | 1 | 1.00 | 0.71 | 0.67 | 0.00 | 1.00 | 1.00 |
| Cosine 2x | 3 | 1.00 | 0.76 | 0.73 | 0.20 | 1.13 | 3.00 |
| Cosine 2x | 5 | 1.00 | 0.76 | 0.73 | 0.20 | 1.27 | 5.00 |
| Cosine 2x | 8 | 1.00 | 0.76 | 0.73 | 0.20 | 1.87 | 8.00 |
| Lexical 2x | 1 | 1.00 | 0.71 | 0.67 | 0.00 | 1.00 | 1.00 |
| Lexical 2x | 3 | 1.00 | 0.76 | 0.73 | 0.20 | 1.13 | 3.00 |
| Lexical 2x | 5 | 1.00 | 0.76 | 0.73 | 0.20 | 1.27 | 5.00 |
| Lexical 2x | 8 | 1.00 | 0.81 | 0.80 | 0.40 | 1.73 | 8.00 |

## MMR

| Method | k | Hit@k | Family recall@k | All-family coverage@k | Multi-family all-family@k | Unique docs | Unique sections |
|---|---:|---:|---:|---:|---:|---:|---:|
| MMR lambda=0.7, top-10 pool | 1 | 1.00 | 0.71 | 0.67 | 0.00 | 1.00 | 1.00 |
| MMR lambda=0.7, top-10 pool | 3 | 1.00 | 0.76 | 0.73 | 0.20 | 1.13 | 3.00 |
| MMR lambda=0.7, top-10 pool | 5 | 1.00 | 0.76 | 0.73 | 0.20 | 1.33 | 5.00 |
| MMR lambda=0.7, top-10 pool | 8 | 1.00 | 0.81 | 0.80 | 0.40 | 2.00 | 8.00 |
| MMR lambda=0.5, top-10 pool | 1 | 1.00 | 0.71 | 0.67 | 0.00 | 1.00 | 1.00 |
| MMR lambda=0.5, top-10 pool | 3 | 1.00 | 0.81 | 0.80 | 0.40 | 1.33 | 3.00 |
| MMR lambda=0.5, top-10 pool | 5 | 1.00 | 0.81 | 0.80 | 0.40 | 1.40 | 5.00 |
| MMR lambda=0.5, top-10 pool | 8 | 1.00 | 0.81 | 0.80 | 0.40 | 2.00 | 8.00 |

## Current application route

Actual route coverage: expected families cited for 100% of all queries and 100% of multi-family queries; expected-family recall 100%. Runtime retrieval: huggingface_dense_cosine.

| Query | Expected families | Actual filters | Cited documents | Complete | Status |
|---|---|---|---|---|---|
| remote_days | POL-RW- | POL-RW- | POL-RW-01, POL-RW-01, POL-RW-01, POL-RW-01, POL-RW-01 | yes | completed |
| security_access | POL-SEC- | POL-SEC- | POL-SEC-01, POL-SEC-01, POL-SEC-01, POL-SEC-01, POL-SEC-01 | yes | completed |
| pto_carryover | POL-PTO- | POL-PTO- | POL-PTO-01, POL-PTO-01, POL-PTO-01, POL-PTO-01, POL-PTO-01 | yes | completed |
| benefit_enrolment | POL-BEN- | POL-BEN- | POL-BEN-01, POL-BEN-01, POL-BEN-01, POL-BEN-01, POL-BEN-01 | yes | completed |
| conduct_escalation | POL-CON- | POL-CON- | POL-CON-01, POL-CON-01, POL-CON-01, POL-CON-01 | yes | escalated |
| expense_receipts | POL-EXP- | POL-EXP- | POL-EXP-01, POL-EXP-01, POL-EXP-01, POL-EXP-01, POL-EXP-01 | yes | completed |
| service_ticket | POL-SVC- | POL-SVC- | POL-SVC-01, POL-SVC-01, POL-SVC-01, POL-SVC-01, POL-SVC-01 | yes | completed |
| approval_matrix | POL-APR- | POL-APR- | POL-APR-01, POL-APR-01, POL-APR-01, POL-APR-01, POL-APR-01 | yes | completed |
| employment_classification | POL-ONB- | POL-ONB- | POL-ONB-01, POL-ONB-01, POL-ONB-01, POL-ONB-01, POL-ONB-01 | yes | completed |
| medical_leave | POL-LVE- | POL-LVE- | POL-LVE-01, POL-LVE-01, POL-LVE-01, POL-LVE-01, POL-LVE-01 | yes | completed |
| international_confidential_data | POL-RW-, POL-SEC- | POL-SEC-, POL-RW- | POL-SEC-01, POL-RW-01, POL-RW-01, POL-RW-01, POL-SEC-01 | yes | completed |
| international_approval_controls | POL-RW-, POL-SEC-, POL-APR- | POL-SEC-, POL-APR-, POL-RW- | POL-SEC-01, POL-APR-01, POL-RW-01, POL-RW-01, POL-RW-01 | yes | completed |
| expense_approval | POL-EXP-, POL-APR- | POL-EXP-, POL-APR- | POL-EXP-01, POL-APR-01, POL-EXP-01, POL-EXP-01, POL-APR-01 | yes | completed |
| leave_record_privacy | POL-LVE-, POL-REC- | POL-LVE-, POL-REC- | POL-LVE-01, POL-REC-01, POL-LVE-01, POL-LVE-01, POL-REC-01 | yes | completed |
| benefit_exception_records | POL-BEN-, POL-REC- | POL-BEN-, POL-REC- | POL-BEN-01, POL-REC-01, POL-BEN-01, POL-BEN-01, POL-REC-01 | yes | completed |

## Read-only golden policy slice

6 policy QA cases were evaluated with the same rubric, separately from workflow/action cases: status accuracy 100%, citation-prefix accuracy 100%, groundedness proxy 100%.

| Golden item | Status | Citation IDs | Citation pass | Keyword score | Groundedness pass |
|---|---|---|---|---:|---|
| POL-01 | completed (yes) | POL-PTO-01, POL-PTO-01, POL-PTO-01, POL-PTO-01, POL-PTO-01 | yes | 1.00 | yes |
| POL-02 | completed (yes) | POL-EXP-01, POL-EXP-01, POL-EXP-01, POL-EXP-01, POL-EXP-01 | yes | 1.00 | yes |
| POL-03 | completed (yes) | POL-BEN-01, POL-BEN-01, POL-BEN-01, POL-BEN-01, POL-BEN-01 | yes | 1.00 | yes |
| POL-04 | completed (yes) | POL-SEC-01, POL-RW-01, POL-RW-01, POL-RW-01, POL-SEC-01 | yes | 0.50 | yes |
| POL-05 | completed (yes) | POL-SEC-01, POL-SEC-01, POL-SEC-01, POL-SEC-01, POL-SEC-01 | yes | 1.00 | yes |
| POL-06 | completed (yes) | POL-SVC-01, POL-SVC-01, POL-SVC-01, POL-SVC-01, POL-SVC-01 | yes | 1.00 | yes |

## Limits

The hand-authored query set is small and its labels are not independent semantic judgments. Global MMR and score-weight comparisons are retrieval diagnostics, not answer-correctness judgments. Production now uses the pinned ONNX MiniLM backend, lambda 0.5 MMR over the score-ranked top ten, one seed per explicitly routed family, and a five-citation limit. This experiment fixes the embedding model/backend and 120/20 chunks while varying ranking and routing choices. Reassess on a larger independently reviewed query set and latency measurements.
