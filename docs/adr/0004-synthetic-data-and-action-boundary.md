# ADR 0004: Keep Data Synthetic and Mock Actions Confirmation-Gated

- **Status:** Accepted
- **Date:** 2026-09-26

## Context

The course scenario concerns HR information and possible write-like actions. The learning objective can be met without real employee data or production integrations.

## Decision

Use fictional policy documents and synthetic employee records only. Email and ticket tools create local mock artifacts after an explicit confirmation flag. The system must identify the action as mock and must not claim that a real message or record was sent or created.

## Consequences

- Demonstrations and evaluation can exercise action safety without external effects.
- Sensitive cases escalate to an authorized HR professional; the assistant does not investigate or provide professional determinations.
- Any future real integration would be a new, separately reviewed scope requiring stronger identity, authorization, auditing, privacy, and incident controls.

## Evidence

`mock_data/`, `mcp_server/tools.py`, `agent/orchestrator.py`, `tests/test_app.py`, `evaluation/golden_set.json`.
