# Deployment Status

**Application:** [https://project-hr-agent.onrender.com](https://project-hr-agent.onrender.com)

**Health:** [https://project-hr-agent.onrender.com/health/ready](https://project-hr-agent.onrender.com/health/ready)

**Render service:** `Project-HR-Agent` in workspace `MSAIE2027`

**Runtime commit:** `6ce0da8fd3d410d5a1093006463b5896d114fea4`

**Render deployment:** `dep-dasdc7fpn0mc73fu752g`

## Current status

The service is live and readiness returned HTTP 200 on 2026-09-27. It reports the Hugging Face MiniLM 384-dimensional SQLite index and eight MCP tools over stdio. Readiness also reports OpenRouter as configured; that confirms configuration is present, not that generation succeeds.

The deployed runtime commit passed [GitHub Actions run 36306573067](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36306573067) before it was manually deployed. Render auto-deploy is off. The later documentation-only commits on `main` do not change the deployed runtime.

**Hosted answer generation is not verified, so the app is not ready for recording.** After the OpenRouter configuration was refreshed, the latest live preflight returned HTTP 200 for both privacy refusals, then HTTP 503 on the international remote-work request. All four configured model routes returned HTTP 429; `llm_refinement.status` was `unavailable`, and no model resolved. The public app failed closed. A read-only check confirms the local key's Free-model allowance is exhausted; this explains local 429s and is consistent with the hosted result, but Render's key quota cannot be independently inspected. OpenRouter still lists all four configured model IDs as free text models. See the [sanitized hosted acceptance evidence](evidence/hosted-pto-smoke.md).

## Verification and demo gate

Before recording, repeat synthetic requests on the deployed runtime and confirm:

- PTO balance and policy response returns HTTP 200, citations, and `llm_refinement.status=completed` with the actual resolved model.
- International remote-work guidance returns cited policy evidence and the structured compliance result.
- The confirmation-gated email or ticket workflow stops before the mock action until the user confirms.
- Responses show no internal reasoning and preserve the required safety language.

The sanitized automated preflight is `python scripts/smoke_hosted_demo.py`. It sends synthetic requests through the configured OpenRouter chain and uses free-model quota; by default it does not confirm the mock email action. See the [demo runbook](demo/README.md) for the optional explicit confirmation flag.

The hosted cold-start latency has not been isolated and measured. Local evaluation latency excludes OpenRouter and is not a Render cold-start measurement. For setup and deployment procedures, see [`docs/local-to-render-workflow.md`](docs/local-to-render-workflow.md); for the presenter runbook, see [`demo/README.md`](demo/README.md).
