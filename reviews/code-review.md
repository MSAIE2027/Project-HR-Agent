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
- **Hosted answer acceptance — open:** At the time of this review, the latest synthetic preflight passed both privacy refusals, then returned HTTP 503 after all four OpenRouter routes returned HTTP 429. The app withheld the unrefined draft; no model resolved and PTO was not reached. The later ONNX deployment reached OpenRouter and confirmed an account-quota 429 on Qwen; current evidence is in [`../evidence/hosted-pto-smoke.md`](../evidence/hosted-pto-smoke.md).
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

## Code review — ONNX embedding mitigation and release checks

**Review date:** 2026-09-27

**Code baseline:** `a24154d` (user-confirmed)

**Review scope:** Local Hugging Face MiniLM ONNX embedding implementation, SQLite metadata and rebuild behavior, CI/Render index gates, and related requirements/evidence documentation.

### Standards

- No actionable violation of the repository's `AGENTS.md` was found. The implementation keeps the production model/chunk baseline fixed and covers behavior through the public `RagIndex` seam.
- Review found that the embedder's one-model ONNX artifact could be requested under an arbitrary model ID. It now rejects unsupported local model IDs before downloading and records the fallback reason.
- Review found that the cache key omitted the resolved model revision. The cache now keys by model and revision; the public index regression verifies that a revision change loads a new runtime.

### Spec

- The SRS requires a pinned 384-dimensional MiniLM index with 120/20 chunks. Review found that CI and Render only asserted that some semantic embedding revision existed. Both build gates now require the exact model revision, backend, 384 dimensions, and 120/20 settings.
- No remaining implementation mismatch or unrelated scope change was found in this review. OpenRouter composition remains required for citation-bearing answers, and the ONNX change leaves that path unchanged.
- The release-gate and hosted runtime checks have since passed on the deployed commit. Live answer acceptance remains open: the latest Qwen request returned HTTP 429, and the CLI does not expose failure scope. The local key's daily free counter is exhausted, while Render key identity/quota remains unverified.

### Verification

- Full local suite: **99 passed**, one third-party Starlette/AnyIO deprecation warning.
- Pinned SQLite build assertion, FastMCP stdio discovery/tool-call smoke, compile check, both 30-case evaluation transports with thresholds, YAML parsing, and `git diff --check` passed.
- GitHub Actions run [36341666520](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36341666520) passed on `071dfb8`; Render deployment `dep-dasm8l8473hc738v0dkg` serves that exact SHA. The latest preflight memory samples reached 247,119,870/536,870,900 bytes; this is not a concurrency benchmark.
- The latest hosted preflight passed both privacy refusals and retrieval, then returned HTTP 503 after Qwen received HTTP 429. Its CLI output does not include the sanitized failure-scope field; no model resolved. Retry after provider availability is restored.

**Review summary:** Standards — no open actionable findings. Spec — the identified model-support, revision-cache, and exact-index release-gate gaps are fixed and deployed. Hosted answer acceptance remains open after the latest provider 429; the local key is quota-exhausted, but the Render key state is not independently confirmed.

## Review — tokenizer configuration and readiness

**Review date:** 2026-09-27

**Baseline:** `8eded3f` (working-tree changes)

**Standards:** The tokenizer limit is now part of both the SQLite index signature and the cached ONNX runtime key. GitHub Actions and Render call one shared exact-index verifier instead of maintaining duplicate assertions.

**Spec:** The SRS requires a reproducible pinned semantic index. Review found that changing tokenizer truncation could reuse vectors built under the old limit, and `/health/ready` accepted a sparse fallback that did not satisfy the selected MiniLM baseline. Both gaps are fixed: the public `RagIndex` regression verifies rebuild at 256→128 tokens and `/health/ready` rejects sparse fallback or a mismatched production index.

**Verification:** Red/green regressions passed; a clean 14-document/182-chunk index passed the pinned verifier; full local suite **101 passed**; local and hosted readiness, deep MCP discovery, and SQLite document listing returned HTTP 200; compileall, workflow/Blueprint YAML parsing, and `git diff --check` passed. Commit `071dfb8` passed [GitHub Actions run 36341666520](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36341666520) and is live on Render deployment `dep-dasm8l8473hc738v0dkg`.

## Review — demo UI clarity and disclosure

**Review date:** 2026-09-27

**Scope:** Remove duplicated evaluator/example entry points, align initial and failed health messaging, and state the synthetic-data/authentication boundary.

**Findings and changes:** The sidebar evaluator launcher and repeated prompt list were redundant with the header lab button and main example strip; they are removed. The chat greeting now says “Demo assistant,” while the service indicator starts at “Checking service.” Non-JSON health/index responses receive a stable HTTP status message instead of leaking a JavaScript parse exception. The UI, README, and SRS state that the public app has no employee authentication or role authorization; IDs select synthetic fixtures and do not establish access rights.

**Verification:** The public root-page regression passes; the complete local suite passed **101 tests** with the pinned SQLite index path configured. A local browser accessibility-tree review confirmed one evaluator entry point, one example strip, the synthetic/no-auth notice, and an online service indicator. No synthetic 500 response was injected, so the earlier transient local error remains undiagnosed. Production authorization and trace-field redaction remain open follow-up tickets.
