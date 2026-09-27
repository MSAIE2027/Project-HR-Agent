# Design and Evaluation

This document describes the current MSAIE HR Agent architecture and the scope of the latest retrieval comparison.

## Design objective

Provide a local-first, fictional HR support agent that answers policy questions with source citations, consults synthetic employee records, and prepares mock actions only after explicit confirmation.

## Architecture

- app/main.py exposes the FastAPI UI, health, tool registry, and chat endpoints.
- agent/orchestrator.py owns request classification, tool selection, evidence checks, action confirmation, and answer assembly.
- mcp_server/server.py registers typed tools on the official MCP Python SDK FastMCP server.
- mcp_client/client.py supports stdio MCP calls and a local in-process adapter.
- rag/ingest.py reads Markdown and HTML policy sources and builds stable, heading-aware chunks.
- rag/index.py stores vectors and metadata in SQLite, ranks with cosine similarity, and exposes embedding/index status.
- agent/llm.py composes every citation-bearing final response through an ordered OpenRouter chain: pinned Qwen, Nemotron Lightning, and Gemma free model IDs, then `openrouter/free`; the actual resolved route and attempted list are included in the operational trace.

## MCP transport behavior

The local default is in-process. It calls TOOL_REGISTRY functions directly and does not exercise MCP serialization or protocol negotiation. The stdio option launches mcp_server.server as a subprocess, discovers tools through the official MCP client, and exercises FastMCP over the protocol.

The retrieval comparison does not change MCP transport or dependencies.

## Retrieval and embeddings

Production uses sentence-transformers/all-MiniLM-L6-v2 at 384 dimensions and 120-word chunks with 20-word overlap. After expanding the 14 policy files to 15,034 indexed words, the chunk experiment found that 120/20, 160/24, and 220/30 yielded the same 182 chunks and tied on its quality metrics; 120/20 is the smallest of those tied settings. The current raw corpus and page-equivalent estimates are disclosed in the README. Details are in evaluation/ablation-results.md.

The follow-up comparison holds MiniLM and 120/20 fixed. At global k=5, current ranking retrieved all expected families for 1/5 multi-family queries; MMR at λ=0.5 reached 2/5 and raised family recall from 0.76 to 0.81. k=8 reached 2/5 for both current ranking and MMR. Doubling lexical weight did not improve multi-family coverage. Based on this comparison, production uses λ=0.5 MMR over a top-ten candidate pool and returns five results. For explicit multi-family intent it seeds one best result per family, then fills with MMR. The measured gain is modest and the labels are hand-authored.

The updated orchestrator route cited all expected families in 15/15 labeled queries, including 5/5 multi-family probes. The six-item read-only policy golden slice had 100% status, citation-prefix, and groundedness-proxy scores, with `huggingface_dense_cosine` observed. The full 30-case golden-set evaluation is recorded in `evaluation/results.md` and `evaluation/results-stdio.md`; its metric values are deterministic fixture proxies, not independent semantic judgments. The complete query-level matrix and limits are in `evaluation/retrieval-comparison.md`.

Dense local embeddings use cosine similarity plus bounded lexical and title signals. Embedding configuration uses MSAIE_EMBEDDING_*; required OpenRouter answer generation uses MSAIE_LLM_*. Runtime retrieval traces identify the actual path, including huggingface_dense_cosine.

## Refiner fact contract

After deterministic orchestration has retrieved policy evidence and completed any structured-tool checks, the public chat endpoint sends every citation-bearing draft to OpenRouter with the citations, status, and internal structured facts. The model composes and enriches the final wording from that evidence; it does not select tools or authorize actions. Remote-work and PTO workflows attach values such as eligibility, requested days, rolling totals, and notice periods to AgentResult without adding them to the public response schema. Before accepting generated text, the provider checks required status cues, preserves numeric tokens supported by the draft, facts, or retrieved evidence, and rejects unsupported numbers or omitted safety disclaimers. Provider or validation failure returns HTTP 503; an unrefined retrieval draft is never sent to the user.

This is a deterministic consistency guard, not a semantic entailment check. Citation objects remain separate response metadata. API tests exercise the public response seam with a fake provider; the golden-set harness measures deterministic orchestration behavior without making external model calls. Hosted model acceptance is tracked separately in [`evidence/hosted-pto-smoke.md`](evidence/hosted-pto-smoke.md); provider configuration or health alone does not prove a completed answer.

## Evaluation discipline

The retrieval comparison and full 30-case golden-set report are current evidence for their stated scope. The earlier 0.84 report used stale expectations that did not match the current synthetic data/workflow contract; the current evaluation passes its deterministic status, citation-prefix, exact-tool, workflow, clarification/escalation, and safety checks. See `evaluation/failed-test-analysis.md` for the historical discrepancy and remaining limitations.

## Golden-set questions and scoring rubric

The versioned questions and item-level expected values are in [`evaluation/golden_set.json`](evaluation/golden_set.json). The 30 cases cover 5 policy questions, 1 multi-document question, 5 workflows, 4 action-safety cases, 2 clarification cases, 2 missing-record cases, 2 structured lookups, 7 safety refusals, 1 escalation, and 1 out-of-scope question. Representative tasks and presenter prompts are in [`demo/README.md`](demo/README.md).

Each item defines its query, expected status, exact expected MCP tool sequence, expected citation-prefix set, keyword rubric, and confirmation flag. The evaluation computes status accuracy, exact tool-sequence accuracy, citation-prefix coverage/precision, a keyword-based groundedness proxy, workflow completion over the five `workflow` cases only, clarification/escalation accuracy, and action-safety pass rate. Structured lookups and missing-record checks are scored in their own item results and are excluded from the workflow-completion denominator. This gives repeatable expected-answer checks for the listed synthetic cases; it does not prove open-ended semantic correctness. The proxy definitions and complete per-item outputs are in [`evaluation/results.md`](evaluation/results.md) and [`evaluation/results-stdio.md`](evaluation/results-stdio.md).

Both local transports scored 1.0 on deterministic status, groundedness-proxy, citation-prefix, exact-tool-sequence, workflow-completion (5/5 workflow cases), clarification/escalation, and action-safety metrics; mean keyword overlap was 0.95. The in-process run used a separate read-only priming request (6,005.88 ms), followed by a warm 15-task sample (p50 23.59 ms; p95 104.74 ms). Each stdio sample started a fresh MCP subprocess and includes process/model/index initialization; its priming request was 8,478.52 ms and the 15-task p50/p95 were 7,471.90/7,917.17 ms. These are local measurements; the stdio sample is not a Render host cold-start benchmark. Percentiles use nearest rank and are described with the reports.

The chunk ablation and retrieval-only comparison are recorded in [`evaluation/ablation-results.md`](evaluation/ablation-results.md) and [`evaluation/retrieval-comparison.md`](evaluation/retrieval-comparison.md). Their hand-labeled corpus is small, so results justify the local configuration choice only; they are not a general retrieval benchmark.
