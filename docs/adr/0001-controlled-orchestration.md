# ADR 0001: Keep Workflow Control in the Orchestrator

- **Status:** Accepted
- **Date:** 2026-09-26

## Context

The course project needs multi-step tool use and inspectable traces, but the HR domain includes sensitive records and write-like operations. An open-ended model loop would make tool choice, completion, and authorization harder to constrain and reproduce.

## Decision

Use an explicit Python orchestrator for request classification, tool discovery, workflow sequencing, evidence thresholds, safety refusals, and confirmation gates. Every citation-bearing response must pass through OpenRouter's pinned free model chain: Qwen 3.8 27B, Nemotron 3.5 Lightning, and Gemma 4 26B A4B, followed by `openrouter/free`. The selected model composes the final answer from the controlled draft, retrieved policy evidence, and structured facts. The LLM cannot select tools, alter eligibility, or authorize actions. If no route is configured or no route in the chain can return a valid answer, the API returns a safe service error instead of presenting an unrefined retrieval draft.

## Consequences

- Tool sequences and safety transitions are deterministic and testable.
- The UI can show concise operational traces without exposing hidden reasoning.
- Routing rules require maintenance and may miss paraphrases; this is tracked as an evaluation risk.
- Final response composition has string-level consistency checks, not a proof of semantic entailment; rejected outputs fail closed and are not shown to the user.

## Evidence

`agent/orchestrator.py`, `agent/llm.py`, `docs/architecture.md`, `tests/test_app.py`, `tests/test_llm.py`.
