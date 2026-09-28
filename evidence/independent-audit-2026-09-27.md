# Independent Audit Record — 2026-09-27

Independent read-only audit of the project against the official course prompt. No source file,
configuration, test, or index was modified by this audit; all probes were external HTTP calls
and read-only inspection. Runtime facts below are recorded because a command result exists.

Auditor tooling: OMP (opencode-zen/space-bunny-free), acting as auditor and validator. See
[`../ai-tooling.md`](../ai-tooling.md) for the disclosure.

## Scope and method

| Method | Commands | Note |
|---|---|---|
| Source inspection | `read`, `grep` on `rag/`, `agent/`, `mcp_server/`, `mcp_client/`, `app/`, `tests/`, `.github/workflows/ci.yml` | No execution of pytest or the evaluation harness. |
| Live deployed behavior | `curl` against `https://project-hr-agent.onrender.com` | Read-only GETs and one non-confirming `POST /chat`. No mock action was confirmed. |
| CI and access state | `gh run list`, `gh run view`, `gh api repos/.../collaborators/...` | Read-only GitHub API calls. |

## Live deployment verification

| Probe | Result | Wall clock |
|---|---|---|
| `GET /health/ready` | HTTP 200 | 75.161 s (includes Free cold start) |
| `GET /` | HTTP 200 | 30.181 s |
| `POST /chat` — "Can E1001 work remotely overseas for 10 days?" (run 1) | HTTP 200 | 97.873 s |
| `POST /chat` — same request (run 2) | HTTP 200 | 99.449 s |

`/health/ready` reported `status: ok`, `service: msaie-hr-agent`, `version: 2.1.0`,
`mode: agentic-rag-mcp-llm`, MCP `available` over `stdio` with 8 tools, and RAG index
`ready`: 14 documents, 182 chunks, 384 dimensions, `onnxruntime-quint8-avx2`,
`sentence-transformers/all-MiniLM-L6-v2`, revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, 120/20 chunking, `estimated_pages: 37.5`.

The two `/chat` runs returned identical status `provisionally_eligible` with 5 citations, all
`POL-RW-01`, and the operational trace:

1. `discover_tools` — server `MSAIE HR Tools`, transport `stdio`, 8 tool names returned.
2. `search_policy_documents` — `{"query": "international remote work eligibility rolling limit
   security approvals immigration tax", "limit": 5, "document_prefix": "POL-RW-"}`, status `ok`,
   top chunk score `0.7935`, `retrieval_method: huggingface_dense_cosine`.
3. `lookup_employee_profile` — `{"employee_id": "E1001"}`; returned Maya Chen, Singapore
   (`SG-01`), `remote_days_used_rolling_12m: 4`.
4. `check_policy_compliance` — `{"workflow": "remote_work", "employee_id": "E1001",
   "requested_days": 10, "destination": null}`; returned `eligible: true`,
   `days_after_request: 14`, `limit_days: 20`, five required approvals.
5. `llm_refinement` — `status: completed`, `provider: openrouter`, resolved model
   `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`, requested `openrouter/free`, after
   attempting `qwen/qwen3.8-27b:free`, `nvidia/nemotron-3.5-lightning:free`, and
   `google/gemma-4-26b-a4b-it:free`.

This is a live, provider-completed, cited answer on the currently deployed runtime, and it
independently re-verifies the remote-work half of the acceptance gate. The resolved free model
differs from the previously recorded `inclusionai/ling-3.0-flash-fin:free`, which is consistent
with free-route provider variance rather than a code change.

**Not verified by this audit:** the confirmation-gated PTO answer on the deployed instance; the
recorded screen-share demonstration; course-grader repository access; peak or concurrent hosted
memory; any typical-startup latency distribution.

## CI and repository state

- The 8 most recent CI runs on `main` are all `success`; the newest, `36363755320`, ran on
  current HEAD `922a296` and reported `117 passed, 1 warning in 22.36s`.
- The `Deploy tested commit to Render` job reported `skipped`, confirming the deployment gate
  is closed rather than silently deploying.
- The repository is `private: true`, and the collaborator permission query for `quantic-grader`
  returns `{"permission": "none"}`. Grader read access is therefore **not** in place as of this
  audit and remains a required pre-submission action.

## Confirmed implementation facts

- Corpus: 14 policy files under `policies/` — 8 Markdown, 6 HTML — totalling 16,010 words.
  `rag/ingest.py` dispatches on suffix to `load_markdown` (frontmatter plus `#`–`###` heading
  split) or `load_html` (`html.parser` based), then groups paragraphs per section.
- Chunking is deterministic heading-aware sectioning followed by a fixed word window with
  overlap (`chunk_sections`); no sampling or randomness is involved.
- `mcp_server/server.py` registers exactly 8 tools on `mcp.server.fastmcp.FastMCP` and runs
  `transport="stdio"`. `tests/test_mcp.py` performs real `list_tools` and `call_tool` calls
  over a stdio session and asserts at least 8 tools.
- HTTP surface: `/`, `/health`, `/health/ready`, `/api/tools`, `/api/index/documents`,
  `/api/index/documents/{document_id}/chunks`, `POST /chat`, and FastAPI `/docs`.
- Intent routing in `agent/orchestrator.py` is substring keyword matching over
  `TOPIC_PREFIX_MAPPINGS`; when no family matches, the search tool is called with
  `document_prefix: null` as an unfiltered fallback.
- The golden-set "groundedness" metric is implemented in `evaluation/run_evaluation.py` as
  `_keyword_score`, the fraction of hand-authored `gold_keywords` present as substrings in the
  answer, with `groundedness_pass` also requiring expected status and citation families.

## Audit findings on evaluation rigor

These are recorded because they bound what the reported 1.0 scores mean. They do not change any
system behavior.

1. The golden-set harness calls the orchestrator directly and does not invoke live answer
   generation; `llm_generation_included` is `No` in the report. The generation path is covered
   only by unit tests with a fake provider and by hosted smoke runs.
2. Because the orchestrator is deterministic and the gold labels were authored against it, the
   status, tool-sequence, and citation metrics are self-consistency checks, not independent
   correctness measurements. The project discloses this in `evaluation/results.md` and
   `design-and-evaluation.md`.
3. Family coverage in `evaluation/retrieval-comparison.md` is partly produced by the router's
   own `document_prefix` filter, so it measures routing plus retrieval rather than retrieval
   alone. The report labels it as routing and retrieval together.
4. Reported p50/p95 latencies explicitly exclude answer generation. The audit's ~98 s live
   end-to-end figure is the only recorded number that includes it, and it is a cold-instance
   single sample.
5. `estimated_pages` values are declared per file in document frontmatter or HTML meta tags
   (2.5–2.9 each, 37.5 total) rather than measured from a rendering. The raw word count of
   16,010 is the independently checkable figure.
