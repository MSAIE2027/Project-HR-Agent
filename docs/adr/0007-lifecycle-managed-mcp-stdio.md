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
- The MCP subprocess remains resident, so Render memory use must be checked after deployment; reusing a process does not by itself prove the service fits the free-tier limit.
- Tool sequences are serialized. Model generation occurs outside the MCP lock, so a slow OpenRouter call does not hold the shared tool session.
- If the persistent process exits, the affected request returns an MCP-unavailable result. `/health/ready` performs live discovery and reports the service unavailable; restarting the app creates a fresh session. The MCP SDK's stdio task group is owned by the lifespan task, so request handlers do not close or replace it.
- Render memory and answer generation remain post-deploy acceptance checks. Reusing a process does not prove the service fits its free-tier memory limit.

## Verification

The public `/chat` integration test sends two cited questions over stdio and asserts one subprocess start, then simulates a disconnected session and verifies the request fails safely and readiness turns unhealthy. A separate readiness test verifies live MCP discovery is part of `/health/ready`. Hosted memory and answer-generation acceptance remain separate release checks.

## Evidence

`mcp_client/client.py`, `app/main.py`, `tests/test_app.py`, [deployment status](../../deployed.md), and [hosted preflight evidence](../../evidence/hosted-pto-smoke.md).
