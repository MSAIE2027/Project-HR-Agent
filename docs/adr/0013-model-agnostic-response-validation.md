# ADR 0013: Model-Agnostic Response Validation

- **Status:** Accepted
- **Amends:** the response-validation rules behind [ADR 0001](0001-controlled-orchestration.md) (draft-first composition) and [ADR 0008](0008-openrouter-quota-aware-fallback.md) (provider cascade), both of which depend on a completion surviving validation

## Context

Between 2026-09-30 and 2026-10-01 the answer validator rejected **every** model in the cascade,
producing HTTP 503 for workflows that had worked for the previous week. The failures arrived in
three waves, and each wave looked like a new bug:

| Wave | Rule that fired | Rejected phrase |
|---|---|---|
| 1 | `confirmation_required` status marker | "I need your confirmation first" |
| 2 | `mock_action_completed` status marker | "I created a local draft" |
| 3 | `no_action_disclaimer_omitted` | "No email has left the system" |

Each rule accepted one narrow family of sentences. The free-model chain happened to produce
sentences inside that family, so the rules passed. The moment the chain was reordered to
`nvidia/nemotron-3-nano-30b-a3b` and `qwen/qwen-2.5-7b-instruct` (ADR 0011), those models
paraphrased the same facts and every route was rejected in turn.

A systematic sweep of the remaining status markers then found **nine more** faithful phrasings
rejected, concentrated in `provisionally_eligible` and `not_eligible` — the two most frequently
returned statuses in the corpus.

## Root cause

The validator encoded **one model's phrasing as if it were the fact.** A status marker is a
legitimate check that an answer does not contradict the app's computed status. It is not legitimate
to require a specific sentence, because which sentence a model produces is a property of the
model, not of the answer's correctness.

The distinction that matters:

- **A check on meaning** — "does this text convey that the employee is not eligible?" — is correct.
- **A check on wording** — "does this text contain the literal string `not eligible`?" — is a
  model-specific heuristic wearing the costume of a safety check.

The second kind fails closed, which is the safe direction, but "fails closed" is not "correct." In
a chain that requires a live completion, over-rejection is indistinguishable from outage: the user
receives HTTP 503 and no answer at all.

## Decision

Every status marker and no-action disclaimer now accepts a set of **faithful paraphrases**, while
remaining distinct from the other statuses and from the anti-fabrication rules.

Two properties are enforced by test rather than by inspection:

1. **Recall** — 22 realistic paraphrases across all seven statuses are accepted.
2. **Distinctness** — widening one marker never makes it satisfy a different status, so
   `_STATUS_CONTRADICTIONS` and the `_APPROVAL_*` rules keep operating on unambiguous input.

The anti-fabrication layer is deliberately **unchanged**: `unsupported_numeric_fact`,
`status_contradiction`, `internal_reasoning_exposed`, and the approval-claim rules stay narrow.
Those checks prevent the model from asserting something untrue, and there is no cost to being
strict when the failure is a refusal rather than a silent wrong answer.

## What was not changed, and why

| Rule | Kept strict because |
|---|---|
| `unsupported_numeric_fact` | An invented number is the highest-severity failure mode. Rejecting a valid number is cheaper than accepting a fabricated one. |
| `status_contradiction` | Catches `not_eligible` answers claiming the employee "is eligible" or "approved". Precision is what makes it useful. |
| `_APPROVAL_*_CLAIM` | Prevents a composed answer from asserting that approval was granted. Also negating its own false positives, because a missed approval claim is a correctness defect, not a wording defect. |
| `internal_reasoning_exposed` | Cheap and rarely fires. |

## Consequences

**The validator is now model-agnostic.** A provider swap no longer requires auditing prose rules.
This is the property that was missing and that the cascade depends on.

**The real action boundary is unchanged.** Every rule in `_APPROVAL_*` and the
`requires_confirmation` gate are untouched. The disclaimers and status markers govern the wording a
user reads; the gate that prevents an action is enforced by the orchestrator, which cannot be
satisfied by any amount of text.

**Coverage is now behavioural rather than incidental.** 34 new cases in `tests/test_llm.py` lock
both directions: paraphrases that must be accepted, and phrasings that must stay rejected. The
first wave of this defect was possible precisely because no test asserted a natural paraphrase
either way.

## Alternatives rejected

| Alternative | Why rejected |
|---|---|
| Drop status markers entirely | Loses the contradiction check, which is a real guardrail. |
| Prompt the model to use exact required wording | Puts a brittle contract in the prompt; models drift, and it is unauditable from a trace. |
| Keep strict markers and accept 503 as correct behaviour | Converts a model-family dependency into a documented outage. |
| Use a fuzzy or embedding-based marker match | Unauditable, non-deterministic, and harder to review than a documented alternation set. |
| Loosen the anti-fabrication rules for symmetry | Fabricated numbers and false approval claims are correctness defects, not wording defects. |
