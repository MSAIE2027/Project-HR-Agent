# Source Materials Review

This inventory records which supplied materials informed the project and how they connect to its requirements and design. The official project prompt is the grading authority. The course summaries, agent-building guide, and blueprint image provide design context; they do not override the prompt or establish a grading score.

| Supplied source | Reviewed concepts | Connection to this project |
|---|---|---|
| `AI ENGINEERING TECHNIQUES AND ARCHITECTURES project prompt.pdf` (Quantic, 8 pages) | Required HR RAG corpus, mock data, multi-step agent workflows, MCP tools, web/API, deployment, CI/CD, evaluation, design documentation, AI-tool disclosure, repository and video submission. | Primary source for [`../specs/system-requirements.md`](../specs/system-requirements.md), [`traceability-matrix.md`](traceability-matrix.md), demo acceptance, and external delivery tickets. It requires a deployed shareable URL and a 7–10 minute narrated demonstration of two tasks. |
| `AI-Agents-summary.pdf` (Quantic, 2025, 6 pages) | Agent layers, orchestration, tool use and MCP discovery, single/multi-agent trade-offs, context management, guardrails, evaluation, and injection risk. | Informs the bounded single-orchestrator choice in [ADR 0001](adr/0001-controlled-orchestration.md), [ADR 0003](adr/0003-mcp-transport.md), and [ADR 0004](adr/0004-synthetic-data-and-action-boundary.md). |
| `a-practical-guide-to-building-agents.pdf` (OpenAI, 34 pages; sections on agent components, orchestration, and guardrails) | Model/tool/instruction separation, incremental single-agent systems, run boundaries, layered safeguards, privacy, and tool-risk checks. | Supports starting with a small, inspectable workflow design and layered safety controls. The project deliberately keeps tool sequencing in deterministic orchestration instead of an open-ended LLM tool loop; this improves repeatability but makes phrase-based routing a known limitation. |
| `LLM-Based-Apps-Summary.pdf` (Quantic, 2024, 2 pages) | RAG components and the document-loader → chunk → embed → store pipeline; stack choices by performance, cost, and operating constraints. | Informs the RAG flow and resource trade-offs documented in [ADR 0002](adr/0002-retrieval-baseline.md) and [architecture](architecture.md). |
| `Prompt-Engineering-Course-Summary.pdf` (Quantic, 2023, 4 pages) | Prompt task/instruction/context, hallucination and citation limitations, prompt hacking, and token limits. | Informs evidence-first controlled drafts, injection refusal, refiner validation, and the explicit limitation that fixture checks do not prove semantic entailment. |
| `Adopting-AI-in-Your-Organization-Course-Summary (1).pdf` (Quantic, 2024, 5 pages) | RAG and chunking, task-specific evaluation, data privacy, least privilege, prompt injection, and organizational risk categories. | Informs synthetic-only data, confirmation-gated mock actions, the task-specific golden set, and the privacy boundary in [ADR 0004](adr/0004-synthetic-data-and-action-boundary.md). |
| `blueprint for building hr agentic system.jpg` (project-supplied diagram) | Quality metrics (groundedness, citations, match rate), behavior metrics (tool choice, workflow, safety pass), and system metrics (latency, cold start, ablation). | Used as an evaluation coverage checklist in the [SRS](../specs/system-requirements.md), [traceability matrix](traceability-matrix.md), and [evidence index](../evidence/index.md). Local latency and fixture proxies are reported separately from hosted memory samples; the first ONNX-backed query stayed live, and one hosted Free wake-to-ready sample took 33.466 seconds; a representative latency distribution has not been established. |

## Source-to-artifact path

1. The official project prompt defines acceptance requirements; the SRS states those requirements in testable terms.
2. The traceability matrix maps each requirement to code and evidence, including requirements that remain external.
3. The supplemental course materials inform design rationale recorded in the ADRs and architecture documentation.
4. Tickets and TDD slices track implementation and verification against those requirements.
5. The code review, evidence index, and demo runbook record review status, local proof, limits, and presenter steps.

## Important scope limits

- No weighted instructor score is inferred from the prompt's qualitative rubric.
- The project uses deterministic tool sequencing with required OpenRouter final-answer generation, not an LLM-selected tool loop. Tool choice, confirmation, and policy checks are visible and reproducible, but intent routing can miss paraphrases.
- Golden-set groundedness and citation measures are deterministic rubric proxies. They are not independent human entailment judgments.
- The supplied PDFs and image remain in the user's course materials folder; this repository records their titles and use without copying those source files into the project.
