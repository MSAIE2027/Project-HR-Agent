# Architecture

## Request lifecycle

The browser calls the FastAPI app in app/main.py. The application starts the SQLite policy index and discovers the configured tool set. In the required demo and Render stdio configuration, the FastAPI lifespan also starts one managed MCP process and reuses it for requests. The local quick-start defaults to in-process MCP. Each chat request is routed through agent/orchestrator.py, which chooses tools, checks structured results, retrieves policy evidence, applies safety and confirmation rules, and produces a controlled draft.

Every citation-bearing answer first uses the OpenRouter response-generation step. The chain tries `qwen/qwen3.8-27b:free`, `nvidia/nemotron-3.5-lightning:free`, and `google/gemma-4-26b-a4b-it:free`, followed by `openrouter/free`. OpenRouter receives the controlled draft, retrieved policy text, and structured facts; citation metadata stays on the application response. A recognized account-wide daily-quota HTTP 429 moves directly to the OpenCode Zen chain instead of spending more OpenRouter requests. Model/provider-specific and unclassified 429s continue through the remaining OpenRouter routes; OpenCode Zen is tried after that chain is exhausted. Its configured free-model chain currently defaults to Nemotron 3.5 Lightning Free, Big Pickle, and Space Bunny Free. The OpenCode Zen model list is configurable because its model availability and free status can change.

Either live model provider may only format and enrich the controlled draft; neither can select tools, change eligibility, or authorize an action. Both use the same deterministic validation for workflow status, supported numbers, safety language, process narration, and truncation. Those checks are not semantic entailment judgments. Provider bodies never enter the response or trace. If both live routes fail, a build-seeded SQLite template may format current MCP facts and policy citations for a supported read-only PTO or provisionally eligible remote-work workflow. The SQLite stores template strings and their required facts, not employee answers; each request still runs fresh guards, MCP lookups, and retrieval. A template miss, insufficient evidence, or confirmation-gated action remains fail-closed with HTTP 503. Requests refused before retrieval stop before the LLM.

```mermaid
flowchart LR
    OR[OpenRouter model chain<br/>validate each completion] --> OR_RESULT{Route result}
    OR_RESULT -->|Valid completion| ANSWER[Return enriched cited answer]
    OR_RESULT -->|Invalid output or scoped throttle; more routes| OR
    OR_RESULT -->|Account quota or chain exhausted| OC[OpenCode Zen model chain<br/>validate each completion]
    OC --> OC_RESULT{Route result}
    OC_RESULT -->|Valid completion| ANSWER
    OC_RESULT -->|Invalid output; more routes| OC
    OC_RESULT -->|All routes exhausted| CACHE{Supported SQLite template match?}
    CACHE -->|Yes; current facts + citations| CACHED[Return formatted answer; trace cache hit]
    CACHE -->|No; unsafe/action/template miss| FAIL[HTTP 503; withhold controlled draft]
```

An explicit model/provider/route scope overrides matching quota wording in other provider fields. The classifier returns only the sanitized scope label; raw error text and metadata stay private.

`nvidia/nemotron-3.5-content-safety:free` is not an answer-generation fallback. OpenRouter describes it as a guardrail that classifies prompts and responses as safe or unsafe and emits safety labels; its output contract is moderation, not a grounded employee answer. If the project adds a model-based moderation pass, treat it as a separate safety stage and validate its labels at that boundary. See the [OpenRouter model page](https://openrouter.ai/nvidia/nemotron-3.5-content-safety:free).

```mermaid
sequenceDiagram
    actor Employee
    participant Browser as Browser workspace
    participant API as FastAPI
    participant Agent as Deterministic orchestrator
    participant Client as Official MCP client
    participant Server as FastMCP stdio process
    participant MiniLM as Pinned HF MiniLM ONNX Runtime
    participant DB as Service-local SQLite vector index
    participant OR as OpenRouter free-model chain
    participant OC as OpenCode Zen free-model chain
    participant Templates as Build-seeded SQLite response templates
    Employee->>Browser: HR question
    Browser->>API: POST /chat
    API->>Agent: Validate and route request
    Agent->>Client: Discover and call policy / HR tools
    Client->>Server: tools/list and tools/call over stdio
    Server->>MiniLM: Embed policy query locally
    MiniLM-->>Server: Query vector
    Server->>DB: Hybrid retrieval + family routing + MMR
    DB-->>Server: Policy passages and citation metadata
    Server-->>Client: Evidence and structured tool results
    Client-->>Agent: Tool results
    Agent->>API: Controlled draft + status + structured facts
    API->>OR: Primary response composition
    Note over API,OR: Draft + retrieved evidence + structured facts
    alt OpenRouter route returns a validated answer
        OR-->>API: Answer + resolved model and sanitized attempts
    else OpenRouter account quota or chain exhausted
        API->>OC: Retry composition with same evidence and facts
        alt OpenCode route returns a validated answer
            OC-->>API: Answer + resolved model and sanitized attempts
        else Both live model chains fail
            API->>Templates: Match workflow, structured facts, and citation family
            Templates-->>API: Seeded text template; no stored employee answer
            API->>API: Format current facts and trace SQLite template key
        end
    end
    API-->>Browser: Validated answer or fail-closed HTTP 503 + trace
    Browser-->>Employee: Display actual response path
```

## Modules

- app/: FastAPI endpoints and static employee workspace.
- agent/: request orchestration, response models, OpenRouter/OpenCode Zen composers, and the fact-bound SQLite template fallback.
- mcp_client/: transport selection and official MCP client calls.
- mcp_server/: FastMCP server and synthetic HR tools.
- rag/: Markdown/HTML ingestion, chunking, vector generation, SQLite storage, and ranking.
- policies/: fictional HR policy corpus.
- mock_data/: synthetic employee, PTO, benefits, office, and ticket records.

## MCP paths

The server registers eight typed tools on the MCP SDK FastMCP server.

- inprocess calls functions through TOOL_REGISTRY directly. It is the local default and does not validate MCP serialization or protocol behavior.
- stdio starts one `mcp_server.server` subprocess for the FastAPI app lifetime. The official MCP client initializes the session once, discovers tools, and reuses the session for chat requests. A lock serializes each orchestrated tool sequence over that shared session; app shutdown closes it. This keeps the MiniLM model resident and avoids creating another Python model process for every turn.
- Standalone smoke and evaluation callers that do not manage an app lifetime may still use a temporary stdio session.

If the persistent MCP connection fails, the current request returns an explicit MCP-unavailable result and updates cached MCP health. Routine `/health/ready` probes read that state without waiting on the session lock, so a first model load cannot stall Render's health check. `/health?deep=true` performs explicit live discovery. Restart the service to create a fresh session after a failed stdio process. The first policy search after app start may download/load the pinned quantized ONNX MiniLM in the long-lived MCP process; later turns reuse the ONNX session and SQLite connection. The app serializes MCP tool sequences while leaving answer generation outside that lock. On the current ONNX deployment, Render sampled 274,866,180 bytes one minute after startup and after the first policy query, against a 536,870,900-byte limit; the process stayed live. This limited sample is not a peak or concurrency benchmark. Historical PyTorch samples peaked 606,200 bytes below the same limit, and a later request restarted during model loading without a Python exception or explicit OOM record. Resource pressure was plausible but not proven. Continue observing hosted memory before making a capacity claim.

## Retrieval

rag/ingest.py extracts Markdown and HTML sections with document IDs, titles, headings, source paths, and page estimates. The selected chunk settings are 120 words with 20-word overlap. MiniLM is the only intended dense embedding model: sentence-transformers/all-MiniLM-L6-v2 at 384 dimensions, pinned to revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. The service uses the model repository's `onnx/model_quint8_avx2.onnx` CPU export with ONNX Runtime and truncates tokenizer inputs at 256 tokens. SQLite metadata and the index signature include the tokenizer limit, backend, and revision; a change rebuilds the vectors and uses a distinct cached tokenizer/runtime. Readiness requires this exact semantic index instead of accepting the sparse fallback. Embedding provider, base URL, key, and model use MSAIE_EMBEDDING_*; MSAIE_LLM_* configures the separate, required OpenRouter final-answer step.

Hugging Face is the model-weight source; MiniLM document and query embeddings run locally in the app's managed MCP process. At startup, policy files are chunked and their embeddings are stored in the service's SQLite vector index. At request time, the policy tool embeds the query locally, applies hybrid lexical and dense ranking, and uses family routing with MMR to select citations. Current chunking, ranking settings, experiments, results, and limitations are recorded in [`evaluation/ablation-results.md`](../evaluation/ablation-results.md) and [`evaluation/retrieval-comparison.md`](../evaluation/retrieval-comparison.md); the chart is [`visuals/retrieval-comparison.svg`](../visuals/retrieval-comparison.svg).

`RagIndex.search(query, limit=k)` returns score-ranked candidates; `RagIndex.rerank_mmr` applies MMR using stored MiniLM vectors without exposing vectors to MCP callers. The orchestrator uses the same index to return at most five citations. The build seeds versioned response templates into that SQLite database; the API exposes their safe metadata, while runtime lookup is read-only.

The evaluator lab reads document and chunk rows through `/api/index/documents` and `/api/index/documents/{document_id}/chunks`, and lists template keys through the same read-only index API. These endpoints show citation metadata and complete text for a bounded preview, not vector payloads or the database filesystem path. The browser is a read-only view of the active SQLite index.

## Safety and generation

All records and actions are fictional. Prompt-injection checks, missing-data handling, policy evidence checks, and action confirmation remain deterministic. Requests referring to multiple synthetic employees are refused before MCP access; the guard recognizes roster names as well as explicit employee IDs. Requests to retrieve an individual's medical records or files are refused before employee lookup and point to the confidential HR channel. Mock email and ticket tools never send a message or create a production record.

The live response composers check eligibility, escalation, clarification, confirmation, and mock-action status cues; preserve supported numeric tokens and known no-action disclaimers; and reject unsupported numbers or omitted numbers. On a live-provider outage, only the explicitly supported fact-and-citation template matches can answer. Other validation failures, confirmation-gated actions, unsafe or unsupported cases, and cache misses return HTTP 503; the service never presents the unrefined policy draft as the final response. These string-level checks cannot prove semantic entailment; the full design is documented in design-and-evaluation.md.
