# AI Tooling Disclosure

## AI tools used

- **Claude Code, Codex, AntiGravity, and OpenCode:** the project owner confirmed these were used before this completion pass. Project records do not identify which tool contributed to each earlier design, implementation, documentation, retrieval-evaluation, or debugging activity, so no tool-specific attribution is inferred.
- **OpenAI Codex (this completion pass):** used to map the course prompt into SRS/traceability artifacts, inspect and correct code/tests/docs, regenerate local evaluation evidence, rehearse the UI with browser automation, and run separate standards/spec reviews.

## What worked and what needed review

In this completion pass, Codex was useful for following links across the requirements-to-evidence chain, reproducing local failures, correcting stale sample prompts and test configuration, and generating repeatable checks. Human review remains necessary: fixture scores do not establish semantic correctness, and the independent review caught a latency-reporting defect that required a measurement-method change. Browser inspection confirmed the local UI flows but does not replace screen-reader, contrast, or hosted-service review. The project records do not contain a tool-by-tool retrospective for Claude Code, AntiGravity, or OpenCode, so this disclosure makes no claims about which of those tools worked better or contributed specific code.

The MSAIE HR Agent behavior, policies, examples, and synthetic records are specific to this standalone project. No real employee data was supplied to the agent in this completion pass.

The project instructions for future coding agents are in `AGENTS.md`. Local agent skills are developer tooling and are ignored by Git; they are not application dependencies.

## Verification record

The production embedding baseline remains `sentence-transformers/all-MiniLM-L6-v2` at 384 dimensions, with 120-word chunks and 20-word overlap. The 120/20 setting was the smallest of three tied configurations (120/20, 160/24, and 220/30). LLM endpoint settings remain separate from embedding settings.

The MiniLM-only retrieval comparison covered 15 hand-labeled policy queries, including five multi-family cases, at global k=1, 3, 5, and 8. On the expanded corpus, global top-five ranking covered every expected family in 1/5 multi-family probes; MMR λ=0.5 raised that to 2/5 and family recall from 0.76 to 0.81. Production then explicitly routes detected families, seeds one result per family, and covers all expected families in all five labeled multi-family route probes. Scoring weights, model, chunk size, and output budget remain unchanged.

A fresh read-only route comparison measured 100% expected-family coverage across the 15 queries, including 5/5 multi-family probes. The six-item read-only policy golden slice scored 100% on status, citation-prefix, and groundedness-proxy checks. Runtime retrieval reported `huggingface_dense_cosine`. These small, hand-authored query sets measure retrieval and deterministic proxy outcomes; they do not establish general semantic correctness.

Regression coverage was added for MMR diversity and family citations. In this completion pass, Codex was used to inspect the assignment requirements, correct outdated demo/test configuration, repair direct script imports, add CI and traceability documentation, and run local verification.

The full local test suite passed: 64 passed, with one third-party Starlette/AnyIO deprecation warning. Both 25-case golden-set runs passed their deterministic proxy checks over in-process and stdio transports; workflow completion uses the five workflow-category cases. In-process priming took 6,369.82 ms; its warm 15-task p50/p95 were 20.28/62.54 ms. Stdio tasks include a fresh MCP subprocess and model/index initialization; their 15-task p50/p95 were 8,645.27/11,180.99 ms after a separate 9,659.28 ms priming request. Both CI evaluation commands fail on any failed case check or aggregate threshold regression. A local desktop/narrow-viewport browser review exercised both demo workflows over stdio and is recorded in `evidence/ui-review.md`. The detailed reports are `evaluation/results.md`, `evaluation/results-stdio.md`, and `evidence/index.md`.

These values are local and fixture-based. The full golden set is not an independent semantic entailment evaluation. No hosted CI result, public deployment, or cold-start measurement has yet been recorded. Two current-index live `/chat` preflight calls returned 503; a later retry on the same 182-chunk index returned 200 with five citations and `llm_refinement=completed` through the required four-route chain. The earlier separate successful call used a stale 126-chunk index. A non-fatal Hugging Face cache metadata write warning appeared during local MiniLM use; the model loaded and retrieval/evaluation completed.

All employee records, policies, tickets, and actions remain fictional. No production HR system is connected.
