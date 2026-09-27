# ADR 0009: Run pinned MiniLM with quantized ONNX Runtime

**Status:** Accepted; local and hosted first-query checks passed, hosted OpenRouter completion remains blocked by account quota
**Date:** 2026-09-27

## Context

The service uses Hugging Face MiniLM locally for policy-query embeddings and stores document vectors in its service-local SQLite index. During the previous Render deployment, memory samples reached 536,264,700 bytes against a 536,870,900-byte limit. An earlier request ended with HTTP 502 and the process restarted without a Python exception or explicit out-of-memory record. The close memory headroom supports resource pressure as a likely risk, but does not prove that memory caused that restart.

The previous runtime loaded Sentence Transformers and PyTorch for a 384-dimensional embedding model. The retrieval baseline, chunking, policy data, and OpenRouter response-generation path must remain unchanged while reducing embedding-runtime overhead.

## Decision

Use the same Hugging Face repository, `sentence-transformers/all-MiniLM-L6-v2`, pinned to revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Load `onnx/model_quint8_avx2.onnx` and `tokenizer.json` from that revision with `onnxruntime`, Hugging Face Hub, and `tokenizers`. Run CPU inference with sequential execution and one intra/inter-op thread by default. Apply the model's attention-mask mean pooling and L2 normalization before storing or searching 384-dimensional vectors.

Persist the embedding backend, revision, and tokenizer maximum length in SQLite metadata. Include them in the index configuration signature so an embedding implementation, revision, or truncation change rebuilds the index. Cache the runtime by model, resolved revision, and tokenizer maximum length, and reject unsupported local Hugging Face model IDs before attempting a download. Readiness requires this pinned semantic baseline and does not treat a sparse fallback as ready. Keep the Hugging Face embedding settings independent from the required OpenRouter response-refinement settings.

## Evidence and validation

- Local ONNX vectors were compared with FP32 Sentence Transformers output for four policy queries. Cosine similarity ranged from 0.991501 to 0.994461; this is a narrow parity check, not a broad retrieval-quality result.
- A fresh SQLite index built with 14 documents, 182 chunks, 384 dimensions, semantic embeddings enabled, the pinned revision, and no embedding error.
- The public `RagIndex` regression changes the tokenizer maximum from 256 to 128 and verifies that both the SQLite index and cached tokenizer/runtime rebuild; metadata reports the active maximum.
- The production-vs-independent retrieval ordering and candidate-set check matched on 15/15 queries. The existing read-only six-case policy slice passed; the chunk ablation was rerun and retained 120/20 as the smallest tied configuration.
- Full local pytest completed with 99 passed and one third-party deprecation warning. MCP stdio smoke and both 30-case orchestrator evaluations completed on the ONNX index. The golden evaluations still exclude live LLM generation (`llm_generation_included=false`).
- The shared `scripts/verify_pinned_index.py` release gate verifies the exact MiniLM repository and revision, ONNX backend, 256-token maximum, 384 dimensions, and 120/20 chunk configuration in both GitHub Actions and `render.yaml`. `/health/ready` checks the same production baseline and fails closed if only sparse fallback vectors are available.
- Local process peak RSS was 121.6 MB during the ONNX experiment. That local result is not directly comparable to Render's prior memory sample and does not establish hosted capacity.
- CI run [36336569726](https://github.com/MSAIE2027/Project-HR-Agent/actions/runs/36336569726) passed the build gate, tests, MCP smoke, and both threshold-gated evaluations. Render deployment `dep-dasl2lh7lnhs739ltkb0` is live on the same tested commit `eeceda7`; the first policy request completed without a process restart. Render sampled 71,155,710 bytes after startup and 274,866,180 bytes after the first policy request against a 536,870,900-byte service limit. These two samples are not a peak or concurrency benchmark.
- The first hosted citation-bearing request reached OpenRouter after retrieval and three MCP tool calls. Qwen returned an account-wide free-tier quota 429; the trace reports `failure_scope=account_quota`, and the app stopped the chain after one attempt and returned HTTP 503 without the unrefined draft. No answer model resolved; successful hosted LLM generation remains pending quota availability.

## Consequences

- Fresh installs no longer need PyTorch or Sentence Transformers for the production embedding path, reducing runtime dependencies and avoiding loading the full PyTorch stack.
- New indexes use a pinned quantized model export and record which backend/revision/tokenizer limit produced their vectors. Old indexes rebuild because the configuration signature changes.
- The selected `quint8_avx2` export requires a compatible CPU instruction set. The index build check fails if the backend cannot load or produce the required semantic index.
- GitHub Actions and the Render build install the same pinned dependencies and assert the same exact index. The CI-passing SHA is deployed manually; Render auto-deploy remains off.
- This change does not mitigate OpenRouter rate limits. Every citation-bearing response still requires the configured OpenRouter chain and fails closed if no model returns a valid answer.
- The CI-passing ONNX commit is deployed. The first hosted policy query completed and the service stayed ready at the recorded memory samples; those few points do not establish peak or concurrent capacity. Hosted answer acceptance remains open because OpenRouter returned an identifiable account-wide free-tier quota 429 before any model resolved.

## Alternatives considered

- Keep PyTorch and increase the Render plan: would retain the previous runtime profile and add a recurring hosting cost; no plan change is made here.
- Use sparse hashing: lighter, but it would replace the selected semantic MiniLM baseline and alter retrieval behavior.
- Use a remote embedding API: it would add another live-provider dependency and move query embeddings off the service; it is not the selected architecture.

## Revisit when

Revisit if the pinned ONNX backend fails on Render's CPU, the hosted cold-load still approaches the memory limit, or a larger independently judged retrieval set shows material quality loss.
