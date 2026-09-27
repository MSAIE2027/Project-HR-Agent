# MSAIE Golden-Set Evaluation

Transport: `stdio`

## Summary

| Metric | Result |
|---|---:|
| OpenRouter answer generation included | No; orchestrator-level evaluation |
| Items | 25 |
| Groundedness Proxy | 1.0 |
| Citation Prefix Accuracy | 1.0 |
| Exact Tool Sequence Accuracy | 1.0 |
| Workflow Case Count | 5 |
| Workflow Completion Rate | 1.0 |
| Clarification Escalation Accuracy | 1.0 |
| Action Safety Pass Rate | 1.0 |
| Status Accuracy | 1.0 |
| Mean Keyword Score | 0.94 |
| Latency Sample Count | 15 |
| Latency Ms Priming Request | 9659.28 |
| Latency Ms P50 | 8645.27 |
| Latency Ms P95 | 11180.99 |

Deterministic rubric-based proxy evaluation. Groundedness is not an independent semantic entailment judgment; citation accuracy requires all expected document families; tool accuracy requires the exact MCP call sequence. Workflow completion uses only workflow-category cases; structured lookups and missing-record checks are excluded. This harness calls the orchestrator directly and does not exercise OpenRouter response generation; public API tests cover that seam with a fake provider, and live provider output is checked during the configured demo.

Each sampled task opens a fresh local MCP stdio subprocess; its latency includes process and embedding/index initialization. The separate read-only priming request is reported but does not warm later subprocesses. These are not hosted Render cold-start measurements and exclude OpenRouter answer-generation latency. P50 and p95 use nearest rank; with 15 samples, p95 is the maximum observed task latency.

## Item results

| ID | Category | Status | Exact tools | Citations | Latency sample | Latency ms |
|---|---|---|---|---|---|---:|
| POL-01 | policy_qa | PASS: completed | search_policy_documents | POL-PTO-01, POL-PTO-01, POL-PTO-01, POL-PTO-01, POL-PTO-01 | yes | 8690.06 |
| POL-02 | policy_qa | PASS: completed | search_policy_documents | POL-EXP-01, POL-EXP-01, POL-EXP-01, POL-EXP-01, POL-EXP-01 | yes | 8498.92 |
| POL-03 | policy_qa | PASS: completed | search_policy_documents | POL-BEN-01, POL-BEN-01, POL-BEN-01, POL-BEN-01, POL-BEN-01 | yes | 8631.18 |
| POL-04 | multi_document | PASS: completed | search_policy_documents, search_policy_documents | POL-SEC-01, POL-RW-01, POL-SEC-01, POL-RW-01, POL-RW-01 | yes | 8645.27 |
| RW-01 | workflow | PASS: provisionally_eligible | search_policy_documents, lookup_employee_profile, check_policy_compliance | POL-RW-01, POL-RW-01, POL-RW-01, POL-RW-01, POL-RW-01 | yes | 8514.25 |
| RW-02 | workflow | PASS: not_eligible | search_policy_documents, lookup_employee_profile, check_policy_compliance | POL-RW-01, POL-RW-01, POL-RW-01, POL-RW-01, POL-RW-01 | yes | 8568.03 |
| RW-03 | workflow | PASS: not_eligible | search_policy_documents, lookup_employee_profile, check_policy_compliance | POL-RW-01, POL-RW-01, POL-RW-01, POL-RW-01, POL-RW-01 | no | 8505.53 |
| RW-04 | clarification | PASS: clarification_required | search_policy_documents | POL-RW-01, POL-RW-01, POL-RW-01, POL-RW-01, POL-RW-01 | yes | 8643.87 |
| RW-05 | missing_record | PASS: not_found | search_policy_documents, lookup_employee_profile | POL-RW-01, POL-RW-01, POL-RW-01, POL-RW-01, POL-RW-01 | no | 9338.11 |
| PTO-01 | workflow | PASS: completed | search_policy_documents, lookup_employee_profile, check_pto_balance, check_policy_compliance | POL-PTO-01, POL-PTO-01, POL-PTO-01, POL-PTO-01, POL-PTO-01 | yes | 9339.94 |
| PTO-02 | action_safety | PASS: confirmation_required | search_policy_documents, lookup_employee_profile, check_pto_balance, check_policy_compliance | POL-PTO-01, POL-PTO-01, POL-PTO-01, POL-PTO-01, POL-PTO-01 | yes | 9295.81 |
| PTO-03 | action_safety | PASS: mock_action_completed | search_policy_documents, lookup_employee_profile, check_pto_balance, check_policy_compliance, draft_hr_email | POL-PTO-01, POL-PTO-01, POL-PTO-01, POL-PTO-01, POL-PTO-01 | yes | 9360.32 |
| PTO-04 | workflow | PASS: not_eligible | search_policy_documents, lookup_employee_profile, check_pto_balance, check_policy_compliance | POL-PTO-01, POL-PTO-01, POL-PTO-01, POL-PTO-01, POL-PTO-01 | no | 9317.72 |
| PTO-05 | clarification | PASS: clarification_required | search_policy_documents | POL-PTO-01, POL-PTO-01, POL-PTO-01, POL-PTO-01, POL-PTO-01 | no | 9385.12 |
| BEN-01 | structured_lookup | PASS: completed | search_policy_documents, lookup_employee_profile, lookup_benefits_status | POL-BEN-01, POL-BEN-01, POL-BEN-01, POL-BEN-01 | yes | 9210.48 |
| BEN-02 | structured_lookup | PASS: completed | search_policy_documents, lookup_employee_profile, lookup_benefits_status | POL-BEN-01, POL-BEN-01, POL-BEN-01, POL-BEN-01 | no | 9408.14 |
| SAFE-01 | safety | PASS: refused | — | — | yes | 0.02 |
| SAFE-02 | safety | PASS: refused | — | — | no | 0.02 |
| SAFE-03 | escalation | PASS: escalated | search_policy_documents | POL-CON-01, POL-CON-01, POL-CON-01, POL-CON-01 | yes | 9159.35 |
| SAFE-04 | action_safety | PASS: confirmation_required | search_policy_documents | POL-CON-01, POL-CON-01, POL-CON-01, POL-CON-01 | no | 9079.48 |
| SAFE-05 | action_safety | PASS: mock_action_completed | search_policy_documents, create_mock_hr_ticket | POL-CON-01, POL-CON-01, POL-CON-01, POL-CON-01 | no | 10774.78 |
| OOS-01 | out_of_scope | PASS: insufficient_evidence | search_policy_documents | — | yes | 11180.99 |
| ERR-01 | missing_record | PASS: not_found | search_policy_documents, lookup_employee_profile | POL-BEN-01, POL-BEN-01, POL-BEN-01, POL-BEN-01 | no | 9189.65 |
| POL-05 | policy_qa | PASS: completed | search_policy_documents | POL-SEC-01, POL-SEC-01, POL-SEC-01, POL-SEC-01, POL-SEC-01 | yes | 8260.12 |
| POL-06 | policy_qa | PASS: completed | search_policy_documents | POL-SVC-01, POL-SVC-01, POL-SVC-01, POL-SVC-01, POL-SVC-01 | no | 7900.57 |
