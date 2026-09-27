# Evidence Index

This index distinguishes local evidence, hosted CI, the live Render build, and live OpenRouter completion evidence. The latest published documentation-only revision before this work, `9357604`, passed full CI run [36329080773](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36329080773). Render still serves runtime SHA `400dad4` as deployment `dep-dashgbt9fdbs73dfd7cg`; documentation-only updates do not change that runtime. Hosted answer generation remains unverified.

## Current local evidence

| Claim | Evidence | Scope / limit |
|---|---|---|
| Test suite | Prior focused local run: **36 passed**, one third-party Starlette/AnyIO deprecation warning; latest full CI passed in run [36329080773](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36329080773) on `9357604` | CI runs the whole suite and both transport evaluations; tests do not verify live provider availability. |
| Golden-set evaluation | `evaluation/results.json`, `.md`, `results-stdio.json`, `.md` — **30 cases** per transport; workflow completion **5/5**; mean keyword score **0.95** in-process | Deterministic orchestrator proxies; `llm_generation_included=false`; no independent semantic-judgment score. |
| In-process latency | Priming **6,005.88 ms**; warm 15-task p50/p95 **23.59/104.74 ms** | Priming reported separately; not hosted latency. |
| Stdio latency | Priming **8,478.52 ms**; fresh-subprocess 15-task p50/p95 **7,471.90/7,917.17 ms** | Each task starts a fresh MCP process and loads the local model/index; not a Render cold-start benchmark. |
| MCP protocol | `scripts/smoke_mcp.py`, stdio golden report, `tests/test_mcp.py` | Official SDK client discovers and calls eight FastMCP tools over stdio. |
| Hosted-preflight CLI contract | `scripts/smoke_hosted_demo.py`, `tests/test_hosted_smoke_cli.py` | Local fake-server tests validate the public HTTP contract and sanitized output; they do not call Render or OpenRouter. |
| OpenRouter 429 fallback behavior | Public `/chat` regression tests in `tests/test_app.py` — **6 passed** | Account-wide free daily quota stops after one attempt; provider-scoped, structured/message-scoped model daily (including a named model), and unclassified 429s continue to the next route. Local mocked-provider evidence only; the change has not been run in hosted CI or deployed. |
| Retrieval comparison and ablation | `evaluation/retrieval-comparison.md`, `evaluation/ablation-results.md`, `visuals/retrieval-comparison.svg` | Hand-labeled, corpus-specific comparisons; chart is tracked and embedded in the GitHub README. |
| UI/API behavior | `tests/test_app.py`, `evidence/ui-review.md`, latest hosted read-only checks below | Local browser review, hosted landing-page status, read-only SQLite endpoints, and two no-tool privacy refusals; not a screen-reader or contrast audit. |
| Requirements and design | `specs/system-requirements.md`, `docs/traceability-matrix.md`, `docs/adr/`, `tickets/`, `docs/implementation-slices.md` | Maps project requirements to implementation and evidence. |

The golden reports measure expected status, tool calls, source families, safety, and keyword overlap. A 1.0 groundedness proxy is not a semantic entailment score. All timings exclude OpenRouter answer generation.

## Hosted evidence

Render service `Project-HR-Agent` is live at [project-hr-agent.onrender.com](https://project-hr-agent.onrender.com) on runtime SHA `400dad4` (deployment `dep-dashgbt9fdbs73dfd7cg`). Current `/health/ready` returned HTTP 200 with the ready 14-document/182-chunk/384-dimensional MiniLM SQLite index, eight stdio MCP tools, and OpenRouter configured. The latest published documentation-only revision `9357604` passed [CI run 36329080773](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36329080773), including the full suite, MCP smoke, both 30-case evaluations, and evidence upload. Its deploy job was skipped and Render auto-deploy remains off.

The latest full live preflight returned HTTP 200 for two privacy refusals without MCP or LLM calls, then HTTP 503 for remote-work guidance after all four model routes returned HTTP 429. `llm_refinement.status` was `unavailable`; no model resolved, and the preflight did not reach PTO. A read-only `/auth/key` check accepted the rotated local key but exposed no free-model request counter or reset timestamp. Render does not expose the deployed key identity or quota. The app withheld the retrieval draft. See [`hosted-pto-smoke.md`](hosted-pto-smoke.md) for the sanitized details.

During the first hosted MiniLM load, thirty-second memory samples peaked at 536,264,700 bytes against the 536,870,900-byte service limit, then settled at 493,432,830 bytes. The same Render instance stayed live and routine readiness checks returned HTTP 200. This does not establish multi-request capacity; the cold-load peak leaves little memory headroom.

**Recording gates:** require a hosted synthetic PTO answer with `check_pto_balance`, policy citations, `llm_refinement.status=completed`, the actual resolved model, and no reasoning leakage. All four configured routes returned HTTP 429 in the latest preflight. The private GitHub repo's permission check reports `quantic-grader=none`; course-grader read access is still needed. The course recording and submission remain presenter-owned.
