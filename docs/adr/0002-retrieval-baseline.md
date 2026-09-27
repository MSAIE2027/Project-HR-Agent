# ADR 0002: Retain the Measured MiniLM Retrieval Baseline

- **Status:** Accepted
- **Date:** 2026-09-26

## Context

The project must retrieve policy evidence on modest resources and justify chunking, embedding, ranking, citations, and multi-document coverage. Changing several retrieval variables together would make the measured effect unclear.

## Decision

Keep `sentence-transformers/all-MiniLM-L6-v2` at 384 dimensions, 120-word chunks with 20-word overlap, existing score weights, a five-citation cap, and MMR λ=0.5 over up to ten candidates. For explicitly multi-family questions, retrieve up to three candidates per detected family, seed the strongest evidence per intended family, then fill remaining citation slots with MMR. Abstain when any intended family has no candidate over the existing 0.12 evidence threshold.

## Consequences

- On the expanded corpus at global k=5, λ=0.5 MMR increased multi-family all-family coverage from 1/5 to 2/5 and family recall from 0.76 to 0.81. The explicit family-routed application covered every expected family in all five labeled multi-family queries.
- The routed application covered every intended family in the five labeled multi-family probes; the route-specific result must not be conflated with global ranking results.
- 120/20 was the smallest of three chunk settings tied on this corpus; it is not a universal optimum.
- If hashing fallback is active, MMR keeps score order because the fallback vectors are not used for cosine diversity.

## Evidence

`evaluation/ablation-results.md`, `evaluation/retrieval-comparison.md`, `rag/index.py`, `agent/orchestrator.py`.
