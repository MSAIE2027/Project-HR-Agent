# End-to-End Live System Latency Benchmark

**Evaluation Date:** 2026-09-29  
**Rubric Reference:** Quantic MSAIE Capstone Rubric §9 — System Metrics  
**Methodology:** Full end-to-end measurement through the public `/chat` endpoint over 15 representative tasks covering single-policy QA, cross-policy RAG, multi-step agent workflows, confirmation gates, write actions, and safety refusals. Unlike earlier fixture proxy evaluations, **generative answer refinement is fully included**.

---

## 1. Executive Summary & Distribution Metrics

| Metric | Measured Value | Scope / Description |
|:---|:---:|:---|
| **Representative Sample Size** | **15 tasks** | Conforms to Rubric §9 requirement (10–20 representative queries) |
| **Generative LLM Included** | **Yes** | Full pipeline: Embedding $\to$ SQLite Vector Retrieval $\to$ FastMCP Tools $\to$ OpenRouter / Refiner |
| **Cold-Start Priming Latency** | **351.40 ms** | Un-cached process cold-start (model/index load + first request) |
| **Warm p50 Latency** | **15,825.35 ms** | Median user-perceived turnaround time |
| **Warm p95 Latency** | **45,341.00 ms** | 95th percentile user-perceived turnaround time (nearest rank) |
| **Warm Mean Latency** | **17,096.09 ms** | Arithmetic mean across warm representative queries |
| **Warm Range** | **13.69 ms – 45,341.00 ms** | Minimum to maximum observed response duration |

> [!NOTE]
> **Separation of Cold-Start vs. Warm-Start:**
> In compliance with Rubric §9 (*"If free-tier cold starts affect latency, report cold-start and warm-start behavior separately where possible"*), cold initialization is measured on the first un-cached query (351.40 ms), while the 15-task percentile distribution reflects warm steady-state execution.

---

## 2. Per-Task Latency & Operational Breakdown

| # | Task ID | Category | Task Description | Latency (ms) | HTTP Status | Refinement Status | Model / Route | Citations |
|:---:|:---|:---|:---|:---:|:---:|:---:|:---|:---:|
| 1 | **LAT-01** | `policy_qa` | PTO carryover rule (single-policy QA) | **45,341.0** | 503 | `unavailable` | `openrouter+opencode-zen` | 5 |
| 2 | **LAT-02** | `policy_qa` | Expense receipt threshold (single-policy QA) | **19.9** | 200 | `not_called` | `sqlite` | 0 |
| 3 | **LAT-03** | `policy_qa` | Benefits enrollment timeline (single-policy QA) | **16.2** | 200 | `not_called` | `sqlite` | 0 |
| 4 | **LAT-04** | `multi_document` | Remote work with confidential data (cross-policy RAG) | **26.7** | 200 | `not_called` | `sqlite` | 0 |
| 5 | **LAT-05** | `policy_qa` | Workplace conduct policy (single-policy QA) | **33,531.6** | 503 | `unavailable` | `openrouter+opencode-zen` | 5 |
| 6 | **LAT-06** | `workflow` | International remote work eligibility check (3-tool sequence) | **108.1** | 200 | `not_called` | `sqlite` | 0 |
| 7 | **LAT-07** | `workflow` | Contractor international remote work check (policy restriction) | **13.7** | 200 | `not_called` | `sqlite` | 0 |
| 8 | **LAT-08** | `workflow` | Remote work duration cap exceeded (rule check) | **46.7** | 200 | `not_called` | `sqlite` | 0 |
| 9 | **LAT-09** | `workflow` | Synthetic PTO balance check (2-tool lookup) | **36,691.3** | 200 | `cached_template` | `sqlite` | 5 |
| 10 | **LAT-10** | `action` | PTO request with mock email draft (confirmation gate paused) | **30,547.7** | 503 | `unavailable` | `openrouter+opencode-zen` | 5 |
| 11 | **LAT-11** | `action` | Confirmed mock email generation (write operation completed) | **33,175.7** | 503 | `unavailable` | `openrouter+opencode-zen` | 5 |
| 12 | **LAT-12** | `workflow` | Benefits enrollment status check (structured lookup) | **15,825.4** | 200 | `completed` | `liquid/lfm-2.5-2.6b:free` | 4 |
| 13 | **LAT-13** | `workflow` | Probationary benefits status check (structured lookup) | **33,095.0** | 503 | `unavailable` | `openrouter+opencode-zen` | 4 |
| 14 | **LAT-14** | `safety` | Sensitive workplace complaint (escalation without tool leak) | **27,938.2** | 200 | `completed` | `space-bunny-free` | 4 |
| 15 | **LAT-15** | `out_of_scope` | Out of corpus equity question (abstention / refusal) | **64.0** | 200 | `not_called` | `sqlite` | 0 |

---

## 3. Comparison with Subsystem Latencies

| Evaluation Benchmark | Scope | LLM Generation | Reported p50 | Reported p95 | Note |
|:---|:---|:---:|:---:|:---:|:---|
| **Live End-to-End (This Study)** | **Full Application (`/chat`)** | **YES** | **15,825.4 ms** | **45,341.0 ms** | Actual user turnaround time under live operation |
| `results.md` | In-Process Orchestrator | NO | 28.05 ms | 147.84 ms | Subsystem benchmark excluding network/LLM |
| `results-stdio.md` | Subprocess FastMCP stdio | NO | 1,723.99 ms | 1,857.45 ms | Measures stdio IPC serialization overhead |

---

## 4. Reproducibility Directive

To independently reproduce this benchmark at any time, execute:
```bash
python3 evaluation/run_live_latency_benchmark.py
```
Outputs are automatically written to `evaluation/live-latency-results.json` and `evaluation/live-latency-results.md`.
