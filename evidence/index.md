# Evidence Index

This index distinguishes the current local working tree, hosted CI, the live Render build, and live OpenRouter completion evidence. The account-quota behavior at `a24154d` passed CI run [36331652047](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36331652047) and is live on Render deployment `dep-dasjuau0tbcc73fol7ig`. The ONNX working-tree change has not yet passed clean CI or been deployed. Hosted citation-bearing answer generation remains unverified.

## Current local evidence

| Claim | Evidence | Scope / limit |
|---|---|---|
| Test suite | Current local full suite: **99 passed**, one third-party Starlette/AnyIO deprecation warning | Clean CI for the ONNX dependency set is pending; tests do not verify live provider availability. |
| SQLite index release gate | Local gate passes for the pinned MiniLM repo/revision, ONNX backend, 384 dimensions, and 120/20 chunking | The same assertion is wired into CI and `render.yaml`; hosted build has not run for this candidate. |
| Golden-set evaluation | `evaluation/results.json`, `.md`, `results-stdio.json`, `.md` — **30 cases** per transport; workflow completion **5/5**; mean keyword score **0.95** in-process | Re-run locally on the ONNX index; deterministic orchestrator proxies; `llm_generation_included=false`; no independent semantic-judgment score. |
| In-process latency | Priming **733.66 ms**; warm 15-task p50/p95 **28.05/147.84 ms** | Local ONNX runtime; priming reported separately; not hosted latency. |
| Stdio latency | Priming **2,864.73 ms**; fresh-subprocess 15-task p50/p95 **1,723.99/1,857.45 ms** | Each task starts a fresh MCP process and loads the local ONNX model/index; not a Render cold-start benchmark. |
| MCP protocol | `scripts/smoke_mcp.py`, stdio golden report, `tests/test_mcp.py` | Official SDK client discovers and calls eight FastMCP tools over stdio. |
| Hosted-preflight CLI contract | `scripts/smoke_hosted_demo.py`, `tests/test_hosted_smoke_cli.py` | Local fake-server tests validate the public HTTP contract and sanitized output; they do not call Render or OpenRouter. |
| OpenRouter 429 fallback behavior | Public `/chat` regression tests in `tests/test_app.py` — **6 passed**; CI run [36331652047](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36331652047) | Account-wide free daily quota stops after one attempt; provider-scoped, structured/message-scoped model daily (including a named model), and unclassified 429s continue. `a24154d` is deployed. The most recent hosted request restarted before OpenRouter refinement; no hosted model is resolved. |
| Retrieval comparison and ablation | `evaluation/retrieval-comparison.md`, `evaluation/ablation-results.md`, `visuals/retrieval-comparison.svg` | Re-run on the pinned ONNX backend; hand-labeled, corpus-specific comparisons; chart is tracked and embedded in the GitHub README. |
| Embedding runtime parity | `docs/adr/0009-memory-bounded-huggingface-embeddings.md` | Four-query cosine similarity to FP32 Sentence Transformers ranged 0.991501–0.994461. This is a narrow representation check, not a broad semantic-quality result. |
| UI/API behavior | `tests/test_app.py`, `evidence/ui-review.md`, latest hosted read-only checks below | Local browser review, hosted landing-page status, read-only SQLite endpoints, and two no-tool privacy refusals; not a screen-reader or contrast audit. |
| Requirements and design | `specs/system-requirements.md`, `docs/traceability-matrix.md`, `docs/adr/`, `tickets/`, `docs/implementation-slices.md` | Maps project requirements to implementation and evidence. |

The golden reports measure expected status, tool calls, source families, safety, and keyword overlap. A 1.0 groundedness proxy is not a semantic entailment score. All timings exclude OpenRouter answer generation.

## Hosted evidence

Render service `Project-HR-Agent` is live at [project-hr-agent.onrender.com](https://project-hr-agent.onrender.com) on runtime SHA `a24154d` (deployment `dep-dasjuau0tbcc73fol7ig`). The quota-aware runtime passed CI run [36331652047](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36331652047). Render auto-deploy remains off. The live service's build command still contains the previous explicit PyTorch install/check and must be aligned with the repository's ONNX build command before deploying the candidate.

The latest live preflight returned HTTP 200 for two privacy refusals without MCP or LLM calls, then HTTP 502 on remote-work generation during the first hosted MiniLM query. Render logs showed the app process restart shortly after PyTorch model loading began, with no Python exception or explicit OOM record. This is consistent with low memory headroom but does not prove the restart cause. The request did not reach OpenRouter, `llm_refinement` did not report a resolved model, and PTO was not reached. An earlier hosted request reached the OpenRouter chain and received four 429s; the current hosted key's identity/quota is not exposed. The app withheld the retrieval draft. See [`hosted-pto-smoke.md`](hosted-pto-smoke.md).

The previous PyTorch deployment's thirty-second memory samples peaked at 536,264,700 bytes against the 536,870,900-byte service limit, then settled at 493,432,830 bytes. A later first-query attempt on the quota-aware runtime reached a 409 MB sample before restart. Neither observation proves a specific OOM event or multi-request capacity; the low margin motivated the pinned ONNX runtime change.

**Recording gates:** require a hosted synthetic PTO answer with `check_pto_balance`, policy citations, `llm_refinement.status=completed`, the actual resolved model, and no reasoning leakage. The last run failed before OpenRouter during model loading. Align Render's live build command to `render.yaml`, deploy the CI-passing ONNX SHA, and retest the model chain. The private GitHub repo's permission check reports `quantic-grader=none`; course-grader read access is still needed. The course recording and submission remain presenter-owned.
