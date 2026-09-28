# MSAIE HR Agent

A fictional HR support assistant that combines policy retrieval and structured synthetic employee tools with OpenRouter-first LLM composition, OpenCode Zen failover, and bounded SQLite formatting for a small set of read-only outages. It cites policy evidence, reports its tool workflow, and gates mock actions on explicit confirmation. It does not access real employee data or production HR systems. The public demo has no employee authentication or role authorization; an ID selects a synthetic fixture and does not prove access rights.

## Architecture

```mermaid
flowchart LR
    Presenter([Demo user]) --> Browser[Browser workspace]

    subgraph App["HR agent · Render Python service"]
        direction TB
        Browser -->|POST /chat| API[FastAPI]
        API --> Guard{Deterministic routing<br/>privacy · safety · confirmation}
        Guard -->|refuse or clarify| Refusal[Safe response]
        Guard -->|continue| Client[Official MCP client]
        Client <-->|stdio · tools/list + tools/call| Server[FastMCP server<br/>8 typed tools]

        Server -->|policy search| SearchTool[Policy search tool]
        Server -->|employee lookup| HRTool[Structured HR tools]

        subgraph Retrieval["Local policy retrieval"]
            direction LR
            Query[MiniLM query embedding] --> Search[Hybrid search<br/>family routing · MMR]
            Index[(SQLite<br/>policy vectors)] --> Search
            Search --> Evidence[Policy passages<br/>citation metadata]
            Policies[Policy corpus] --> Chunk[Section-aware chunks]
            Chunk --> DocEmbed[MiniLM document embeddings]
            DocEmbed --> Index
        end
        SearchTool --> Query
        HRTool --> Records[(Synthetic PTO<br/>benefits · employee data)]

        Evidence --> Context[Controlled answer context<br/>draft · facts · evidence]
        Records --> Context
        Context --> OpenRouter
        OpenRouter -->|validated completion| Answer[Final answer<br/>citations · operational trace]
        OpenRouter -->|invalid result; another route| OpenRouter
        OpenRouter -->|account quota or chain exhausted| OpenCode[OpenCode Zen free-model chain]
        OpenCode -->|validated completion| Answer
        OpenCode -->|invalid result; another route| OpenCode
        OpenCode -->|chain exhausted| Template{Matching SQLite template?}
        Template -->|supported facts + citations| Answer
        Template -->|miss, unsafe, or action request| Fail[HTTP 503<br/>draft withheld]
        Evidence -. citations stay app-owned .-> Answer
        Answer -->|response| API
        Refusal --> API
        Fail -->|response| API

        Browser -->|read-only SQLite preview| API
        API -->|bounded document and chunk rows| Index
    end

    HF[Hugging Face<br/>MiniLM weight source] -. weights only .-> Query
    HF -. weights only .-> DocEmbed
    OpenRouter[OpenRouter<br/>required free-model chain]

    classDef client fill:#eff6ff,stroke:#2563eb,color:#1e3a8a
    classDef local fill:#ecfdf5,stroke:#059669,color:#064e3b
    classDef external fill:#fff7ed,stroke:#ea5800,color:#7c2d12
    classDef output fill:#f5f3ff,stroke:#7c3aed,color:#3b0764
    class Presenter,Browser client
    class API,Guard,Client,Server,SearchTool,HRTool,Query,Search,Index,Evidence,Policies,Chunk,DocEmbed,Records,Context local
    class HF,OpenRouter,OpenCode external
    class Refusal,Template,Answer,Fail output
```

**Reading the diagram:** blue is the user interface, green is app-local processing and data, orange is an external model service, and purple marks response and safety boundaries. MCP retrieves policy evidence and synthetic HR facts; OpenRouter composes answers first, OpenCode Zen is the configured model fallback, and build-seeded SQLite templates provide a fact-bound fallback for supported read-only workflows. Neither model provider chooses tools, sets eligibility, authorizes actions, or owns citations. Requests refused before retrieval stop before model generation. Local quick-start can use in-process MCP; CI and Render exercise the stdio path.

### Data and storage

```mermaid
flowchart LR
    subgraph Build[Policy index build]
        DOCS[Policy files] --> CHUNK[Section-aware chunks]
        CHUNK --> EMBED[Local MiniLM document embeddings]
        EMBED --> DB[(SQLite vector index)]
        TEMPLATES[Versioned response templates] --> DB
    end

    subgraph Request[Runtime evidence]
        QUESTION[Policy question] --> QUERY[Local MiniLM query embedding]
        DB --> RETRIEVE[Hybrid retrieval + family routing + MMR]
        QUERY --> RETRIEVE
        RETRIEVE --> PASSAGES[Evidence chunks + citation metadata]
        HR[(Synthetic HR records)] --> FACTS[Typed structured facts]
    end

    PASSAGES --> PROMPT[Controlled draft + evidence + structured facts]
    FACTS --> PROMPT
    PROMPT --> COMPOSE[OpenRouter model chain<br/>each route validated]
    COMPOSE -->|valid answer| RESPONSE[Answer + citations]
    COMPOSE -->|invalid or scoped throttle; try next route| COMPOSE
    COMPOSE -->|account quota or chain exhausted| OPENCODE[OpenCode Zen free-model chain<br/>each route validated]
    OPENCODE -->|valid answer| RESPONSE
    OPENCODE -->|invalid result; try next route| OPENCODE
    OPENCODE -->|chain exhausted| CACHE{Matching SQLite template?}
    CACHE -->|supported workflow; fresh facts + citations| RESPONSE
    CACHE -->|miss, unsafe, or action request| SAFE[HTTP 503; draft withheld]
    UI[Browser SQLite viewer] -->|read-only API request| API[FastAPI]
    API -->|bounded document, chunk, and template metadata| DB
    DB --> API --> UI
    HF[Hugging Face model source] -. model weights downloaded to app .-> EMBED
    HF -. model weights downloaded to app .-> QUERY

    classDef local fill:#ecfdf5,stroke:#059669,color:#064e3b
    classDef external fill:#fff7ed,stroke:#ea5800,color:#7c2d12
    classDef output fill:#f5f3ff,stroke:#7c3aed,color:#3b0764
    class DOCS,CHUNK,EMBED,DB,TEMPLATES,QUESTION,QUERY,RETRIEVE,PASSAGES,HR,FACTS,PROMPT local
    class HF,COMPOSE,OPENCODE external
    class CACHE,RESPONSE,SAFE output
```

Policy embeddings, the vector index, and versioned formatting templates ship in the app's SQLite database. OpenRouter is the primary answer composer: Qwen 3.8 27B, Nemotron 3.5 Lightning, Gemma 4 26B A4B, then `openrouter/free`. A detected account-wide free quota cap moves directly to the configured OpenCode Zen model chain; other OpenRouter errors exhaust that chain first. If both model routes fail, supported PTO balance/request and positive remote-work eligibility cases can use SQLite templates with freshly retrieved policy citations and current MCP facts. No employee answers are cached. Validation fails closed on unavailable, truncated, unsupported, or unsafe output when no safe template applies. Requests refused before retrieval return without model generation. The active hosted release and its acceptance status are maintained in [deployment status](deployed.md).

The project uses fixed synthetic records so the same demo query produces a repeatable scenario. The workspace includes examples for several employee IDs and a read-only browser for the SQLite policy documents and chunks; vector payloads are not exposed.

## Run locally

Use Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Set MSAIE_LLM_API_KEY in .env; optionally add OPENCODE_API_KEY for live fallback, then:
./scripts/start_local.sh
```

The launcher loads `.env`, starts the service, waits for readiness, and opens the browser. The first start builds the SQLite index and loads the pinned Hugging Face `sentence-transformers/all-MiniLM-L6-v2` INT8 ONNX export. Embeddings run locally through CPU ONNX Runtime and are stored in the SQLite vector index; OpenRouter is the primary answer composer, followed by optional OpenCode Zen and bounded SQLite template fallbacks. Restart the service after changing `.env`.

For the required protocol path, set `MSAIE_MCP_TRANSPORT=stdio`. `inprocess` is available for quick local development, while the demo and CI exercise the official MCP SDK client and FastMCP server over stdio.

## Configuration and endpoints

Keep provider credentials in the ignored `.env` file or shell environment. Never commit secrets.

- OpenRouter: `MSAIE_LLM_BASE_URL`, `MSAIE_LLM_API_KEY` (or legacy `OPENROUTER_API_KEY` for local runs), and `MSAIE_LLM_FALLBACK_MODEL`.
- OpenCode Zen fallback: `OPENCODE_API_KEY`, `OPENCODE_ZEN_BASE_URL`, and `OPENCODE_ZEN_MODELS`. OpenCode currently lists Nemotron 3.5 Lightning Free, Big Pickle, and Space Bunny Free as zero-priced, limited-time routes; availability and access can change. The environment setting can reorder or select a subset of the code allowlist; add replacement model IDs only through a reviewed code/test change. See the [OpenCode Zen catalog](https://opencode.ai/docs/en/zen/).
- Embeddings: `MSAIE_EMBEDDING_*` settings are separate from LLM generation. The default model is `sentence-transformers/all-MiniLM-L6-v2` at 384 dimensions, pinned to Hugging Face revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` and run with the `onnx/model_quint8_avx2.onnx` CPU export. SQLite stores vectors; ONNX Runtime embeds queries locally.
- `/`: synthetic HR workspace and evaluator lab.
- `/health` and `/health/ready`: service, SQLite index, MCP, and provider status.
- `/api/index/documents` and `/api/index/documents/{document_id}/chunks`: read-only SQLite index preview without stored vectors; the document endpoint also lists safe template metadata.
- `/api/tools`: discover the available MCP tools.
- `/docs`: API schema.

## Project map

| Deliverable | Location |
|---|---|
| Fictional HR policy corpus | `policies/` |
| Source review, requirements, and traceability | `docs/source-materials-review.md`, `specs/`, `docs/traceability-matrix.md` |
| Architecture, design, and decisions | `docs/architecture.md`, [`docs/architecture-deepening-review.md`](docs/architecture-deepening-review.md), `design-and-evaluation.md`, `docs/adr/` |
| Tickets and TDD implementation slices | `tickets/README.md`, `docs/implementation-slices.md` |
| Orchestrator, API, and browser app | `agent/`, `app/` |
| MCP tools (`mcp/` equivalent) | `mcp_server/` (server and tools), `mcp_client/` (protocol client) |
| Synthetic records | `mock_data/` |
| Retrieval evaluation and visualizations | `evaluation/`, `visuals/` |
| Tests and GitHub Actions | `tests/`, `.github/workflows/ci.yml` |
| Review and acceptance evidence | `reviews/`, `evidence/` |
| Security boundaries and residual risks | [`docs/security-control-map.md`](docs/security-control-map.md) |
| Demo runbook | `demo/README.md`, `docs/demo-script.md` |
| AI tooling disclosure and deployment status | `ai-tooling.md`, `deployed.md` |

## Verification

Run from the repository root:

```bash
python -m compileall -q app agent rag mcp_server mcp_client evaluation scripts
python -m pytest -q
python -m evaluation.run_evaluation --transport inprocess
python -m evaluation.run_evaluation --transport stdio
python scripts/smoke_mcp.py
```

For hosted acceptance when the provider routes are available, run `python scripts/smoke_hosted_demo.py`. It sends synthetic chat requests through the live app and may consume Free-tier allowance; by default it stops before the confirmation-gated mock email action. The `--confirm-mock-email` option explicitly exercises that fictional local-only action. Output is sanitized. See [deployment status](deployed.md) before using it.

The golden set measures orchestrator behavior and deterministic control-flow proxies; it does not include OpenRouter generation or independent semantic judging. See [evaluation limits and results](evaluation/), [the review](reviews/code-review.md), and the [evidence index](evidence/index.md) for the current acceptance record. Deployment health and live request evidence are in [deployed.md](deployed.md).

## Retrieval visualization

The retrieval comparison chart is checked into the repository and embedded here so it is visible in GitHub. It compares top-k coverage and MMR for the labeled policy queries; the result is corpus-specific, not a general answer-quality score.

![Retrieval comparison chart](visuals/retrieval-comparison.svg)

See the [retrieval comparison report](evaluation/retrieval-comparison.md) and [chunk ablation report](evaluation/ablation-results.md) for methods and limitations.

## Hosting

- GitHub repository: [MSAIE2027/Project-HR-Agent](https://github.com/MSAIE2027/Project-HR-Agent).
- Assigned Render URL: [project-hr-agent.onrender.com](https://project-hr-agent.onrender.com).
- Deployment procedure: [local-to-Render workflow](docs/local-to-render-workflow.md).
- See [deployed.md](deployed.md) for verified live status and current release evidence.
