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

The current working tree is not yet hosted. GitHub Actions run [36293782172](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36293782172) and Render deployment `dep-das9kd59fdbs73cfutpg` apply to the earlier `1130dde` release. The live service is health-checked and reports OpenRouter configured, but two synthetic E1002 PTO requests after key replacement returned HTTP 503 with all attempts marked unavailable. A current local E1002 PTO run completed all four MCP calls, then all four model routes returned HTTP 429 and no model resolved. The hosted end-to-end response requirement remains open; see [`../evidence/hosted-pto-smoke.md`](../evidence/hosted-pto-smoke.md).
