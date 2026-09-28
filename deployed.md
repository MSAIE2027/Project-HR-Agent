# Deployment Status & Production Architecture
### Quantic School of Business and Technology — Master of Science in AI Engineering (MSAIE)

> [!IMPORTANT]
> **Academic Demonstration & Synthetic Data Notice:**
> This hosted web service is an academic capstone demonstration deployed on Render for the **Quantic MSAIE** degree curriculum. All employee profiles, leave balances, corporate policies, and support workflows are synthetic and fictional. The service does not access production human resources information systems (HRIS) or real personal identifiable information (PII).

---

## 1. Live Deployment Metadata

| Configuration Property | Runtime Specification | Verification Source |
|:---|:---|:---|
| **Public Web Service** | [https://project-hr-agent.onrender.com](https://project-hr-agent.onrender.com) | Live HTTP/2 gateway |
| **Readiness Probe** | [https://project-hr-agent.onrender.com/health/ready](https://project-hr-agent.onrender.com/health/ready) | Application health check |
| **Deep Health Probe** | [https://project-hr-agent.onrender.com/health?deep=true](https://project-hr-agent.onrender.com/health?deep=true) | Full MCP & index inspection |
| **Compute Environment** | Render Free Web Service (`plan: free`, 512 MB RAM, 1 CPU) | Render service metadata |
| **Service Identifier** | `Project-HR-Agent` (Render Workspace: `MSAIE2027`) | `render.yaml` specification |
| **Repository Remote** | [https://github.com/MSAIE2027/Project-HR-Agent](https://github.com/MSAIE2027/Project-HR-Agent) | GitHub Git remote (`main`) |
| **Release CI/CD Gate** | Automated deploy hook gated on 117-test passing CI (`RENDER_DEPLOY_ENABLED=true`) | `.github/workflows/ci.yml` |

---

## 2. Live Verification Matrix

The deployed service at `https://project-hr-agent.onrender.com` has been empirically verified across all functional, security, and protocol requirements:

| Verification Target | Expected Behavioral Outcome | Live Verified Result | Status |
|:---|:---|:---|:---:|
| **Readiness Probe (`GET /health/ready`)** | HTTP 200; 8 FastMCP tools over `stdio`; 182-chunk INT8 ONNX MiniLM index ready. | HTTP 200; 8 tools enumerated; pinned ONNX index ready (`sentence-transformers/all-MiniLM-L6-v2`, 384d, 120w/20w). | **PASS** |
| **Medical PII Refusal (`POST /chat`)** | HTTP 200 `status: refused`; zero MCP tool calls; zero external provider calls. | HTTP 200 `refused`; instant rejection; zero tool or LLM trace events. | **PASS** |
| **Multi-Employee Privacy (`POST /chat`)** | HTTP 200 `status: refused`; zero tool calls; zero external provider calls. | HTTP 200 `refused`; batch inspection rejected; zero trace events. | **PASS** |
| **Agentic Task 1: Remote Work (`POST /chat`)** | HTTP 200 `provisionally_eligible`; 5 citations from `POL-RW-01`; full 3-tool MCP sequence. | HTTP 200 `provisionally_eligible`; executed `search_policy_documents` → `lookup_employee_profile` → `check_policy_compliance`; completed LLM refinement. | **PASS** |
| **Agentic Task 2: PTO Guidance (`POST /chat`)** | HTTP 200 `confirmation_required`; 5 citations from `POL-PTO-01`; 4-tool MCP sequence. | HTTP 200 `confirmation_required`; executed `search_policy_documents` → `lookup_employee_profile` → `check_pto_balance` → `check_policy_compliance`. | **PASS** |
| **Action Safety Confirmation Gate** | Halts strictly before invoking `draft_hr_email`; draft withheld until confirmed turn. | Verified: `confirmation_gate` recorded in trace; zero unauthorized email creation. | **PASS** |

---

## 3. Resilience & Provider Cascade Architecture

To ensure high availability during third-party API rate limits, the hosted service implements a three-tier provider cascade:

```
[ User Request ] ──> [ Deterministic MCP Orchestrator ] ──> [ Structured Facts + Citations ]
                                                                       │
                       ┌───────────────────────────────────────────────┴──────────────────────────────────────────────┐
                       ▼                                               ▼                                               ▼
             [ Tier 1: OpenRouter ]                         [ Tier 2: OpenCode Zen ]                        [ Tier 3: SQLite Cache ]
             - Free model rotation                          - Failover on HTTP 429 quota                    - Bounded formatting templates
             - Verified citations & status                  - Same validation rules                         - Supported read-only workflows only
```

- **Fail-Closed Security Invariant:** Action-gated workflows (such as email drafting or ticket creation) and unverified query contexts never fall back to cached templates and strictly fail closed (`status: llm_unavailable`, HTTP 503).

---

## 4. Compute Constraints & Hosting Lifecycle

- **Memory Optimization:** Container RAM is bounded by running vector inference through an INT8-quantized CPU ONNX runtime (`onnxruntime-quint8-avx2`). Initial startup memory samples at ~71 MB, settling at ~275 MB under query load, operating safely within Render's 512 MB ceiling.
- **Cold-Start Latency:** Render Free web services spin down after 15 minutes of inactivity. Initial wake-up from an idle state requires approximately 33 to 75 seconds for container provisioning and SQLite index verification. Warm responses complete in under 50 ms for local retrieval and 15–20 seconds for multi-model LLM refinement.

---

## 5. Course Grader Access Gate

- **Repository Permissions:** The repository is private (`MSAIE2027/Project-HR-Agent`).
- **Collaborator Invitation:** Official GitHub collaborator invitation ID `335007413` with `write` permissions was generated for `quantic-grader` on `2026-09-28T04:58:00Z` and is active (`expired: false`).
- **API Technical Detail:** The GitHub REST API endpoint `/repos/{owner}/{repo}/collaborators/{username}` reports `{"permission": "none"}` until the recipient accepts the invitation.
- **Submission Recommendation:** To avoid grading delays or authentication friction, repository visibility should be toggled to **Public** (`Settings -> Change repository visibility -> Make public`) immediately prior to capstone submission on the Quantic dashboard.
