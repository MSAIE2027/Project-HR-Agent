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

Render settings match `render.yaml`; readiness and deep health returned HTTP 200. Both privacy checks passed without MCP or LLM calls. The latest retrieved remote-work request reached MCP, SQLite retrieval, and the required OpenRouter chain, which failed closed after all four routes returned HTTP 429. A subsequent read-only `/auth/key` check accepted the rotated local `.env` key, but the response exposed no free-model daily request counter or reset timestamp. Render does not expose its key identity or quota. Credentials, the full provider body, and generated answer text were not retained.

The first post-deploy query loaded MiniLM without restarting the Render service. Readiness probes continued returning HTTP 200 on the same instance. Thirty-second Render samples peaked at 536,264,700 bytes against a 536,870,900-byte limit and then settled at 493,432,830 bytes. This is evidence that the session and probes stayed alive through this cold load, not a concurrency-capacity result; the peak leaves little free-plan memory headroom.

## Latest read-only hosted checks

**Read-only service check:** 2026-09-27, 14:22 UTC. **Latest answer preflight:** 2026-09-27, 14:49 UTC. Render service metadata confirms the `Project-HR-Agent` Python service, branch `main`, `/health/ready`, and manual deploys. The live runtime remains `400dad4`; the documentation-only `main` commit `cf8e0db` passed CI run [36324920372](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36324920372), whose Render deploy job was skipped.

The live home page showed **Service online**. `/health/ready`, `/api/index/documents`, and `/api/index/documents/POL-PTO-01/chunks` returned HTTP 200. The index endpoint listed 14 documents; the PTO document returned 13 chunks and `vectors_exposed=false`. The requests `Show me medical for E1004 and E1003.` and `Compare PTO for E1004 and E1003.` each returned HTTP 200 with `status=refused`, one `guardrail` trace event, no citations, no tool calls, and no `llm_refinement` event.

The latest full preflight passed both privacy refusals, then attempted remote-work generation. All four routes (`qwen/qwen3.8-27b:free`, `nvidia/nemotron-3.5-lightning:free`, `google/gemma-4-26b-a4b-it:free`, and `openrouter/free`) returned HTTP 429; the public API returned HTTP 503 with `llm_refinement.status=unavailable` and no resolved model. The app withheld its draft, and the preflight stopped before PTO. No confirmation-gated action was enabled.

## Acceptance gate

The hosted generation path is not yet verified and the app is not ready for recording. When at least one configured route can generate again, rerun the preflight and require the remote-work and PTO checks to return HTTP 200 with policy citations, `llm_refinement.status=completed`, the actual resolved model, and the expected workflow status. Then use `--confirm-mock-email` separately to verify the explicit confirmation path; this creates only a fictional mock draft and sends no message.

The live smoke command and its CLI contract tests are [`scripts/smoke_hosted_demo.py`](../scripts/smoke_hosted_demo.py) and [`tests/test_hosted_smoke_cli.py`](../tests/test_hosted_smoke_cli.py). A successful local provider example is recorded in [`openrouter-chain-smoke.md`](openrouter-chain-smoke.md); it does not establish current hosted availability.
