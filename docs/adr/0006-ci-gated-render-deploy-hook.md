# ADR 0006: Trigger a tested Render commit from GitHub Actions

- **Status:** Accepted
- **Date:** 2026-09-26

## Context

Render can deploy a connected service directly from a source-control update. That could publish a commit before its required CI checks finish, so deployment must be gated on the exact commit that passed CI.

## Decision

Use the existing service name `Project-HR-Agent` in the Blueprint and set `autoDeployTrigger: off`. GitHub Actions owns the deploy gate: its `deploy` job depends on the complete `test` job, is disabled by default, and runs only for a push to `main` after `RENDER_DEPLOY_ENABLED=true` and `RENDER_DEPLOY_HOOK_URL` are configured. The deploy hook receives the tested `GITHUB_SHA` as `ref`.

## Consequences

- The deploy job runs only after the complete test job succeeds and passes the tested `GITHUB_SHA` to Render.
- The deploy hook is opt-in through repository configuration; its secret is never printed to workflow logs.
- Current deployment health and release evidence are kept in [`../../deployed.md`](../../deployed.md) and [`../../evidence/index.md`](../../evidence/index.md), not in this decision record.

## References

- [Render deploy hooks](https://render.com/docs/deploy-hooks)
- [Render deployment and auto-deploy settings](https://render.com/docs/deploys)
