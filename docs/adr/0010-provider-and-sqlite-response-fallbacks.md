# ADR 0010: Add Provider and SQLite Response Fallbacks

- **Status:** Accepted
- **Date:** 2026-09-27

## Context

OpenRouter's free account quota can make citation-backed demo answers unavailable even when MCP and SQLite retrieval succeed. Returning retrieval text directly would skip the required final composition step and can reproduce awkward, incomplete chunk formatting. Persisting arbitrary generated answers risks serving stale or fact-specific content.

## Decision

1. Keep OpenRouter as the primary answer composer and preserve its configured model order. A recognized account-wide free daily quota response stops further OpenRouter attempts and advances directly to OpenCode Zen. Model/provider-specific or unclassified throttles continue through the OpenRouter chain; OpenCode Zen is tried after that chain is exhausted. OpenCode Zen requests use the OpenAI-compatible `/v1/chat/completions` interface, the same evidence/facts prompt, and the same response validator. The key is read only from `OPENCODE_API_KEY`; endpoint and model IDs are configurable through `OPENCODE_ZEN_BASE_URL` and `OPENCODE_ZEN_MODELS`.
2. If live composition remains unavailable or fails validation, allow only curated, versioned templates stored in the build-generated SQLite index. They format current MCP facts and current citations for supported read-only PTO balance/request and provisionally eligible remote-work responses. A match requires an allowed workflow status, required typed facts, and the expected policy citation family. Confirmation-gated actions, refusals, unsupported workflows, missing facts/citations, and template misses never use the templates.
3. Store template definitions, not personalized answers. Each request still runs request guards, MCP lookups, and policy retrieval. Runtime template reads use SQLite read-only connections. Template version participates in index freshness so a code template change rebuilds the database. The UI and `llm_refinement` trace identify the actual live model or SQLite template path.

OpenCode Zen's current official catalog lists Nemotron 3.5 Lightning Free, Big Pickle, and Space Bunny Free at zero per-token cost through `https://opencode.ai/zen/v1/chat/completions`; the catalog marks them as limited-time offers. Zen is otherwise pay-as-you-go, account setup asks for billing details, and workspace admins can disable model access. A configured key or successful `/models` response does not establish that generation is enabled, so the hosted preflight must verify a completed chat. Free-route data practices vary; some free models may use requests to improve their models. This app therefore accepts only synthetic HR fixtures. See the [OpenCode Zen model catalog and access notes](https://opencode.ai/docs/en/zen/).

## Consequences

- OpenRouter quota exhaustion can still produce a true live-model answer when an OpenCode key and model route are available.
- The answer retains fresh evidence and synthetic structured facts when it falls back to SQLite, and the trace distinguishes it from live LLM generation.
- The SQLite layer does not guarantee an answer for arbitrary queries. Unsafe, action, insufficient-evidence, and unmatched requests still fail closed with HTTP 503.
- No model answer or employee fact is persisted as a reusable cache entry; stale personalization is avoided.
- OpenCode Zen models and free-tier access are an external dependency and must be confirmed before recording. The deterministic SQLite templates provide a bounded demo fallback, not general-purpose language generation.

## Evidence

- Public `/chat` tests cover OpenRouter account-quota routing to OpenCode Zen, validated responses, and SQLite fallback when the primary quota is exhausted.
- `/api/index/documents` lists seeded template metadata; UI tests assert the SQLite template viewer is available.
- `agent/response_cache.py`, `agent/llm.py`, `rag/index.py`, and `app/main.py` implement the path.
