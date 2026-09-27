# ADR 0005: Gate Render Auto-Deploy on Passing CI

- **Status:** Superseded by ADR 0006
- **Date:** 2026-09-26

**Superseded by [ADR 0006](0006-ci-gated-render-deploy-hook.md).** This records the original checksPass approach; current deployment uses a tested-SHA GitHub deploy job and disables independent Render auto-deploy.

## Context

At the time this initial decision was recorded, the assignment required a free-tier-compatible deployment gated on checks passing, and no Git remote or verified Render service had been confirmed. Later hosting inspection found a linked Render resource whose settings differed from the Blueprint; see superseding ADR 0006.

## Decision

Keep the Render Blueprint as the hosting definition and set `autoDeployTrigger: checksPass`. Add GitHub Actions CI for syntax/import checks, pytest, and MCP stdio coverage. Keep API credentials in host-managed environment variables. The blueprint uses `MSAIE_LLM_API_KEY`, matching the application’s configuration.

## Consequences

- Once a GitHub repository and Render service are connected, Render waits for linked CI checks before auto-deploying.
- No hosted behavior or public URL is claimed until a deployment is explicitly configured and health-checked.
- Render cold starts may rebuild the local SQLite index and load/download MiniLM; deployment measurements must distinguish cold from warm operation.

## Evidence

`.github/workflows/ci.yml`, `render.yaml`, `docs/local-to-render-workflow.md`, `deployed.md`.

## Reference

Render’s Blueprint reference documents `checksPass` as “Trigger a deploy only if the linked branch's CI checks pass”: <https://render.com/docs/blueprint-spec>. Render's deployment guide states that no deploy is triggered if checks fail or no checks are detected: <https://render.com/docs/deploys>.
