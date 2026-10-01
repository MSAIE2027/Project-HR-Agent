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
| FR-02 | Build a reproducible, lightweight retrieval index. | The selected MiniLM 384-dimensional embedding baseline uses the pinned Hugging Face revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` and its `onnx/model_quint8_avx2.onnx` CPU export through ONNX Runtime. It truncates tokenizer inputs at 256 tokens, uses 120-word chunks and 20-word overlap, stores complete chunk text plus backend/revision/token-limit metadata in SQLite, and rebuilds when any embedding setting changes. Health and a read-only document/chunk browser make index contents inspectable without exposing vector payloads; readiness rejects a sparse fallback or mismatched baseline. |
| FR-03 | Answer policy questions with evidence. | Responses contain citation IDs and snippets; requests without sufficient policy evidence abstain or redirect. |
| FR-16 | Generate evidence-backed final responses and preserve useful answers during provider outages. | Each citation-bearing `/chat` first passes the controlled draft, retrieved snippets, status, and structured facts to `https://openrouter.ai/api/v1`. Try the two metered routes `nvidia/nemotron-3-nano-30b-a3b` and `qwen/qwen-2.5-7b-instruct`, then the zero-priced `openrouter/free`. The metered tier leads because the account-wide free daily quota returns 429 before a completion exists; the project brief permits the owner's own API keys. A recognized account-wide daily quota 429 stops further OpenRouter attempts and routes directly to the configured OpenCode Zen free-model chain; other provider/model failures exhaust the OpenRouter chain before trying OpenCode. Both live providers must pass the same response validation and traces identify the provider/model attempts. If both live routes fail, only a versioned template seeded in the build-time SQLite database may format fresh facts and matching citations for supported read-only cases. A confirmation-gated PTO request may use the `pto_confirmation_gate` template, reported as `response_mode: confirmation_gate_template` with `model_composed: false`; the action boundary is unchanged and an action tool is never invoked. |
| FR-04 | Cover cross-policy questions. | A multi-family question can retrieve and cite each intended family, or abstain when one family has no evidence above the configured threshold. |
| FR-05 | Orchestrate multi-step HR work. | The orchestrator selects and calls MCP tools for international remote-work and PTO workflows, including synthetic profile/balance data and compliance rules. |
| FR-06 | Provide MCP tools. | The MCP SDK server exposes at least five typed tools, including policy retrieval and structured/mock-action tools; the client discovers and calls tools. |
| FR-07 | Show operational traces. | The UI/API exposes tool names, arguments, results, citations, outcome status, safety decisions, and live OpenRouter/OpenCode model attempts or an explicit SQLite template fallback without hidden chain-of-thought. A truncated model completion is rejected. |
| FR-08 | Handle missing or unsafe requests. | Missing IDs/inputs request clarification; missing records and MCP failures are explicit; sensitive matters escalate; injection is refused before tool use; medical record/file requests and requests referring to multiple synthetic employees are refused before any employee lookup. Multiple employees are detected from the fixture roster as well as explicit IDs. |
| FR-09 | Gate write-like operations. | Email/ticket tools create fictional local records only after explicit confirmation; responses state that no external system was contacted. |
| FR-10 | Provide an inspectable web/API surface. | `/` serves the workspace and SQLite browser, `/chat` accepts requests and returns answer/evidence/trace, `/api/index/documents` and `/api/index/documents/{id}/chunks` expose safe index rows and build-seeded response-template metadata, and `/health` reports service, MCP, retrieval, and provider status. |
| FR-11 | Support local reproduction and hosting. | Python 3.12 setup, dependencies, local startup, health checks, environment configuration, and Render configuration are documented. |
| FR-12 | Evaluate quality, behavior, and system performance. | A 20–30 item golden set covers policy QA, cross-policy, workflows, actions, clarification, missing records, safety, and out-of-scope requests; metrics include groundedness/citation/tool/workflow/safety/latency and one ablation. |
| FR-13 | Automate checks before deployment. | GitHub Actions runs syntax/import checks, tests, MCP protocol coverage, and threshold-gated golden evaluations. Its optional tested-SHA Render deploy job depends on the complete test job; independent Render auto-deploy is disabled. |
| FR-14 | Provide demo materials. | Two end-to-end tasks have exact prompts, expected MCP sequence, evidence, status, and recording guidance. |
| FR-15 | Disclose AI tooling and limitations. | `ai-tooling.md` describes assistance; project documents distinguish small deterministic proxies from independent semantic judgments and deployment evidence. |

## Non-functional requirements

- **Privacy:** Use only fictional policies, identities, and records. Keep secrets in environment configuration and never include them in traces or committed files.
- **Authentication boundary:** Authentication and employee-role authorization are not implemented. The public app is a synthetic-data demonstration; an employee ID selects a fixture and does not prove authorization. Do not enter real HR information or describe the app as production self-service.
- **Safety:** No production actions, legal/medical/tax/immigration determinations, hidden reasoning disclosure, or unsupported policy claims.
- **Reproducibility:** Pin or constrain dependencies, keep retrieval settings documented, and provide one-command checks.
- **Free-tier fit:** Use a small corpus, local SQLite storage, and quantized CPU inference; document index rebuild and cold-start implications. Verify hosted memory after a clean deployment; local measurements do not establish Render capacity.
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
