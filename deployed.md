# Deployment Status

**Application:** [https://project-hr-agent.onrender.com](https://project-hr-agent.onrender.com)

**Health:** [https://project-hr-agent.onrender.com/health/ready](https://project-hr-agent.onrender.com/health/ready)

**Render service:** `Project-HR-Agent` in workspace `MSAIE2027`

**Runtime commit:** `703a180b1ee4438ba0ae2771868801cdf12af598`

**Render deployment:** `dep-daso4le0tbcc7389lbm0`

## Current status

**Current hosted answer acceptance is pending re-verification.** The recorded warm OpenCode request completed successfully, but it does not verify the latest saved Render OpenCode key. Render auto-deploy is Off, so the reviewed candidate must first pass CI and be deployed manually; then run one read-only synthetic acceptance request and inspect its sanitized trace. Keep this gate separate from CI evidence. The private repository still reports no `quantic-grader` permission. Do not call the hosted demo fully ready until the post-deploy answer and repository-access gates pass.

The live Render runtime is commit 703a180b1ee4438ba0ae2771868801cdf12af598, deployed as dep-daso4le0tbcc7389lbm0. This exact revision passed [GitHub Actions run 36349401555](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36349401555), including the pinned SQLite build gate, full test suite, MCP stdio smoke, both golden evaluations, and artifact upload. The manual deploy used this CI-tested SHA. Render metadata confirms Project-HR-Agent, branch main, Python runtime, /health/ready, auto-deploy Off, and healthy service state; the live build command matches render.yaml.

Verifier implementation commit `83dbb50` passed [full GitHub Actions run 36353250083](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36353250083), including 117 tests, the pinned SQLite build, MCP stdio smoke, and both golden evaluations. It completes the smoke trace verifier and shares model-route constants without changing live request behavior. The evidence-only follow-up `d57667c` also passed [full run 36353534151](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36353534151). Render remains on `703a180`; both deploy jobs were skipped because automatic deployment is disabled.

The OpenCode Zen provider fallback and bounded SQLite response templates are live. A previous complete hosted smoke passed both read-only privacy refusals, remote-work guidance, and the PTO confirmation gate. The answer cases resolved `space-bunny-free` after OpenRouter Qwen returned an account-quota 429 and the first two OpenCode routes returned 403. The PTO response remained `confirmation_required`; no mock action was invoked. A later warm read-only remote-work request returned HTTP 200 with five citations, resolving `space-bunny-free` in 6.781 seconds after the same OpenRouter quota and two OpenCode 403s. Free-model availability remains variable. These prior traces do not verify the latest saved Render key.

The successful requests above establish that the key configured at that time completed those samples; they do not establish that the latest saved Render key is active. During this audit, a generic PTO policy-summary request returned HTTP 503 after OpenRouter quota exhaustion, two OpenCode 403 responses, and a timeout on the third OpenCode route. That query was outside the SQLite template allowlist, so fail-closed behavior was expected. When model generation is unavailable, only supported read-only requests with fresh matching facts and citations use the build-seeded SQLite templates; confirmation-gated PTO still fails closed. See the [sanitized hosted acceptance evidence](evidence/hosted-pto-smoke.md) and [fallback implementation record](docs/adr/0010-provider-and-sqlite-response-fallbacks.md).

At 18:50 UTC, a read-only OpenRouter key-status request using the local `.env` key reported the free-model daily counter at 51 used / 50 limit / 0 remaining. No extra OpenRouter generation retry was made after the 429. This is local-key metadata only; the Render key's quota is not independently confirmed. OpenRouter documents the [current-key counter](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key) and [free-tier request limit](https://openrouter.ai/pricing/).

The live `703a180` service reports a ready MiniLM ONNX/SQLite index: 14 documents, 182 chunks, 384 dimensions, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, 256-token limit, and 120/20 chunking. Deep health discovered all eight MCP tools over stdio. Readiness and document inspection returned HTTP 200. Recorded privacy probes returned `refused` with no MCP tool calls or LLM event. Recorded hosted answer traces show OpenRouter's `account_quota` 429 followed by a completed OpenCode response.

After ONNX deployment, Render sampled memory at 71,155,710 bytes after startup and 274,866,180 bytes one minute later after the first policy request, against the 536,870,900-byte service limit. The service stayed live. This small sample does not establish peak or concurrent capacity. Historical PyTorch observations reached 536,264,700 bytes and later restarted during model loading, without an explicit OOM record.

Render live service metadata confirms the web compute plan is Free (plan=free), with one instance; buildPlan=starter is the separate build-pipeline tier. Render documents that Free web services spin down after 15 minutes without inbound traffic and take about one minute to spin up ([Free service limits](https://render.com/docs/free), [compute plans](https://render.com/docs/compute-plans)).

The first post-wake read-only chat ran from 22:10:35.018843 to 22:10:51.235556 UTC (**16.216 seconds**, HTTP 200, five citations). Its trace used the bounded SQLite template (cached_template) after live providers failed, so it was not model generation. After the OpenCode credential update, a second read-only chat on the already-warm instance ran from 22:18:02.042895 to 22:18:08.715677 UTC (**6.672 seconds**, HTTP 200, five citations, provisionally_eligible). OpenRouter reported account quota; OpenCode Zen completed with space-bunny-free after four model attempts. No action tool ran. This confirms the currently configured OpenCode route worked for this sample; it does not establish future free-model availability.

## Verification and demo gate

The previous complete hosted smoke and a subsequent live request completed through OpenCode; a separate generic policy-summary request failed closed during provider errors. Treat those as historical samples until a post-deploy read-only request verifies the latest saved Render key. Before recording, confirm the app remains healthy and use the operational trace to distinguish live model output from a cached SQLite template. The recorded evidence is:

- Previous complete hosted smoke: PTO and international remote-work each returned HTTP 200 with five citations and `llm_refinement.status=completed`, provider `opencode-zen`, resolved model `space-bunny-free`. The warm direct read-only remote-work probe returned HTTP 200, five citations, 6.781 seconds, and the same resolved model; neither verifies the latest saved key.
- Generic PTO policy-summary probe: HTTP 503 after OpenRouter quota, OpenCode 403s, and a timeout. It did not match the narrow SQLite allowlist; the controlled draft remained withheld.
- The PTO confirmation gate stopped before `draft_hr_email`; the hosted smoke did not confirm or create a mock action.
- Privacy refusals returned HTTP 200 with no MCP tool call or LLM attempt; answer checks rejected reasoning markers.
- One earlier remote-work request used the SQLite template after both model chains failed. Its trace was labeled `cached_template`; this is an answer formatter for supported read-only cases, not live generation.
- Render had no application-level error logs after the new deployment. One wake-to-ready sample is now measured at 33.466 seconds; a typical-startup distribution, peak memory, and concurrent capacity remain unmeasured.
- Show the course quality, behavior, and system evidence: include the one hosted wake-to-ready sample, keep local latency separate from hosted timing, and identify deterministic scores as proxies.
- Keep the separate OpenRouter account-quota handoff and SQLite template paths visible in the trace. The 429 classifier stops only on an identifiable account-wide free daily cap; provider-specific 429s continue the route chain.

The sanitized automated preflight is `python scripts/smoke_hosted_demo.py`. It sends synthetic requests through the configured OpenRouter chain and uses free-model quota; by default it does not confirm the mock email action. See the [demo runbook](demo/README.md) for the optional explicit confirmation flag.

## Repository access gate

The GitHub repository is private. A current read-only permission check reports `quantic-grader` has no repository permission (`none`). The repository link therefore is not yet verified as accessible to the course grader; the repository owner must grant read access before submission.

One Render Free wake-to-ready sample is recorded above. The exact spin-down event was not exposed, and the first post-wake chat used the SQLite template; the later live OpenCode request ran on an already-warm instance. Do not combine these into a cold-start-to-live-answer figure or present one sample as an SLA. For a repeat, verify idle state, time the readiness request, then time a separate model-backed request and record both scopes. See the [demo runbook](demo/README.md) and [deployment workflow](docs/local-to-render-workflow.md).
