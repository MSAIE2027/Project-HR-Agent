# Deployment Status

**Application:** [https://project-hr-agent.onrender.com](https://project-hr-agent.onrender.com)

**Health:** [https://project-hr-agent.onrender.com/health/ready](https://project-hr-agent.onrender.com/health/ready)

**Render service:** `Project-HR-Agent` in workspace `MSAIE2027`

**Runtime commit:** `a24154dceff033a5c2baabf7899b873e82765610`

**Render deployment:** `dep-dasjuau0tbcc73fol7ig`

## Current status

The Render runtime is live on 2026-09-27 at commit `a24154d`; that code passed [GitHub Actions run 36331652047](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36331652047). The ONNX working-tree change is not yet in CI or deployed. Render service metadata confirms `Project-HR-Agent`, branch `main`, Python runtime, `/health/ready`, manual deploys, and auto-deploy Off. Its live build command still explicitly installs and checks PyTorch, while the current repository `render.yaml` uses ONNX Runtime. Update the service build command to match `render.yaml` before deploying the ONNX candidate. Readiness and SQLite previews were previously verified; health does not establish that generation succeeds.

The deployed `a24154d` runtime passed [GitHub Actions run 36331652047](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36331652047), including the full test suite and evaluations. The ONNX candidate requires its own clean CI run before deployment. Render auto-deploy is off; after CI passes, deploy the exact tested SHA manually.

**Hosted answer generation is not verified, so the app is not ready for recording.** The latest preflight passed both privacy refusals, then returned HTTP 502 on the first remote-work query while the deployed PyTorch MiniLM model was loading. Render logs showed a process restart shortly afterward, without a Python exception or explicit OOM record. This suggests a low-memory risk but does not prove the cause; the request did not reach OpenRouter, did not resolve a model, and did not reach PTO. An earlier run reached all four OpenRouter routes and received 429s. The local `.env` key has since been rotated, but Render's stored key identity/quota is not exposed. See the [sanitized hosted acceptance evidence](evidence/hosted-pto-smoke.md).

The live home page currently displays **Service online**. Read-only SQLite endpoints return 14 document rows and 13 chunks for `POL-PTO-01`, with vector payloads excluded. Two hosted privacy probes—medical details for two IDs and comparing PTO for two IDs—returned `refused` with a guardrail trace and no MCP tool calls or LLM event. These checks do not establish successful answer generation.

The prior PyTorch runtime's first MiniLM load completed, but memory samples peaked at 536,264,700 bytes against the 536,870,900-byte service limit and later settled at 493,432,830 bytes. A later first-query attempt restarted after a sample near 409 MB. These separate observations do not prove an OOM event or concurrent capacity; reducing inference overhead with pinned ONNX Runtime is the current mitigation. Hosted memory must be sampled again after the candidate deploy.

## Verification and demo gate

Before recording, align the live Render build command with `render.yaml`, push the candidate, wait for its full CI run, then deploy that tested SHA manually. Repeat synthetic requests and confirm:

- PTO balance and policy response returns HTTP 200, citations, and `llm_refinement.status=completed` with the actual resolved model.
- International remote-work guidance returns cited policy evidence and the structured compliance result.
- The confirmation-gated email or ticket workflow stops before the mock action until the user confirms.
- Responses show no internal reasoning and preserve the required safety language.
- The first model-backed request completes without a service restart and ONNX cold-load memory leaves reasonable headroom.
- A citation-bearing answer reaches OpenRouter and reports its actual resolved model; the 429 classifier stops only on an identifiable account-wide free daily cap.

The sanitized automated preflight is `python scripts/smoke_hosted_demo.py`. It sends synthetic requests through the configured OpenRouter chain and uses free-model quota; by default it does not confirm the mock email action. See the [demo runbook](demo/README.md) for the optional explicit confirmation flag.

## Repository access gate

The GitHub repository is private. A current read-only permission check reports `quantic-grader` has no repository permission (`none`). The repository link therefore is not yet verified as accessible to the course grader; the repository owner must grant read access before submission.

The hosted cold-start latency has not been isolated and measured. Local evaluation latency excludes OpenRouter and is not a Render cold-start measurement. For setup and deployment procedures, see [`docs/local-to-render-workflow.md`](docs/local-to-render-workflow.md); for the presenter runbook, see [`demo/README.md`](demo/README.md).
