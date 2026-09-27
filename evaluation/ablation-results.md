# MiniLM Retrieval Chunk Ablation

This retrieval-only comparison fixes sentence-transformers/all-MiniLM-L6-v2 (384 dimensions) to onnxruntime-quint8-avx2 at HF revision 1110a243fdf4706b3f48f1d95db1a4f5529b4d41, keeps ranking weights unchanged, and compares chunk size and overlap over labeled policy-family queries.

Cases: 15 total, including 5 multi-document queries. Query-time measurements use a warmed local model. No transaction workflows are included.

Corpus: 14 policy files and 15,034 parsed policy-text words, or about 37.6 page-equivalents at 400 words per page. The index metadata sums per-file estimates; neither figure is a rendered page count.

Hit@k means at least one expected policy family appears in the global top k; family recall@5 is the fraction of expected families present in the global top five. Filtered metrics are simulated family-specific searches, not measured route selection.

Selection order: global multi-document all-family coverage at 5, family-filtered score coverage, global all-family coverage at 5, family recall at 5, then family MRR. If quality ties, choose the smallest index, then fewer chunks, then the smallest chunk cap, followed by warm build time and median search latency.

| Chunk / overlap | Chunks | Hit@1 | Hit@3 | Hit@5 | Family recall@5 | All families@5 | Multi-doc all families@5 | Filtered families@5 (sim.) | Filtered score coverage (sim.) | Index KiB | Search p50 ms | Search p95 ms | Warm build s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 60 / 10 | 326 | 1.00 | 1.00 | 1.00 | 0.76 | 0.73 | 0.20 | 1.00 | 1.00 | 1750.2 | 12.770 | 65.472 | 7.737 |
| 90 / 15 | 279 | 1.00 | 1.00 | 1.00 | 0.76 | 0.73 | 0.20 | 1.00 | 1.00 | 1750.2 | 13.895 | 71.855 | 9.173 |
| 120 / 20 | 182 | 1.00 | 1.00 | 1.00 | 0.76 | 0.73 | 0.20 | 1.00 | 1.00 | 1750.2 | 12.764 | 63.789 | 7.253 |
| 160 / 24 | 182 | 1.00 | 1.00 | 1.00 | 0.76 | 0.73 | 0.20 | 1.00 | 1.00 | 1750.2 | 18.185 | 74.323 | 7.224 |
| 220 / 30 | 182 | 1.00 | 1.00 | 1.00 | 0.76 | 0.73 | 0.20 | 1.00 | 1.00 | 1750.2 | 14.621 | 71.516 | 9.107 |

Selected: 120 words / 20 overlap. It shares the best quality metrics. Among tied configurations, selection uses index size, chunk count, the smallest chunk cap, then measured build and search time.

Average result diversity at global top 5 before reranking: 1.27 distinct documents and 5.00 distinct sections. See retrieval-comparison.md for the MMR comparison and current production reranker.

The best quality metrics tie across 60/10, 90/15, 120/20, 160/24, 220/30. The selected 120/20 setting is the smallest cap in that tied group; the selected index contains 182 chunks. Raw global top-five all-family coverage is 1/5 (0.20) for multi-document probes. Family-filtered figures are simulated; the separate retrieval comparison measures actual application routing and MMR. These results are a small hand-authored retrieval benchmark, not an independent semantic judgment. They measure expected document-family coverage, not final answer correctness, workflow status, or transaction behavior. Re-run after policy corpus or embedding changes.
