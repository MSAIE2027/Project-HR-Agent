# MiniLM Retrieval Chunk Ablation

This retrieval-only comparison fixes the embedding model to sentence-transformers/all-MiniLM-L6-v2 (384 dimensions), keeps ranking weights unchanged, and compares chunk size and overlap over labeled policy-family queries.

Cases: 15 total, including 5 multi-document queries. Query-time measurements use a warmed local model. No transaction workflows are included.

Hit@k means at least one expected policy family appears in the global top k; family recall@5 is the fraction of expected families present in the global top five. Filtered metrics are simulated family-specific searches, not measured route selection.

Selection order: global multi-document all-family coverage at 5, family-filtered score coverage, global all-family coverage at 5, family recall at 5, then family MRR. If quality ties, choose the smallest index, then fewer chunks, then the smallest chunk cap, followed by warm build time and median search latency.

| Chunk / overlap | Chunks | Hit@1 | Hit@3 | Hit@5 | Family recall@5 | All families@5 | Multi-doc all families@5 | Filtered families@5 (sim.) | Filtered score coverage (sim.) | Index KiB | Search p50 ms | Search p95 ms | Warm build s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 60 / 10 | 212 | 1.00 | 1.00 | 1.00 | 0.76 | 0.73 | 0.20 | 1.00 | 1.00 | 1951.4 | 16.776 | 78.561 | 2.064 |
| 90 / 15 | 168 | 1.00 | 1.00 | 1.00 | 0.81 | 0.80 | 0.40 | 1.00 | 1.00 | 1581.2 | 18.679 | 66.561 | 2.600 |
| 120 / 20 | 126 | 1.00 | 1.00 | 1.00 | 0.81 | 0.80 | 0.40 | 1.00 | 1.00 | 1219.1 | 11.854 | 43.228 | 1.980 |
| 160 / 24 | 126 | 1.00 | 1.00 | 1.00 | 0.81 | 0.80 | 0.40 | 1.00 | 1.00 | 1219.1 | 13.628 | 46.988 | 2.021 |
| 220 / 30 | 126 | 1.00 | 1.00 | 1.00 | 0.81 | 0.80 | 0.40 | 1.00 | 1.00 | 1219.1 | 13.269 | 44.561 | 2.019 |

Selected: 120 words / 20 overlap. It shares the best quality metrics. Among tied configurations, selection uses index size, chunk count, the smallest chunk cap, then measured build and search time.

Before reranking, global top 5 averaged 1.60 distinct documents and 5.00 distinct sections. The follow-up comparison found MMR λ=0.5 increased multi-family coverage; production now uses MMR over a top-ten pool and returns five results. The separate actual route also seeds a result for each explicitly selected family.

On this corpus, 120/20, 160/24, and 220/30 produced identical chunk content (126 chunks) and retrieval metrics. The 120-word cap is selected as the smallest cap in that tied group, a corpus-specific efficiency choice rather than a universal optimum. The 90/15 index was larger with lower family coverage; 60/10 had lower all-family coverage. Family-filtered columns simulate one top-3 search per expected family, merge those results, and keep five. The actual orchestrator route now evaluates that family intent and cites all expected families in 5/5 probes; MMR λ=0.5 also raises global top-five coverage to 3/5. Limitations: this is a small hand-authored retrieval benchmark, not an independent semantic judgment. It measures expected document-family retrieval and score coverage, not answer correctness, workflow status, or transaction behavior. Rerun after policy corpus or embedding changes.

The follow-up top-k, routing, MMR, and ranking-weight comparison is documented in [retrieval-comparison.md](retrieval-comparison.md) with a chart in [visuals/retrieval-comparison.svg](../visuals/retrieval-comparison.svg).
