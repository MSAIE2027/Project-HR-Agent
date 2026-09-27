# Evidence Index

This index distinguishes local evidence, hosted CI, the live Render build, and live OpenRouter completion evidence. Commit `6ce0da8fd3d410d5a1093006463b5896d114fea4` passed hosted CI and is live on Render. Hosted answer generation remains unverified: the latest preflight after the OpenRouter configuration refresh returned HTTP 503 after four HTTP 429 responses.

## Current local evidence

| Claim | Evidence | Scope / limit |
|---|---|---|
| Test suite | `./.venv/bin/python -m pytest -q` — **86 passed**, one third-party Starlette/AnyIO deprecation warning | Includes API, RAG, provider validation, safety, MCP, and hosted-preflight CLI contract tests; does not verify live provider availability. |
| Golden-set evaluation | `evaluation/results.json`, `.md`, `results-stdio.json`, `.md` — **30 cases** per transport; workflow completion **5/5**; mean keyword score **0.95** in-process | Deterministic orchestrator proxies; `llm_generation_included=false`; no independent semantic-judgment score. |
| In-process latency | Priming **6,005.88 ms**; warm 15-task p50/p95 **23.59/104.74 ms** | Priming reported separately; not hosted latency. |
| Stdio latency | Priming **8,478.52 ms**; fresh-subprocess 15-task p50/p95 **7,471.90/7,917.17 ms** | Each task starts a fresh MCP process and loads the local model/index; not a Render cold-start benchmark. |
| MCP protocol | `scripts/smoke_mcp.py`, stdio golden report, `tests/test_mcp.py` | Official SDK client discovers and calls eight FastMCP tools over stdio. |
| Hosted-preflight CLI contract | `scripts/smoke_hosted_demo.py`, `tests/test_hosted_smoke_cli.py` | Local fake-server tests validate the public HTTP contract and sanitized output; they do not call Render or OpenRouter. |
| Retrieval comparison and ablation | `evaluation/retrieval-comparison.md`, `evaluation/ablation-results.md`, `visuals/retrieval-comparison.svg` | Hand-labeled, corpus-specific comparisons; chart is tracked and embedded in the GitHub README. |
| UI/API behavior | `tests/test_app.py`, `evidence/ui-review.md` | API regression and prior local browser review. Current Markdown rendering and SQLite browser have automated regression coverage; this does not replace screen-reader or hosted-browser review. |
| Requirements and design | `specs/system-requirements.md`, `docs/traceability-matrix.md`, `docs/adr/`, `tickets/`, `docs/implementation-slices.md` | Maps project requirements to implementation and evidence. |

The golden reports measure expected status, tool calls, source families, safety, and keyword overlap. A 1.0 groundedness proxy is not a semantic entailment score. All timings exclude OpenRouter answer generation.

## Hosted evidence

Render service `Project-HR-Agent` is live at [project-hr-agent.onrender.com](https://project-hr-agent.onrender.com) on SHA `6ce0da8` (deployment `dep-dasdc7fpn0mc73fu752g`). `/health/ready` returned HTTP 200, with Python runtime, a ready 14-document/182-chunk/384-dimensional Hugging Face MiniLM SQLite index, eight stdio MCP tools, and OpenRouter configuration. The hosted UI and read-only SQLite browser API return HTTP 200; the PTO index endpoint shows 13 text chunks and `vectors_exposed=false`. Hosted CI run [36306573067](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36306573067) passed on the same SHA, including pytest, MCP stdio smoke, both 30-case evaluations, and evidence upload. The tested SHA was deployed manually after CI passed; Render auto-deploy remains off.

The latest live preflight returned HTTP 200 for two privacy refusals without MCP or LLM calls, then HTTP 503 for remote-work guidance after all four model routes returned HTTP 429. `llm_refinement.status` was `unavailable`; no model resolved. The app withheld its unrefined draft. See [`hosted-pto-smoke.md`](hosted-pto-smoke.md) for the compact sanitized acceptance record.

**Recording gate:** do not record the hosted workflow until the deployed tested SHA returns a synthetic PTO answer with `check_pto_balance`, policy citations, `llm_refinement.status=completed`, the actual resolved model, and no reasoning leakage. The 429 response cause is not established by this check. The course recording and submission remain presenter-owned.
