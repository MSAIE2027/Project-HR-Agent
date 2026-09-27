# ADR 0007: Reuse the MCP stdio Session for the App Lifetime

- **Status:** Accepted
- **Date:** 2026-09-27

## Context

Before this decision, the hosted app opened a new MCP stdio subprocess for every chat request. Each policy search could load another Python process and Hugging Face MiniLM model. A hosted request returned HTTP 502 during a model-load window; Render metrics peaked at 535,429,120 bytes against a 536,870,900-byte service limit. The logs contained no application exception, so memory pressure is a strong hypothesis rather than a proven root cause.

## Decision

The FastAPI lifespan starts one official MCP SDK `ClientSession` over a FastMCP stdio subprocess. The app reuses that session for requests, serializes each orchestrated tool sequence through it, and closes it during shutdown. One-off smoke and evaluation callers may continue using temporary sessions when they do not manage an app lifespan. OpenRouter composition happens after the MCP sequence releases its lock.

This keeps the real MCP protocol, tool schemas, retrieval model, chunking, ranking, and public response contract unchanged.

## Consequences

- The first policy search after startup can still pay the MiniLM model-load cost. Later searches reuse the loaded model and SQLite connections.
- The deployed first MiniLM query kept the Render instance live and readiness probes continued to pass. Thirty-second samples peaked at 536,264,700 bytes against the 536,870,900-byte service limit, then settled at 493,432,830 bytes. The peak leaves little margin and does not establish concurrent capacity.
- Tool sequences are serialized. Model generation occurs outside the MCP lock, so a slow OpenRouter call does not hold the shared tool session.
- If the persistent process exits, the affected request returns an MCP-unavailable result and updates the cached MCP health state. Routine `/health/ready` probes read that state without waiting for the MCP session lock. Explicit `/health?deep=true` performs live discovery; restarting the app creates a fresh session. The MCP SDK's stdio task group is owned by the lifespan task, so request handlers do not close or replace it.
- Hosted OpenRouter answer acceptance remains pending because all four configured routes returned HTTP 429. The rotated local key is accepted by read-only key metadata, but that response does not expose a free-model request counter or reset time, so the source of the route failures is not confirmed.

## Verification

The public `/chat` integration test sends two cited questions over stdio and asserts one subprocess start, then simulates a disconnected session and verifies the request fails safely and readiness turns unhealthy. A separate readiness test verifies probes do not wait on the MCP lock. GitHub Actions run `36321773923` passed, and the tested commit `400dad4` is live on Render deployment `dep-dashgbt9fdbs73dfd7cg`; readiness and deep tool discovery returned HTTP 200. That deployment's first hosted MiniLM load remained live but sampled near the service memory limit. A later preflight on `a24154d` returned HTTP 502 and the process restarted during PyTorch model loading; the cause was not proven and is tracked in [`../../evidence/hosted-pto-smoke.md`](../../evidence/hosted-pto-smoke.md). The OpenRouter answer path remains a separate release gate.

## Evidence

`mcp_client/client.py`, `app/main.py`, `tests/test_app.py`, [deployment status](../../deployed.md), and [hosted preflight evidence](../../evidence/hosted-pto-smoke.md).
