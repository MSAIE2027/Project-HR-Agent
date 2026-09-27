# Evidence Index

This index separates the current local working tree from the last hosted release. The local changes are based on published SHA `1130dde62a5751c2fd64ee19092c2b16f7c4dfed`; they still need GitHub CI and a Render deploy before they can be called hosted evidence.

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

Render service `Project-HR-Agent` is live at [project-hr-agent.onrender.com](https://project-hr-agent.onrender.com) on SHA `1130dde` (deployment `dep-das9kd59fdbs73cfutpg`). `/health/ready` reports HTTP 200, Python runtime, a 14-document/182-chunk Hugging Face MiniLM SQLite index, eight discovered stdio MCP tools, and OpenRouter configuration. Hosted CI run [36293782172](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36293782172) passed on this SHA with the earlier 25-case set. The current local changes have not passed hosted CI or been deployed.

After the OpenRouter key replacement, readiness continued to report the provider as configured. Two hosted synthetic E1002 PTO requests completed policy search, employee lookup, balance lookup, and compliance, then returned HTTP 503 after 56.97 and 64.16 seconds; their trace did not expose per-route HTTP codes. A current-working-tree local synthetic E1002 request returned HTTP 503 in 10.72 seconds after the same four MCP calls; all four routes returned HTTP 429. There were no citations or resolved model, and the app withheld the unrefined draft. These results do not identify the provider-side cause. See [`hosted-pto-smoke.md`](hosted-pto-smoke.md) for sanitized details.

**Recording gate:** do not record the hosted workflow until the deployed tested SHA returns a synthetic PTO answer with `check_pto_balance`, policy citations, `llm_refinement.status=completed`, the actual resolved model, and no reasoning leakage. The course recording and submission remain presenter-owned.
