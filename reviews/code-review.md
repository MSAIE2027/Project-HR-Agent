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

## Review — OpenRouter quota-aware fallback

**Review date:** 2026-09-27

**Code baseline:** `9357604` (working-tree changes, including new ADR 0008)

**Review scope:** Stop retrying only for an identifiable account-wide free-model daily quota 429; preserve fallback for model/provider-scoped and unclassified 429s; sanitize public trace data.

### Standards

- No documented-standard violations found. The behavior is covered through the public `/chat` seam as required by `AGENTS.md`.
- No actionable Fowler smell remains; repeated fake-provider setup in the added regressions was consolidated into a shared helper.

### Spec

- No remaining mismatch with SRS FR-16 or ADR 0008. The review caught a false stop for model-scoped daily-limit wording; the classifier now gives structured scope and unambiguous model/provider wording precedence over account-quota markers.
- No unrelated behavior or scope creep found.
- Hosted generation acceptance remains open: the last deployed preflight failed closed after four HTTP 429 responses and did not resolve a model. Mocked local tests do not establish a successful hosted answer.

### Verification for this change

- TDD reproduced structured-scope, message-only, and named-model false positives before their fixes.
- Focused public `/chat` regressions: **6 passed**, one third-party Starlette/AnyIO deprecation warning.
- Python syntax compilation and `git diff --check` passed.
- Full CI and deployment have not run for this working-tree change.

**Review summary:** Standards — 0 violations and 0 actionable smells. Spec — 0 remaining implementation mismatches or scope-creep findings. Hosted answer acceptance is a separate open release gate.
