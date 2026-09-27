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

The current local working tree passed 82 tests, with one third-party Starlette/AnyIO deprecation warning. Both 30-case golden-set runs passed their deterministic proxy checks over in-process and stdio transports; workflow completion uses the five workflow-category cases. In-process priming took 6,005.88 ms; its warm 15-task p50/p95 were 23.59/104.74 ms. Stdio tasks include a fresh MCP subprocess and model/index initialization; their 15-task p50/p95 were 7,471.90/7,917.17 ms after a separate 8,478.52 ms priming request. Both CI evaluation commands fail on any failed case check or aggregate threshold regression. Public `/chat` regressions cover citation metadata separation, number-word/digit equivalence, unsupported numbers, process-narration rejection, mixed employee ID/name refusal, and medical-file/chart refusals before employee lookup. A local desktop/narrow-viewport browser review exercised both demo workflows over stdio and is recorded in `evidence/ui-review.md`. The detailed reports are `evaluation/results.md`, `evaluation/results-stdio.md`, and `evidence/index.md`.

These values are fixture-based; the full golden set is not an independent semantic entailment evaluation and excludes OpenRouter generation. Hosted CI run [36306573067](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36306573067) passed on `6ce0da8`, which is live on Render deployment `dep-dasdc7fpn0mc73fu752g` with health checks passing. Historical local remote-work and PTO requests resolved to `poolside/laguna-s-2.1:free` and `inclusionai/ling-3.0-flash-fin:free` for those individual requests. The latest hosted synthetic E1002 request returned 503 after all four MCP calls and HTTP 429 from every configured model route. The current local key authenticated at OpenRouter's current-key endpoint and reported the Free-tier daily request allowance exhausted at 51 used of 50, with none remaining; OpenRouter currently lists 50 daily requests on its [Free pricing tier](https://openrouter.ai/pricing/). No paid model route was called, and no raw provider body, model text, or key was retained. The application remains fail-closed; retry the hosted answer path when the quota replenishes. A non-fatal Hugging Face cache metadata write warning appeared during local MiniLM use; the model loaded and both evaluations completed.

All employee records, policies, tickets, and actions remain fictional. No production HR system is connected.
