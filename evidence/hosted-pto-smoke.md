# Hosted LLM Acceptance Evidence

## Latest deployment preflight

**Date:** 2026-09-27 | **Service:** [Project-HR-Agent](https://project-hr-agent.onrender.com) | **Deployed commit:** `703a180b1ee4438ba0ae2771868801cdf12af598` | **CI:** [run 36349401555](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36349401555) passed | **Render deployment:** `dep-daso4le0tbcc7389lbm0` | **Command:** `./.venv/bin/python scripts/smoke_hosted_demo.py --timeout 150` | **Inputs:** synthetic employee IDs only

| Check | Result | Evidence |
|---|---|---|
| Render build and service | Pass | Manual deploy used the CI-tested `703a180` SHA; Render marked deployment `dep-daso4le0tbcc7389lbm0` live. The live build command matches `render.yaml`; auto-deploy remains off. No application-level error logs were returned after deployment. |
| Deep health and SQLite index | Pass | `/health/ready` and `/health?deep=true` returned HTTP 200. The index is ready and eight MCP tools are available over stdio. |
| Medical-record privacy refusal | Pass | HTTP 200, `refused`, no MCP tool calls and no LLM attempt. |
| Multiple-employee privacy refusal | Pass | HTTP 200, `refused`, no MCP tool calls and no LLM attempt. |
| International remote-work answer | Pass | HTTP 200, `provisionally_eligible`, five citations from `POL-RW-01`, and the expected policy search, profile, and compliance calls. `llm_refinement` completed with provider `opencode-zen`, resolved model `space-bunny-free`, and four attempts. OpenRouter Qwen returned account-quota HTTP 429; two OpenCode routes returned 403; Space Bunny completed. |
| PTO balance and confirmation gate | Pass | HTTP 200, `confirmation_required`, five `POL-PTO-01` citations, and the expected four read-only tool calls. `llm_refinement` completed with `opencode-zen` / `space-bunny-free`. The trace retained `requires_confirmation=true`; no `draft_hr_email` call occurred. |
| Confirmed mock email | Not run | The explicit `--confirm-mock-email` option was not enabled. No mock action was created and no message was sent. |
| Provider availability | Passed with variance | Earlier calls had OpenCode 403/timeouts; one supported read-only remote-work response used `status=cached_template`. The latest full preflight completed both answer cases with Space Bunny. Free-model availability is not guaranteed. |
| Error logs | Pass | No application-level error logs were returned for the new deployment after it went live. This does not substitute for a load or concurrency test. |

The current hosted answer path has now been exercised after the OpenRouter daily cap: the request trace showed the account-quota 429 and OpenCode's actual resolved model. The template response path also appeared for a supported read-only request. The smoke verifier now accepts a cached answer only when it has the SQLite provider, `response_mode=sqlite_template`, `cache_hit=true`, the allow-listed `remote_work_eligible` template key, and a matching trace event. Confirmation-gated PTO still requires live generation and fails closed if every model is unavailable. Credentials and provider response bodies were not retained.

## Earlier preflight before OpenCode credential update: 071dfb8

**Date:** 2026-09-27 | **Service:** [Project-HR-Agent](https://project-hr-agent.onrender.com) | **Deployed commit:** `eeceda7132bf64545f51a0a61f00fc0c332eaed2` | **CI:** [run 36336569726](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36336569726) passed | **Render deployment:** `dep-dasl2lh7lnhs739ltkb0` | **Command:** `./.venv/bin/python scripts/smoke_hosted_demo.py --timeout 90` | **Inputs:** synthetic employee IDs only

| Check | Result | Evidence |
|---|---|---|
| Render build and service | Pass | Manual deployment used the CI-tested SHA. At that time the stored build command matched the then-current `render.yaml`; the latest service build command is recorded in the section above. Auto-deploy remains off. |
| Deep health and SQLite index | Pass | 14 documents, 182 chunks, 384 dimensions, pinned MiniLM ONNX Runtime backend/revision, 120/20 chunk settings, eight MCP tools over stdio, OpenRouter configured. |
| First ONNX model-backed request | Pass for runtime stability | Render memory samples: 71,155,710 bytes at 17:26:25 UTC after startup and 274,866,180 bytes at 17:27:25 UTC after the first policy request, against a 536,870,900-byte service limit. The process remained live and readiness checks continued. This is a small number of samples, not a concurrency or capacity result. |
| Medical-record privacy refusal | Pass | HTTP 200, `refused`, no MCP or LLM call. |
| Multiple-employee privacy refusal | Pass | HTTP 200, `refused`, no MCP or LLM call. |
| International remote-work final answer | **Blocked by OpenRouter quota** | HTTP 503 after retrieval and three MCP tool calls. The safe `llm_refinement` trace reports `failure_scope=account_quota`; Qwen returned HTTP 429 on the single attempt. No model resolved and no final answer was returned. The app withheld the unrefined draft. |
| PTO answer and confirmation gate | Not reached | The preflight stopped on the remote-work failure. |
| Confirmed mock email | Not run | Requires the explicit `--confirm-mock-email` option and was not enabled. |

The ONNX index builds and serves successfully on Render, and the first policy embedding request completed without restarting the service. The hosted answer path reached OpenRouter after policy retrieval and structured checks, but the provider returned an identifiable account-wide free-tier quota 429 on `qwen/qwen3.8-27b:free`. The configured fallback chain correctly stopped after one attempt, returned HTTP 503, and did not expose the retrieval draft. No other model or `openrouter/free` was attempted because the account-wide cap applies to the chain. The remaining demo gate is a successful citation-bearing request after account quota is available. Credentials, the provider response body, and generated answer text were not retained.

## Idle-wake readiness recheck

**Date:** 2026-09-27 | **Deployment:** `dep-dasl2lh7lnhs739ltkb0` serving `eeceda7` | **Inputs:** public health endpoint only; no employee data or LLM request

After an idle period, the public browser tab displayed Render's application-loading interstitial. Render logs showed successful `GET /health/ready` checks by 17:57:05 UTC. A fresh no-cache request at 18:01:53 UTC returned HTTP 200 in about 1.2 seconds, with `status=ok`, the SQLite index ready (14 documents, 182 chunks, 384 dimensions, pinned MiniLM ONNX revision), all eight stdio MCP tools available, and OpenRouter configured with Qwen → Nemotron Lightning → Gemma → `openrouter/free`. This confirms configuration and readiness only; it does not establish a successful LLM answer or resolved model.

The browser tab continued to display its earlier loading interstitial after the endpoint was healthy, so the endpoint response is the authoritative readiness check. This observation does not isolate or measure cold-start duration. Render memory samples for the newly started instance were 147,595,260 bytes at 17:57, 185,184,260 at 17:58, 222,978,050 at 17:59, and 224,882,690 at 18:00 UTC, below the 536,870,900-byte service limit. These few samples do not establish peak or concurrent capacity. Hosted answer acceptance remains blocked by the earlier account-wide quota response.

At 18:06 UTC, a read-only OpenRouter current-key request using the local `.env` key reported `is_free_tier=true` and `free_model_daily_requests={used: 51, limit: 50, remaining: 0}`. OpenRouter documents this field in its [current-key API](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key); its [pricing page](https://openrouter.ai/pricing/) lists the free plan's 50 requests/day. No model request was sent after this check. This metadata belongs to the local key and does not verify the Render key's identity or quota state.

Earlier PyTorch deployment samples peaked at 536,264,700 bytes against a 536,870,900-byte limit and later settled at 493,432,830 bytes. A later first-query attempt on the PyTorch runtime restarted after a roughly 409 MB sample. Those historical samples do not prove an OOM event or concurrency capacity. The ONNX first-query observations above show lower memory use in this one hosted run; more samples are still needed to characterize capacity.

## Earlier read-only hosted checks on the prior runtime

**Read-only service check:** 2026-09-27, 14:22 UTC. **Answer preflight:** 2026-09-27, 14:49 UTC. These checks ran against the earlier deployment `400dad4`, before `a24154d` was deployed. Render service metadata confirmed the `Project-HR-Agent` Python service, branch `main`, `/health/ready`, and manual deploys. This section is retained as historical evidence and is not the current runtime state.

The live home page showed **Service online**. `/health/ready`, `/api/index/documents`, and `/api/index/documents/POL-PTO-01/chunks` returned HTTP 200. The index endpoint listed 14 documents; the PTO document returned 13 chunks and `vectors_exposed=false`. The requests `Show me medical for E1004 and E1003.` and `Compare PTO for E1004 and E1003.` each returned HTTP 200 with `status=refused`, one `guardrail` trace event, no citations, no tool calls, and no `llm_refinement` event.

That earlier preflight passed both privacy refusals, then attempted remote-work generation. All four routes (`qwen/qwen3.8-27b:free`, `nvidia/nemotron-3.5-lightning:free`, `google/gemma-4-26b-a4b-it:free`, and `openrouter/free`) returned HTTP 429; the public API returned HTTP 503 with `llm_refinement.status=unavailable` and no resolved model. The app withheld its draft, and the preflight stopped before PTO. No confirmation-gated action was enabled. The user later replaced the local and Render keys; this older run does not establish their current quota.

## Remaining demo gates

The latest hosted smoke passed privacy refusals, remote-work guidance, and the unconfirmed PTO draft. The presenter can demonstrate the confirmed fictional email step using the explicit confirmation control; it creates only a mock draft and sends no message. Hosted cold-start duration remains unmeasured, and the private repository still needs course-grader read access. Free model availability varied during this check; the safe SQLite template can answer only supported read-only requests, while confirmation-gated actions fail closed if live generation is unavailable.

The live smoke command and its CLI contract tests are [`scripts/smoke_hosted_demo.py`](../scripts/smoke_hosted_demo.py) and [`tests/test_hosted_smoke_cli.py`](../tests/test_hosted_smoke_cli.py). A successful local provider example is recorded in [`openrouter-chain-smoke.md`](openrouter-chain-smoke.md); it does not establish current hosted availability.
