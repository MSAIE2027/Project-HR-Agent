# Deployment Status

**Application:** [https://project-hr-agent.onrender.com](https://project-hr-agent.onrender.com)

**Health:** [https://project-hr-agent.onrender.com/health/ready](https://project-hr-agent.onrender.com/health/ready)

**Render service:** `Project-HR-Agent` in workspace `MSAIE2027`

**Runtime commit:** `ead8c3395436959704c39503e3c72e965f91585e`

**Render deployment:** `dep-dasmt9npn0mc73947ko0`

## Current status

The live Render runtime is commit `ead8c33`, deployed as `dep-dasmt9npn0mc73947ko0`. That exact commit passed [GitHub Actions run 36344335941](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36344335941), including the pinned SQLite build gate, test suite, MCP stdio smoke, and both golden evaluations. Render metadata confirms `Project-HR-Agent`, branch `main`, Python runtime, `/health/ready`, manual deploys, and auto-deploy Off. The live build command matches `render.yaml` and the service started successfully.

The OpenCode Zen provider fallback and bounded SQLite response templates are published at `10833a5`. They passed **105 local tests** under Python 3.12, the pinned-index verifier, MCP stdio smoke, and both 30-case evaluations. [GitHub Actions run 36348984924](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36348984924) passed on that exact commit. The deploy job was skipped because the explicit CI deploy gate is off; the live Render runtime above predates these changes.

**Hosted answer generation is not verified, so the app is not ready for recording.** The latest preflight on the live release passed both privacy refusals and reached OpenRouter after policy retrieval and MCP tool calls. Qwen returned HTTP 429; the API returned HTTP 503 with no resolved model or unrefined draft. The deployed release predates the OpenCode and SQLite response fallbacks. The Render service now has an empty `OPENCODE_API_KEY` field for the owner to populate. Locally, the OpenCode model catalog returned HTTP 200, but a simulated OpenRouter quota handoff got HTTP 403 for two OpenCode routes and timed out on the third; no OpenCode model resolved. See the [sanitized hosted acceptance evidence](evidence/hosted-pto-smoke.md) and [fallback implementation record](docs/adr/0010-provider-and-sqlite-response-fallbacks.md).

At 18:50 UTC, a read-only OpenRouter key-status request using the local `.env` key reported the free-model daily counter at 51 used / 50 limit / 0 remaining. No extra OpenRouter generation retry was made after the 429. This is local-key metadata only; the Render key's quota is not independently confirmed. OpenRouter documents the [current-key counter](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key) and [free-tier request limit](https://openrouter.ai/pricing/).

The live `ead8c33` service reports a ready MiniLM ONNX/SQLite index: 14 documents, 182 chunks, 384 dimensions, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, 256-token limit, and 120/20 chunking. Deep health discovered all eight MCP tools over stdio. Readiness and document inspection returned HTTP 200. Two hosted privacy probes returned `refused` with no MCP tool calls or LLM event. The remote-work request reached OpenRouter after MCP retrieval and checks, then failed on Qwen HTTP 429; the current CLI output does not identify the quota scope.

After ONNX deployment, Render sampled memory at 71,155,710 bytes after startup and 274,866,180 bytes one minute later after the first policy request, against the 536,870,900-byte service limit. The service stayed live. This small sample does not establish peak or concurrent capacity. Historical PyTorch observations reached 536,264,700 bytes and later restarted during model loading, without an explicit OOM record.

A later idle-wake recheck on 2026-09-27 showed Render's loading interstitial in the browser. Render logs recorded successful `GET /health/ready` checks by 17:57:05 UTC; a fresh no-cache request at 18:01:53 UTC returned HTTP 200 with the app, SQLite index, MCP tools, and OpenRouter configuration ready. The browser tab remained on its stale loading page after the service was healthy, so the endpoint response is the readiness signal. This was a qualitative wake observation, not a controlled cold-start timing measurement. Memory samples for the new instance were 147,595,260 bytes at 17:57, 185,184,260 at 17:58, 222,978,050 at 17:59, and 224,882,690 at 18:00 UTC; this short sample is not a peak or concurrency benchmark. OpenRouter configuration was present, but no generation call was made during this recheck.

## Verification and demo gate

Before recording, populate the Render `OPENCODE_API_KEY`, manually deploy the CI-passing `10833a5` source, and rerun the hosted smoke. Confirm:

- PTO balance and policy response returns HTTP 200 with citations and the operational trace. If `llm_refinement.status=completed`, report its resolved model; if the bounded template answers, report `status=cached_template` and do not call it live LLM generation.
- International remote-work guidance returns cited policy evidence and the structured compliance result.
- The confirmation-gated email or ticket workflow stops before the mock action until the user confirms.
- Responses show no internal reasoning and preserve the required safety language.
- The first model-backed request completes without a service restart; the current observed ONNX sample is 274,866,180 bytes, but it is not a concurrency benchmark.
- Show the course quality, behavior, and system evidence: the 30-case proxy results and limits, local latency with priming separated from p50/p95, retrieval ablation, hosted memory observations, and hosted cold-start status. Cold-start duration is currently unmeasured; do not substitute local priming, readiness, or memory samples.
- Test the OpenRouter account-quota handoff to OpenCode and the bounded SQLite template route on the deployed revision. The 429 classifier stops only on an identifiable account-wide free daily cap.

The sanitized automated preflight is `python scripts/smoke_hosted_demo.py`. It sends synthetic requests through the configured OpenRouter chain and uses free-model quota; by default it does not confirm the mock email action. See the [demo runbook](demo/README.md) for the optional explicit confirmation flag.

## Repository access gate

The GitHub repository is private. A current read-only permission check reports `quantic-grader` has no repository permission (`none`). The repository link therefore is not yet verified as accessible to the course grader; the repository owner must grant read access before submission.

The hosted cold-start latency has not been isolated and measured; the idle-wake observation above establishes readiness only, not wake-to-ready duration. The course blueprint calls for system evidence covering latency, cold start, and ablation. Local evaluation latency excludes OpenRouter and is not a Render cold-start measurement. Capture wake-to-ready after Render confirms the instance has spun down, then time the first model-backed request separately; label the request as end-to-end because it includes OpenRouter. The presenter runbook records the protocol and current gap in [`demo/README.md`](demo/README.md). For setup and deployment procedures, see [`docs/local-to-render-workflow.md`](docs/local-to-render-workflow.md).
