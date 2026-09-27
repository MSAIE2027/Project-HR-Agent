# MSAIE HR Agent — Completion Audit

This audit uses the official course project prompt and rubric PDF supplied with the project. It distinguishes locally verified behavior from hosted or presenter deliverables.

## Current local baseline

- 14 fictional policy documents in Markdown and HTML; 15,034 indexed policy-text words, 37.5 summed per-file page estimates, and 182 section-aware chunks in the current index.
- FastAPI workspace and API; explicit orchestrator; eight typed MCP tools; local in-process transport plus stdio MCP client/server path.
- Synthetic employee, PTO, benefits, office, and ticket data. Email and ticket actions are mock-only and confirmation-gated.
- MiniLM 384d, 120/20 chunks, current ranking weights, MMR λ=0.5, ten-candidate pool and five citation cap remain the approved retrieval baseline.
- Commit `6ce0da8`: 82 tests passed locally with one third-party deprecation warning; all 30 cases pass over both in-process and stdio transports. Hosted CI run [36306573067](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36306573067) passed the same SHA with the 30-case set; that SHA is live on Render deployment `dep-dasdc7fpn0mc73fu752g`. Current reports are in `evaluation/results*.json` and `evaluation/results*.md`.

## Delivery status

| Area | Status | Evidence / remaining work |
|---|---|---|
| Requirements, SRS, and traceability | Complete in repository | `specs/system-requirements.md`, `docs/traceability-matrix.md` |
| Supplied source-document review | Complete in repository | `docs/source-materials-review.md` |
| Architecture decisions | Complete in repository | `docs/adr/` |
| Tickets and implementation slices | Complete for local scope | `tickets/README.md`, `docs/implementation-slices.md` |
| Local app, workflows, RAG, MCP, confirmation boundary | Verified locally | `tests/`, `scripts/smoke_mcp.py`, `evaluation/results.md` |
| Retrieval comparison and ablation | Measured; evidence scoped | `evaluation/retrieval-comparison.md`, `evaluation/ablation-results.md` |
| CI and Render deployment gate | Hosted CI passed on the live tested SHA; automatic deploy hook remains opt-in | [GitHub Actions run 36306573067](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36306573067); `.github/workflows/ci.yml`, `render.yaml` |
| Public deployment and URL | Live and health-verified; generated response path awaits quota replenishment | Commit `6ce0da8` is live at `https://project-hr-agent.onrender.com` as deploy `dep-dasdc7fpn0mc73fu752g`; health reports a ready HF/SQLite index and eight-tool stdio discovery. A synthetic E1002 PTO request ran all four tools, then returned HTTP 503 after all four model routes returned HTTP 429. The local key metadata endpoint reported free-tier daily requests used 51/50 and none remaining. See `evidence/hosted-pto-smoke.md`. |
| GitHub grader access | Access unverified | The private repository link is `https://github.com/MSAIE2027/Project-HR-Agent`; `quantic-grader` access remains unverified |
| Hands-on browser/accessibility review | Local browser review complete | `evidence/ui-review.md`; limited to visual/basic keyboard inspection, not screen-reader or automated contrast validation |
| Demo package | Prepared for local rehearsal | `demo/README.md`, `docs/demo-script.md` |
| Recorded 7–10 minute course presentation | Presenter deliverable | Must be recorded and submitted by the student/group |
| Course dashboard submission | Presenter deliverable | Repository/video links and a group agreement when applicable must be submitted through the course workflow |

The 30-case metrics are deterministic rubric proxies, not independent semantic judgments. The hand-labeled retrieval sample is small and corpus-specific. The hosted health report confirms Hugging Face embeddings and real MCP discovery, but does not prove a successful OpenRouter answer. OpenRouter confirms the local key is valid but has exhausted its 50-request daily Free-tier quota; the live app is not demo-ready until a synthetic hosted PTO response returns a validated answer with a resolved model after quota replenishment.

See [`docs/traceability-matrix.md`](docs/traceability-matrix.md) for requirement-by-requirement mapping and [`evidence/index.md`](evidence/index.md) for commands and evidence limits.
