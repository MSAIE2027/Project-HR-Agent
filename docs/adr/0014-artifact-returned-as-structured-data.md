# ADR 0014: Created Artifacts Returned as Structured Data

- **Status:** Accepted
- **Amends:** the answer-composition contract in [ADR 0001](0001-controlled-orchestration.md), extending the validation rules in [ADR 0013](0013-model-agnostic-response-validation.md)

## Context

On 2026-10-01 the confirmed PTO workflow completed successfully and the user reported that the
email draft was nowhere on screen. The trace showed the artifact had been created correctly:

```
action_id : EMAIL-9FAE6298D3
to        : manager.one@example.invalid
subject   : PTO request for 4 day(s) — Noah Williams
sent      : false
```

The composed answer read:

> "You have 8 synthetic PTO days available… **This is a demonstration draft; no email was sent.**"

The draft's recipient, subject, and body were **absent**. The model had kept the disclaimer
sentence and deleted the artifact.

## Root cause

The artifact lived only inside the controlled draft, which is prose handed to the refiner. The
refiner is instructed to return a clean 2–4 sentence answer and to omit tool metadata. It applied
that instruction to the email block and removed it.

No validation rule objected, because none of them checked artifact survival. The
`mock_action_completed` status marker passed on the words *"demonstration draft"*, the
`no_action_disclaimer` rule passed on *"no email was sent"*, and every other check passed. The
answer was returned as a clean success while omitting the thing the user asked for.

This is a design error, not a model error. **A created artifact is structured data. Routing it
through a prose channel and hoping the model preserves it makes the deliverable contingent on
model behaviour.** ADR 0013 established that the validator must not encode one model's phrasing;
this ADR removes the dependency entirely rather than adding another pattern to match.

## Decision

**1. Artifacts are returned as structured data.** `AgentResult` gains `mock_action`, the `/chat`
response gains a `mock_action` field, and the web client renders it as a card:

```json
{
  "mock_action": {
    "action_id": "EMAIL-9FAE6298D3",
    "action_type": "mock_email_draft",
    "sent": false,
    "to": "manager.one@example.invalid",
    "subject": "PTO request for 4 day(s) — Noah Williams",
    "body": "Please review Noah Williams's synthetic PTO request…"
  }
}
```

The field is returned verbatim from the tool result. No model participates in producing it, so no
paraphrase can alter or drop it. It is `null` for every read-only request, and it is populated for
both the email draft and the sensitive-case ticket.

**2. The narrative must still acknowledge it.** A new validator rule,
`created_artifact_omitted`, fires when the controlled draft contains an artifact block and the
refined answer neither references the artifact nor, when the draft has a subject line, quotes that
subject. The completion is rejected and the next route is tried.

The subject requirement is deliberately strict. *"I created a draft"* is not sufficient when the
draft's subject is `PTO request for 4 day(s) — Noah Williams`, because the subject is what
identifies the artifact to the user.

**3. The composer prompt states the obligation.** The refiner is told that a created artifact must
still be named in the narrative even though the full artifact is returned separately.

## Consequences

**The deliverable is now model-independent.** The email the user asked for is in a field no model
can touch. This is stronger than the alternative — widening a pattern until the current model
passes — which ADR 0013 already showed to be a losing game.

**Artifact loss is loud rather than silent.** Before this change the failure produced a successful
HTTP 200 with a missing deliverable. It now produces `created_artifact_omitted`, which the
refinement trace already surfaces per route.

**The action boundary is untouched.** `sent` remains `false` from the tool, `draft_hr_email` still
requires a confirmed turn, and the ticket path still requires confirmation. None of those changed.

**Two latent bugs surfaced while implementing.** `mock_action` was referenced on the return path
of workflows where it was never assigned, raising `UnboundLocalError` for read-only PTO and for
every sensitive-case path. The new tests caught both. The field is now initialised on each path.

## Alternatives rejected

| Alternative | Why rejected |
|---|---|
| Widen the pattern until `nano-30b` passes | Re-encodes this provider's phrasing; fails on the next swap. |
| Drop the email from the controlled draft | The refiner would have no anchor for the action, making `created_artifact_omitted` unfixable. |
| Return the artifact only in the trace | It is already there; it is unreadable in practice and the answer would still claim a draft exists. |
| Render the artifact in prose and skip the structured field | Keeps the deliverable contingent on model behaviour, which is the defect. |
