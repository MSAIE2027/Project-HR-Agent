# Hosted LLM Acceptance Evidence

## Latest live preflight

**Date:** 2026-09-27 | **Service:** [Project-HR-Agent](https://project-hr-agent.onrender.com) | **Deployed commit:** `6ce0da8fd3d410d5a1093006463b5896d114fea4` | **Command:** `./.venv/bin/python scripts/smoke_hosted_demo.py` | **Inputs:** synthetic employee IDs only

| Check | Result | Evidence |
|---|---|---|
| `/health/ready` and deep health | Pass | HTTP 200; index ready, OpenRouter configured, eight MCP tools discovered. |
| Medical-record privacy refusal | Pass | HTTP 200, `refused`, no tool calls, no model call. |
| Multiple-employee privacy refusal | Pass | HTTP 200, `refused`, no tool calls, no model call. |
| International remote-work answer | **Fail** | HTTP 503 after four model attempts; `llm_refinement.status=unavailable`, no resolved model. |
| PTO answer and confirmation gate | Not reached | The preflight stops on its first failed check. |
| Confirmed mock email | Not run | Requires the explicit `--confirm-mock-email` option and was not enabled. |

The refreshed hosted configuration still failed closed: all four model routes returned HTTP 429, so the request produced no resolved model or answer. A read-only check of the refreshed local key returned HTTP 200 and reported Free-tier status with `free_model_daily_requests` at 51 used of 50, with none remaining. This explains why local free-model requests cannot currently complete. OpenRouter lists 50 requests per day for its Free plan ([pricing](https://openrouter.ai/pricing/)) and states that failed attempts count toward the daily allowance ([free-model guide](https://openrouter.ai/blog/tutorials/how-to-get-the-lowest-cost-llm-inference-on-openrouter/)). The hosted 429s are consistent with the same allowance being exhausted, but Render does not expose its key's quota metadata, so their cause is not independently confirmed. Generated text, provider response bodies, and credentials were not retained.

## Acceptance gate

The hosted generation path is not yet verified and the app is not ready for recording. After provider access is available, rerun the preflight and require the remote-work and PTO checks to return HTTP 200 with policy citations, `llm_refinement.status=completed`, the actual resolved model, and the expected workflow status. Then use `--confirm-mock-email` separately to verify the explicit confirmation path; this creates only a fictional mock draft and sends no message.

The live smoke command and its CLI contract tests are [`scripts/smoke_hosted_demo.py`](../scripts/smoke_hosted_demo.py) and [`tests/test_hosted_smoke_cli.py`](../tests/test_hosted_smoke_cli.py). A successful local provider example is recorded in [`openrouter-chain-smoke.md`](openrouter-chain-smoke.md); it does not establish current hosted availability.
