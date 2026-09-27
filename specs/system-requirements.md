# MSAIE HR Agent — System Requirements

**Status:** Baseline SRS for the standalone course project
**Source of graded requirements:** `AI ENGINEERING TECHNIQUES AND ARCHITECTURES project prompt.pdf` (provided with the project)
**Project boundary:** Fictional company, synthetic records, local mock actions; no production HR integrations.

## Purpose

Build, evaluate, and demonstrate an agentic HR support application that grounds policy answers in a small internal policy corpus and completes selected HR workflows through MCP tools and synthetic structured data.

## Users and primary workflows

- An employee asks a policy question and receives a concise, cited answer or a safe refusal/clarification.
- An employee checks a synthetic PTO balance or an international remote-work request; the system combines relevant policy evidence with structured records and states remaining approval requirements.
- An employee requests a mock email or HR ticket; the system pauses for explicit confirmation and never contacts an external system.
- A grader inspects the operational trace, evidence, status, errors, and runtime configuration through the UI and API.

## Functional requirements

| ID | Requirement | Acceptance condition |
|---|---|---|
| FR-01 | Ingest policy sources in at least two text formats. | Markdown and HTML sources produce indexed policy sections with document ID, title, section, path, and snippet metadata. |
| FR-02 | Build a reproducible, lightweight retrieval index. | The selected MiniLM 384-dimensional embedding baseline uses 120-word chunks and 20-word overlap, stored with metadata and complete chunk text in SQLite; health and a read-only document/chunk browser make index contents inspectable without exposing vector payloads. |
| FR-03 | Answer policy questions with evidence. | Responses contain citation IDs and snippets; requests without sufficient policy evidence abstain or redirect. |
| FR-16 | Generate every evidence-backed final response with OpenRouter. | Each citation-bearing `/chat` response passes the controlled draft, retrieved snippets, status, and structured facts to `https://openrouter.ai/api/v1`. The service tries the pinned Qwen, Nemotron Lightning, and Gemma free models in order, then `openrouter/free`; it returns only a validated answer and traces requested/resolved model and attempts. A different host/fallback, missing key, or total provider/validation failure returns HTTP 503 rather than unrefined retrieval text. |
| FR-04 | Cover cross-policy questions. | A multi-family question can retrieve and cite each intended family, or abstain when one family has no evidence above the configured threshold. |
| FR-05 | Orchestrate multi-step HR work. | The orchestrator selects and calls MCP tools for international remote-work and PTO workflows, including synthetic profile/balance data and compliance rules. |
| FR-06 | Provide MCP tools. | The MCP SDK server exposes at least five typed tools, including policy retrieval and structured/mock-action tools; the client discovers and calls tools. |
| FR-07 | Show operational traces. | The UI/API exposes tool names, arguments, results, citations, outcome status, safety decisions, and OpenRouter refinement status/model without hidden chain-of-thought. A truncated model completion is rejected. |
| FR-08 | Handle missing or unsafe requests. | Missing IDs/inputs request clarification; missing records and MCP failures are explicit; sensitive matters escalate; injection is refused before tool use; medical record/file requests and requests referring to multiple synthetic employees are refused before any employee lookup. Multiple employees are detected from the fixture roster as well as explicit IDs. |
| FR-09 | Gate write-like operations. | Email/ticket tools create fictional local records only after explicit confirmation; responses state that no external system was contacted. |
| FR-10 | Provide an inspectable web/API surface. | `/` serves the workspace and SQLite browser, `/chat` accepts requests and returns answer/evidence/trace, `/api/index/documents` and `/api/index/documents/{id}/chunks` expose safe index rows, and `/health` reports service, MCP, retrieval, and provider status. |
| FR-11 | Support local reproduction and hosting. | Python 3.12 setup, dependencies, local startup, health checks, environment configuration, and Render configuration are documented. |
| FR-12 | Evaluate quality, behavior, and system performance. | A 20–30 item golden set covers policy QA, cross-policy, workflows, actions, clarification, missing records, safety, and out-of-scope requests; metrics include groundedness/citation/tool/workflow/safety/latency and one ablation. |
| FR-13 | Automate checks before deployment. | GitHub Actions runs syntax/import checks, tests, MCP protocol coverage, and threshold-gated golden evaluations. Its optional tested-SHA Render deploy job depends on the complete test job; independent Render auto-deploy is disabled. |
| FR-14 | Provide demo materials. | Two end-to-end tasks have exact prompts, expected MCP sequence, evidence, status, and recording guidance. |
| FR-15 | Disclose AI tooling and limitations. | `ai-tooling.md` describes assistance; project documents distinguish small deterministic proxies from independent semantic judgments and deployment evidence. |

## Non-functional requirements

- **Privacy:** Use only fictional policies, identities, and records. Keep secrets in environment configuration and never include them in traces or committed files.
- **Safety:** No production actions, legal/medical/tax/immigration determinations, hidden reasoning disclosure, or unsupported policy claims.
- **Reproducibility:** Pin or constrain dependencies, keep retrieval settings documented, and provide one-command checks.
- **Free-tier fit:** Use a small corpus and local/lightweight storage; document index rebuild and cold-start implications.
- **Service lifecycle:** In stdio mode, reuse one official MCP process for the FastAPI app lifetime, serialize tool sequences, close it on shutdown, report failed operations as unavailable, and keep routine readiness probes independent of the session lock. Explicit deep health may rediscover MCP tools; a service restart restores a broken session. Verify hosted memory after the embedding model has loaded; process reuse alone does not prove fit within the service limit.
- **Usability/accessibility:** Responsive layout, semantic controls, keyboard operation, visible focus, live status updates, and readable citations/traces.
- **Observability:** Report active retrieval method, embedding model/dimensions, MCP transport/tool discovery, and answer-refinement status without exposing credentials.

## Out of scope

Real employee data, production HRIS access, sending email, creating real tickets, autonomous final approvals, legal or medical advice, model training/fine-tuning, and claims of regulatory-framework certification.

## Demo acceptance

1. International remote-work eligibility combines policy search, employee lookup, and compliance check, and preserves provisional approval language.
2. PTO balance/request combines PTO policy, employee/balance/compliance tools, then waits for confirmation before creating a mock email draft.
3. The presenter can show a prompt-injection refusal and an explicitly confirmed sensitive-case mock ticket as safety-boundary examples.
4. Each task can be reproduced from the workspace, with its MCP trace and citations visible.

See [`traceability-matrix.md`](../docs/traceability-matrix.md) for requirement-to-code and evidence mappings.

## Course delivery requirements

The official prompt also requires a shareable deployed application URL, a repository shared with the `quantic-grader` GitHub account, and a 7–10 minute narrated screen-share video that demonstrates two end-to-end tasks and covers MCP tool names, arguments, outputs, citations, design, deployment, CI/CD, and evaluation. All group members must speak, appear on camera, and show government ID if the submission is a group. Group submissions must follow the course's group-agreement instructions. These are release/submission requirements, not claims that the current local checkout has completed them.

The supplied course-material inventory and its relationship to the project are recorded in [`../docs/source-materials-review.md`](../docs/source-materials-review.md).
