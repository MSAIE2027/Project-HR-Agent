# Local UI Review

**Date:** 2026-09-26
**Build:** current working tree, served locally at `http://127.0.0.1:8002/` with `MSAIE_MCP_TRANSPORT=stdio`
**Scope:** visual layout, narrow viewport reflow, basic keyboard/focus behavior, evidence inspection, and the two demo workflows.

## Observations

- At 1280 × 720, the first run exposed that the example panel crowded the active response. The panel now hides after the first user prompt; the remote-work answer, citation summary, and trace control fit in the visible workspace. The header, health indicator, and composer remain visible.
- At 390 × 844, the answer text stayed readable and the layout had no horizontal overflow after the responsive transition settled. The citation card and trace can be reached by scrolling the conversation.
- Keyboard inspection showed a visible skip-link/focus treatment and usable Tab navigation. Opening the evaluator lab and pressing Escape closed it and restored focus to its launch button.
- The international remote-work example returned a provisional eligibility answer with policy citation `POL-RW-01`, the applicable 14/20-day figures, approval caveats, and the ordered policy/profile/compliance trace. Tool discovery and calls showed `transport: stdio`.
- The PTO request first returned `confirmation_required` and stated that nothing had been sent. After confirming the explicitly local mock action, the response showed `mock_action_completed`, a correctly worded subject/body, and the expected policy/profile/PTO-balance/compliance/email-draft trace, also over stdio. No email was sent.

## Limits

This was a local browser review using visible rendering and the browser accessibility tree. It was not a screen-reader session, automated contrast audit, hosted-browser check, or review of a deployed service. The confirmed action wrote only a fictional mock result to the ignored local demo data/log area.

## UI clarity follow-up

**Date:** 2026-09-27

**Build:** local working tree at `http://127.0.0.1:8000/`

**Scope:** evaluator navigation, duplicate examples, initial/health status copy, and synthetic-data boundary.

- The header now has the single Evaluator & Test Lab entry point. The sidebar retains chat navigation and no duplicate evaluator action or repeated prompt list; the main example strip is the one set of chat starters.
- The initial message label reads “Demo assistant” while the service chip begins at “Checking service.” The app updates the chip from `/health`; a failed health request says “Health check failed” instead of presenting a ready state.
- The sidebar and README disclose that the public demo has no employee authentication or role authorization. All available employee data is fictional; an ID is only a fixture selector.
- The local page returned HTTP 200 and its accessibility tree showed the single evaluator entry, one example strip, and an online health state. A source-level regression checks that non-JSON responses are reported as an HTTP error; this follow-up did not inject a synthetic 500, and it does not diagnose the earlier reported local failure.

The follow-up was not a hosted browser review or a security authorization test. See `tickets/README.md` for the separate authorization design work.

## Curated prompt and evaluator review

**Date:** 2026-09-27

**Build:** updated local working tree served by the existing `http://127.0.0.1:8000/` process

**Scope:** four employee-scoped sample prompts, single evaluator entry point, stable automation controls, accessible names, and wide/narrow layout. This was a UI-only browser review; no chat was submitted.

- Replaced the ten-button starter wall with four full questions, each visibly including a synthetic employee ID: two contrasting remote-work examples, the E1001 PTO request, and E1002 benefits status. At 1280 × 800 the cards form a balanced two-column grid; at 390 × 844 they reflow to one column. Both viewports had no document-width overflow.
- Clicked a sample and confirmed its complete text filled the composer while the conversation stayed unchanged. In the evaluator, the Task B Load button filled its full query and left the conversation unchanged. No Run now button, `/chat` request, confirmation control, or mock action was invoked.
- Verified one evaluator launch control and all nine scenario cards. Each card retains one `[data-lab-load]` and one `[data-lab-run]` selector, with scenario-specific accessible names; visible button labels remain Load and Run now.
- The local health panel reported the service online and showed the pinned 384-dimensional semantic embedding, 14 policy documents, 182 chunks, 120/20 chunking, and eight stdio MCP tools. It also reported OpenCode Zen fallback as not configured in this already-running local process. The process was left untouched; no provider request was made. This local observation does not establish Render configuration or hosted answer acceptance.

This review does not claim screen-reader or automated contrast validation, self-identity authorization, hosted UI validation, provider completion, or deployment readiness. The hosted smoke and repository-access gates remain separate evidence.
