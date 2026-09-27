# Evidence Index

This index distinguishes local evidence, hosted CI, the live Render build, and live OpenRouter completion evidence. Commit `6ce0da8fd3d410d5a1093006463b5896d114fea4` passed hosted CI and is live on Render; its current OpenRouter free-tier quota prevents a successful hosted generation check.

## Current local evidence

| Claim | Evidence | Scope / limit |
|---|---|---|
| Test suite | `./.venv/bin/python -m pytest -q` — **82 passed**, one third-party Starlette/AnyIO deprecation warning | Includes API, RAG, provider validation, safety, and MCP tests; does not verify live provider availability. |
| Golden-set evaluation | `evaluation/results.json`, `.md`, `results-stdio.json`, `.md` — **30 cases** per transport; workflow completion **5/5**; mean keyword score **0.95** in-process | Deterministic orchestrator proxies; `llm_generation_included=false`; no independent semantic-judgment score. |
| In-process latency | Priming **6,005.88 ms**; warm 15-task p50/p95 **23.59/104.74 ms** | Priming reported separately; not hosted latency. |
| Stdio latency | Priming **8,478.52 ms**; fresh-subprocess 15-task p50/p95 **7,471.90/7,917.17 ms** | Each task starts a fresh MCP process and loads the local model/index; not a Render cold-start benchmark. |
| MCP protocol | `scripts/smoke_mcp.py`, stdio golden report, `tests/test_mcp.py` | Official SDK client discovers and calls eight FastMCP tools over stdio. |
| Retrieval comparison and ablation | `evaluation/retrieval-comparison.md`, `evaluation/ablation-results.md`, `visuals/retrieval-comparison.svg` | Hand-labeled, corpus-specific comparisons; chart is tracked and embedded in the GitHub README. |
| UI/API behavior | `tests/test_app.py`, `evidence/ui-review.md` | API regression and prior local browser review. Current Markdown rendering and SQLite browser have automated regression coverage; this does not replace screen-reader or hosted-browser review. |
| Requirements and design | `specs/system-requirements.md`, `docs/traceability-matrix.md`, `docs/adr/`, `tickets/`, `docs/implementation-slices.md` | Maps project requirements to implementation and evidence. |

The golden reports measure expected status, tool calls, source families, safety, and keyword overlap. A 1.0 groundedness proxy is not a semantic entailment score. All timings exclude OpenRouter answer generation.

## Hosted evidence

Render service `Project-HR-Agent` is live at [project-hr-agent.onrender.com](https://project-hr-agent.onrender.com) on SHA `6ce0da8` (deployment `dep-dasdc7fpn0mc73fu752g`). `/health/ready` returned HTTP 200, with Python runtime, a ready 14-document/182-chunk/384-dimensional Hugging Face MiniLM SQLite index, eight stdio MCP tools, and OpenRouter configuration. The hosted UI and read-only SQLite browser API return HTTP 200; the PTO index endpoint shows 13 text chunks and `vectors_exposed=false`. Hosted CI run [36306573067](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36306573067) passed on the same SHA, including pytest, MCP stdio smoke, both 30-case evaluations, and evidence upload. The tested SHA was deployed manually after CI passed; Render auto-deploy remains off.

The latest hosted synthetic E1002 PTO request returned HTTP 503 after 79.2 seconds. All four expected MCP calls completed, then each configured OpenRouter route returned HTTP 429; there were no citations or resolved model, and the app withheld the unrefined draft. A local `.env` key authenticated successfully at OpenRouter's current-key endpoint and reported a Free tier allowance of 50 daily requests, with 51 used and none remaining. The hosted behavior is consistent with exhausted free-tier capacity; the Render secret was not read back or compared. No paid model call was made. OpenRouter currently lists 50 requests per day for its Free plan ([pricing](https://openrouter.ai/pricing/)). See [`hosted-pto-smoke.md`](hosted-pto-smoke.md) for sanitized details.

**Recording gate:** do not record the hosted workflow until the deployed tested SHA returns a synthetic PTO answer with `check_pto_balance`, policy citations, `llm_refinement.status=completed`, the actual resolved model, and no reasoning leakage. Retry after the free daily quota replenishes. The course recording and submission remain presenter-owned.
