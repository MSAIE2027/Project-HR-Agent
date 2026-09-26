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

The first start builds a local SQLite policy index and loads the configured embedding model. The Hugging Face model is downloaded on first use. No provider key is needed for local embeddings or deterministic answer generation. If the local model cannot be loaded, retrieval records the failure and uses its hashing fallback; inspect `/health` to see which embedding path is active.

The corpus contains 9,334 policy-text words, or about 31.1 page-equivalents at 300 words per page. The 34.5-page figure reported by index metadata and shown in the workspace is a sum of per-document metadata estimates, not a measured or rendered page count.

## Configuration

`.env.example` contains safe local defaults. Keep provider credentials in the ignored `.env` file or the shell environment; never commit secrets.

- `MSAIE_MCP_TRANSPORT=inprocess` is the local default. It calls the registered tool functions directly.
- Set `MSAIE_MCP_TRANSPORT=stdio` to use the official MCP client and launch the FastMCP server as a subprocess.
- Optional OpenAI-compatible answer refinement uses `MSAIE_LLM_BASE_URL`, `MSAIE_LLM_API_KEY`, and `MSAIE_LLM_MODEL`.
- Retrieval uses `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions). Optional remote serving can use the same model through the separate `MSAIE_EMBEDDING_*` variables; `MSAIE_LLM_*` configures answer refinement only.

## Architecture

```text
Browser -> FastAPI -> request controls and orchestrator
                         |-> in-process tool calls (local default)
                         |-> official MCP client -> FastMCP server (stdio mode)
                         |-> SQLite policy retrieval with cosine ranking
                         |-> constrained answer refinement (optional)
```

The orchestrator controls tool selection, safety checks, and action confirmation. The language model can only refine a grounded draft; it does not select tools or approve actions. All records and actions are synthetic.

## Useful endpoints

- `/`: employee workspace
- `/health`: app, retrieval, MCP, and provider status
- `/api/tools`: available MCP tools
- `/docs`: API schema

To rebuild the index after policy changes, run `python scripts/build_index.py --force` from the repository root.

The MiniLM 384d chunk comparison selected 120/20 as the smallest tied setting. Global top-five results covered every expected family in 2 of 5 multi-family probes; MMR at λ=0.5 improved that to 3 of 5. Production now reranks the top ten to five citations with MMR and seeds one result per explicitly routed policy family. The broader route comparison is documented in [the retrieval ablation](evaluation/ablation-results.md) and [routing comparison](evaluation/retrieval-comparison.md).

See [architecture](docs/architecture.md) and [design and evaluation](design-and-evaluation.md).

## Retrieval comparison

The latest comparison fixes MiniLM 384d and 120/20 chunks while measuring global k, actual policy routing, MMR, and ranking-weight alternatives. It also runs a six-case read-only policy slice. The script builds in a temporary index and writes reports to evaluation/ and the chart to visuals/; it does not run pytest or action workflows.

- [Comparison report](evaluation/retrieval-comparison.md)
- [Coverage chart](visuals/retrieval-comparison.svg)
- [Failure analysis and scope](evaluation/failed-test-analysis.md)
- [AI tooling and verification record](ai-tooling.md)

After adding multi-family intent routing and production MMR, the actual route cited every expected family in all 5 labeled multi-family probes. The six-case read-only golden policy slice scored 100% on status, citation-prefix, and groundedness-proxy checks. Runtime evidence reported huggingface_dense_cosine. The sample is hand-labeled and small; it does not establish general answer correctness.
