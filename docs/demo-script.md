# Grader Demonstration Script

1. Open `/health?deep=true`. Show service status, MCP discovery, RAG index metadata, embedding provider/model/dimension, and LLM configuration status. Do not expose secrets.
2. Run `Can E1001 work remotely overseas for 10 days?` and show policy search, employee lookup, compliance check, citations, and provisional wording.
3. Run `How much PTO does E1001 have and draft an email for 5 days?` and show the confirmation-required state. Confirm only through the explicit confirmation control.
4. Run a prompt-injection request and show refusal before MCP or LLM access.
5. Run an unknown employee and a sensitive HR request. Show clarification or escalation rather than fabrication.
6. Expand the trace and identify every tool, argument, result, citation, safety decision, and LLM fallback.
7. Record URL, commit SHA, test command, timestamp, and active provider metadata in `deployed.md`.
