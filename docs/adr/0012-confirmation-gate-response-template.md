# ADR 0012: Confirmation-Gate Response Template

- **Status:** Accepted
- **Date:** 2026-10-01
- **Amends:** [ADR 0010](0010-provider-and-sqlite-response-fallbacks.md) and the action-boundary rule in [ADR 0004](0004-synthetic-data-and-action-boundary.md)

## Context

[ADR 0010](0010-provider-and-sqlite-response-fallbacks.md) scoped the build-seeded SQLite response
templates to supported **read-only** workflows and excluded confirmation-gated actions entirely. The
stated reason was that an action-intent request must not receive an answer that was not composed by a
live model.

That rule had one intended effect and one unintended effect.

**Intended and preserved:** no draft is ever created without explicit confirmation. That boundary is
enforced by the orchestrator — `requires_confirmation` gates the `draft_hr_email` tool call — not by
the template decision. The templates never invoke a tool.

**Unintended:** the confirmation-gated PTO request was the only workflow with **no** fallback at all.
It could not use live generation when every provider tier was exhausted, and it could not use the
templates. A total upstream outage therefore produced HTTP 503 for the one workflow the course
requires demonstrating.

Hosted evidence on 2026-10-01 made this concrete. All six routes failed — two metered routes whose
completions the status-marker validator rejected, `openrouter/free` on an account-wide quota 429, and
three OpenCode routes on 403 and timeout. The read-only PTO and remote-work workflows still answered
from templates; the gated one returned nothing.

## Decision

Allow the template path for `status == "confirmation_required"` on the PTO workflow, via a fourth
seeded template `pto_confirmation_gate`.

The template restates the verified facts, restates the gate, and states in the answer body that it was
formatted locally rather than model-composed.

To keep the distinction auditable, the refinement trace carries a **different** `response_mode` for
this case:

| Field | Read-only template | Confirmation-gate template |
|---|---|---|
| `status` | `cached_template` | `cached_template` |
| `response_mode` | `sqlite_template` | **`confirmation_gate_template`** |
| `model_composed` | `false` | `false` |
| `action_taken` | `false` | `false` |
| `template_key` | `pto_balance` / `pto_request` / `remote_work_eligible` | **`pto_confirmation_gate`** |

A reviewer can therefore never read a gated response as live generation.

## Consequences

**The action boundary is unchanged.** `draft_hr_email` still requires an explicit confirmation turn.
The template formats prose about a pending request; it does not create, send, or simulate a draft.
`tests/test_app.py::test_sqlite_template_does_not_bypass_confirmation_gate_after_quota_failure` now
asserts the invariant that actually matters — HTTP 200, `requires_confirmation` still true, and
`draft_hr_email` absent from the tool trace — rather than the old rule that the request must 503.

**Other workflows remain excluded.** A confirmation flag on the remote-work workflow means the request
escalated to a sensitive-case mock ticket, so `cached_response` returns `None` there. Only the PTO
draft path is eligible.

**The honest-reporting rule still holds.** The rendered text states that it was formatted locally
because live generation was unavailable, and the trace labels it `confirmation_gate_template` with
`model_composed: false`. Nothing here represents a template as a model completion.

## Alternatives rejected

| Alternative | Why rejected |
|---|---|
| Keep the exclusion | A total provider outage blocks the second required demo task outright. |
| Extend templates to *all* gated workflows | A sensitive-case ticket carries different facts and escalation semantics; the PTO draft path is the only one with verified fact bindings. |
| Return the raw controlled draft instead | The draft is deliberately never surfaced, confirmed by the existing sentinel assertion. |
| Remove the template path entirely | Throws away working resilience for the three read-only workflows that already answer during an outage. |
