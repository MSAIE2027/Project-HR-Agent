# AI Tooling & Academic Integrity Disclosure
### Quantic School of Business and Technology — Master of Science in AI Engineering (MSAIE)

> [!IMPORTANT]
> **Academic Demonstration & Synthetic Data Notice:**
> This project is an academic capstone developed for the **Quantic MSAIE** degree curriculum. All employee profiles, leave balances, corporate policies, and support workflows are synthetic and fictional. The system does not access production human resources information systems (HRIS) or real personal identifiable information (PII).

---

## 1. Scope of AI Assistant Collaboration

In accordance with Quantic's Academic Integrity Policy and disclosure guidelines, multiple AI engineering assistants supported the design, implementation, and verification of this capstone repository. The project owner maintains full intellectual ownership, architectural direction, and ultimate responsibility for all committed source code, documentation, and empirical claims.

| AI Assistant / System | Operational Role | Key Contribution Scope | Verification Method |
|:---|:---|:---|:---|
| **Anthropic Claude Code** | Implementation Assistant | Initial scaffolding, FASTApi routing, and MCP protocol integration. | Automated unit tests and human code review. |
| **OpenAI Codex** | Implementation & Refactoring | Traceability matrix, requirements cross-referencing, and initial documentation drafting. | Git commit review and requirements mapping. |
| **OpenCode Zen (`space-bunny-free`)** | Independent External Auditor | Read-only external audit on 2026-09-27 (`evidence/independent-audit-2026-09-27.md`), verifying live HTTP endpoints, CI logs, and evaluation proxies. | Recorded HTTP transcripts and command logs. |
| **Antigravity (Google DeepMind)** | Senior AI Engineering Architect & Validator | End-to-end technical, architectural, and rubric audit across all 10 Quantic Capstone criteria (2026-09-28). Diagnosed and implemented regex status validator refinement in `agent/llm.py`, verified 117/117 test suite in Python 3.12, validated live Render deployment, investigated GitHub API invitation status, audited HCD/WCAG 2.1 AA accessibility, and authored comprehensive audit reports. | Pytest suite, live automated smoke preflight, and GitHub REST API inspection. |

---

## 2. Engineering Evaluation: Effective Practices vs. Corrected Limitations

### 2.1 Practices That Proved Effective
- **Formal Interface Contracts:** Defining explicit JSON schemas for the Model Context Protocol (MCP) server over `stdio` IPC enabled modular, decoupled unit testing across client and server layers without external network dependencies.
- **Deterministic Evaluation Harness:** Authoring a 30-case golden benchmark covering workflows, policy lookups, and adversarial safety inputs provided repeatable, non-flaky regression gates for CI/CD.
- **Fail-Closed Two-Phase Confirmation:** Gating destructive or external side-effects (`draft_hr_email`, `create_mock_hr_ticket`) behind an explicit user confirmation turn prevented unauthorized autonomous agent actions.

### 2.2 Areas Requiring Human & Architectural Correction
- **Regex Status Validation Over-Rigidity:** Free-tier LLMs generated valid semantic synonyms (e.g., `"demonstration draft"`, `"confirmation is mandatory"`). The original validator expected narrow literal phrases, causing false-positive validation rejections (HTTP 503). Corrected by expanding `_STATUS_REQUIREMENTS` in `agent/llm.py` to recognize legitimate semantic variations while strictly preserving safety invariants.
- **Evaluation Proxy Candor:** Early automated metrics reported high groundedness scores. Technical review revealed that the evaluation harness uses lexical substring matching (`_keyword_score`) rather than an open-ended natural language inference (NLI) model. This proxy was explicitly documented in `evaluation/results.md` to maintain academic transparency.
- **Memory Optimization for Free-Tier Hosting:** Raw PyTorch inference for embeddings consumed ~536 MB RAM, leading to out-of-memory container terminations on Render's 512 MB Free tier. Corrected by compiling `all-MiniLM-L6-v2` to an INT8 ONNX export (`onnxruntime-quint8-avx2`), reducing peak RAM to ~71 MB and search latency to <5 ms.

---

## 3. Academic Integrity & Operational Boundaries

1. **No Real PII or Production Access:** All employee IDs (`E1001`–`E1005`), names, jurisdictions, and leave figures are deterministic synthetic fixtures defined in `mock_data/`.
2. **Deterministic Regression Tests vs. Live Generation:** The 30-case golden benchmark isolates orchestrator state transitions, tool dispatch, and citation synthesis deterministically (`llm_generation_included: false`) to ensure fast, zero-flakiness CI execution. Live multi-turn natural language generation is validated separately via unit tests (`tests/test_llm.py`) and live hosted smoke scripts (`scripts/smoke_hosted_demo.py`).
3. **Repository Access:** An official collaborator invitation (ID: `335007413`, `permissions: "write"`) was created for `quantic-grader` on 2026-09-28T04:58:00Z and is pending acceptance.

---

## 4. Academic References

1. Anthropic. (2024). *Model Context Protocol (MCP) Specification*. Anthropic, PBC. https://modelcontextprotocol.io
2. Carbonell, J., & Goldstein, J. (1998). The use of MMR, diversity-based reranking for reordering documents and producing summaries. In *Proceedings of the 21st Annual International ACM SIGIR Conference on Research and Development in Information Retrieval* (pp. 335–336). Association for Computing Machinery. https://doi.org/10.1145/290941.291025
3. National Institute of Standards and Technology. (2023). *Artificial Intelligence Risk Management Framework (AI RMF 1.0)* (NIST AI 100-1). U.S. Department of Commerce. https://doi.org/10.6028/NIST.AI.100-1
4. Nielsen, J. (1994). 10 usability heuristics for user interface design. *Nielsen Norman Group*. https://www.nngroup.com/articles/ten-usability-heuristics/
5. Wang, W., Wei, F., Dong, L., Bao, H., Yang, N., & Zhou, M. (2020). MiniLM: Deep self-attention distillation for task-agnostic compression of pre-trained transformers. In *Advances in Neural Information Processing Systems* (Vol. 33, pp. 5776–5788). Curran Associates, Inc.
6. World Wide Web Consortium. (2018). *Web Content Accessibility Guidelines (WCAG) 2.1* (W3C Recommendation). W3C. https://www.w3.org/TR/WCAG21/
