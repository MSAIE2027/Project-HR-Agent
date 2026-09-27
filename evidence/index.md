# Evidence Index

This index distinguishes the published source, hosted CI, the live Render build, and live OpenRouter completion evidence. Runtime `eeceda7` passed CI run [36336569726](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36336569726) and is live on Render deployment `dep-dasl2lh7lnhs739ltkb0`. The first hosted request completed ONNX retrieval and MCP checks, but OpenRouter's account-wide free quota returned 429 on Qwen; citation-bearing answer completion remains unverified.

## Current local evidence

| Claim | Evidence | Scope / limit |
|---|---|---|
| Test suite | **99 passed** in local verification and CI run [36336569726](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36336569726), one third-party Starlette/AnyIO deprecation warning locally | Tests do not verify live provider availability. |
| SQLite index release gate | Exact MiniLM repo/revision, ONNX backend, 384 dimensions, and 120/20 chunking pass in CI and the live Render build | Hosted `/health` also reports the pinned semantic index. |
| Golden-set evaluation | `evaluation/results.json`, `.md`, `results-stdio.json`, `.md` — **30 cases** per transport; workflow completion **5/5**; mean keyword score **0.95** in-process | Deterministic orchestrator proxies; `llm_generation_included=false`; no independent semantic-judgment score. |
| In-process latency | Priming **733.66 ms**; warm 15-task p50/p95 **28.05/147.84 ms** | Local ONNX runtime; priming reported separately; not hosted latency. |
| Stdio latency | Priming **2,864.73 ms**; fresh-subprocess 15-task p50/p95 **1,723.99/1,857.45 ms** | Each task starts a fresh MCP process and loads the local ONNX model/index; not a Render cold-start benchmark. |
| MCP protocol | `scripts/smoke_mcp.py`, stdio golden report, `tests/test_mcp.py` | Official SDK client discovers and calls eight FastMCP tools over stdio. |
| Hosted-preflight CLI contract | `scripts/smoke_hosted_demo.py`, `tests/test_hosted_smoke_cli.py` | Local fake-server tests validate the public HTTP contract and sanitized output; they do not call Render or OpenRouter. |
| OpenRouter 429 fallback behavior | Public `/chat` regression tests in `tests/test_app.py` — **6 passed**; CI run [36336569726](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36336569726) | The hosted trace confirms `failure_scope=account_quota` for Qwen's 429; the chain stopped after one attempt and returned 503 without exposing the draft. Provider/model-scoped and unclassified 429s continue through fallback. |
| Retrieval comparison and ablation | `evaluation/retrieval-comparison.md`, `evaluation/ablation-results.md`, `visuals/retrieval-comparison.svg` | Measured on the pinned ONNX backend; hand-labeled, corpus-specific comparisons; chart is tracked and embedded in the GitHub README. |
| Embedding runtime parity | `docs/adr/0009-memory-bounded-huggingface-embeddings.md` | Four-query cosine similarity to FP32 Sentence Transformers ranged 0.991501–0.994461. This is a narrow representation check, not a broad semantic-quality result. |
| UI/API behavior | `tests/test_app.py`, `evidence/ui-review.md`, latest hosted read-only checks below | Local browser review, hosted landing-page status, read-only SQLite endpoints, and two no-tool privacy refusals; not a screen-reader or contrast audit. |
| Requirements and design | `specs/system-requirements.md`, `docs/traceability-matrix.md`, `docs/adr/`, `tickets/`, `docs/implementation-slices.md` | Maps project requirements to implementation and evidence. |

The golden reports measure expected status, tool calls, source families, safety, and keyword overlap. A 1.0 groundedness proxy is not a semantic entailment score. All timings exclude OpenRouter answer generation.

## Hosted evidence

Render service `Project-HR-Agent` is live at [project-hr-agent.onrender.com](https://project-hr-agent.onrender.com) on runtime SHA `eeceda7` (deployment `dep-dasl2lh7lnhs739ltkb0`). CI run [36336569726](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36336569726) passed the exact index build, 99 tests, MCP smoke, and both golden evaluations. Render's build command matches `render.yaml`; auto-deploy remains off.

The latest hosted preflight returned HTTP 200 for two privacy refusals, then completed the first ONNX-backed policy request through three MCP tool calls. OpenRouter returned an account-wide free-tier quota 429 for Qwen; the sanitized trace records `failure_scope=account_quota`, the chain stopped after one attempt, and the API returned HTTP 503 without an unrefined draft. No model resolved and the PTO step was not reached. Render memory samples were 71,155,710 bytes after startup and 274,866,180 bytes after the first policy request, against a 536,870,900-byte limit; the process stayed ready. These two samples do not establish peak or concurrent capacity. See [`hosted-pto-smoke.md`](hosted-pto-smoke.md).

**Recording gates:** when free-model quota is available, rerun hosted PTO and remote-work requests; require citations, `llm_refinement.status=completed`, an actual resolved model, and no reasoning leakage. The private GitHub repo's permission check reports `quantic-grader=none`; course-grader read access is still needed. The course recording and submission remain presenter-owned.
