# Hosted LLM Acceptance Evidence

## Latest live preflight

**Date:** 2026-09-27 | **Service:** [Project-HR-Agent](https://project-hr-agent.onrender.com) | **Deployed commit:** `400dad45b329e35999feadd889bc249cda296969` | **CI:** [run 36321773923](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36321773923) passed | **Render deployment:** `dep-dashgbt9fdbs73dfd7cg` | **Command:** `./.venv/bin/python scripts/smoke_hosted_demo.py --timeout 150` | **Inputs:** synthetic employee IDs only

| Check | Result | Evidence |
|---|---|---|
| `/health/ready` and deep health | Pass | HTTP 200; Python service ready, 14-document/182-chunk/384-dimensional Hugging Face SQLite index ready, OpenRouter configured, eight MCP tools discovered over stdio. |
| Medical-record privacy refusal | Pass | HTTP 200, `refused`, no tool calls, no model call. |
| Multiple-employee privacy refusal | Pass | HTTP 200, `refused`, no tool calls, no model call. |
| International remote-work answer | **Fail** | HTTP 503 after four model attempts; all three pinned models and `openrouter/free` returned HTTP 429; `llm_refinement.status=unavailable`, no resolved model. |
| PTO answer and confirmation gate | Not reached | The preflight stops on its first failed check. |
| Confirmed mock email | Not run | Requires the explicit `--confirm-mock-email` option and was not enabled. |

Render settings match `render.yaml`; readiness and deep health returned HTTP 200. Both privacy checks passed without MCP or LLM calls. The first retrieved remote-work request reached MCP, SQLite retrieval, and the required OpenRouter chain, which failed closed after all four routes returned HTTP 429. A separate request using the refreshed local `.env` key returned HTTP 429 with OpenRouter's message: `Rate limit exceeded: free-models-per-day. Add 10 credits to unlock 1000 free model requests per day.` This confirms the local key's account is at its free-model daily limit. Render does not expose its key's account metadata; the hosted four-route 429 is consistent with that same limit. No credits were purchased or paid route substituted. Credentials, the full provider body, and generated answer text were not retained.

The first post-deploy query loaded MiniLM without restarting the Render service. Readiness probes continued returning HTTP 200 on the same instance. Thirty-second Render samples peaked at 536,264,700 bytes against a 536,870,900-byte limit and then settled at 493,432,830 bytes. This is evidence that the session and probes stayed alive through this cold load, not a concurrency-capacity result; the peak leaves little free-plan memory headroom.

## Acceptance gate

The hosted generation path is not yet verified and the app is not ready for recording. After the free-model daily limit resets or the account owner enables free-model access, rerun the preflight and require the remote-work and PTO checks to return HTTP 200 with policy citations, `llm_refinement.status=completed`, the actual resolved model, and the expected workflow status. Then use `--confirm-mock-email` separately to verify the explicit confirmation path; this creates only a fictional mock draft and sends no message.

The live smoke command and its CLI contract tests are [`scripts/smoke_hosted_demo.py`](../scripts/smoke_hosted_demo.py) and [`tests/test_hosted_smoke_cli.py`](../tests/test_hosted_smoke_cli.py). A successful local provider example is recorded in [`openrouter-chain-smoke.md`](openrouter-chain-smoke.md); it does not establish current hosted availability.
