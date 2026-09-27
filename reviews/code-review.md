# Code Review — MCP Lifecycle and Demo Readiness

**Review date:** 2026-09-27

**Code baseline:** `400dad4`

**Review scope:** MCP stdio lifecycle, readiness checks, safety behavior, architecture documentation, and hosted demo acceptance.

## Standards review

- **Architecture accuracy:** The README and architecture note distinguish local quick-start in-process MCP from the official stdio path used by CI and Render. They show Hugging Face as the model-weight source, local MiniLM inference, SQLite vector storage, and OpenRouter composition after retrieval.
- **Lifecycle and cleanup:** FastAPI owns one MCP session per stdio app lifespan and closes it at shutdown. Failed operations update cached MCP health; routine readiness probes do not wait on the tool lock, while deep health performs explicit discovery.
- **Test isolation:** The stdio integration test restores shared `app.state` after its nested TestClient lifecycle.

## Spec review

- **MCP protocol and workflow:** The app reuses the official MCP SDK session over FastMCP stdio without changing tool schemas or response contracts. The full protocol smoke and both golden evaluations pass in CI.
- **Operational behavior:** A disconnected session produces an explicit MCP-unavailable result and updates cached MCP health. Routine readiness returns HTTP 503 without waiting on the tool lock; deep health performs discovery.
- **Hosted answer acceptance — open:** The latest synthetic preflight passed both privacy refusals, then returned HTTP 503 after all four OpenRouter routes returned HTTP 429. The app withheld the unrefined draft; no model resolved and PTO was not reached. See [`../evidence/hosted-pto-smoke.md`](../evidence/hosted-pto-smoke.md).
- **Course access — open:** The private repository permission check reports `quantic-grader=none`; grader read access remains unverified. See [`../deployed.md`](../deployed.md).

## Verification

- Focused local app/MCP suite: **36 passed**, with one third-party Starlette/AnyIO deprecation warning.
- Runtime commit `400dad4` passed [GitHub Actions run 36321773923](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36321773923) and is live on Render deployment `dep-dashgbt9fdbs73dfd7cg`.
- Documentation commit `cf8e0db` passed [GitHub Actions run 36324920372](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36324920372); its Render deploy job was skipped.
- The current documentation diff passed `git diff --check`.
- Live read-only checks returned HTTP 200 for readiness, document listing, and the PTO chunk preview. The hosted medical-record and multi-employee prompts were refused before MCP or LLM calls.
