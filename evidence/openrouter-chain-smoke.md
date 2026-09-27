# Local OpenRouter Runtime Evidence

**Verified:** 2026-09-27 01:57 UTC | **Environment:** local FastAPI, MCP stdio, synthetic data | **Request:** `Can E1001 work remotely overseas for 10 days?`

| Check | Result |
|---|---|
| Service readiness | `/health/ready` and `/health?deep=true` returned HTTP 200; eight MCP tools available |
| Retrieval | Hugging Face MiniLM 384d; service-local SQLite index with 14 policy documents and 182 chunks |
| MCP calls | `search_policy_documents` → `lookup_employee_profile` → `check_policy_compliance` |
| Response | HTTP 200; `provisionally_eligible`; five policy citations; `llm_refinement=completed` |
| Resolved model | `poolside/laguna-s-2.1:free` |

This single local synthetic request verifies the retrieval, real stdio MCP, and OpenRouter composition path for that request. It does not establish current provider availability or hosted behavior; see [`hosted-pto-smoke.md`](hosted-pto-smoke.md). No generated answer text or credential value is retained.
