# Implementation Status

| Area | Current implementation | Current-copy evidence |
|---|---|---|
| Web application | FastAPI API and static employee workspace | Startup and /health were verified in the earlier local setup pass; no new browser review in this pass |
| Orchestration | Explicit routing, evidence checks, and confirmation gates | Read-only policy route exercised across 15 retrieval queries |
| MCP | SDK FastMCP server; official client in stdio mode | In-process policy calls exercised; stdio protocol path not exercised in this pass |
| RAG | Markdown/HTML ingestion, SQLite vectors, cosine ranking | MiniLM 384d at 120/20; production MMR λ=0.5, top ten to five results |
| Embeddings | Local sentence-transformers MiniLM default and hashing fallback | Runtime trace reported huggingface_dense_cosine; remote embedding configuration is separate and disabled in the comparison |
| LLM | Optional constrained OpenAI-compatible refinement | Structured-status/numeric validator and fallback were implemented; pytest cases not run |
| Safety | Synthetic data, prompt-injection refusal, confirmation-gated mock actions | No action or transaction scenario run in this pass |
| Evaluation | Golden set plus chunk and ranking ablations | 15-query route comparison reached 100% expected-family coverage (5/5 multi-family); six-case read-only golden policy slice scored 100% on its three proxies; full evaluation remains unrun |
| Visuals | Retrieval comparison chart in visuals | SVG includes an accessible title and description; no browser UI review in this pass |
| Deployment | Optional Render service definition | Not deployed or verified from this checkout |

The retrieval measures are small, hand-labeled proxies. They are not a full answer-quality score or a production release claim.
