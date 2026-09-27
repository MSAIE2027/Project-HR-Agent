# MSAIE HR Agent

A fictional HR support assistant that combines policy retrieval, structured synthetic employee tools, and required LLM response composition. It cites policy evidence, reports its tool workflow, and gates mock actions on explicit confirmation. It does not access real employee data or production HR systems.

## Architecture

```mermaid
flowchart LR
    subgraph EXPERIENCE[Employee experience]
        EMP([Employee]) --> UI[Browser workspace]
    end

    subgraph CONTROL[Application and deterministic control]
        API[FastAPI chat API] --> G[Safety and workflow gates]
        INDEXAPI[Read-only SQLite index API]
        G --> AGENT[Agent orchestrator]
        AGENT --> DRAFT[Controlled draft + structured facts]
        CHECK[Answer and safety validation]
    end

    subgraph PROTOCOL[Official MCP protocol over stdio]
        CLIENT[MCP SDK client] --> SERVER[FastMCP server]
        SERVER -->|tools/call| TOOLS[Synthetic HR tools]
        TOOLS -->|read or update fixture| RECORDS[(Fictional employee records)]
        RECORDS -->|structured result| TOOLS
        TOOLS -->|MCP result| SERVER
    end

    subgraph RETRIEVAL[Local policy retrieval]
        SEARCH[Policy search] --> EMBED[Hugging Face MiniLM]
        EMBED --> SQLITE[(SQLite vector index)]
        SQLITE --> CITED[Evidence chunks + citations]
    end

    subgraph GENERATION[Required answer composition]
        OR[OpenRouter model chain<br/>Qwen → Nemotron → Gemma → free fallback]
    end

    UI --> API
    UI -. browse documents and chunks .-> INDEXAPI
    INDEXAPI -. safe rows only .-> SQLITE
    AGENT --> CLIENT
    SERVER --> SEARCH
    CITED --> SERVER
    SERVER --> CLIENT
    CLIENT --> AGENT
    DRAFT --> OR
    OR --> CHECK
    CHECK --> OUT[Validated answer + citations + trace]
    OUT --> UI

    classDef user fill:#eef2ff,stroke:#4f46e5,color:#1e1b4b
    classDef service fill:#eff6ff,stroke:#2563eb,color:#172554
    classDef protocol fill:#ecfeff,stroke:#0891b2,color:#164e63
    classDef local fill:#ecfdf5,stroke:#059669,color:#064e3b
    classDef hosted fill:#fff7ed,stroke:#ea580c,color:#7c2d12
    classDef output fill:#f5f3ff,stroke:#7c3aed,color:#3b0764
    class EMP,UI user
    class API,INDEXAPI,G,AGENT,DRAFT,CHECK service
    class CLIENT,SERVER,TOOLS protocol
    class RECORDS,SEARCH,EMBED,SQLITE,CITED local
    class OR hosted
    class OUT output
```

Every citation-bearing response goes through OpenRouter before the application returns it. The chain tries Qwen 3.8 27B, Nemotron 3.5 Lightning, and Gemma 4 26B A4B, then `openrouter/free`. The model formats and enriches a controlled draft using retrieved policy text and structured facts. It cannot select tools, change eligibility, or authorize actions. If the response is unavailable, truncated, unsupported, or unsafe, the API withholds the draft and reports a safe failure.

The project uses fixed synthetic records so the same demo query produces a repeatable scenario. The workspace includes examples for several employee IDs and a read-only browser for the SQLite policy documents and chunks; vector payloads are not exposed.

## Run locally

Use Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Set MSAIE_LLM_API_KEY in .env, then:
./scripts/start_local.sh
```

The launcher loads `.env`, starts the service, waits for readiness, and opens the browser. The first start builds the SQLite index and loads `sentence-transformers/all-MiniLM-L6-v2` from Hugging Face. Embeddings run locally; OpenRouter is used for final answer generation. Restart the service after changing `.env`.

For the required protocol path, set `MSAIE_MCP_TRANSPORT=stdio`. `inprocess` is available for quick local development, while the demo and CI exercise the official MCP SDK client and FastMCP server over stdio.

## Configuration and endpoints

Keep provider credentials in the ignored `.env` file or shell environment. Never commit secrets.

- OpenRouter: `MSAIE_LLM_BASE_URL`, `MSAIE_LLM_API_KEY`, and `MSAIE_LLM_FALLBACK_MODEL`.
- Embeddings: `MSAIE_EMBEDDING_*` settings are separate from LLM generation. The default model is `sentence-transformers/all-MiniLM-L6-v2` at 384 dimensions.
- `/`: synthetic HR workspace and evaluator lab.
- `/health` and `/health/ready`: service, SQLite index, MCP, and provider status.
- `/api/index/documents` and `/api/index/documents/{document_id}/chunks`: read-only SQLite index preview without stored vectors.
- `/api/tools`: discover the available MCP tools.
- `/docs`: API schema.

## Project map

| Deliverable | Location |
|---|---|
| Fictional HR policy corpus | `policies/` |
| Requirements and traceability | `specs/`, `docs/traceability-matrix.md` |
| Architecture and decisions | `docs/architecture.md`, `docs/adr/` |
| Orchestrator, API, and browser app | `agent/`, `app/` |
| MCP client, server, and tools | `mcp_client/`, `mcp_server/` |
| Synthetic records | `mock_data/` |
| Retrieval evaluation and visualizations | `evaluation/`, `visuals/` |
| Tests and GitHub Actions | `tests/`, `.github/workflows/ci.yml` |
| Review and acceptance evidence | `reviews/`, `evidence/` |
| Demo runbook | `demo/README.md`, `docs/demo-script.md` |

The brief's `mcp/` category is implemented as the separately named `mcp_client/` and `mcp_server/` packages.

## Verification

Run from the repository root:

```bash
python -m compileall -q app agent rag mcp_server mcp_client evaluation scripts
python -m pytest -q
python -m evaluation.run_evaluation --transport inprocess
python -m evaluation.run_evaluation --transport stdio
python scripts/smoke_mcp.py
```

The golden set measures orchestrator behavior and deterministic control-flow proxies; it does not include OpenRouter generation or independent semantic judging. See [evaluation limits and results](evaluation/), [the review](reviews/code-review.md), and the [evidence index](evidence/index.md) for the current acceptance record. Deployment health and live request evidence are in [deployed.md](deployed.md).

## Retrieval visualization

The retrieval comparison chart is checked into the repository and embedded here so it is visible in GitHub. It compares top-k coverage and MMR for the labeled policy queries; the result is corpus-specific, not a general answer-quality score.

![Retrieval comparison chart](visuals/retrieval-comparison.svg)

See the [retrieval comparison report](evaluation/retrieval-comparison.md) and [chunk ablation report](evaluation/ablation-results.md) for methods and limitations.

## Hosting

- GitHub repository: [MSAIE2027/Project-HR-Agent](https://github.com/MSAIE2027/Project-HR-Agent).
- Assigned Render URL: [project-hr-agent.onrender.com](https://project-hr-agent.onrender.com).
- See [deployed.md](deployed.md) for verified live status and current release evidence.
