# Architecture

## Request lifecycle

The browser calls the FastAPI app in app/main.py. The application starts the SQLite policy index and discovers the configured tool set. Each chat request is routed through agent/orchestrator.py, which chooses tools, checks structured results, retrieves policy evidence, applies safety and confirmation rules, and produces a controlled draft.

When configured, the answer refiner receives that draft, citation metadata, the structured status, and internal structured facts. It cannot select tools, change eligibility, or authorize an action. A deterministic post-generation check preserves status cues, numeric facts, and no-action disclaimers; a rejected rewrite falls back to the controlled draft.

## Modules

- app/: FastAPI endpoints and static employee workspace.
- agent/: request orchestration, response models, and optional LLM provider.
- mcp_client/: transport selection and official MCP client calls.
- mcp_server/: FastMCP server and synthetic HR tools.
- rag/: Markdown/HTML ingestion, chunking, vector generation, SQLite storage, and ranking.
- policies/: fictional HR policy corpus.
- mock_data/: synthetic employee, PTO, benefits, office, and ticket records.

## MCP paths

The server registers eight typed tools on the MCP SDK FastMCP server.

- inprocess calls functions through TOOL_REGISTRY directly. It is the local default and does not validate MCP serialization or protocol behavior.
- stdio starts mcp_server.server as a subprocess. The official MCP client initializes the session, discovers tools, and calls them over stdio.

## Retrieval

rag/ingest.py extracts Markdown and HTML sections with document IDs, titles, headings, source paths, and page estimates. The selected chunk settings are 120 words with 20-word overlap. MiniLM is the only intended dense embedding model: sentence-transformers/all-MiniLM-L6-v2 at 384 dimensions. Embedding provider, base URL, key, and model use MSAIE_EMBEDDING_*; MSAIE_LLM_* configures answer refinement only.

The chunk comparison selected 120/20 as the smallest setting among tied 120/20, 160/24, and 220/30 configurations. At global k=5, MMR λ=0.5 improved multi-family all-family coverage from 2/5 to 3/5 and family recall from 0.81 to 0.86. Production now searches up to ten score-ranked candidates, applies cosine MMR at λ=0.5, and returns five citations. For multi-family intent, it searches the top three per selected family and seeds the strongest result from each family before filling remaining slots with MMR. Scoring weights, embedding model, chunk size, and output budget remain fixed.

rag/index.py computes dense cosine and adds bounded lexical-overlap, title-hit, and exact-phrase signals. If local embedding setup fails, the index records the error and uses a sparse hashing fallback. Each result and MCP trace reports runtime retrieval_method; the comparison confirmed huggingface_dense_cosine. When dense vectors are unavailable and the configured hashing fallback is active, reranking retains score order because sparse vectors are not used for MMR cosine diversity.

The updated orchestrator route cited all expected families in the five labeled multi-family probes and in the six-case read-only golden policy slice. It infers multiple policy families from explicit terms such as international work plus confidential data, expense plus approval, and leave or benefits plus records retention. Each intended family must return evidence above the existing 0.12 threshold or the request abstains. These are small, hand-labeled coverage proxies. See evaluation/retrieval-comparison.md for per-query results.

RagIndex.search(query, limit=k) returns score-ranked candidates; RagIndex.rerank_mmr applies MMR using stored MiniLM vectors without exposing vectors to MCP callers. The orchestrator uses the same persistent index to return at most five citations. Explicit regression behavior for non-positive k, empty queries, tied scores, zero vectors, and dimension changes remains open.

## Safety and generation

All records and actions are fictional. Prompt-injection checks, missing-data handling, policy evidence checks, and action confirmation remain deterministic. Mock email and ticket tools never send a message or create a production record.

The refiner checks the eligibility, escalation, and mock-action status cues; preserves numeric tokens and known no-action disclaimers; and rejects unsupported new numbers. It uses a controlled-draft fallback when the check fails. This string-level validation cannot prove semantic entailment; the full design is documented in design-and-evaluation.md.
