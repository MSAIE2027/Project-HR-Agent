# ADR 0006: Trigger a tested Render commit from GitHub Actions

- **Status:** Accepted locally; external secrets and Render synchronization remain pending.
- **Date:** 2026-09-26

## Context

At the time of this decision, the linked Render service had no deploy history and differed from the Blueprint: Docker runtime, deploy on commit, and no health-check path. Auto-deploy was switched Off in the dashboard and verified on 2026-09-27 before publishing `main`; the Docker runtime and health-check mismatch remain. Hosted CI passed on published commit `42de2e8`, while the opt-in deploy job was skipped. A deploy on commit could otherwise run before CI completes.

## Decision

Use the existing service name `Project-HR-Agent` in the Blueprint and set `autoDeployTrigger: off`. GitHub Actions owns the deploy gate: its `deploy` job depends on the complete `test` job, is disabled by default, and runs only for a push to `main` after `RENDER_DEPLOY_ENABLED=true` and `RENDER_DEPLOY_HOOK_URL` are configured. The deploy hook receives the tested `GITHUB_SHA` as `ref`.

## Consequences

- After the Blueprint has been synchronized, a code push cannot trigger Render independently of the configured CI gate.
- The deploy job is reviewable in the repository and deploys only after compile, pytest, stdio MCP smoke, both transport evaluations, and evidence upload complete.
- The GitHub secret must never appear in logs. The job suppresses the hook response and reports only the commit SHA.
- The current external service still needs a Blueprint sync or dashboard reconciliation. The repo must be connected, the Render deploy-hook secret added, and the repository variable enabled before the deploy job can run.
- Hosted health, OpenRouter generation, and cold-start evidence remain separate post-deploy checks.

## References

- [Render deploy hooks](https://render.com/docs/deploy-hooks)
- [Render deployment and auto-deploy settings](https://render.com/docs/deploys)
