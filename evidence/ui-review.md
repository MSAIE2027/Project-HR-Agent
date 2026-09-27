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
