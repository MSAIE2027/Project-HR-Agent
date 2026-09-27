# MSAIE HR Agent

A standalone, fictional HR support agent. It answers policy questions with cited retrieval, looks up synthetic employee records, and prepares confirmation-gated mock actions. It does not access real employee data or contact production HR systems.

## Run locally

Use Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
./scripts/start_local.sh
```

The launcher loads `.env`, uses `.venv`, starts the web app, waits for its health endpoint, and opens the local page. The readiness wait defaults to 180 seconds; set `MSAIE_STARTUP_TIMEOUT_SECONDS` to override it. Pass `--no-browser` to keep it in the terminal without opening a browser. Use `./scripts/start_local.sh --detach` and `./scripts/stop_local.sh` for a background process.

The server reads `.env` only at startup. After changing OpenRouter settings, stop the current process with `./scripts/stop_local.sh` and start it again so the running app receives the new configuration.

The first start builds a local SQLite policy index and loads the configured embedding model. The Hugging Face model is downloaded on first use. Embeddings run locally and need no provider key. Every citation-bearing answer requires `https://openrouter.ai/api/v1`: copy `.env.example` to `.env`, add your OpenRouter API key, and verify `/health/ready` passes before rehearsal. Health only checks provider configuration, so also send a synthetic `/chat` request and verify `llm_refinement=completed` before recording. The app tries Qwen 3.8 27B, Nemotron 3.5 Lightning, and Gemma 4 26B A4B in order, then falls back to `openrouter/free`. Each candidate gets one request with an 18-second maximum; the four-route chain is bounded to about 72 seconds plus request setup. It fails closed with HTTP 503 if all routes are unavailable or return invalid answers, and the failure response retains the attempted model trace. If the local embedding model cannot be loaded, retrieval records the failure and uses its hashing fallback; inspect `/health` to see which embedding path is active.

The 14 policy files contain 15,034 indexed policy-text words, or about 37.6 page-equivalents at 400 words per page. The index metadata sums individually rounded per-document estimates to 37.5 pages. Neither number is a rendered page count; the corpus text and method are reported so the rubric's page floor can be inspected without treating the estimate as a PDF measurement.

## Configuration

`.env.example` contains safe local defaults. Keep provider credentials in the ignored `.env` file or the shell environment; never commit secrets.

- `MSAIE_MCP_TRANSPORT=inprocess` is the quick local-development default. The demo and operator runbooks use stdio to exercise MCP protocol calls.
- Set `MSAIE_MCP_TRANSPORT=stdio` to use the official MCP client and launch the FastMCP server as a subprocess.
- Required OpenRouter response generation uses `MSAIE_LLM_BASE_URL=https://openrouter.ai/api/v1`, `MSAIE_LLM_API_KEY`, and `MSAIE_LLM_FALLBACK_MODEL=openrouter/free`. `MSAIE_LLM_MODEL` and `OPENROUTER_MODEL` remain supported aliases for the fallback setting, and `OPENROUTER_API_KEY` remains a supported key alias for a local `.env` carried over from `HR-Agent_static`. The endpoint and fallback model are validated. The three pinned answer models are ordered in application code.
- Retrieval uses `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) and stores vectors in the local SQLite index. Optional remote serving can use the same model through the separate `MSAIE_EMBEDDING_*` variables; embeddings and answer generation use separate configuration.

## Architecture

```text
Browser -> FastAPI -> deterministic safety gates and orchestrator
                         |-> official MCP client -> FastMCP server -> synthetic HR tools
                         |-> Hugging Face MiniLM -> local SQLite vector retrieval
                         |-> controlled draft + evidence + structured facts
                         |-> OpenRouter free LLM composition (required for cited answers)
                         |-> consistency validation -> final answer + citations + trace
```

The orchestrator controls tool selection, safety checks, and action confirmation. Every citation-bearing response is composed by the required OpenRouter model chain from the controlled draft, retrieved policy evidence, and structured facts; a missing, misconfigured, unavailable, or rejected LLM response fails closed with HTTP 503 instead of returning unrefined vector-derived text. The operational trace records the requested and resolved model plus the attempted fallback sequence. The LLM does not select tools or approve actions. Injection refusals that retrieve no policy evidence stop before the LLM. All records and actions are synthetic.

## Useful endpoints

- `/`: employee workspace
- `/health`: app, retrieval, MCP, and provider status
- `/health/ready`: readiness gate requiring the policy index, MCP tools, and OpenRouter configuration
- `/api/tools`: available MCP tools
- `/docs`: API schema

To rebuild the index after policy changes, run `python scripts/build_index.py --force` from the repository root.

The MiniLM 384d chunk comparison selected 120/20 as the smallest tied setting. On the expanded corpus, global top-five ranking covered every expected family in 1 of 5 multi-family probes; MMR at λ=0.5 improved that to 2 of 5 and family recall from 0.76 to 0.81. Production then routes explicitly detected families and seeds one result per family; that routed comparison covered all expected families in all five labeled multi-family probes. These are small retrieval checks, not answer-quality scores. See [the chunk ablation](evaluation/ablation-results.md) and [routing comparison](evaluation/retrieval-comparison.md).

See [architecture](docs/architecture.md) and [design and evaluation](design-and-evaluation.md).

## Requirements, verification, and demo

- [Supplied source-material review](docs/source-materials-review.md)
- [System requirements](specs/system-requirements.md) and [traceability matrix](docs/traceability-matrix.md)
- [Architecture decision records](docs/adr/)
- [Implementation slices and project tickets](docs/implementation-slices.md) and [tickets](tickets/README.md)
- [Final code review](reviews/code-review.md)
- [Evidence index](evidence/index.md)
- [Demo runbook](demo/README.md) and [compact demo script](docs/demo-script.md)

### Deliverable locations

| Brief deliverable | This repository |
|---|---|
| Policy corpus and source documents | `policies/` (14 fictional policy files) |
| SRS and requirement traceability | `specs/system-requirements.md`, `docs/traceability-matrix.md` |
| Architecture and ADRs | `docs/architecture.md`, `docs/adr/` |
| Agent application and UI | `agent/`, `app/`, `app/static/` |
| MCP server and client (`mcp/` in the brief) | `mcp_server/` (FastMCP server and tools), `mcp_client/` (official SDK stdio client) |
| Synthetic records (`mock_data/` in the brief) | `mock_data/` |
| Evaluation and retrieval ablation | `evaluation/`, `visuals/` |
| Tests and CI | `tests/`, `.github/workflows/ci.yml` |
| Implementation tickets and TDD slices | `tickets/`, `docs/implementation-slices.md` |
| Review, evidence, and demo package | `reviews/`, `evidence/`, `demo/` |
| Hosting configuration and status | `render.yaml`, `deployed.md`, `docs/local-to-render-workflow.md` |

The brief's `mcp/` label is a deliverable category; this project keeps the separately named `mcp_server/` and `mcp_client/` source packages.

Run the local checks and complete evaluation from the repository root:

```bash
python -m compileall -q app agent rag mcp_server mcp_client evaluation scripts
python -m pytest -q
python -m evaluation.run_evaluation --transport inprocess
python -m evaluation.run_evaluation --transport stdio
python scripts/smoke_mcp.py
```

GitHub Actions runs the suite, protocol smoke, and 25-case golden set over both in-process and stdio transports, then uploads the JSON and Markdown reports. A separate deploy job depends on the full `test` job and is disabled until the repository variable `RENDER_DEPLOY_ENABLED=true` and secret `RENDER_DEPLOY_HOOK_URL` are configured. The job requests the exact tested SHA. `render.yaml` turns off Render's independent auto-deploy so a commit cannot bypass that CI gate. The existing Render service still needs its Blueprint settings synchronized before use; see [deployment status](deployed.md).

### Hosting target

- GitHub repository: [MSAIE2027/Project-HR-Agent](https://github.com/MSAIE2027/Project-HR-Agent) (`origin` is configured locally).
- Assigned Render URL: [https://project-hr-agent.onrender.com](https://project-hr-agent.onrender.com).
- The Blueprint service name is `Project-HR-Agent`, which matches the assigned hostname. The URL is not verified as live: the local source has not been pushed and the existing Render service settings still differ from `render.yaml`.

## Retrieval comparison

The latest comparison fixes MiniLM 384d and 120/20 chunks while measuring global k, actual policy routing, MMR, and ranking-weight alternatives. It also runs a six-case read-only policy slice. The script builds in a temporary index and writes reports to evaluation/ and the chart to visuals/; it does not run pytest or action workflows.

- [Comparison report](evaluation/retrieval-comparison.md)
- [Coverage chart](visuals/retrieval-comparison.svg)
- [Failure analysis and scope](evaluation/failed-test-analysis.md)
- [AI tooling and verification record](ai-tooling.md)

After adding multi-family intent routing and production MMR, the actual route cited every expected family in all 5 labeled multi-family probes. The six-case read-only golden policy slice scored 100% on status, citation-prefix, and groundedness-proxy checks. Runtime evidence reported huggingface_dense_cosine. The sample is hand-labeled and small; it does not establish general answer correctness.
