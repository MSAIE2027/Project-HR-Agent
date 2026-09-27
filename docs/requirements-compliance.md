# Requirements Compliance Snapshot

The complete source-to-evidence map is [`traceability-matrix.md`](traceability-matrix.md); its SRS source is [`../specs/system-requirements.md`](../specs/system-requirements.md).

| Area | Implementation | Current status |
|---|---|---|
| Web/API and local operation | FastAPI chat/workspace/health, Python 3.12 venv, local SQLite | Automated API tests and local setup commands pass. |
| Orchestration and workflows | Explicit tool routing, international remote-work and PTO flows, safety boundaries | Covered by the 25-case evaluation and API tests. |
| MCP | FastMCP SDK with eight typed tools; in-process local and stdio protocol path | stdio discovery/calls pass locally. |
| RAG and citations | Markdown/HTML ingestion, MiniLM 384d, 120/20 chunks, SQLite, MMR and family seeding | Measured comparison/ablation; local evaluation reports 100% citation-family proxy. |
| OpenRouter response generation | Required composition of every citation-bearing response from controlled draft, retrieved evidence, and structured facts; fail-closed provider and validation errors | Public API tests verify invocation on cited responses and HTTP 503 on missing provider or provider failure. One current-index local public `/chat` call passed with five citations and `llm_refinement=completed`; the golden set excludes OpenRouter calls. String-level checks do not prove semantic entailment, and hosted behavior remains unverified. |
| Safety | Synthetic records, injection refusal, escalation, confirmation gates, mock-only actions | Golden set action-safety proxy is 100%; no real HR system is connected. |
| Evaluation | 25-item golden set over in-process and stdio; 15-task latency sample | Workflow completion covers five workflow cases. In-process priming 6,369.82 ms; warm p50/p95 20.28/62.54 ms. Stdio priming 9,659.28 ms; p50/p95 8,645.27/11,180.99 ms include a fresh subprocess/model initialization per task. Fixture proxies, not human semantic judging; OpenRouter generation is excluded. |
| CI/CD and deploy configuration | GitHub Actions compile, tests, MCP smoke, threshold-gated golden evaluations and artifacts; optional tested-SHA Render deploy job | Hosted run `36289121722` passed for `42de2e8`; deploy job was skipped because the GitHub variable/secret are not configured. Render auto-deploy is Off; the service runtime and health path still need synchronization. |
| Deployment | Render service linked to `MSAIE2027/Project-HR-Agent`; assigned URL `https://project-hr-agent.onrender.com` | No deploy history; the existing service settings differ from the checked-in Blueprint, and no public response/cold-start is verified. |
| Demo | Current prompts and runbook for two full workflows plus safety examples | Local demo package and browser rehearsal are ready; recording and course submission remain presenter-owned. |

These values describe this checkout and this run only. Do not claim a score, a hosted URL, or deployed embedding settings without new evidence.
