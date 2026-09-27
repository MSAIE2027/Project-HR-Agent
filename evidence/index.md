# Evidence Index

This index distinguishes local evidence, hosted CI, the live Render build, and live OpenRouter completion evidence. Commit `400dad45b329e35999feadd889bc249cda296969` passed [hosted CI run 36321773923](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36321773923) and is live on Render as `dep-dashgbt9fdbs73dfd7cg`. Hosted answer generation remains unverified because the required OpenRouter chain returns HTTP 429 for every route.

## Current local evidence

| Claim | Evidence | Scope / limit |
|---|---|---|
| Test suite | Current focused local run: **36 passed**, one third-party Starlette/AnyIO deprecation warning; current full suite also passed in CI run [36321773923](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36321773923) | The focused run covered changed API/MCP code. CI reran the whole suite and both transport evaluations; tests do not verify live provider availability. |
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

Render service `Project-HR-Agent` is live at [project-hr-agent.onrender.com](https://project-hr-agent.onrender.com) on SHA `400dad4` (deployment `dep-dashgbt9fdbs73dfd7cg`). `/health/ready` and `/health?deep=true` returned HTTP 200, with the ready 14-document/182-chunk/384-dimensional Hugging Face MiniLM SQLite index, eight stdio MCP tools, and OpenRouter configuration. The current full CI run [36321773923](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36321773923) passed on the same SHA, including pytest, MCP stdio smoke, both 30-case evaluations, and evidence upload. The tested SHA was deployed manually after CI passed; Render auto-deploy remains off.

The latest live preflight returned HTTP 200 for two privacy refusals without MCP or LLM calls, then HTTP 503 for remote-work guidance after all four model routes returned HTTP 429. `llm_refinement.status` was `unavailable`; no model resolved. A direct request using the refreshed local `.env` key returned OpenRouter's `free-models-per-day` rate-limit message, which says adding 10 credits unlocks 1,000 free-model requests per day. The hosted key's metadata is not exposed by Render, although its four-route failure matches the same limit. The app withheld its unrefined draft. See [`hosted-pto-smoke.md`](hosted-pto-smoke.md) for the compact sanitized acceptance record.

During the first hosted MiniLM load, thirty-second memory samples peaked at 536,264,700 bytes against the 536,870,900-byte service limit, then settled at 493,432,830 bytes. The same Render instance stayed live and routine readiness checks returned HTTP 200. This does not establish multi-request capacity; the cold-load peak leaves little memory headroom.

**Recording gate:** do not record the hosted workflow until the deployed tested SHA returns a synthetic PTO answer with `check_pto_balance`, policy citations, `llm_refinement.status=completed`, the actual resolved model, and no reasoning leakage. The local key is blocked by the free-model daily limit; wait for its reset or for the account owner to enable free-model access. The course recording and submission remain presenter-owned.
