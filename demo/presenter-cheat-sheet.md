# Quantic MSAIE Capstone: 1-Page Screen-Share Recording Speaker Cheat Sheet

#### Document Overview & Presenter Guidelines
This reference cheat sheet is designed for a solo presenter recording a **tight 8:00 to 9:00 minute** screen-share video demonstration of the Quantic Master of Science in AI Engineering (MSAIE) Capstone HR Agent. The delivery strictly maintains AST100 technical English, emphasizes exact architectural metrics, articulates live operational trace outputs on camera, and demonstrates full compliance with all Quantic rubric requirements.

##### Recording Execution Directives
* **Target Timing:** **8:30 minutes** (Strict limits: 7:00 minimum to 10:00 maximum).
* **Video & Audio Setup:** Presenter headshot camera must show facial view alongside physical Government ID during Section 1. Voiceover must be authoritative, precise, and direct.
* **Screen Workspace Layout:** Pre-arrange browser tabs in order of presentation flow:
  - **Tab 1:** Live Web UI (`https://project-hr-agent.onrender.com`)
  - **Tab 2:** GitHub Repo (`MSAIE2027/Project-HR-Agent`) displaying `README.md` & `SENIOR_AI_ARCHITECT_AUDIT_REPORT.md`
  - **Tab 3:** Live Readiness Endpoint (`https://project-hr-agent.onrender.com/health/ready`)
  - **Tab 4:** GitHub Actions CI (`.github/workflows/ci.yml`)
  - **Tab 5:** Evaluation Dashboard (`evaluation/results.md`, `evaluation/semantic-groundedness-study.md`, & `evaluation/live-latency-results.md`)

---

#### 1. Minute 0:00 - 1:00 | Section 1: Intro, Academic Disclosure & ID Verification (Slide 1)
* **Screen Tab Location:** Camera view (Full screen video with presenter holding physical Government ID), transitioning to Live Hosted Web App ([https://project-hr-agent.onrender.com](https://project-hr-agent.onrender.com)).

| Time / Visual Focus | Verbatim Presenter Script & Action Cues |
|:---|:---|
| **0:00 - 0:25**<br>**SCREEN:** Full Headshot Camera | **SPEAK:** "Hello, my name is **[Your Name]**, presenting my Capstone Project for the Quantic Master of Science in AI Engineering program: the **Quantic HR Agent Capstone**."<br><br>**ACTION:** *(Hold physical Government ID steadily up to the camera lens for exactly 5 seconds to satisfy grading identity verification rules).* |
| **0:25 - 1:00**<br>**SCREEN:** Live Web App<br>`https://project-hr-agent.onrender.com` | **SPEAK:** "Before demonstrating the live application, I declare the mandatory Academic Integrity and Synthetic Data Notice: All employee profiles from E1001 through E1005, leave balances, corporate policies, email drafts, and support tickets are entirely synthetic and fictional. The system operates with zero access to real production HRIS systems or personal identifiable information (PII)."<br><br>**SPEAK:** "This repository was engineered with AI assistant collaboration—specifically Anthropic Claude Code, OpenAI Codex, OpenCode Zen, and Google DeepMind Antigravity—under human architectural oversight." |

---

#### 2. Minute 1:00 - 2:15 | Section 2: System Architecture & MCP Tooling Integration (Slide 2)
* **Screen Tab Location:** GitHub Repository (`MSAIE2027/Project-HR-Agent`) displaying architecture diagram or browser chat tab metadata.

* **Direct Presenter Script:**
  **SPEAK:** "The architecture cleanly decouples agent orchestration from core domain logic through Anthropic's Model Context Protocol (MCP). All domain capabilities are exposed via 8 strongly typed FastMCP tools running over standard input/output (stdio) inter-process communication (IPC). During initialization, `agent/orchestrator.py` dynamically discovers tools via `tools/list` and executes them via `tools/call` using JSON-RPC over stdio IPC, proving zero hard-coded Python function shortcuts bypass protocol serialization."

* **Resilience Cascade Script:**
  **SPEAK:** "For final response synthesis, the system implements a 3-Tier LLM Provider Cascade: Tier 1 executes OpenRouter model rotation starting with Qwen 3.8 27B, Nemotron 3.5 Lightning, and Gemma 4 26B. Upon encountering HTTP 429 rate limits, Tier 2 triggers automatic failover to OpenCode Zen. Tier 3 provides a bounded SQLite template fallback restricted strictly to read-only workflows. Any unconfirmed state-changing action or unverified context strictly fails closed with an HTTP 503 status (`llm_unavailable`), while fully preserving retrieved policy citations and operational traces."

##### FastMCP Tool Schema Callouts
* `search_policy_documents(query, limit=4, document_prefix=None)`: Dense ONNX vector search over 182 chunks in SQLite.
* `get_policy_section(document_id, section=None)`: Exact passage retrieval by normalized document ID and section heading.
* `lookup_employee_profile(employee_id)`: Relational SQLite query returning synthetic tenure, jurisdiction, and rolling usage history.
* `check_pto_balance(employee_id, requested_days=0)`: Accrual calculation returning synthetic available leave, sufficiency, and post-approval balance.
* `lookup_benefits_status(employee_id)`: Synthetic benefits eligibility, plan enrollment status, and coverage details.
* `check_policy_compliance(workflow, employee_id, requested_days=0, destination=None)`: Validates statutory notice requirements, rolling limits, and mandatory approval hierarchies.
* `draft_hr_email(employee_id, purpose, requested_days=0, confirmed=False)`: Action-Gated Tool: Stages synthetic email draft locally (`sent: false`). Requires `confirmed: true`.
* `create_mock_hr_ticket(employee_id, category, summary, confirmed=False)`: Action-Gated Tool: Generates synthetic support ticket (`production_system: false`). Requires `confirmed: true`.

---

#### 3. Minute 2:15 - 3:30 | Section 3: Embedded Quantized RAG & Memory Optimization (Slide 3)
* **Screen Tab Location:** Live `/health/ready` HTTP endpoint JSON response ([https://project-hr-agent.onrender.com/health/ready](https://project-hr-agent.onrender.com/health/ready)) or `rag/index.py` source file.

* **Direct Presenter Script:**
  **SPEAK:** "To operate reliably within Render's 512 MB Free tier memory ceiling, the vector retrieval pipeline runs entirely in-process without external database dependencies. We ingested 14 enterprise policy documents—comprising 16,010 total words across Markdown and HTML—and segmented them into exactly 182 chunks using a heading-aware 120-word window with a 20-word overlap strategy."

* **Embedding Mechanics Script:**
  **SPEAK:** "While unquantized PyTorch embedding models consume ~536 MB RAM, compiling `sentence-transformers/all-MiniLM-L6-v2` to an INT8 ONNX export (`onnxruntime-quint8-avx2`) reduced peak RAM consumption during vector inference to ~71 MB. Embeddings are stored as 384-dimensional packed binary blobs in SQLite (`.data/rag_index.sqlite3`) and evaluated via dot-product cosine similarity locally on CPU."

* **Reranking & Retrieval Mathematics Script:**
  **SPEAK:** "In our standalone retrieval benchmarks, unfiltered dense retrieval across 182 chunks achieved 76% Family recall at k=5 with a 20% multi-family coverage due to intra-document clustering. Implementing Maximal Marginal Relevance (MMR, $\lambda = 0.5$) reranking over a top-10 candidate pool doubled multi-family coverage to 40% and raised recall to 0.81. Combining $\lambda = 0.5$ MMR with domain family routing achieves 100% multi-family coverage and 1.00 recall while maintaining sub-5 millisecond vector search latency."

---

#### 4. Minute 3:30 - 5:00 | Section 4: Live Agentic Task 1 – International Remote Work Eligibility (Slide 4)
* **Screen Tab Location:** Live Hosted Web Application Chat UI ([https://project-hr-agent.onrender.com](https://project-hr-agent.onrender.com)).
* **Presenter Visual Commands:**
  1. **ACTION:** Switch to Web UI Tab
  2. **ACTION:** Paste Prompt into Input Box
  3. **ACTION:** Click Submit and Expand Operational Trace Accordion

```text
[EXACT PROMPT INPUT]
Can E1001 work remotely overseas for 10 days?
```

##### MCP Stdio Transport Trace Sequence
```text
[User Prompt] ──> "Can E1001 work remotely overseas for 10 days?"
│
▼ [MCP Stdio Transport Trace (agent/orchestrator.py)]
├── 1. search_policy_documents(query="international remote work eligibility...", limit=5, document_prefix="POL-RW-")
│   └── Returns 5 grounded policy chunks from POL-RW-01
├── 2. lookup_employee_profile(employee_id="E1001")
│   └── Returns synthetic record: Jurisdiction US-CA, 14 rolling days already used
└── 3. check_policy_compliance(workflow="remote_work", employee_id="E1001", requested_days=10)
    └── Returns compliance object: status="provisionally_eligible", total_after_request=24, limit=20
```

* **Verbatim Spoken Verification Points:**
  * **SPEAK:** "Observe the live operational trace: The agent executes a 3-tool MCP sequence entirely over stdio IPC."
  * **SPEAK:** "Articulate on camera that employee E1001 has utilized 14 of 20 allowed rolling days under POL-RW-01."
  * **SPEAK:** "Point out that adding 10 requested days brings the total to 24 days, making the request provisionally eligible subject to statutory approvals."
  * **SPEAK:** "Crucially, point out on camera that the synthesized answer explicitly demarcates **Binding Policy Requirements** (statutory 20-day limit, 14 days already used) from **Advisory Recommendations** (tax review, manager discussion, security clearances) fulfilling Rubric Section 3."
  * **SPEAK:** "Highlight that the response explicitly cites POL-RW-01 section passages and warns that manager, HR, tax, information security, and immigration reviews remain outstanding before final travel authorization."

---

#### 5. Minute 5:00 - 6:45 | Section 5: Live Agentic Task 2 – PTO Guidance & 2-Phase Confirmation Gate (Slide 5)
* **Screen Tab Location:** Live Hosted Web Application Chat UI ([https://project-hr-agent.onrender.com](https://project-hr-agent.onrender.com)).

```text
====================================================================================================
MULTI-TURN CONVERSATION CONTAINER: SAFETY GATE TRANSITION
====================================================================================================
[TURN 1 PROMPT INPUT]
How much PTO does E1001 have and draft an email for 5 days?

[TURN 1 MCP STDIO TRACE EXECUTED]
├── search_policy_documents(query="paid time off balance eligibility...", limit=5, document_prefix="POL-PTO-")
├── lookup_employee_profile(employee_id="E1001")
├── check_pto_balance(employee_id="E1001", requested_days=5)
└── check_policy_compliance(workflow="pto", employee_id="E1001", requested_days=5)

[TURN 1 SAFETY GATE HALT STATE]
└── System Status: confirmation_required
    ├── [CRITICAL VERIFICATION] Execution HALTS strictly before calling draft_hr_email.
    └── Spoken Values: 14 available PTO days, 9 net days remaining post-approval. Zero side-effects.
----------------------------------------------------------------------------------------------------
[TURN 2 ACTION COMMAND]
Click the interactive "Confirm action" button (or send confirmation message).

[TURN 2 MCP STDIO TRACE EXECUTED]
└── draft_hr_email(employee_id="E1001", purpose="PTO request", requested_days=5, confirmed=True)

[TURN 2 UI VERIFICATION POINTS]
├── Staged Draft Displayed: Local email draft rendered in UI workspace with Action ID.
└── Safety Payload Flag: Sent status is explicitly flagged sent: false (no transmission occurs).
====================================================================================================
```

* **Direct Presenter Script:**
  * **SPEAK:** "During Turn 1, the orchestrator evaluates policy and employee balances, identifying 14 available PTO days and 9 remaining days if approved."
  * **SPEAK:** "Note that the response cleanly separates binding balance calculations from advisory email guidance."
  * **SPEAK:** "Crucially, observe the two-phase safety gate: Even though the user asked to draft an email, the agent transitions to status `confirmation_required` and halts strictly before executing `draft_hr_email`."
  * **SPEAK:** "On Turn 2, upon clicking 'Confirm action', the agent passes `confirmed=True` to `draft_hr_email`. Point out on camera that the generated payload contains the flag `sent: false`, proving that no actual external transmission occurred."
  * **SPEAK:** "Notice our fail-closed architectural invariant: If an upstream provider rate limits, action-gated workflows never forge an unconfirmed action; they preserve the retrieved citations, display the operational trace, and fail closed."

---

#### 6. Minute 6:45 - 7:45 | Section 6: CI/CD Pipeline & Course Grader Access Gate (Slide 6)
* **Screen Tab Location:** GitHub Actions Workflow tab (`.github/workflows/ci.yml`) and Repository Settings / Collaborator Access.

```text
====================================================================================================
CI/CD PREFLIGHT REQUIREMENTS & GRADATION ACCESS CHECKLIST
====================================================================================================
[✓] 118 Passing Automated Tests: Verifies pytest execution across Python 3.12 compilation,
    FastAPI routing, unit logic, out-of-scope threshold checks, and medical PII/disability refusal filters.
[✓] Automated MCP Discovery Test: Verifies CI job executing `python scripts/smoke_mcp.py`
    to test stdio FastMCP tool enumeration and protocol execution before build approval.
[✓] Dual Golden-Set Evaluation: Runs both in-process and fresh stdio subprocess evaluations in CI across 34 cases.
[✓] Course Grader Collaborator Invitation: Displays active GitHub collaborator invitation
[✓] Public Visibility Confirmed: Repository is confirmed public ('visibility': 'public')
    eliminating all grading access friction.
====================================================================================================
```

* **Direct Presenter Script:**
  **SPEAK:** "Every commit triggers our GitHub Actions CI pipeline. The workflow compiles Python 3.12 code, executes 118 automated unit and security tests, and runs `python scripts/smoke_mcp.py` to verify stdio FastMCP tool discovery. Furthermore, our master Senior AI Architect Audit Report (`SENIOR_AI_ARCHITECT_AUDIT_REPORT.md`) verifies 5/5 readiness across all 10 Quantic rubric criteria. The repository is confirmed public with collaborator invitation ID 335007413 issued to `quantic-grader`, guaranteeing immediate and unrestricted access for course evaluation faculty."

---

#### 7. Minute 7:45 - 8:30 | Section 7: Empirical Evaluation, Dual-Track Rigor & Wrap-up (Slide 7)
* **Screen Tab Location:** `evaluation/results.md` and `evaluation/semantic-groundedness-study.md` in GitHub Repository or Evaluation Dashboard.

##### Dual-Track Benchmark Scorecard
| Metric Category | Track 1: Deterministic CI Suite | Track 2: Semantic Groundedness Study | Target Metric | Status |
|:---|:---:|:---:|:---:|:---:|
| **Workflow Status Accuracy** | **100%** (34/34 cases) | **100%** (15/15 cases) | > 95% | **PASS** |
| **Exact Tool Sequence Accuracy** | **100%** (34/34 cases) | **100%** (15/15 cases) | > 95% | **PASS** |
| **Citation Precision / Coverage** | **100%** (34/34 cases) | **100%** (15/15 cases) | > 95% | **PASS** |
| **Factual Claim Groundedness** | **95.2%** (Keyword Proxy) | **92.5%** (Claim Entailment: 37/40) / **93.9%** (Mean Groundedness) | > 85% | **PASS** |
| **Complex Workflow Completion** | **100%** (5/5 cases) | **100%** (5/5 cases) | 100% | **PASS** |
| **Action Safety Pass Rate** | **100%** (0 bypasses) | **100%** (0 bypasses) | 100% | **PASS** |
| **Local Retrieval Latency (p50)** | **28.05 ms** (In-process RAG) | < 5 ms (Vector Search) | < 100 ms | **PASS** |
| **Live End-to-End Latency (p50/p95)** | N/A (Excluded in Track 1) | **Bimodal Route-Split** (Fast Lookups <100ms; Live LLM ~18s; Provider Timeout ~32s) | Rubric §9 Met | **PASS** |
| **Observed Host Cold-Start** | **33.466 s** (Single Sample) | 33–75 s (Typical Container Provisioning) | Disclosed Scope | **PASS** |

* **Presenter Script on Evaluation Rigor & Latency:**
  **SPEAK:** "To maintain academic evaluation rigor, we separate deterministic CI regression testing from semantic generation evaluation. Track 1 verifies tool sequencing, state transitions, and out-of-scope abstentions deterministically across 34 cases—including 4 realistic uncovered HR policy queries like RSUs and 401k matches gated by our 0.42 cosine threshold—achieving 100% pass with zero API spend. Track 2 evaluates 15 live LLM completions across 40 factual claims for claim-level entailment, achieving an honest 92.5% Claim Entailment Rate and 93.9% Mean Groundedness against source policy chunks, with reproducible validation via `python evaluation/run_semantic_eval.py`."
  
  **SPEAK:** "Regarding system latency, local in-process vector retrieval operates at a swift p50 of 28.05 ms. To satisfy Rubric Section 9 for end-to-end latency including answer generation, our live benchmarking over 15 representative tasks is fully instrumented in `evaluation/live-latency-results.md`. We explicitly disclose the bimodal nature of the architecture: deterministic Fast-Path lookups and safety refusals return in under 100 milliseconds, live LLM answer refinement completes in ~18 seconds, and upstream provider cascade timeouts fail closed in ~32 seconds without dropping citations. Finally, note on camera that the reported 33.466-second Render cold-start represents a single container wake-up observation sample following 15 minutes of inactivity—with typical host cold-starts ranging between 33 and 75 seconds—and is not a statistical p50 percentile."

```text
====================================================================================================
FINAL RECORDING WRAP-UP CHECKLIST
====================================================================================================
[ ] 1. Express formal gratitude to the Quantic evaluation faculty:
       "Thank you to the Quantic evaluation faculty for reviewing the Quantic HR Agent Capstone."
[ ] 2. Verify total recording duration is strictly between 8:00 and 9:00 minutes.
[ ] 3. Stop screen capture and camera recording.
[ ] 4. Upload recording and submit both video URL and GitHub repository URL to Quantic.
====================================================================================================
```
