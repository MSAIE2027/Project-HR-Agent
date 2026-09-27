# Code Review — MCP Lifecycle and Demo Readiness

**Review date:** 2026-09-27

**Baseline:** `5371a488a496b77f71e2fda875e75c7cd4b1d39e`

**Scope:** MCP stdio session lifecycle, readiness checks, regression tests, architecture wording, and source-to-demo records.

## Standards review

- **Architecture accuracy — pass:** The README and architecture notes identify in-process MCP as the local quick-start default and label stdio process reuse as the required CI/Render path.
- **Lifecycle and cleanup — pass:** FastAPI owns one MCP session per stdio app lifespan and closes it at shutdown. Failed operations mark cached MCP health unavailable; routine `/health/ready` probes do not wait on the tool lock, while `/health?deep=true` performs live discovery.
- **Test isolation — pass:** The stdio integration test restores the shared `app.state` after its nested TestClient lifecycle.

## Spec review

- **MCP protocol and workflow — pass locally:** The app reuses the official MCP SDK session over FastMCP stdio without changing tool schemas or user-facing response contracts.
- **Operational status — pass locally:** A disconnected session produces an explicit MCP-unavailable result and updates cached MCP health. Routine readiness returns HTTP 503 without waiting on the tool lock; explicit deep health performs discovery.
- **Hosted acceptance — partial:** CI run [36321773923](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36321773923) passed and commit `400dad4` is live as Render deployment `dep-dashgbt9fdbs73dfd7cg`. Health and MCP discovery pass. The cold MiniLM load did not restart the service, though sampled memory peaked near its limit. Hosted answer acceptance is blocked: all four routes returned 429, and a direct request with the refreshed local key identified OpenRouter's free-model daily limit.
- **Submission-owned items:** Recording the course video and confirming `quantic-grader` repository access remain presenter actions and are not represented as complete.

## Verification

- `./.venv/bin/python -m pytest -q tests/test_app.py tests/test_mcp.py` — **36 passed** after the cached-readiness adjustment. One third-party Starlette/AnyIO deprecation warning.
- `git diff --check` — passed before the documentation refresh; rerun on the final tree.
- GitHub Actions — run [36321773923](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36321773923) passed; Render deployment `dep-dashgbt9fdbs73dfd7cg` is live.
- Hosted model acceptance remains open until citation-bearing responses report `llm_refinement.status=completed` and a resolved model.
