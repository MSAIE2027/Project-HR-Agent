# ADR 0011: Metered-First OpenRouter Routing

- **Status:** Accepted
- **Date:** 2026-09-30
- **Supersedes:** the OpenRouter route ordering in [ADR 0008](0008-openrouter-quota-aware-fallback.md) and [ADR 0001](0001-controlled-orchestration.md); their quota-classification and fail-closed rules are unchanged.

## Context

On 2026-09-30 the hosted service returned `llm_unavailable` (HTTP 503) on 3 of 4 identical
confirmation-gated PTO requests, while the OpenRouter account dashboard showed thirteen successful
generations in the same window. The two observations were consistent: the provider key
authenticated and served traffic, but the **account-wide free daily quota** was exhausted, so the
gateway returned HTTP 429 before a completion existed. Nothing in the answer-validation layer
rejected these responses — most attempts never produced one to validate.

The existing cascade handled this correctly by falling through to the OpenCode Zen free chain, which
succeeded on a minority of attempts. That produced an unreliable demonstration of the second required
agentic task, whose workflow is confirmation-gated and therefore cannot fall back to the SQLite
response templates.

## Decision

Reorder the OpenRouter chain so two **metered** routes lead, and drop the explicit zero-priced routes
down to a single final fallback:

```
nvidia/nemotron-3-nano-30b-a3b  ->  openai/gpt-oss-120b  ->  openrouter/free
```

Rationale for the two specific models:

- Both are general-purpose composers. Safeguard-tuned models are excluded because their hedging
  trips the binding-status-language validator.
- The two slots are deliberately from **different model families**. The second slot originally held
  `qwen/qwen-2.5-7b-instruct`, which began returning **HTTP 404 on 2026-10-01 while still being
  listed in `GET /api/v1/models`** — OpenRouter retires a slug's serving endpoint without removing
  it from the catalogue. A same-family pair would have left the chain with a single point of
  failure, and a catalogue check would not have caught it. Route health must be verified by
  **calling** the route, not by reading the catalogue.
- `openai/gpt-oss-120b` costs roughly $0.20 per million input tokens against the nano route's
  $0.10. That is immaterial at the observed volume (about 1,400 input tokens per request) and buys a
  second independent provider path.

Per-route timeouts rise from 12s/8s to **15s/12s**, because free-tier generations were observed
truncating at the previous cap and surfacing as timeouts rather than answers.

The project brief permits the owner's own API keys. At the observed token volumes (about 1,400 input
and 400–900 output tokens per request) a full evaluation run costs a small fraction of a cent.

## Consequences

**Answer composition does not depend on credit.** `openrouter/free` remains the final OpenRouter
route, the OpenCode Zen free chain still follows, and the build-seeded SQLite templates remain the
last resort for supported read-only workflows. A deployment with zero credit still produces live
answers.

**Worst-case cascade time is bounded at 81 seconds** — three OpenRouter routes at 15s plus three
OpenCode routes at 12s — before RAG/MCP overhead. This is lower than the pre-change bound of 72
seconds only in the realistic path: with metered routes first, a healthy deployment completes on
attempt one. The bound is reached only when every route is unreachable.

**Documentation that asserted a zero-cost composer became inaccurate and was corrected.** Affected
files are listed in `tickets/README.md` under the ticket that recorded this change. Dated evidence
records under `evidence/` were deliberately **not** rewritten; they describe what was measured on
the day.

**Previously reported latency figures are superseded.** `evaluation/live-latency-results.md` was
measured against the exhausted free-tier chain and reported a bimodal distribution in which only
2 of 15 tasks produced a live answer. It is re-measured in the same change so the Rubric 9 system
metrics describe the deployed configuration.

## Alternatives rejected

| Alternative | Why rejected |
|---|---|
| Keep the free chain first, add credit only as fallback | Leaves the 429 wall in the primary path; Task B stays unreliable. |
| `openai/gpt-oss-safeguard-20b` as second route | Refusal-leaning behaviour trips `status_marker_missing`. |
| Retain all three explicit zero-priced routes | Longer cascade, more timeouts, and the same quota wall; no added resilience over `openrouter/free`. |
| Extend SQLite templates to confirmation-gated cases | Removes live generation from the second demo task and weakens the fail-closed story. |
