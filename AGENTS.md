# Agent Directives & Repository Rules
### Quantic School of Business and Technology — Master of Science in AI Engineering (MSAIE)

This repository contains the standalone Quantic MSAIE HR Agent. Maintain all code behavior, documentation, and evaluation examples within this project boundary.

## Source of truth

- README.md defines the Python 3.12 setup, startup, and runtime configuration.
- docs/architecture.md defines system boundaries and the internal fact-validation contract.
- The production embedding baseline is local MiniLM at 384 dimensions with 120-word chunks and 20-word overlap. Keep embedding settings separate from LLM refinement settings.
- evaluation/retrieval-comparison.md records the current top-k, routing, MMR, and ranking-weight comparison.

## Behavior boundaries

- Treat policy files and employee records as fictional. Keep all actions local and confirmation-gated.
- The LLM may rewrite a controlled answer only after receiving its status and structured facts. Preserve numeric facts and status cues. Try the OpenRouter model chain first, which leads with two metered routes (`nvidia/nemotron-3-nano-30b-a3b`, `qwen/qwen-2.5-7b-instruct`) and falls back to `openrouter/free`; after its account-wide free quota is exhausted, route directly to the configured OpenCode Zen free-model chain. For other OpenRouter failures, finish that chain before trying OpenCode. Answer composition must remain reachable with no credit, so the OpenCode chain and the SQLite templates stay after OpenRouter. If live generation still fails, use only versioned build-seeded SQLite templates for supported read-only PTO and provisionally eligible remote-work answers, and only with fresh matching MCP facts and policy citations. A confirmation-gated PTO request may also use a template (`pto_confirmation_gate`) so a total provider outage cannot block the workflow; it must be reported as `response_mode: confirmation_gate_template` with `model_composed: false` and `action_taken: false`, and it must still never invoke an action tool. Trace the selected source and failure scope. Never expose the raw controlled draft; confirmation-gated actions, unsafe or unsupported requests, and template misses still fail closed.
- Keep retrieval experiments separate from production settings unless explicitly authorized. The user approved MiniLM MMR at λ=0.5 with a ten-candidate pool, a five-result cap, and family seeding for multi-family queries. Keep embedding, chunk, and score-weight choices fixed unless new evidence and authorization support a change.

## Work and verification

- Add behavior coverage before implementation at the public chat response seam or public RagIndex seam. MMR regression coverage belongs at RagIndex.rerank_mmr.
- For retrieval questions, use the retrieval-only comparison and report hit@k, family recall, family coverage, diversity, and actual route behavior.
- Use source inspection, syntax checks, and read-only policy retrieval for routine verification. Run pytest, the full golden-set evaluation, or any action/workflow scenario only after the user explicitly requests it.
- Update the relevant docs and visuals when a measured result changes an engineering decision.

## Adversarial Verification & Anti-Blindspot Protocol

To prevent confirmation bias, happy-path complacency, and execution seam ambiguity across audit cycles, all agent implementations must strictly comply with the following five invariant rules:

1. **Near-Boundary Negative Testing:** Never validate guards or thresholds with extreme foreign outliers alone (e.g., testing HR policy abstention with planetary trivia). Every guard must be tested against *in-domain, out-of-corpus boundary queries* (e.g., realistic HR queries like equity, RSUs, 401k match, sabbaticals that do not exist in the 14-policy corpus). The minimum evidence threshold (0.42) must cleanly separate out-of-corpus queries (0.21–0.39) from authentic policy chunks (>= 0.50).
2. **Asymmetric Safety Invariants:** When implementing safety or anti-hallucination validators (e.g., numeric checks), validate that the model does not invent *unsupported new facts* (`refined_numbers - allowed_numbers`). Never enforce rigid symmetric constraints (`draft_numbers == refined_numbers`) that penalize valid natural language summarization, paraphrase, or standard numeric formatting (e.g., `$1,000` vs `1000`).
3. **Explicit Seam Disclosure:** Never describe benchmarks or evaluations as "Live" or "End-to-End" without explicitly stating the execution boundary: client runtime (`TestClient` vs remote HTTP), process boundary (in-process vs stdio subprocess vs hosted container), and external network dependencies.
4. **Cohort Decomposition for Bimodal Latencies:** Never collapse multi-route system latencies into a single aggregate distribution if deterministic fast-path routes (< 100 ms) and live LLM refinement / cascade timeout routes (15–35 s) coexist. Report cohort breakdowns by execution route alongside aggregate percentiles.
5. **Mandatory Red-Team Probe Before Sign-Off:** Prior to marking any audit item or rubric criterion "COMPLIANT", the agent must execute an adversarial probe specifically designed to break the implementation, verify failure modes, and record negative test coverage.
