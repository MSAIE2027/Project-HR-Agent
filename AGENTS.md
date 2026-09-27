# Project agent instructions

This is the standalone MSAIE HR Agent. Keep product behavior, documentation, and examples within this project.

## Source of truth

- README.md defines the Python 3.12 setup, startup, and runtime configuration.
- docs/architecture.md defines system boundaries and the internal fact-validation contract.
- The production embedding baseline is local MiniLM at 384 dimensions with 120-word chunks and 20-word overlap. Keep embedding settings separate from LLM refinement settings.
- evaluation/retrieval-comparison.md records the current top-k, routing, MMR, and ranking-weight comparison.

## Behavior boundaries

- Treat policy files and employee records as fictional. Keep all actions local and confirmation-gated.
- The LLM may rewrite a controlled answer only after receiving its status and structured facts. Preserve numeric facts and status cues. If OpenRouter is unavailable or answer validation fails, return HTTP 503; never expose an unrefined draft for a citation-bearing response.
- Keep retrieval experiments separate from production settings unless explicitly authorized. The user approved MiniLM MMR at λ=0.5 with a ten-candidate pool, a five-result cap, and family seeding for multi-family queries. Keep embedding, chunk, and score-weight choices fixed unless new evidence and authorization support a change.

## Work and verification

- Add behavior coverage before implementation at the public chat response seam or public RagIndex seam. MMR regression coverage belongs at RagIndex.rerank_mmr.
- For retrieval questions, use the retrieval-only comparison and report hit@k, family recall, family coverage, diversity, and actual route behavior.
- Use source inspection, syntax checks, and read-only policy retrieval for routine verification. Run pytest, the full golden-set evaluation, or any action/workflow scenario only after the user explicitly requests it.
- Update the relevant docs and visuals when a measured result changes an engineering decision.
