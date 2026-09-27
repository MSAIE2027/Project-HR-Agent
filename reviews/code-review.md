# Code Review — Completion Worktree

**Review date:** 2026-09-27
**Baseline:** published commit `1130dde62a5751c2fd64ee19092c2b16f7c4dfed`
**Scope:** OpenRouter answer composition and output validation; employee privacy refusals; SQLite index inspection; UI response formatting; evaluation, README, and evidence updates.

## Standards

The README now provides a grouped Mermaid architecture diagram with the application, real MCP stdio boundary, local Hugging Face/SQLite retrieval, required OpenRouter model chain, validation, final response, and read-only SQLite inspection path. The answer arrow goes from validation through the final response into the browser. The former deployment-status and experiment-scope commentary has been removed from the README; current deployment claims are in `deployed.md`, and retrieval methods/results are in `evaluation/`.

Evaluation reports now use the same 30-case set; historical timeouts are distinguished by request in the evidence log.

## Spec

Multi-employee refusals now count explicit IDs and names in the fixed synthetic roster. Requests for medical records, files, or charts stop before employee lookup, including a PTO question combined with a medical-record request. Public `/chat` regression tests and golden cases `SAFE-06`–`SAFE-10` cover these boundaries. The evidence-based composer rejects truncated completions at the provider seam and continues through the configured model chain; a separate public `/chat` test verifies fail-closed behavior for model-generated process narration.

The local suite passes **82 tests** with one third-party Starlette/AnyIO deprecation warning. The refreshed in-process and stdio golden sets each pass **30/30**; `llm_generation_included=false`, and the groundedness figure is a deterministic proxy rather than semantic answer judging. Full test and evaluation details are in [`../evidence/index.md`](../evidence/index.md).

## Release status

Commit `6ce0da8` is published, passed GitHub Actions run [36306573067](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36306573067), and is live on Render as deployment `dep-dasdc7fpn0mc73fu752g`. Health and tool discovery pass. The latest synthetic E1002 PTO request returned HTTP 503 after four MCP calls; all four OpenRouter routes returned 429. The current local key metadata shows the OpenRouter free-tier daily allowance is exhausted (51 used of 50, none remaining), consistent with the hosted failures. The hosted end-to-end answer requirement remains open until quota replenishes and a cited response records a resolved model; see [`../evidence/hosted-pto-smoke.md`](../evidence/hosted-pto-smoke.md).
