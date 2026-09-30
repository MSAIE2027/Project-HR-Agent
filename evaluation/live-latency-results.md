# End-to-End LLM Refinement & Pipeline Latency Benchmark

**Evaluation Date:** 2026-09-29  
**Target Environment:** `Local FastAPI Engine (TestClient) + Remote Live OpenRouter API`  
**Rubric Reference:** Quantic MSAIE Capstone Rubric §9 — System Metrics  
**Methodology:** Full end-to-end measurement through the public `/chat` endpoint over 15 representative tasks covering single-policy QA, cross-policy RAG, multi-step agent workflows, confirmation gates, write actions, and safety refusals. Unlike earlier fixture proxy evaluations, **generative answer refinement is fully included**.

---

## 1. Executive Summary & Distribution Metrics

| Metric | Measured Value | Scope / Description |
|:---|:---:|:---|
| **Representative Sample Size** | **15 tasks** | Conforms to Rubric §9 requirement (10–20 representative queries) |
| **Execution Environment** | **Local FastAPI Engine (TestClient) + Remote Live OpenRouter API** | Disclosed runtime environment (local engine + live remote provider) |
| **Generative LLM Included** | **Yes** | Full pipeline: Embedding $\to$ SQLite Vector Retrieval $\to$ FastMCP Tools $\to$ OpenRouter / Refiner |
| **Cold-Start Priming Latency** | **30,638.79 ms** | Initial process cold-start (model/index load + first request) |
| **Warm p50 Latency (Overall)** | **23,115.75 ms** | Median user-perceived turnaround time across all tasks |
| **Warm p95 Latency (Overall)** | **45,421.44 ms** | 95th percentile user-perceived turnaround time (nearest rank) |
| **Warm Mean Latency (Overall)** | **25,675.14 ms** | Arithmetic mean across warm representative queries |
| **Warm Range** | **78.00 ms – 45,421.44 ms** | Minimum to maximum observed response duration |

> [!NOTE]
> **Separation of Cold-Start vs. Warm-Start:**
> In compliance with Rubric §9 (*"If free-tier cold starts affect latency, report cold-start and warm-start behavior separately where possible"*), cold initialization is measured on the first un-cached query (30,638.79 ms), while the 15-task percentile distribution reflects warm steady-state execution. Distinctly, Render cloud container wake-ups require ~33–75 seconds after 15 minutes of inactivity.

---

## 1.1 Bimodal Latency Distribution Analysis (Route Breakdown)

The latency distribution across 15 representative tasks is structurally bimodal due to the architectural separation between deterministic policy routes and external generative LLM synthesis:

| Execution Route | Task Count | p50 Latency | Mean Latency | Latency Range | Architectural Behavior |
|:---|:---:|:---:|:---:|:---:|:---|
| **Fast-Path / Deterministic Refusals** | **1** | **78.0 ms** | **78.0 ms** | 78.0 – 78.0 ms | Resolved via deterministic policy checks or input validation without external LLM calls. |
| **Live LLM Refinement Completed** | **9** | **19,856.6 ms** | **23,360.3 ms** | 15,177.6 – 43,257.0 ms | Successfully generated and validated through live upstream LLM models (e.g. Liquid LFM, OpenCode Zen). |
| **Cached Template Fallback** | **1** | **32,971.3 ms** | **32,971.3 ms** | 32,971.3 – 32,971.3 ms | Cascaded through model attempts, timed out / rate-limited, and fell back to SQLite response template. |
| **Cascade Exhaustion (Fail-Closed)** | **4** | **32,857.2 ms** | **35,458.8 ms** | 30,641.9 – 45,421.4 ms | Action-gated workflows where upstream rate limits triggered fail-closed HTTP 503 while preserving citations. |

---

## 2. Per-Task Latency & Operational Breakdown

| # | Task ID | Category | Task Description | Latency (ms) | HTTP Status | Refinement Status | Model / Route | Citations |
|:---:|:---|:---|:---|:---:|:---:|:---:|:---|:---:|
| 1 | **LAT-01** | `policy_qa` | PTO carryover rule (single-policy QA) | **30,641.9** | 503 | `unavailable` | `openrouter+opencode-zen` | 5 |
| 2 | **LAT-02** | `policy_qa` | Expense receipt threshold (single-policy QA) | **32,914.6** | 503 | `unavailable` | `openrouter+opencode-zen` | 5 |
| 3 | **LAT-03** | `policy_qa` | Benefits enrollment timeline (single-policy QA) | **18,501.9** | 200 | `completed` | `nvidia/nemotron-3.5-content-safety:free` | 5 |
| 4 | **LAT-04** | `multi_document` | Remote work with confidential data (cross-policy RAG) | **19,856.6** | 200 | `completed` | `nvidia/nemotron-3-super-120b-a12b:free` | 5 |
| 5 | **LAT-05** | `policy_qa` | Workplace conduct policy (single-policy QA) | **18,697.9** | 200 | `completed` | `inclusionai/ling-3.0-flash-sante:free` | 4 |
| 6 | **LAT-06** | `workflow` | International remote work eligibility check (3-tool sequence) | **32,971.3** | 200 | `cached_template` | `sqlite` | 5 |
| 7 | **LAT-07** | `workflow` | Contractor international remote work check (policy restriction) | **32,857.2** | 503 | `unavailable` | `openrouter+opencode-zen` | 5 |
| 8 | **LAT-08** | `workflow` | Remote work duration cap exceeded (rule check) | **32,006.7** | 200 | `completed` | `inclusionai/ling-3.0-flash-sante:free` | 5 |
| 9 | **LAT-09** | `workflow` | Synthetic PTO balance check (2-tool lookup) | **43,257.0** | 200 | `completed` | `space-bunny-free` | 5 |
| 10 | **LAT-10** | `action` | PTO request with mock email draft (confirmation gate paused) | **15,177.6** | 200 | `completed` | `poolside/laguna-s-2.1:free` | 5 |
| 11 | **LAT-11** | `action` | Confirmed mock email generation (write operation completed) | **45,421.4** | 503 | `unavailable` | `openrouter+opencode-zen` | 5 |
| 12 | **LAT-12** | `workflow` | Benefits enrollment status check (structured lookup) | **23,115.8** | 200 | `completed` | `nvidia/nemotron-3-ultra-550b-a55b:free` | 4 |
| 13 | **LAT-13** | `workflow` | Probationary benefits status check (structured lookup) | **18,435.4** | 200 | `completed` | `inclusionai/ling-3.0-flash-sante:free` | 4 |
| 14 | **LAT-14** | `safety` | Sensitive workplace complaint (escalation without tool leak) | **21,194.0** | 200 | `completed` | `space-bunny-free` | 4 |
| 15 | **LAT-15** | `out_of_scope` | Out of corpus equity question (abstention / refusal) | **78.0** | 200 | `not_called` | `sqlite` | 0 |

---

## 3. Comparison with Subsystem Latencies

| Evaluation Benchmark | Scope | LLM Generation | Reported p50 | Reported p95 | Note |
|:---|:---|:---:|:---:|:---:|:---|
| **Live End-to-End (This Study)** | **Full Application (`/chat`)** | **YES** | **23,115.8 ms** | **45,421.4 ms** | Actual user turnaround time under live operation |
| `results.md` | In-Process Orchestrator | NO | 28.05 ms | 147.84 ms | Subsystem benchmark excluding network/LLM |
| `results-stdio.md` | Subprocess FastMCP stdio | NO | 1,723.99 ms | 1,857.45 ms | Measures stdio IPC serialization overhead |

---

## 4. Reproducibility Directive

To independently reproduce this benchmark at any time, execute:
```bash
python3 evaluation/run_live_latency_benchmark.py
```
To run against a deployed cloud instance, specify:
```bash
python3 evaluation/run_live_latency_benchmark.py --base-url https://project-hr-agent.onrender.com
```
Outputs are automatically written to `evaluation/live-latency-results.json` and `evaluation/live-latency-results.md`.
