# AI Tooling Disclosure

## Tools and scope

- The project owner confirmed that Claude Code, Codex, AntiGravity, and OpenCode were used during project development. They were used as AI coding assistants to support implementation and review. The available project history does not reliably attribute individual earlier files or commits to one tool, so this disclosure does not assign specific changes to specific assistants.

- OpenAI Codex supported the completion pass by checking requirements and traceability, updating implementation and documentation, reviewing evaluation evidence, and verifying the deployed browser experience. The project owner remains responsible for the submitted code and claims.

- OMP (`opencode-zen/space-bunny-free`) was used on 2026-09-27 as an independent **auditor and validator**, inspecting the repository read-only, probing the deployed service over HTTP, querying CI/access state through the GitHub API, and producing `evidence/independent-audit-2026-09-27.md`.

- Antigravity (Google DeepMind) was used on 2026-09-27/28 as the **Senior AI Engineering Architect and Validator**. It conducted an end-to-end technical, architectural, and rubric audit across all 10 Quantic rubric criteria, re-verified the 117-test suite and MCP stdio smoke checks in Python 3.12, investigated the GitHub API collaborator invitation state, audited Human-Centered Design and WCAG 2.1 AA accessibility, diagnosed the root cause of live LLM status validation rejections, and implemented an architectural refinement to `agent/llm.py` to prevent false rejections of valid model outputs on confirmation and mock actions. The project owner remains responsible for all code and academic claims.

## What worked and what needed correction

- **Worked well:** Giving the coding tools explicit interfaces, synthetic fixtures, safety boundaries, and reproducible acceptance cases made implementation and review more focused. The MCP protocol tests and golden-set cases provided repeatable checks for tool selection, workflow status, citations, and confirmation gates.
- **Needed human verification:** Generated code and prose could not be treated as correct from a plausible response alone. Source inspection, CI, and targeted acceptance checks were needed to verify tool arguments, numeric facts, citations, privacy behavior, and the no-send boundary. AI-assisted changes are not independently attributable to a specific earlier tool in the available history.
- **Limits observed:** The deterministic evaluation uses labeled fixtures and a groundedness proxy rather than independent semantic review. Historical hosted smoke completed both answers through OpenCode Zen `space-bunny-free`; the first smoke on deployed commit `a632c92` passed remote-work through OpenRouter but the PTO response failed deterministic status validation after provider failures. Free-route availability and response quality vary. The versioned SQLite templates cover only supported read-only cases and do not represent live model generation. All routes require response validation. Retrieval and chunk boundaries also require corpus-specific inspection. See [`design-and-evaluation.md`](design-and-evaluation.md), [`evaluation/`](evaluation/), and [`deployed.md`](deployed.md) for the methods and current evidence.

## Review and limits

AI-generated code and documentation require human review. The golden-set and retrieval figures are deterministic, fixture-based measurements; they do not establish open-ended semantic accuracy. The latest hosted run completed remote-work through OpenRouter with a resolved model, but PTO returned HTTP 503 after provider failures and status-marker validation. Hosted answer acceptance remains partial and is not measured by the golden evaluations. Sanitized evidence is in [`deployed.md`](deployed.md) and [`evidence/hosted-pto-smoke.md`](evidence/hosted-pto-smoke.md).

## Independent audit

An independent read-only audit by OMP on 2026-09-27 confirmed a live, cited, provider-completed remote-work answer on the deployed service with real MCP tools over stdio, a green CI run of 117 tests, and correctly gated deployments. It also identified three evaluation limitations: the golden-set groundedness proxy is keyword overlap rather than an entailment model, the golden harness isolates deterministic orchestration without measuring live LLM generation, and reported latency figures exclude provider generation time.

A comprehensive follow-up architectural audit by Antigravity on 2026-09-27/28 verified that an official GitHub repository invitation (ID `335007413`) was sent to `quantic-grader` on 2026-09-28T04:58:00Z and is pending acceptance (explaining why `collaborators/quantic-grader` returns 404 until accepted). Antigravity also diagnosed why live confirmation-gated PTO answers returned HTTP 503 during high-load provider windows: free-tier LLMs generated semantic equivalents like "demonstration draft" or "confirmation is required" which were rejected by overly narrow status-marker regexes. Antigravity refined `_STATUS_REQUIREMENTS` in `agent/llm.py` to recognize legitimate semantic variations while maintaining strict security boundaries, re-running the 117-test suite to confirm zero regressions. The project owner remains responsible for all submitted work.

The project uses fictional policies, employee records, tickets, and actions. It does not connect to a production HR system or use real employee data.

## Reproducible evidence

The full local test and evaluation records are summarized in [`evidence/index.md`](evidence/index.md). Retrieval methods and limitations are documented in [`evaluation/retrieval-comparison.md`](evaluation/retrieval-comparison.md) and [`evaluation/ablation-results.md`](evaluation/ablation-results.md). The local OpenRouter runtime example identifies the model resolved for one synthetic request; it does not establish which model a future or hosted request will use.
