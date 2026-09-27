# Evidence Index

This index distinguishes local evidence from hosted evidence. Commit `42de2e8` is published to the private repository `MSAIE2027/Project-HR-Agent`. Hosted CI run [36289121722](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36289121722) passed. The Render service is linked to that repository and has the assigned URL `https://project-hr-agent.onrender.com`, but it has no deploy history and does not yet match the Python Blueprint; no hosted app behavior or cold-start measurement is claimed.

| Evidence | Artifact / command | What it establishes | Limit |
|---|---|---|---|
| Source baseline | `git status --short --branch`; `git log -1 --oneline` | Initial baseline `32497e5`; the reviewed implementation was published as `42de2e8`. | This evidence index is being updated to include the first hosted CI run. |
| Full tests | `./.venv/bin/python -m pytest -q`; [hosted CI run](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36289121722) | 64 passed locally, 1 third-party Starlette/AnyIO deprecation warning; hosted pytest also passed on commit `42de2e8`. | Does not test live OpenRouter generation or hosted app behavior. |
| Current OpenRouter runtime | [`openrouter-chain-smoke.md`](openrouter-chain-smoke.md) | On the rebuilt 14-document / 182-chunk Hugging Face → SQLite index, a synthetic cited `/chat` retry returned 200 with five citations and `llm_refinement=completed`; the resolved model was `poolside/laguna-s-2.1:free`. | Two earlier calls returned 503; this identifies one remote-work request only, not a separate PTO request or sustained availability. |
| Historical OpenRouter success | [`openrouter-smoke.md`](openrouter-smoke.md) | A previous cited request completed with five `POL-RW-01` citations and `llm_refinement=completed`. | Historical only: it used the stale 126-chunk index and does not verify current behavior. |
| Complete golden sets | `evaluation/results.json`, `evaluation/results.md`, `evaluation/results-stdio.json`, `evaluation/results-stdio.md` | All 25 cases pass status, citation-prefix, exact tool sequence, workflow completion, clarification/escalation, and action-safety fixture checks over in-process and stdio transports. Workflow completion is 5/5 workflow-category cases. | `llm_generation_included=false`; deterministic proxies are not independent semantic judgments. Stdio latency includes subprocess/model/index initialization. |
| Retrieval comparison | `evaluation/retrieval-comparison.md`, `.json`, `visuals/retrieval-comparison.svg` | Chunk/top-k/MMR/routing and ranking-weight measurements. | Small, hand-labeled corpus-specific sample. |
| Chunk ablation | `evaluation/ablation-results.md`, `.json` | Five chunk configurations compared with the chosen MiniLM model. | Does not establish a universal chunk optimum. |
| MCP protocol smoke | `./.venv/bin/python scripts/smoke_mcp.py`; stdio golden report | Stdio discovery of eight MCP tools, read-only policy/profile calls, and all 25 golden scenarios over the protocol; both browser workflows were rehearsed over stdio. | Does not replace a hosted MCP check. |
| CLI help | `./.venv/bin/python scripts/build_index.py --help` | Direct documented script invocation imports correctly. | Help path only; it does not rebuild or overwrite the local index. |
| UI/API regression | `tests/test_app.py` | Current example prompts, workflow tool order, action confirmation, refusal, escalation, missing-record behavior, and response contract. | Automated markup/API checks do not prove visual or assistive-technology quality. |
| CI/deployment gate | `.github/workflows/ci.yml`, `render.yaml`, [hosted run](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36289121722) | Hosted compile, pytest, MCP discovery/calls, both threshold-gated golden evaluations, and evidence upload passed for `42de2e8`. The tested-SHA Render hook job depends on `test`; independent Render auto-deploy is Off. | The Render deploy job was skipped because opt-in settings are absent; service runtime and health path still need reconciliation. |
| Code review | [`reviews/code-review.md`](../reviews/code-review.md) | Separate standards/spec reviews of completion changes against baseline `32497e5`, including findings and disposition. | Local review; hosted CI passed, but no remote PR review was performed. |
| Human/browser review | [`ui-review.md`](ui-review.md), `docs/grader-ux-validation.md`, `demo/README.md` | Local desktop and narrow-viewport review, keyboard focus behavior, Escape close/focus restoration, citations/trace, and confirmation-gated demo flow. | Visual and basic keyboard review only; no screen-reader, automated contrast, hosted-browser, or deployed-interface audit. |
| Course presentation | `demo/README.md`, `docs/demo-script.md` | Presenter prompts, expected calls, timings, limitations, and recording checklist. | The human-recorded 7–10 minute video and course submission are presenter-owned. |

## Golden-set result snapshot

The local reports are in `evaluation/results.json` (in-process) and `evaluation/results-stdio.json` (protocol-backed stdio). Each records:

- 25/25 task statuses matched the rubric fixtures.
- Groundedness proxy, citation-prefix accuracy, exact tool-sequence accuracy, workflow completion, clarification/escalation accuracy, and action-safety pass rate each scored 1.0.
- Mean gold-keyword overlap was 0.94.
- `llm_generation_included` is `false`; these are orchestrator-level results and exclude OpenRouter generation.
- In-process priming request: 6,369.82 ms; subsequent 15-task warm sample: p50 20.28 ms, p95 62.54 ms.
- Stdio priming request: 9,659.28 ms; each sampled task starts a fresh MCP process, so the 15-task p50/p95 were 8,645.27/11,180.99 ms, including process and model/index initialization.

The full test suite and both golden evaluations passed locally and in the hosted CI workflow for `42de2e8`. MCP stdio smoke, direct CLI help, and syntax compilation also passed. These results establish a successful hosted CI run, not a Render deployment.

These scores are fixture metrics. The groundedness check is not a human entailment judgment. In-process figures are warm-request latencies after a separate priming request; stdio figures include per-task MCP subprocess/model initialization. Neither is a Render cold-start measurement.
