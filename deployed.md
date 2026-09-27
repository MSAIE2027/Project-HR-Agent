# Deployment Status

**Application:** [https://project-hr-agent.onrender.com](https://project-hr-agent.onrender.com)

**Health:** [https://project-hr-agent.onrender.com/health/ready](https://project-hr-agent.onrender.com/health/ready)

**Render service:** `Project-HR-Agent` in workspace `MSAIE2027`

**Runtime commit:** `071dfb8a8f590057f446684bc76ccc06b264435e`

**Render deployment:** `dep-dasm8l8473hc738v0dkg`

## Current status

The Render runtime is live on 2026-09-27 at commit `071dfb8`; it passed [GitHub Actions run 36341666520](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36341666520) and deployed as `dep-dasm8l8473hc738v0dkg`. The live build command matches `render.yaml`, including the shared pinned ONNX index assertion. Render service metadata confirms `Project-HR-Agent`, branch `main`, Python runtime, `/health/ready`, manual deploys, and auto-deploy Off. The service built the semantic SQLite index and started successfully.

The deployed `071dfb8` runtime passed [GitHub Actions run 36341666520](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36341666520), including the full test suite, MCP stdio smoke, both golden evaluations, and artifact upload. The manual deploy used that exact tested SHA. Render auto-deploy remains off.

**Hosted answer generation is not verified, so the app is not ready for recording.** The latest preflight passed both privacy refusals and reached OpenRouter after policy retrieval and MCP tool calls. Qwen returned HTTP 429; the API returned HTTP 503 with no resolved model or unrefined draft. This smoke output does not expose the sanitized failure-scope field, and the Render key's quota state is not independently visible. A separate read-only check of the local `.env` key showed its free-model daily allowance exhausted; this does not prove the Render key is the same. See the [sanitized hosted acceptance evidence](evidence/hosted-pto-smoke.md).

At 18:50 UTC, a read-only OpenRouter key-status request using the local `.env` key reported the free-model daily counter at 51 used / 50 limit / 0 remaining. No model-generation retry was made after the 429. This is local-key metadata only; the Render key is not exposed by the available read-only service APIs, so its quota state is not independently confirmed. OpenRouter documents the [current-key counter](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key) and [free-tier request limit](https://openrouter.ai/pricing/).

The live `071dfb8` service reports a ready MiniLM ONNX/SQLite index: 14 documents, 182 chunks, 384 dimensions, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, 256-token limit, and 120/20 chunking. Deep health discovered all eight MCP tools over stdio. Readiness and document inspection returned HTTP 200. Two hosted privacy probes returned `refused` with no MCP tool calls or LLM event. The remote-work request reached OpenRouter after MCP retrieval and checks, then failed on Qwen HTTP 429; the current CLI output does not identify the quota scope.

After ONNX deployment, Render sampled memory at 71,155,710 bytes after startup and 274,866,180 bytes one minute later after the first policy request, against the 536,870,900-byte service limit. The service stayed live. This small sample does not establish peak or concurrent capacity. Historical PyTorch observations reached 536,264,700 bytes and later restarted during model loading, without an explicit OOM record.

A later idle-wake recheck on 2026-09-27 showed Render's loading interstitial in the browser. Render logs recorded successful `GET /health/ready` checks by 17:57:05 UTC; a fresh no-cache request at 18:01:53 UTC returned HTTP 200 with the app, SQLite index, MCP tools, and OpenRouter configuration ready. The browser tab remained on its stale loading page after the service was healthy, so the endpoint response is the readiness signal. This was a qualitative wake observation, not a controlled cold-start timing measurement. Memory samples for the new instance were 147,595,260 bytes at 17:57, 185,184,260 at 17:58, 222,978,050 at 17:59, and 224,882,690 at 18:00 UTC; this short sample is not a peak or concurrency benchmark. OpenRouter configuration was present, but no generation call was made during this recheck.

## Verification and demo gate

Before recording, wait until OpenRouter's account-wide free quota is available and rerun the hosted smoke. Confirm:

- PTO balance and policy response returns HTTP 200, citations, and `llm_refinement.status=completed` with the actual resolved model.
- International remote-work guidance returns cited policy evidence and the structured compliance result.
- The confirmation-gated email or ticket workflow stops before the mock action until the user confirms.
- Responses show no internal reasoning and preserve the required safety language.
- The first model-backed request completes without a service restart; the current observed ONNX sample is 274,866,180 bytes, but it is not a concurrency benchmark.
- Show the course quality, behavior, and system evidence: the 30-case proxy results and limits, local latency with priming separated from p50/p95, retrieval ablation, hosted memory observations, and hosted cold-start status. Cold-start duration is currently unmeasured; do not substitute local priming, readiness, or memory samples.
- A citation-bearing answer reaches OpenRouter and reports its actual resolved model; the 429 classifier stops only on an identifiable account-wide free daily cap.

The sanitized automated preflight is `python scripts/smoke_hosted_demo.py`. It sends synthetic requests through the configured OpenRouter chain and uses free-model quota; by default it does not confirm the mock email action. See the [demo runbook](demo/README.md) for the optional explicit confirmation flag.

## Repository access gate

The GitHub repository is private. A current read-only permission check reports `quantic-grader` has no repository permission (`none`). The repository link therefore is not yet verified as accessible to the course grader; the repository owner must grant read access before submission.

The hosted cold-start latency has not been isolated and measured; the idle-wake observation above establishes readiness only, not wake-to-ready duration. The course blueprint calls for system evidence covering latency, cold start, and ablation. Local evaluation latency excludes OpenRouter and is not a Render cold-start measurement. Capture wake-to-ready after Render confirms the instance has spun down, then time the first model-backed request separately; label the request as end-to-end because it includes OpenRouter. The presenter runbook records the protocol and current gap in [`demo/README.md`](demo/README.md). For setup and deployment procedures, see [`docs/local-to-render-workflow.md`](docs/local-to-render-workflow.md).
