# Hosted LLM Acceptance Evidence

## Latest live preflight

**Date:** 2026-09-27 | **Service:** [Project-HR-Agent](https://project-hr-agent.onrender.com) | **Deployed commit:** `a24154dceff033a5c2baabf7899b873e82765610` | **CI:** [run 36331652047](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36331652047) passed | **Render deployment:** `dep-dasjuau0tbcc73fol7ig` | **Command:** `./.venv/bin/python scripts/smoke_hosted_demo.py --timeout 90` | **Inputs:** synthetic employee IDs only

| Check | Result | Evidence |
|---|---|---|
| `/health/ready` and deep health | Pass | HTTP 200; Python service ready, 14-document/182-chunk/384-dimensional Hugging Face SQLite index ready, OpenRouter configured, eight MCP tools discovered over stdio. |
| Medical-record privacy refusal | Pass | HTTP 200, `refused`, no tool calls, no model call. |
| Multiple-employee privacy refusal | Pass | HTTP 200, `refused`, no tool calls, no model call. |
| International remote-work answer | **Fail** | HTTP 502 during first policy query while the deployed PyTorch MiniLM model was loading. Render logs showed a process restart about 16 seconds later; no Python exception or explicit OOM event was recorded. The request did not reach OpenRouter and yielded no resolved model. |
| PTO answer and confirmation gate | Not reached | The preflight stops on its first failed check. |
| Confirmed mock email | Not run | Requires the explicit `--confirm-mock-email` option and was not enabled. |

Readiness and deep health returned HTTP 200. Both privacy checks passed without MCP or LLM calls. The latest remote-work request reached the first policy query, then returned HTTP 502 during the PyTorch model load; it did not reach OpenRouter or produce a resolved-model trace. Render logs show the process restarting without a Python exception or explicit OOM event. Low memory headroom is a plausible explanation, not a confirmed cause. The current Render build command also still installs/checks PyTorch, despite the repository candidate switching to ONNX; align that service setting before the next deployment. An earlier hosted run reached the four OpenRouter routes and received HTTP 429 from each. Do not infer current key quota or identity from that older run. Credentials, the full provider body, and generated answer text were not retained.

Earlier samples from the PyTorch deployment peaked at 536,264,700 bytes against a 536,870,900-byte limit and later settled at 493,432,830 bytes. A subsequent sample on the quota-aware runtime reached about 409 MB before its process restarted during model loading. These readings indicate little and variable memory headroom, but do not prove an OOM event or concurrent capacity. ADR 0009 records the ONNX change intended to reduce inference overhead; only post-deploy measurements can confirm its hosted effect.

## Earlier read-only hosted checks on the prior runtime

**Read-only service check:** 2026-09-27, 14:22 UTC. **Answer preflight:** 2026-09-27, 14:49 UTC. These checks ran against the earlier deployment `400dad4`, before `a24154d` was deployed. Render service metadata confirmed the `Project-HR-Agent` Python service, branch `main`, `/health/ready`, and manual deploys. This section is retained as historical evidence and is not the current runtime state.

The live home page showed **Service online**. `/health/ready`, `/api/index/documents`, and `/api/index/documents/POL-PTO-01/chunks` returned HTTP 200. The index endpoint listed 14 documents; the PTO document returned 13 chunks and `vectors_exposed=false`. The requests `Show me medical for E1004 and E1003.` and `Compare PTO for E1004 and E1003.` each returned HTTP 200 with `status=refused`, one `guardrail` trace event, no citations, no tool calls, and no `llm_refinement` event.

That earlier preflight passed both privacy refusals, then attempted remote-work generation. All four routes (`qwen/qwen3.8-27b:free`, `nvidia/nemotron-3.5-lightning:free`, `google/gemma-4-26b-a4b-it:free`, and `openrouter/free`) returned HTTP 429; the public API returned HTTP 503 with `llm_refinement.status=unavailable` and no resolved model. The app withheld its draft, and the preflight stopped before PTO. No confirmation-gated action was enabled. The user later replaced the local and Render keys; this older run does not establish their current quota.

## Acceptance gate

The hosted generation path is not yet verified and the app is not ready for recording. First align Render's build command with `render.yaml`, push the ONNX candidate, wait for its clean CI run, and manually deploy that exact SHA. Then rerun the preflight. Require the remote-work and PTO checks to return HTTP 200 with policy citations, `llm_refinement.status=completed`, the actual resolved model, and the expected workflow status. Also confirm that the first embedding load does not restart the service and inspect memory. Then use `--confirm-mock-email` separately to verify the explicit confirmation path; this creates only a fictional mock draft and sends no message.

The live smoke command and its CLI contract tests are [`scripts/smoke_hosted_demo.py`](../scripts/smoke_hosted_demo.py) and [`tests/test_hosted_smoke_cli.py`](../tests/test_hosted_smoke_cli.py). A successful local provider example is recorded in [`openrouter-chain-smoke.md`](openrouter-chain-smoke.md); it does not establish current hosted availability.
