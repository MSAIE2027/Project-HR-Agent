# Deployment Status

**Application:** [https://project-hr-agent.onrender.com](https://project-hr-agent.onrender.com)

**Health:** [https://project-hr-agent.onrender.com/health/ready](https://project-hr-agent.onrender.com/health/ready)

**Render service:** `Project-HR-Agent` in workspace `MSAIE2027`

**Runtime commit:** `400dad45b329e35999feadd889bc249cda296969`

**Render deployment:** `dep-dashgbt9fdbs73dfd7cg`

## Current status

The service is live on 2026-09-27 at commit `400dad4`. The deployed settings match `render.yaml`: `Project-HR-Agent`, branch `main`, Python runtime, `/health/ready`, and manual deploys. Both `/health/ready` and `/health?deep=true` returned HTTP 200; the app reports the Hugging Face MiniLM 384-dimensional SQLite index (14 documents, 182 chunks) and all eight MCP tools over stdio. OpenRouter is configured, but health does not establish that generation succeeds.

The deployed runtime commit passed [GitHub Actions run 36321773923](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36321773923), including the full test suite, MCP smoke, and both golden-set evaluations. Render auto-deploy is off; the exact tested `main` commit was manually deployed.

**Hosted answer generation is not verified, so the app is not ready for recording.** The latest synthetic preflight returned HTTP 200 for both privacy refusals, then HTTP 503 for international remote-work guidance after all four configured model routes returned HTTP 429. `llm_refinement.status` was `unavailable`, and no model resolved; the app withheld its unrefined draft. A separate read-only request using the refreshed local `.env` key returned HTTP 429 with OpenRouter's message `Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day.` The deployed key's account metadata is not exposed by Render, but the hosted four-route failure is consistent with the same account-level limit. No credits were purchased and no paid model was substituted. See the [sanitized hosted acceptance evidence](evidence/hosted-pto-smoke.md).

The first post-deploy MiniLM query loaded the model without restarting the service, and Render readiness probes continued returning HTTP 200. Thirty-second memory samples peaked at 536,264,700 bytes against the 536,870,900-byte service limit, then settled at 493,432,830 bytes. The process remained live, but that cold-load peak leaves very little headroom and does not establish concurrent-load capacity.

## Verification and demo gate

Before recording, repeat synthetic requests on the deployed runtime after OpenRouter free-model access is available and confirm:

- PTO balance and policy response returns HTTP 200, citations, and `llm_refinement.status=completed` with the actual resolved model.
- International remote-work guidance returns cited policy evidence and the structured compliance result.
- The confirmation-gated email or ticket workflow stops before the mock action until the user confirms.
- Responses show no internal reasoning and preserve the required safety language.
- The first model-backed request completes without a service restart; current cold-load memory was near the free-plan limit.

The sanitized automated preflight is `python scripts/smoke_hosted_demo.py`. It sends synthetic requests through the configured OpenRouter chain and uses free-model quota; by default it does not confirm the mock email action. See the [demo runbook](demo/README.md) for the optional explicit confirmation flag.

The hosted cold-start latency has not been isolated and measured. Local evaluation latency excludes OpenRouter and is not a Render cold-start measurement. For setup and deployment procedures, see [`docs/local-to-render-workflow.md`](docs/local-to-render-workflow.md); for the presenter runbook, see [`demo/README.md`](demo/README.md).
