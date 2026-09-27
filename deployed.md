# Deployment Status

**Runtime:** Live at [https://project-hr-agent.onrender.com](https://project-hr-agent.onrender.com), deployed from commit `1130dde62a5751c2fd64ee19092c2b16f7c4dfed` in Render deployment `dep-das9kd59fdbs73cfutpg`.

**Demo readiness:** Not ready for recording. Render health and tool discovery are healthy, and the hosted PTO trace completes the four MCP calls, but OpenRouter refinement returns HTTP 503. Do not claim a resolved hosted PTO model until `/chat` returns a cited response with `llm_refinement.status=completed` and its resolved `model`.

## Verified deployment configuration

- Render service `Project-HR-Agent`, workspace `MSAIE2027`, linked to `MSAIE2027/Project-HR-Agent` on `main`.
- Python runtime, `/health/ready` health check, and auto-deploy Off. The deploy was manually triggered only after hosted CI passed for the exact SHA.
- GitHub Actions run [36293782172](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36293782172) passed on `1130dde`, including the CPU-only assertion, dense Hugging Face SQLite index build, pytest, MCP stdio smoke, both 25-case evaluations, and evidence upload. The opt-in automatic Render job was skipped because its deploy hook is not configured. This is the prior hosted run; current working-tree changes still need CI.
- `GET /health/ready` and `GET /health?deep=true` returned HTTP 200. The live index reports 14 documents, 182 chunks, 384-dimensional `sentence-transformers/all-MiniLM-L6-v2` embeddings from Hugging Face, and no embedding error. Deep health discovered all eight MCP tools over stdio. OpenRouter is configured with Qwen 3.8 27B, Nemotron 3.5 Lightning, Gemma 4 26B A4B, then `openrouter/free`.

## Hosted response evidence

Earlier synthetic `/chat` requests against the live SHA timed out at 55–65 seconds or received HTTP 502 from the public edge. Later instrumented PTO requests returned application HTTP 503 after 51.7–138 seconds with the complete four-tool MCP trace. The latest pre-key-change retry received HTTP 429 from every route; another run had Nemotron numeric validation failure and a fallback timeout, and another returned an empty fallback completion with `finish_reason=length`. No model resolved. After the OpenRouter key was replaced, health still returned HTTP 200 and reported the provider as configured; two synthetic E1002 PTO requests returned HTTP 503 after 56.97 and 64.16 seconds, with all four routes marked unavailable and no citations or resolved model. An intentionally invalid `/chat` payload returned the expected HTTP 422, confirming the endpoint is reachable. The hosted calls confirm tool execution but not successful answer generation.

A local synthetic PTO request using the same configured model chain and real stdio MCP first returned HTTP 503 after 27.9 seconds: Qwen and Gemma returned 429, Nemotron failed numeric validation, and `openrouter/free` omitted a required structured number. A later local retry returned HTTP 200 with five `POL-PTO-01` citations and `llm_refinement.status=completed`; the requested route was `openrouter/free`, and the actual resolved model was `inclusionai/ling-3.0-flash-fin:free`. The prior successful local remote-work request resolved to `poolside/laguna-s-2.1:free`. Each model attribution applies only to its specific local request. The latest current-working-tree local PTO call after key replacement returned HTTP 503 in 10.72 seconds; all four routes returned HTTP 429 after the four MCP calls, with no citations or resolved model. No raw model output or key is retained.

Direct synthetic diagnostics then exercised the pinned InclusionAI route against five SQLite passages. Removing document/chunk/source-path metadata from the composer prompt produced three consecutive 2,000-token completions that passed the current validator in 1.3–3.3 seconds. This supports a prompt change for the app, but it does not prove a public `/chat` response or resolve the fact that the candidate is finance-focused. No raw model output or key is retained.

Sanitized request details are recorded in [`evidence/hosted-pto-smoke.md`](evidence/hosted-pto-smoke.md); earlier local route results remain in [`evidence/openrouter-chain-smoke.md`](evidence/openrouter-chain-smoke.md).

## Required before recording

Keep the key restricted to synthetic validation. Diagnose why the configured hosted model chain remains unavailable, then push the local fixes and wait for full CI. Manually deploy that tested SHA and repeat the synthetic PTO request. The demo gate is a hosted HTTP 200 with `check_pto_balance`, policy citations, `llm_refinement.status=completed`, an actual resolved model, and no reasoning leakage. Verify the remote-work scenario and confirmation-gated action flow on the exact live build before recording.

The user records and submits the 7–10 minute course presentation. See [`demo/README.md`](demo/README.md) and [`docs/local-to-render-workflow.md`](docs/local-to-render-workflow.md) for the rehearsal and deployment procedures.
