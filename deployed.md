# Deployment Status

**Runtime:** Live at [https://project-hr-agent.onrender.com](https://project-hr-agent.onrender.com), deployed from commit `6ce0da8fd3d410d5a1093006463b5896d114fea4` in Render deployment `dep-dasdc7fpn0mc73fu752g`.

**Demo readiness:** Not ready for recording. Render health and tool discovery are healthy, and the hosted PTO trace completes the four MCP calls, but OpenRouter refinement returns HTTP 503. Do not claim a resolved hosted PTO model until `/chat` returns a cited response with `llm_refinement.status=completed` and its resolved `model`.

## Verified deployment configuration

- Render service `Project-HR-Agent`, workspace `MSAIE2027`, linked to `MSAIE2027/Project-HR-Agent` on `main`.
- Python runtime, `/health/ready` health check, and auto-deploy Off. The deploy was manually triggered only after hosted CI passed for the exact SHA.
- GitHub Actions run [36306573067](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36306573067) passed on `6ce0da8` in 5m03s, including the CPU-only assertion, dense Hugging Face SQLite index build, pytest, MCP stdio smoke, both 30-case evaluations, and evidence upload. The opt-in automatic Render job is not configured; the exact tested `main` SHA was manually deployed after CI passed.
- `GET /health/ready` and `GET /health?deep=true` returned HTTP 200. The live index reports 14 documents, 182 chunks, 384-dimensional `sentence-transformers/all-MiniLM-L6-v2` embeddings from Hugging Face, and no embedding error. Deep health discovered all eight MCP tools over stdio. OpenRouter is configured with Qwen 3.8 27B, Nemotron 3.5 Lightning, Gemma 4 26B A4B, then `openrouter/free`.

## Hosted response evidence

Earlier synthetic `/chat` requests against the live SHA timed out at 55–65 seconds or received HTTP 502 from the public edge. Later instrumented PTO requests returned application HTTP 503 after 51.7–138 seconds with the complete four-tool MCP trace. The latest pre-key-change retry received HTTP 429 from every route; another run had Nemotron numeric validation failure and a fallback timeout, and another returned an empty fallback completion with `finish_reason=length`. No model resolved. After the OpenRouter key was replaced, health still returned HTTP 200 and reported the provider as configured; two synthetic E1002 PTO requests returned HTTP 503 after 56.97 and 64.16 seconds, with all four routes marked unavailable and no citations or resolved model. An intentionally invalid `/chat` payload returned the expected HTTP 422, confirming the endpoint is reachable. The hosted calls confirm tool execution but not successful answer generation.

The latest request, against deployed commit `6ce0da8`, asked for synthetic employee `E1002`'s PTO balance. It returned HTTP 503 after 79.2 seconds. Policy search, profile lookup, balance lookup, and compliance all completed; each of the four OpenRouter routes returned HTTP 429, so the response contained no citations or resolved model. Separately, the current local `.env` key authenticated successfully at OpenRouter's current-key endpoint and reported a free-tier allowance of 50 daily requests, 51 used, and 0 remaining. This is consistent with the hosted 429 responses, though Render's stored key was not read back or compared. No paid route was called, and no key, provider response body, or generated answer is stored. OpenRouter currently lists a 50-request daily cap for its Free plan ([pricing](https://openrouter.ai/pricing/)).

A local synthetic PTO request using the same configured model chain and real stdio MCP first returned HTTP 503 after 27.9 seconds: Qwen and Gemma returned 429, Nemotron failed numeric validation, and `openrouter/free` omitted a required structured number. A later local retry returned HTTP 200 with five `POL-PTO-01` citations and `llm_refinement.status=completed`; the requested route was `openrouter/free`, and the actual resolved model was `inclusionai/ling-3.0-flash-fin:free`. The prior successful local remote-work request resolved to `poolside/laguna-s-2.1:free`. Each model attribution applies only to its specific local request. The latest current-working-tree local PTO call after key replacement returned HTTP 503 in 10.72 seconds; all four routes returned HTTP 429 after the four MCP calls, with no citations or resolved model. No raw model output or key is retained.

Direct synthetic diagnostics then exercised the pinned InclusionAI route against five SQLite passages. Removing document/chunk/source-path metadata from the composer prompt produced three consecutive 2,000-token completions that passed the current validator in 1.3–3.3 seconds. This supports a prompt change for the app, but it does not prove a public `/chat` response or resolve the fact that the candidate is finance-focused. No raw model output or key is retained.

Sanitized request details are recorded in [`evidence/hosted-pto-smoke.md`](evidence/hosted-pto-smoke.md); earlier local route results remain in [`evidence/openrouter-chain-smoke.md`](evidence/openrouter-chain-smoke.md).

## Required before recording

Keep the key restricted to synthetic validation. The current local OpenRouter free-tier allowance is exhausted; wait for its daily quota to become available, then repeat the hosted synthetic PTO request. The demo gate is a hosted HTTP 200 with `check_pto_balance`, policy citations, `llm_refinement.status=completed`, an actual resolved model, and no reasoning leakage. Verify the remote-work scenario and confirmation-gated action flow on the exact live build before recording.

The user records and submits the 7–10 minute course presentation. See [`demo/README.md`](demo/README.md) and [`docs/local-to-render-workflow.md`](docs/local-to-render-workflow.md) for the rehearsal and deployment procedures.
