# AI Tooling Disclosure

## Tools and scope

- The project owner confirmed that Claude Code, Codex, AntiGravity, and OpenCode were used during earlier project work. The repository does not attribute individual earlier changes to a specific tool.
- OpenAI Codex was used during this completion pass to review the supplied requirements, connect source requirements to implementation and evidence, update code and documentation, run local evaluations, and rehearse the browser workflows. The current Git history and evidence index show the resulting changes and checks.

## Review and limits

AI-generated code and documentation require human review. The golden-set and retrieval figures are deterministic, fixture-based measurements; they do not establish open-ended semantic accuracy. Hosted OpenRouter generation is a separate acceptance check and remains unverified after the latest preflight returned HTTP 429 from all four configured model routes. No resolved model was reported. Current release status is in [`deployed.md`](deployed.md), with detailed evidence in [`evidence/index.md`](evidence/index.md).

The project uses fictional policies, employee records, tickets, and actions. No production HR system is connected, and no real employee data was supplied to the agent during this completion pass.

## Reproducible evidence

The full local test and evaluation records are summarized in [`evidence/index.md`](evidence/index.md). Retrieval methods and limitations are documented in [`evaluation/retrieval-comparison.md`](evaluation/retrieval-comparison.md) and [`evaluation/ablation-results.md`](evaluation/ablation-results.md). The local OpenRouter runtime example identifies the model resolved for one synthetic request; it does not establish which model a future or hosted request will use.
