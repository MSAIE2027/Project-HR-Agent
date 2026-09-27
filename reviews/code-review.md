# Code Review — HR Agent Demo Readiness

**Review date:** 2026-09-27

**Published baseline:** `1130dde62a5751c2fd64ee19092c2b16f7c4dfed`

**Previously reviewed head:** `56e6ef4`

**Follow-up:** Structured-facts contract fix and public chat regression coverage are in the current working tree.

## Standards review

- **MCP protocol — pass:** The demo path discovers and calls tools through the official MCP Python SDK client and FastMCP server over stdio.
- **Safety and response boundary — pass:** Multi-employee and individual medical-record requests stop before MCP and OpenRouter. Mock actions require explicit confirmation and remain local. Citation-bearing answers fail closed when OpenRouter is unavailable or validation rejects a response.
- **Structured-facts contract — fixed:** The earlier review found that PTO confirmation responses sent only the confirmation flag to OpenRouter, and benefits responses sent an empty facts object. Both paths now pass their checked synthetic record values. Public `/chat` regression tests verify the provider context for the two flows.
- **SQLite inspection — pass:** The browser exposes bounded document and chunk rows, without vectors or the database path.
- **Non-blocking test cleanup:** A hosted-smoke test contains duplicated fake-response cases. This is a maintainability opportunity and does not change runtime behavior or the acceptance result.

## Spec review

- The README and design documentation now show the app boundary, local embedding and SQLite path, MCP tool calls, required OpenRouter response composition, and fail-closed validation. User-visible status and citations remain separate from the provider's structured validation context.
- The latest hosted citation-bearing workflow has **not** passed acceptance. The current deployment returned HTTP 503 after all four configured model routes returned HTTP 429; refusal behavior and service readiness were available. See [`../deployed.md`](../deployed.md) and [`../evidence/hosted-pto-smoke.md`](../evidence/hosted-pto-smoke.md).
- The golden-set groundedness score is a keyword proxy for deterministic control flow, not an independent semantic judgment or live LLM quality score. The retrieval comparison is based on a small hand-labeled corpus. See [`../evaluation/`](../evaluation/) for methods and limits.
- The presenter-recorded video and `quantic-grader` repository invitation are external submission steps. They are not represented as complete in this repository.

## Verification

- The two new public `/chat` tests failed before the implementation change because structured facts were missing, then passed after the change. Run: `./.venv/bin/python -m pytest -q tests/test_app.py::test_pto_confirmation_sends_structured_values_to_llm tests/test_app.py::test_benefits_response_sends_structured_record_to_llm`.
- The published baseline passed [GitHub Actions run 36315955802](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36315955802), including its full test and evaluation jobs. The follow-up code change still needs a fresh CI run before it can be called verified by CI.
- The deployed runtime remains on commit `6ce0da8fd3d410d5a1093006463b5896d114fea4`; the local documentation/code follow-up is not yet deployed.
