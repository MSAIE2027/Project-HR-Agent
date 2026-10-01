# ADR 0001: Keep Workflow Control in the Orchestrator

- **Status:** Accepted
- **Date:** 2026-09-26

## Context

The course project needs multi-step tool use and inspectable traces, but the HR domain includes sensitive records and write-like operations. An open-ended model loop would make tool choice, completion, and authorization harder to constrain and reproduce.

## Decision

Use an explicit Python orchestrator for request classification, tool discovery, workflow sequencing, evidence thresholds, safety refusals, and confirmation gates. Citation-bearing responses first pass through OpenRouter's model chain, which leads with two metered routes (`nvidia/nemotron-3-nano-30b-a3b`, `openai/gpt-oss-120b`) and falls back to `openrouter/free`. The metered tier was adopted on 2026-10-01 after hosted evidence showed the account-wide free daily quota returning 429 before any completion existed, which stranded otherwise successful workflows at HTTP 503. Answer composition remains reachable with no credit because the OpenCode Zen chain and the SQLite templates follow OpenRouter. OpenCode Zen free models are the configured secondary composer after the OpenRouter quota cap or exhausted chain. The selected live model composes the final answer from the controlled draft, retrieved policy evidence, and structured facts. If both live routes fail, a versioned SQLite template may format fresh facts and citations for a small set of read-only workflows. The LLM cannot select tools, alter eligibility, or authorize actions; SQLite never stores personalized answers. Unsafe, unsupported, confirmation-gated, and template-miss requests remain fail-closed.

## Consequences

- Tool sequences and safety transitions are deterministic and testable.
- The UI can show concise operational traces without exposing hidden reasoning.
- Routing rules require maintenance and may miss paraphrases; this is tracked as an evaluation risk.
- Final response composition has string-level consistency checks, not a proof of semantic entailment; rejected outputs fail closed and are not shown to the user.

## Evidence

`agent/orchestrator.py`, `agent/llm.py`, `docs/architecture.md`, `tests/test_app.py`, `tests/test_llm.py`.
