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
- agent/llm.py optionally refines a controlled draft using an OpenAI-compatible endpoint.

## MCP transport behavior

The local default is in-process. It calls TOOL_REGISTRY functions directly and does not exercise MCP serialization or protocol negotiation. The stdio option launches mcp_server.server as a subprocess, discovers tools through the official MCP client, and exercises FastMCP over the protocol.

The retrieval comparison does not change MCP transport or dependencies.

## Retrieval and embeddings

Production uses sentence-transformers/all-MiniLM-L6-v2 at 384 dimensions and 120-word chunks with 20-word overlap. The chunk-size experiment found that 120/20, 160/24, and 220/30 yielded the same 126 chunks and measured retrieval quality on this corpus; 120/20 is the smallest of those tied settings. Details are in evaluation/ablation-results.md.

The follow-up comparison holds MiniLM and 120/20 fixed. At global k=5, current ranking retrieved all expected families for 2/5 multi-family queries; MMR at λ=0.5 reached 3/5 and raised family recall from 0.81 to 0.86. k=8 reached 3/5 with either current ranking or MMR. Doubling lexical weight did not improve coverage. Based on this comparison, production uses λ=0.5 MMR over a top-ten candidate pool and returns five results. For explicit multi-family intent it seeds one best result per family, then fills with MMR. The measured gain is modest and the labels are hand-authored.

The updated orchestrator route cited all expected families in 5/5 multi-family probes. The six-item read-only policy golden slice had 100% status, citation-prefix, and groundedness-proxy scores, with `huggingface_dense_cosine` observed. This small slice does not replace the unrun full evaluation. The complete query-level matrix and limits are in evaluation/retrieval-comparison.md.

Dense local embeddings use cosine similarity plus bounded lexical and title signals. Embedding configuration uses MSAIE_EMBEDDING_*; optional answer refinement uses MSAIE_LLM_*. Runtime retrieval traces identify the actual path, including huggingface_dense_cosine.

## Refiner fact contract

The chat composition passes the structured result status and internal structured facts to the refiner. Remote-work and PTO workflows attach values such as eligibility, requested days, rolling totals, and notice periods to AgentResult without adding them to the public response schema. Before accepting generated text, the provider checks required status cues, preserves all numeric tokens and known no-action disclaimers from the controlled draft, and rejects unsupported new numbers. Contradictions or omissions return the controlled draft and record a fallback status.

This is a deterministic consistency guard, not a semantic entailment check. Citation objects remain separate response metadata. Regression coverage was added at the provider and chat seams; it has not been run.

## Evaluation discipline

The retrieval comparison and six-case policy-only golden slice are current evidence for their stated scope. They do not reproduce the previously reported 0.84 full evaluation result. The full golden set contains workflow and action cases and remains unrun until authorized. See evaluation/failed-test-analysis.md for the exact boundary.
