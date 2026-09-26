# MSAIE HR Agent Baseline Audit

This note describes the standalone working copy and separates source inspection from current retrieval evidence.

## What is present

- FastAPI application and responsive employee workspace.
- Explicit request orchestrator with safety checks and confirmation-gated synthetic actions.
- Eight HR tools registered on the MCP SDK FastMCP server, with an official MCP client for stdio mode.
- Local in-process tool calls for development.
- Markdown/HTML policy ingestion, SQLite vector storage, MiniLM dense cosine ranking, and a hashing fallback.
- Optional OpenAI-compatible answer refinement with a structured status/numeric consistency guard.
- Synthetic employee, PTO, benefits, office, and ticket data.

## Current engineering baseline

- Python 3.12 local environment; see README.md for setup and startup.
- MiniLM 384d embeddings with 120/20 word/overlap chunks.
- Production uses MMR λ=0.5 on the score-ranked top ten, returns five results, and seeds one candidate per explicitly routed family for multi-family requests. Embedding, chunk size, and score weights remain fixed.
- Latest comparison covers top-k, actual read-only route selection, MMR, and score weights. See evaluation/retrieval-comparison.md and visuals/retrieval-comparison.svg.

## Verification boundary

The 15-query read-only route comparison cited all expected families, including all five multi-family cases. The six-case read-only golden policy slice scored 100% on status, citation-prefix, and groundedness proxies; runtime reported huggingface_dense_cosine. The full 0.84 evaluation was not reproduced because the full golden set includes workflow/action cases. Pytest, action/transaction scenarios, and deployment remain unrun.
