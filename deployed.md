# Deployment Status

**Application:** [https://project-hr-agent.onrender.com](https://project-hr-agent.onrender.com)

**Health:** [https://project-hr-agent.onrender.com/health/ready](https://project-hr-agent.onrender.com/health/ready)

**Render service:** `Project-HR-Agent` in workspace `MSAIE2027`

**Runtime commit:** `703a180b1ee4438ba0ae2771868801cdf12af598`

**Render deployment:** `dep-daso4le0tbcc7389lbm0`

## Current status

The live Render runtime is commit `703a180`, deployed as `dep-daso4le0tbcc7389lbm0`. That exact commit passed [GitHub Actions run 36349401555](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36349401555), including the pinned SQLite build gate, full test suite, MCP stdio smoke, both golden evaluations, and artifact upload. The manual deploy used this CI-tested SHA. Render metadata confirms `Project-HR-Agent`, branch `main`, Python runtime, `/health/ready`, and auto-deploy Off. The live build command matches `render.yaml` and the service is healthy.

Main has since advanced to `83dbb50`, which passed [full GitHub Actions run 36353250083](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36353250083), including 117 tests, the pinned SQLite build, MCP stdio smoke, and both golden evaluations. That change completes the smoke trace verifier and shares model-route constants; it does not change live request behavior. Render remains on `703a180`, and the deploy job was skipped because automatic deployment is disabled.

The OpenCode Zen provider fallback and bounded SQLite response templates are live. The latest complete hosted smoke passed both read-only privacy refusals, the remote-work guidance, and the PTO confirmation gate. The two answer cases resolved `space-bunny-free` after OpenRouter Qwen returned an account-quota 429 and the first two OpenCode routes returned 403. The PTO response remained `confirmation_required`; no mock action was invoked. Earlier attempts saw provider 403s/timeouts and one safe remote-work `cached_template` response, so free-model availability remains variable.

The latest smoke confirmed the OpenCode key is usable for live generation on `space-bunny-free`. When model generation is unavailable, the UI and trace identify the bounded SQLite template route for supported read-only requests. The confirmation-gated PTO path requires a live model and returns fail-closed if none resolves. See the [sanitized hosted acceptance evidence](evidence/hosted-pto-smoke.md) and [fallback implementation record](docs/adr/0010-provider-and-sqlite-response-fallbacks.md).

At 18:50 UTC, a read-only OpenRouter key-status request using the local `.env` key reported the free-model daily counter at 51 used / 50 limit / 0 remaining. No extra OpenRouter generation retry was made after the 429. This is local-key metadata only; the Render key's quota is not independently confirmed. OpenRouter documents the [current-key counter](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key) and [free-tier request limit](https://openrouter.ai/pricing/).

The live `703a180` service reports a ready MiniLM ONNX/SQLite index: 14 documents, 182 chunks, 384 dimensions, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, 256-token limit, and 120/20 chunking. Deep health discovered all eight MCP tools over stdio. Readiness and document inspection returned HTTP 200. The latest privacy probes returned `refused` with no MCP tool calls or LLM event. The hosted answer traces show OpenRouter's `account_quota` 429 followed by a completed OpenCode response.

After ONNX deployment, Render sampled memory at 71,155,710 bytes after startup and 274,866,180 bytes one minute later after the first policy request, against the 536,870,900-byte service limit. The service stayed live. This small sample does not establish peak or concurrent capacity. Historical PyTorch observations reached 536,264,700 bytes and later restarted during model loading, without an explicit OOM record.

A later idle-wake recheck on 2026-09-27 showed Render's loading interstitial in the browser. Render logs recorded successful `GET /health/ready` checks by 17:57:05 UTC; a fresh no-cache request at 18:01:53 UTC returned HTTP 200 with the app, SQLite index, MCP tools, and OpenRouter configuration ready. The browser tab remained on its stale loading page after the service was healthy, so the endpoint response is the readiness signal. This was a qualitative wake observation, not a controlled cold-start timing measurement. Memory samples for the new instance were 147,595,260 bytes at 17:57, 185,184,260 at 17:58, 222,978,050 at 17:59, and 224,882,690 at 18:00 UTC; this short sample is not a peak or concurrency benchmark. OpenRouter configuration was present, but no generation call was made during this recheck.

## Verification and demo gate

The latest hosted smoke passed. Before recording, confirm the app remains healthy and use the operational trace to distinguish live model output from a cached SQLite template. The current evidence is:

- Latest hosted smoke: PTO and international remote-work each returned HTTP 200 with five citations and `llm_refinement.status=completed`, provider `opencode-zen`, resolved model `space-bunny-free`.
- The PTO confirmation gate stopped before `draft_hr_email`; the hosted smoke did not confirm or create a mock action.
- Privacy refusals returned HTTP 200 with no MCP tool call or LLM attempt; answer checks rejected reasoning markers.
- One earlier remote-work request used the SQLite template after both model chains failed. Its trace was labeled `cached_template`; this is an answer formatter for supported read-only cases, not live generation.
- Render had no application-level error logs after the new deployment. Cold-start duration and peak/concurrent memory remain unmeasured.
- Show the course quality, behavior, and system evidence: the 30-case proxy results and limits, local latency with priming separated from p50/p95, retrieval ablation, hosted memory observations, and hosted cold-start status. Cold-start duration is currently unmeasured; do not substitute local priming, readiness, or memory samples.
- Keep the separate OpenRouter account-quota handoff and SQLite template paths visible in the trace. The 429 classifier stops only on an identifiable account-wide free daily cap; provider-specific 429s continue the route chain.

The sanitized automated preflight is `python scripts/smoke_hosted_demo.py`. It sends synthetic requests through the configured OpenRouter chain and uses free-model quota; by default it does not confirm the mock email action. See the [demo runbook](demo/README.md) for the optional explicit confirmation flag.

## Repository access gate

The GitHub repository is private. A current read-only permission check reports `quantic-grader` has no repository permission (`none`). The repository link therefore is not yet verified as accessible to the course grader; the repository owner must grant read access before submission.

The hosted cold-start latency has not been isolated and measured; the idle-wake observation above establishes readiness only, not wake-to-ready duration. The course blueprint calls for system evidence covering latency, cold start, and ablation. Local evaluation latency excludes OpenRouter and is not a Render cold-start measurement. Capture wake-to-ready after Render confirms the instance has spun down, then time the first model-backed request separately; label the request as end-to-end because it includes OpenRouter. The presenter runbook records the protocol and current gap in [`demo/README.md`](demo/README.md). For setup and deployment procedures, see [`docs/local-to-render-workflow.md`](docs/local-to-render-workflow.md).
