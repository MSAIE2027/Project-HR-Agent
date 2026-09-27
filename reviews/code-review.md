# Code Review — HR Agent Demo Readiness

**Review date:** 2026-09-27

**Baseline:** published commit `1130dde62a5751c2fd64ee19092c2b16f7c4dfed`
**Scope:** OpenRouter composition and output validation; employee privacy boundaries; MCP tool execution; SQLite index inspection; UI formatting; evaluation and deployment evidence.

## Review findings

- **Privacy boundary — pass:** Multi-employee requests and requests for an individual's medical records are refused before MCP or OpenRouter calls. Regression coverage is in `tests/test_app.py` and `SAFE-06`–`SAFE-10` in `evaluation/golden_set.json`.
- **LLM boundary — pass:** Successful citation-bearing answers use OpenRouter composition. Truncated output, unsupported changes, process narration, and provider failures are rejected or fail closed; public API and provider tests cover these cases in `tests/test_app.py` and `tests/test_llm.py`.
- **MCP boundary — pass:** The stdio integration uses the official MCP client/server protocol for discovery and tool calls; `tests/test_mcp.py` and `scripts/smoke_mcp.py` exercise it.
- **SQLite inspection — pass:** The browser reads bounded document and chunk rows without exposing stored vectors or the database path; `tests/test_app.py` covers the read-only endpoints.
- **Hosted generation — open:** The service passes health and tool discovery, but a hosted citation-bearing answer has not passed acceptance. See the current [deployment status](../deployed.md) and [hosted acceptance evidence](../evidence/hosted-pto-smoke.md).

## Verification

The local suite passed **86 tests** with one third-party Starlette/AnyIO deprecation warning. The 30-case in-process and stdio golden evaluations passed; they are deterministic control-flow proxies, exclude LLM generation, and do not independently judge semantic groundedness. The hosted runtime commit passed [GitHub Actions run 36306573067](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36306573067). Current CI and deployment evidence is summarized in [`../evidence/index.md`](../evidence/index.md).
