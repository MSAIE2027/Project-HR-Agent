# AI Tooling Disclosure

## Tools and scope

- The project owner confirmed that Claude Code, Codex, AntiGravity, and OpenCode were used during earlier project work. The repository does not attribute individual earlier changes to a specific tool.
- OpenAI Codex supported the current completion work: requirements review, implementation and documentation updates, evaluation, and browser verification.

## Review and limits

AI-generated code and documentation require human review. The golden-set and retrieval figures are deterministic, fixture-based measurements; they do not establish open-ended semantic accuracy. Hosted OpenRouter generation is a separate acceptance check; its current status and sanitized evidence are in [`deployed.md`](deployed.md) and [`evidence/index.md`](evidence/index.md).

The project uses fictional policies, employee records, tickets, and actions. It does not connect to a production HR system or use real employee data.

## Reproducible evidence

The full local test and evaluation records are summarized in [`evidence/index.md`](evidence/index.md). Retrieval methods and limitations are documented in [`evaluation/retrieval-comparison.md`](evaluation/retrieval-comparison.md) and [`evaluation/ablation-results.md`](evaluation/ablation-results.md). The local OpenRouter runtime example identifies the model resolved for one synthetic request; it does not establish which model a future or hosted request will use.
