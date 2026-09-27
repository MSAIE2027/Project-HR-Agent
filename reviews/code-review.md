# Code Review — MCP Lifecycle and Demo Readiness

**Review date:** 2026-09-27

**Baseline:** `5371a488a496b77f71e2fda875e75c7cd4b1d39e`

**Scope:** MCP stdio session lifecycle, readiness checks, regression tests, architecture wording, and source-to-demo records.

## Standards review

- **Architecture accuracy — pass:** The README and architecture notes identify in-process MCP as the local quick-start default and label stdio process reuse as the required CI/Render path.
- **Lifecycle and cleanup — pass:** FastAPI owns one MCP session per stdio app lifespan and closes it at shutdown. A failed session is reported as unavailable; `/health/ready` performs live tool discovery. Restarting the service creates a new session.
- **Test isolation — pass:** The stdio integration test restores the shared `app.state` after its nested TestClient lifecycle.
- **Non-blocking maintainability note:** Several test-specific `FakeOrchestrator` classes repeat the optional `gateway` constructor parameter. They remain small local fakes with different response behavior; consolidating them is optional cleanup.

## Spec review

- **MCP protocol and workflow — pass locally:** The app reuses the official MCP SDK session over FastMCP stdio without changing tool schemas or user-facing response contracts.
- **Operational status — pass locally:** A disconnected session produces an explicit MCP-unavailable result and updates cached MCP health. Routine readiness returns HTTP 503 without waiting on the tool lock; explicit deep health performs discovery.
- **Hosted acceptance — pending:** The change still needs hosted CI, a Render deploy, and post-deploy memory observation after MiniLM loads. A successful hosted OpenRouter-composed answer is also required before recording; prior hosted attempts failed closed after HTTP 429 responses.
- **Submission-owned items:** Recording the course video and confirming `quantic-grader` repository access remain presenter actions and are not represented as complete.

## Verification

- `./.venv/bin/python -m pytest -q tests/test_app.py tests/test_mcp.py` — **36 passed** after the cached-readiness adjustment. One third-party Starlette/AnyIO deprecation warning.
- `git diff --check` — passed for this change.
- GitHub Actions and hosted Render acceptance are pending for this change.
