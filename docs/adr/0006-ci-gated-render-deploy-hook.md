# ADR 0006: Trigger a tested Render commit from GitHub Actions

- **Status:** Accepted; the service is synchronized and deployed. The optional automatic deploy hook remains unconfigured.
- **Date:** 2026-09-26

## Context

At the time of this decision, the linked Render service had no deploy history and differed from the Blueprint: Docker runtime, deploy on commit, and no health-check path. Auto-deploy was switched Off in the dashboard and verified on 2026-09-27 before publishing `main`; later reconciliation set the service to Python with `/health/ready`. Hosted CI passed on `1130dde`, which was then deployed manually as `dep-das9kd59fdbs73cfutpg`; the opt-in deploy job was skipped. A deploy on commit could otherwise run before CI completes.

## Decision

Use the existing service name `Project-HR-Agent` in the Blueprint and set `autoDeployTrigger: off`. GitHub Actions owns the deploy gate: its `deploy` job depends on the complete `test` job, is disabled by default, and runs only for a push to `main` after `RENDER_DEPLOY_ENABLED=true` and `RENDER_DEPLOY_HOOK_URL` are configured. The deploy hook receives the tested `GITHUB_SHA` as `ref`.

## Consequences

- After the Blueprint has been synchronized, a code push cannot trigger Render independently of the configured CI gate.
- The deploy job is reviewable in the repository and deploys only after compile, pytest, stdio MCP smoke, both transport evaluations, and evidence upload complete.
- The GitHub secret must never appear in logs. The job suppresses the hook response and reports only the commit SHA.
- The service is linked to the repository and currently matches the Python runtime, build/start commands, and health path. The repo must have the Render deploy-hook secret added and the repository variable enabled before the opt-in job can run.
- Hosted health has passed, but OpenRouter generation remains unverified. The latest synthetic PTO request completed MCP retrieval and record checks, then returned 503 after two 429s, one model timeout, and an empty fallback response. Cold-start evidence is also pending.

## References

- [Render deploy hooks](https://render.com/docs/deploy-hooks)
- [Render deployment and auto-deploy settings](https://render.com/docs/deploys)
