# Historical OpenRouter Runtime Smoke

> This successful request predates the pinned four-route model chain and used the old 126-chunk index. It is retained as engineering history; the current 182-chunk index and chain result are in [`openrouter-chain-smoke.md`](openrouter-chain-smoke.md).

**Date:** 2026-09-26
**Environment:** Local isolated service on port 8011, MCP stdio, synthetic records only.

## Configuration and readiness

`/health/ready` returned HTTP 200. `/health?deep=true` reported service `ok`, OpenRouter configured at host `openrouter.ai` with model `openrouter/free`, Hugging Face `sentence-transformers/all-MiniLM-L6-v2` embeddings at 384 dimensions, and the ready SQLite index at `.data/rag_index.sqlite3` with 14 documents and 126 chunks. MCP stdio discovered all eight typed tools.

The local `.env` used the legacy `OPENROUTER_API_KEY` name. The current app accepts that key alias while keeping the endpoint and model fixed to the required OpenRouter free route. No credential value was displayed or written to the log or this report.

## Synthetic cited request

Request: `Can E1001 work remotely overseas for 10 days?`

| Check | Result |
|---|---|
| `/chat` HTTP status | 200 |
| Agent status | `provisionally_eligible` |
| Citations | Five `POL-RW-01` chunks |
| MCP call order | `search_policy_documents` → `lookup_employee_profile` → `check_policy_compliance` |
| Final trace event | `llm_refinement` |
| Refinement status | `completed` |
| Model route / host | `openrouter/free` / `openrouter.ai` |
| Generation attempts | 1 |

The full model answer and API key are intentionally not included. The user supplied operational example contains the four orchestration steps but not the final LLM event; this runtime check confirms the additional generation step is present in the current API trace.

## Validator regression caught during verification

The first real model response was rejected because the provisional-eligibility guard treated a negated phrase like “not yet approved” as affirmative approval. The validator now distinguishes an affirmative approval claim from nearby negation. Unit coverage checks both the negative wording and a truly contradictory approval statement. The next live synthetic request passed validation and returned the completed trace above.

## Limitations

This is one live request through a free-model router, not a broad semantic-quality evaluation or stable latency benchmark. The underlying model selected by the free router can change. The deterministic 25-case evaluation remains separate and excludes live OpenRouter calls. Hugging Face emitted non-fatal cache metadata write warnings in the local sandbox; the model loaded, embeddings were generated, and retrieval completed.
