# Evidence Index

This index points to evidence for the current local checkout. `origin` is configured as `https://github.com/MSAIE2027/Project-HR-Agent.git`, but the current local source has not been pushed. A Render service is linked to that private GitHub repository and has the assigned URL `https://project-hr-agent.onrender.com`, but Render reports no deploy history; no hosted URL, CI result, or cold-start measurement is claimed.

| Evidence | Artifact / command | What it establishes | Limit |
|---|---|---|---|
| Source baseline | `git status --short --branch`; `git log -1 --oneline` | Initial baseline `32497e5`; work began with a clean tree. | Completion changes are still in the working tree unless committed later. |
| Full tests | `./.venv/bin/python -m pytest -q` | 64 passed, 1 Starlette/AnyIO deprecation warning. Covers API/UI, RAG, MCP stdio, OpenRouter validation, semantic embedding configuration, evaluation thresholds, and golden evaluation. | Local environment only; no GitHub Actions run is recorded. |
| Current OpenRouter runtime | [`openrouter-chain-smoke.md`](openrouter-chain-smoke.md) | On the rebuilt 14-document / 182-chunk Hugging Face → SQLite index, the latest synthetic cited `/chat` retry returned 200 with five citations and `llm_refinement=completed` after all four routes were attempted. | Two earlier calls returned 503; the successful local preflight verifies one request, not sustained free-model availability or hosted deployment. |
| Historical OpenRouter success | [`openrouter-smoke.md`](openrouter-smoke.md) | A previous cited request completed with five `POL-RW-01` citations and `llm_refinement=completed`. | Historical only: it used the stale 126-chunk index and does not verify current behavior. |
| Complete golden sets | `evaluation/results.json`, `evaluation/results.md`, `evaluation/results-stdio.json`, `evaluation/results-stdio.md` | All 25 cases pass status, citation-prefix, exact tool sequence, workflow completion, clarification/escalation, and action-safety fixture checks over in-process and stdio transports. Workflow completion is 5/5 workflow-category cases. | `llm_generation_included=false`; deterministic proxies are not independent semantic judgments. Stdio latency includes subprocess/model/index initialization. |
| Retrieval comparison | `evaluation/retrieval-comparison.md`, `.json`, `visuals/retrieval-comparison.svg` | Chunk/top-k/MMR/routing and ranking-weight measurements. | Small, hand-labeled corpus-specific sample. |
| Chunk ablation | `evaluation/ablation-results.md`, `.json` | Five chunk configurations compared with the chosen MiniLM model. | Does not establish a universal chunk optimum. |
| MCP protocol smoke | `./.venv/bin/python scripts/smoke_mcp.py`; stdio golden report | Stdio discovery of eight MCP tools, read-only policy/profile calls, and all 25 golden scenarios over the protocol; both browser workflows were rehearsed over stdio. | Does not replace a hosted MCP check. |
| CLI help | `./.venv/bin/python scripts/build_index.py --help` | Direct documented script invocation imports correctly. | Help path only; it does not rebuild or overwrite the local index. |
| UI/API regression | `tests/test_app.py` | Current example prompts, workflow tool order, action confirmation, refusal, escalation, missing-record behavior, and response contract. | Automated markup/API checks do not prove visual or assistive-technology quality. |
| CI/deployment gate | `.github/workflows/ci.yml`, `render.yaml` | GitHub Actions source runs compileall, pytest, MCP discovery/calls, threshold-gated golden evaluations, and evidence upload. The optional tested-SHA Render hook job depends on the full test job; independent Render auto-deploy is disabled. | No hosted workflow has run; the Render service must be synchronized with the Blueprint and GitHub deploy settings before deployment. |
| Code review | [`reviews/code-review.md`](../reviews/code-review.md) | Separate standards/spec reviews of completion changes against baseline `32497e5`, including findings and disposition. | Local working-tree review; no remote PR review or hosted checks. |
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

The full test suite and both golden evaluations were run in this working tree after the index-freshness fix. MCP stdio smoke, direct CLI help, and syntax compilation also passed. These results are local; they do not establish a hosted CI run or deployment.

These scores are fixture metrics. The groundedness check is not a human entailment judgment. In-process figures are warm-request latencies after a separate priming request; stdio figures include per-task MCP subprocess/model initialization. Neither is a Render cold-start measurement.
