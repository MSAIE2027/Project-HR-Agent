# Requirements Traceability Matrix

The authoritative grading source is the course project prompt and rubric PDF provided with this project. This matrix records implementation locations and evidence from the current local checkout; it does not claim a public deployment or a submitted presentation.

| Requirement | Implementation / source | Verification evidence | Status |
|---|---|---|---|
| Supplied source review and requirement authority | `docs/source-materials-review.md`, official course prompt PDF | Source inventory identifies the project prompt as authoritative and maps supplemental materials to SRS/ADRs. | Reviewed and mapped locally |
| Environment and reproducibility | `README.md`, `requirements.txt`, `.env.example`, `scripts/start_local.sh` | Local startup and `/health` smoke check; syntax compilation | Verified locally |
| Markdown + HTML ingestion and metadata | `rag/ingest.py`, `policies/` | `tests/test_rag.py`; current index reports 14 documents, 15,034 parsed policy words, 37.5 summed page estimates, and 182 chunks | Verified locally |
| Embedding and chunk choice | `rag/index.py`, `evaluation/ablation-results.md` | MiniLM 384d, 120/20; comparison report records equal metrics for 120/20, 160/24, and 220/30 | Verified for this corpus |
| RAG, citations, multi-family evidence | `agent/orchestrator.py`, `mcp_server/tools.py` | `tests/test_evaluation.py`; `evaluation/results.md`; `evaluation/retrieval-comparison.md` | Verified locally; small labeled sets |
| Required OpenRouter response generation | `app/main.py`, `agent/llm.py`, `.env.example`, `render.yaml` | Public `/chat` tests assert cited responses call the provider, confirmation/clarification statuses are included, missing provider fails closed, and invalid output is rejected; current expanded-index smoke and attempts are in `evidence/openrouter-chain-smoke.md` | Implemented and passed one current-index local live preflight; still requires hosted verification |
| Agent orchestration and two workflows | `agent/orchestrator.py` | `tests/test_app.py`; 25-item `evaluation/results.md` | Verified locally |
| MCP server, typed tools, protocol client | `mcp_server/server.py`, `mcp_server/tools.py`, `mcp_client/client.py` | `tests/test_mcp.py`; `scripts/smoke_mcp.py`; all 25 golden scenarios pass over stdio in `evaluation/results-stdio.md` | Verified locally over protocol |
| Trace and safe failure behavior | `app/main.py`, `agent/models.py`, `agent/orchestrator.py` | API/UI tests; golden-set safety, clarification, missing-record, and escalation cases | Verified locally |
| Confirmation-gated mock actions | `agent/orchestrator.py`, `mcp_server/tools.py` | Tests and golden cases cover unconfirmed and confirmed email/ticket actions; no live integration exists | Verified locally |
| Web application and health endpoint | `app/main.py`, `app/static/index.html` | API/UI tests and [`evidence/ui-review.md`](../evidence/ui-review.md) local desktop/narrow viewport review | Verified locally; no screen-reader or contrast audit |
| Deployment and public URL | `render.yaml`, `.github/workflows/ci.yml`, `deployed.md` | Tested-SHA deploy job depends on the full CI test job and is disabled until external secrets are set; Render resource is linked to the private repo but has no deploy history; auto-deploy is Off, while Docker runtime and health-check settings still need synchronization | Pending Render configuration sync, credential setup, and hosted app validation |
| GitHub repository and grader access | GitHub repository link and repository permission for `quantic-grader` | Private repo `MSAIE2027/Project-HR-Agent` contains published `main`; hosted CI passed on `42de2e8`; grader access remains unverified. | Published; grader-access verification pending |
| CI/CD and deployment gate | `.github/workflows/ci.yml`, `render.yaml` | Workflow runs compileall, full pytest, explicit MCP discovery/tool-call smoke, per-case plus aggregate-threshold golden gates, and uploads both report pairs; first hosted run passed all checks; deploy job depends on CI and is opt-in via GitHub variable/secret | Hosted CI passed; deploy remains disabled pending configuration |
| 20–30 task evaluation, metrics, latency | `evaluation/golden_set.json`, `evaluation/run_evaluation.py`, `evaluation/results*.json`, `evaluation/results*.md` | 25 cases over in-process and stdio; workflow completion denominator is the five `workflow` cases; priming time separated; nearest-rank p50/p95 and transport-specific interpretation | Verified locally; not an independent semantic evaluation |
| Ablation/comparison | `evaluation/run_ablation.py`, `evaluation/ablation-results.*`, `evaluation/retrieval-comparison.*` | Existing measured chunk/top-k/MMR comparisons | Verified locally; corpus-specific |
| Architecture and design documentation | `docs/architecture.md`, `design-and-evaluation.md`, `docs/adr/` | Architecture and decisions linked from README | Verified in source |
| AI-tooling disclosure | `ai-tooling.md` | File present; update includes this completion pass | Verified in source |
| Demo tasks and presenter instructions | `docs/demo-script.md`, `demo/` | Exact current prompts and expected traces; both workflows rehearsed locally and recorded in `evidence/ui-review.md` | Local demo package ready |
| Recorded 7–10 minute presentation | Presenter-created video and course submission | Runbook covers two task walkthroughs, MCP details, design, deployment, CI/CD, and evaluation; no recording or submission is present. Group members must follow the course camera/ID and agreement rules if applicable. | Presenter deliverable |
| Course dashboard submission | Repository and presentation links; group agreement when applicable | Course submission is external to this repository. | Presenter deliverable |

## Evidence quality notes

- The local full golden-set run reports deterministic rubric-based proxies; groundedness is not an independent semantic entailment judgment.
- The retrieval route and ablation queries are hand-labeled and small. They support the documented configuration choice for this corpus, not a universal optimum.
- `huggingface_dense_cosine` evidence is from this local checkout. It does not establish the embedding path of a deployed service.
- One current-index local free-model response passed preflight after two transient failures. Hosted CI passed for commit `42de2e8`; the public host has no deploy history, and cold-start and hosted provider behavior remain unverified.
- The recorded presentation, GitHub grader access, and course-dashboard submission are not artifacts that can be verified from this local checkout.
