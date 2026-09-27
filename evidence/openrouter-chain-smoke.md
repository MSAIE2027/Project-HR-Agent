# OpenRouter Model-Chain Smoke

**Date:** 2026-09-26
**Environment:** Local FastAPI service on port 8031, MCP stdio, fictional employee data only.
**Purpose:** Verify the current expanded Hugging Face → SQLite retrieval path followed by the required OpenRouter response chain.

## Readiness

`/health/ready` and `/health?deep=true` returned HTTP 200. The local service reported status `ok`, eight available MCP tools, Hugging Face `sentence-transformers/all-MiniLM-L6-v2` embeddings at 384 dimensions, and the configured SQLite file `.data/rag_index.sqlite3` with 14 policy documents and 182 chunks. The required OpenRouter provider was configured; no credential value was displayed or saved.

## Earlier current-index failures

Request: `Can E1001 work remotely overseas for 10 days?`

The operational path retrieved policy evidence, looked up the synthetic employee, and ran the compliance check before answer composition. The first two `/chat` requests against the rebuilt 182-chunk index returned HTTP 503 after exhausting the required four-route chain. The more detailed sanitized trace was:

| Route, in configured order | Outcome | Sanitized detail |
|---|---|---|
| `qwen/qwen3.8-27b:free` | unavailable | HTTP 429 |
| `nvidia/nemotron-3.5-lightning:free` | rejected | Local validation: `unsupported_numeric_fact`; model answer omitted |
| `google/gemma-4-26b-a4b-it:free` | unavailable | HTTP 429 |
| `openrouter/free` | unavailable | Request timeout |

Those two `llm_refinement` events recorded `status=unavailable`. The service preserved MCP call names and returned no unrefined retrieval draft.

## Latest current-index success

**Verified:** 2026-09-27 01:57 UTC. The same synthetic request, `Can E1001 work remotely overseas for 10 days?`, was then sent to the public local `/chat` endpoint. It returned HTTP 200 with status `provisionally_eligible`, five citations, and `llm_refinement=completed`.

The MCP sequence was `search_policy_documents` → `lookup_employee_profile` → `check_policy_compliance`. The service attempted the configured chain in order: Qwen, Nemotron Lightning, Gemma, and `openrouter/free`. The accepted resolved model was `poolside/laguna-s-2.1:free`. The request therefore verifies the full Hugging Face → 182-chunk local SQLite → real MCP stdio → OpenRouter response path against the expanded corpus. The full model answer and credentials are not stored here.

## Earlier successful smoke and scope

An earlier isolated request also returned HTTP 200 but used a stale 126-chunk SQLite index; it is retained in [`openrouter-smoke.md`](openrouter-smoke.md) as historical evidence. The latest 182-chunk success clears the local preflight once. It does not establish provider availability over time or verify a hosted Render deployment.

No API key or generated answer text is stored in either report. Free model capacity and router selection can change between requests; verify a fresh `llm_refinement=completed` on the deployed service before recording.
