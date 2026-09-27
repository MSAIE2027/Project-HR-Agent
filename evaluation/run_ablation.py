from __future__ import annotations

import argparse
import json
import os
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any

from rag.index import DEFAULT_LOCAL_MODEL, RagIndex
from rag.ingest import load_policy_sections

ROOT = Path(__file__).resolve().parents[1]
MINIMUM_EVIDENCE_SCORE = 0.12
TOP_K = 5
FAMILY_TOP_K = 3

# Retrieval-only policy questions. Multi-family cases measure citation coverage,
# including the remote-work plus information-security path used by the agent.
QUERIES = [
    {"id": "remote_days", "query": "international remote work rolling day limit", "expected_prefixes": ["POL-RW-"]},
    {"id": "security_access", "query": "corporate VPN multi-factor authentication overseas", "expected_prefixes": ["POL-SEC-"]},
    {"id": "pto_carryover", "query": "PTO carry over five days", "expected_prefixes": ["POL-PTO-"]},
    {"id": "benefit_enrolment", "query": "benefits qualifying life event enrolment", "expected_prefixes": ["POL-BEN-"]},
    {"id": "conduct_escalation", "query": "harassment confidential HR escalation", "expected_prefixes": ["POL-CON-"]},
    {"id": "expense_receipts", "query": "expense receipt threshold", "expected_prefixes": ["POL-EXP-"]},
    {"id": "service_ticket", "query": "mock ticket does not contact production", "expected_prefixes": ["POL-SVC-"]},
    {"id": "approval_matrix", "query": "manager approval matrix tax immigration", "expected_prefixes": ["POL-APR-"]},
    {"id": "employment_classification", "query": "part-time employment classification", "expected_prefixes": ["POL-ONB-"]},
    {"id": "medical_leave", "query": "medical leave documentation privacy", "expected_prefixes": ["POL-LVE-"]},
    {
        "id": "international_confidential_data",
        "query": "What controls apply when working internationally with confidential data?",
        "expected_prefixes": ["POL-RW-", "POL-SEC-"],
    },
    {
        "id": "international_approval_controls",
        "query": "What approvals and security checks apply to international remote work?",
        "expected_prefixes": ["POL-RW-", "POL-SEC-", "POL-APR-"],
    },
    {
        "id": "expense_approval",
        "query": "What receipts are required for business expenses and when is manager approval needed?",
        "expected_prefixes": ["POL-EXP-", "POL-APR-"],
    },
    {
        "id": "leave_record_privacy",
        "query": "How should medical leave documents be handled and retained privately?",
        "expected_prefixes": ["POL-LVE-", "POL-REC-"],
    },
    {
        "id": "benefit_exception_records",
        "query": "When can a life event change benefits enrollment and how are employee records protected?",
        "expected_prefixes": ["POL-BEN-", "POL-REC-"],
    },
]

CONFIGURATIONS = [
    {"name": "compact", "chunk_words": 60, "overlap_words": 10},
    {"name": "small", "chunk_words": 90, "overlap_words": 15},
    {"name": "120/20", "chunk_words": 120, "overlap_words": 20},
    {"name": "large", "chunk_words": 160, "overlap_words": 24},
    {"name": "broad", "chunk_words": 220, "overlap_words": 30},
]


def _use_minilm() -> None:
    os.environ["MSAIE_EMBEDDING_PROVIDER"] = "huggingface"
    os.environ["MSAIE_EMBEDDING_MODEL"] = DEFAULT_LOCAL_MODEL


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = max(0, min(len(ordered) - 1, round(fraction * (len(ordered) - 1))))
    return ordered[position]


def _index_size_bytes(index: RagIndex) -> int:
    paths = [index.path, Path(f"{index.path}-wal")]
    return sum(path.stat().st_size for path in paths if path.exists())


def _rank_for_prefix(results: list[dict[str, Any]], prefix: str) -> int | None:
    return next(
        (position for position, item in enumerate(results, 1) if item["document_id"].startswith(prefix)),
        None,
    )


def _search(
    index: RagIndex,
    query: str,
    timings_ms: list[float],
    *,
    limit: int,
    document_prefix: str | None = None,
) -> list[dict[str, Any]]:
    started = time.perf_counter()
    results = index.search(query, limit=limit, document_prefix=document_prefix)
    timings_ms.append((time.perf_counter() - started) * 1000)
    return results


def warm_local_model() -> None:
    """Load MiniLM before timing chunk configurations; exclude first-load cost."""
    _use_minilm()
    with tempfile.TemporaryDirectory(prefix="msaie-ablation-warmup-") as directory:
        RagIndex(Path(directory) / "warmup.sqlite3").build(
            chunk_words=120,
            overlap_words=20,
            force=True,
        )


def evaluate(configuration: dict[str, int | str]) -> dict[str, Any]:
    _use_minilm()
    with tempfile.TemporaryDirectory(prefix="msaie-ablation-") as directory:
        index = RagIndex(Path(directory) / "index.sqlite3")
        started = time.perf_counter()
        stats = index.build(
            chunk_words=int(configuration["chunk_words"]),
            overlap_words=int(configuration["overlap_words"]),
            force=True,
        )
        build_seconds = time.perf_counter() - started
        if (
            stats.get("embedding_model") != DEFAULT_LOCAL_MODEL
            or stats.get("embedding_provider") != "huggingface"
            or stats.get("dimensions") != 384
            or not stats.get("semantic_embeddings")
        ):
            raise RuntimeError(f"Ablation requires dense MiniLM/384 embeddings; got {stats}")

        search_timings: list[float] = []
        family_counts = {cutoff: 0 for cutoff in (1, 3, 5)}
        any_family_hits = {cutoff: 0 for cutoff in (1, 3, 5)}
        family_total = 0
        family_reciprocal_ranks: list[float] = []
        all_family_hits_at_5 = 0
        multi_document_all_family_at_5 = 0
        multi_document_count = 0
        filtered_all_family_at_5 = 0
        filtered_family_above_threshold = 0
        unique_documents: list[int] = []
        unique_sections: list[int] = []
        rows = []

        for item in QUERIES:
            query = item["query"]
            prefixes = item["expected_prefixes"]
            results = _search(index, query, search_timings, limit=10)
            ranks = {prefix: _rank_for_prefix(results, prefix) for prefix in prefixes}
            family_total += len(prefixes)
            family_reciprocal_ranks.extend(1 / rank if rank else 0.0 for rank in ranks.values())
            for cutoff in family_counts:
                found = sum(rank is not None and rank <= cutoff for rank in ranks.values())
                family_counts[cutoff] += found
                any_family_hits[cutoff] += found > 0
            all_family_hits_at_5 += all(rank is not None and rank <= TOP_K for rank in ranks.values())
            unique_documents.append(len({row["document_id"] for row in results[:TOP_K]}))
            unique_sections.append(
                len({(row["document_id"], row["section"]) for row in results[:TOP_K]})
            )

            filtered: list[dict[str, Any]] = []
            each_family_has_evidence = True
            for prefix in prefixes:
                family_results = _search(
                    index,
                    query,
                    search_timings,
                    limit=FAMILY_TOP_K,
                    document_prefix=prefix,
                )
                filtered.extend(family_results)
                each_family_has_evidence &= any(
                    row["score"] >= MINIMUM_EVIDENCE_SCORE for row in family_results
                )
            filtered.sort(key=lambda row: row["score"], reverse=True)
            filtered_top_k = filtered[:TOP_K]
            route_covered = all(
                any(row["document_id"].startswith(prefix) for row in filtered_top_k)
                for prefix in prefixes
            )
            filtered_all_family_at_5 += route_covered
            filtered_family_above_threshold += each_family_has_evidence
            if len(prefixes) > 1:
                multi_document_count += 1
                multi_document_all_family_at_5 += all(
                    rank is not None and rank <= TOP_K for rank in ranks.values()
                )
            rows.append(
                {
                    "id": item["id"],
                    "query": query,
                    "expected_prefixes": prefixes,
                    "global_family_ranks": ranks,
                    "global_top_ids": [row["document_id"] for row in results[:TOP_K]],
                    "filtered_top_ids": [row["document_id"] for row in filtered_top_k],
                    "filtered_all_families_at_5": route_covered,
                    "each_family_has_score_at_least_0_12": each_family_has_evidence,
                }
            )

        query_count = len(QUERIES)
        metrics = {
            "query_count": query_count,
            "required_family_count": family_total,
            "multi_document_query_count": multi_document_count,
            "hit_at_1": round(any_family_hits[1] / query_count, 4),
            "hit_at_3": round(any_family_hits[3] / query_count, 4),
            "hit_at_5": round(any_family_hits[5] / query_count, 4),
            "family_recall_at_1": round(family_counts[1] / family_total, 4),
            "family_recall_at_3": round(family_counts[3] / family_total, 4),
            "family_recall_at_5": round(family_counts[5] / family_total, 4),
            "family_mrr": round(statistics.mean(family_reciprocal_ranks), 4),
            "all_family_coverage_at_5": round(all_family_hits_at_5 / query_count, 4),
            "multi_document_all_family_coverage_at_5": round(
                multi_document_all_family_at_5 / max(multi_document_count, 1), 4
            ),
            "filtered_all_family_coverage_at_5": round(filtered_all_family_at_5 / query_count, 4),
            "filtered_family_score_coverage": round(
                filtered_family_above_threshold / query_count, 4
            ),
            "mean_unique_documents_top5": round(statistics.mean(unique_documents), 3),
            "mean_unique_sections_top5": round(statistics.mean(unique_sections), 3),
            "search_ms_p50": round(_percentile(search_timings, 0.50), 3),
            "search_ms_p95": round(_percentile(search_timings, 0.95), 3),
            "build_seconds_warm": round(build_seconds, 3),
            "index_bytes": _index_size_bytes(index),
        }
        return {
            **configuration,
            "metrics": metrics,
            "index": {key: value for key, value in stats.items() if key != "path"},
            "queries": rows,
        }


def _quality(item: dict[str, Any]) -> tuple[float, ...]:
    metrics = item["metrics"]
    return (
        metrics["multi_document_all_family_coverage_at_5"],
        metrics["filtered_family_score_coverage"],
        metrics["all_family_coverage_at_5"],
        metrics["family_recall_at_5"],
        metrics["family_mrr"],
    )


def select_configuration(configurations: list[dict[str, Any]]) -> dict[str, Any]:
    best_quality = max(_quality(item) for item in configurations)
    finalists = [item for item in configurations if _quality(item) == best_quality]
    return min(
        finalists,
        key=lambda item: (
            item["metrics"]["index_bytes"],
            item["index"]["chunks"],
            item["chunk_words"],
            item["metrics"]["build_seconds_warm"],
            item["metrics"]["search_ms_p50"],
        ),
    )


def to_markdown(report: dict[str, Any]) -> str:
    best = report["selected_configuration"]
    best_metrics = best["metrics"]
    quality_fields = (
        "multi_document_all_family_coverage_at_5",
        "filtered_family_score_coverage",
        "all_family_coverage_at_5",
        "family_recall_at_5",
        "family_mrr",
    )
    best_quality = tuple(round(best_metrics[field], 4) for field in quality_fields)
    tied_configurations = [
        item
        for item in report["configurations"]
        if tuple(round(item["metrics"][field], 4) for field in quality_fields) == best_quality
    ]
    tied_labels = ", ".join(
        f"{item['chunk_words']}/{item['overlap_words']}" for item in tied_configurations
    )
    multi_document_cases = report["multi_document_query_count"]
    multi_document_hits = round(
        best_metrics["multi_document_all_family_coverage_at_5"] * multi_document_cases
    )
    corpus_word_count = report["corpus_word_count"]
    corpus_page_equivalents = report["corpus_page_equivalents_400_words"]
    lines = [
        "# MiniLM Retrieval Chunk Ablation",
        "",
        "This retrieval-only comparison fixes the embedding model to sentence-transformers/all-MiniLM-L6-v2 (384 dimensions), keeps ranking weights unchanged, and compares chunk size and overlap over labeled policy-family queries.",
        "",
        f"Cases: {report['query_count']} total, including {report['multi_document_query_count']} multi-document queries. Query-time measurements use a warmed local model. No transaction workflows are included.",
        "",
        f"Corpus: {report['corpus_document_count']} policy files and {corpus_word_count:,} parsed policy-text words, or about {corpus_page_equivalents:.1f} page-equivalents at 400 words per page. The index metadata sums per-file estimates; neither figure is a rendered page count.",
        "",
        "Hit@k means at least one expected policy family appears in the global top k; family recall@5 is the fraction of expected families present in the global top five. Filtered metrics are simulated family-specific searches, not measured route selection.",
        "",
        "Selection order: global multi-document all-family coverage at 5, family-filtered score coverage, global all-family coverage at 5, family recall at 5, then family MRR. If quality ties, choose the smallest index, then fewer chunks, then the smallest chunk cap, followed by warm build time and median search latency.",
        "",
        "| Chunk / overlap | Chunks | Hit@1 | Hit@3 | Hit@5 | Family recall@5 | All families@5 | Multi-doc all families@5 | Filtered families@5 (sim.) | Filtered score coverage (sim.) | Index KiB | Search p50 ms | Search p95 ms | Warm build s |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in report["configurations"]:
        metrics = item["metrics"]
        lines.append(
            f"| {item['chunk_words']} / {item['overlap_words']} | {item['index']['chunks']} | "
            f"{metrics['hit_at_1']:.2f} | {metrics['hit_at_3']:.2f} | {metrics['hit_at_5']:.2f} | "
            f"{metrics['family_recall_at_5']:.2f} | {metrics['all_family_coverage_at_5']:.2f} | "
            f"{metrics['multi_document_all_family_coverage_at_5']:.2f} | "
            f"{metrics['filtered_all_family_coverage_at_5']:.2f} | "
            f"{metrics['filtered_family_score_coverage']:.2f} | "
            f"{metrics['index_bytes'] / 1024:.1f} | {metrics['search_ms_p50']:.3f} | "
            f"{metrics['search_ms_p95']:.3f} | {metrics['build_seconds_warm']:.3f} |"
        )
    lines += [
        "",
        f"Selected: {best['chunk_words']} words / {best['overlap_words']} overlap. It shares the best quality metrics. Among tied configurations, selection uses index size, chunk count, the smallest chunk cap, then measured build and search time.",
        "",
        f"Average result diversity at global top 5 before reranking: {best_metrics['mean_unique_documents_top5']:.2f} distinct documents and {best_metrics['mean_unique_sections_top5']:.2f} distinct sections. See retrieval-comparison.md for the MMR comparison and current production reranker.",
        "",
        f"The best quality metrics tie across {tied_labels}. The selected {best['chunk_words']}/{best['overlap_words']} setting is the smallest cap in that tied group; the selected index contains {best['index']['chunks']} chunks. Raw global top-five all-family coverage is {multi_document_hits}/{multi_document_cases} ({best_metrics['multi_document_all_family_coverage_at_5']:.2f}) for multi-document probes. Family-filtered figures are simulated; the separate retrieval comparison measures actual application routing and MMR. These results are a small hand-authored retrieval benchmark, not an independent semantic judgment. They measure expected document-family coverage, not final answer correctness, workflow status, or transaction behavior. Re-run after policy corpus or embedding changes.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="evaluation/ablation-results.json")
    parser.add_argument("--markdown", default="evaluation/ablation-results.md")
    args = parser.parse_args()
    _use_minilm()
    warm_local_model()
    configurations = [evaluate(item) for item in CONFIGURATIONS]
    policy_sections = load_policy_sections(ROOT / "policies")
    corpus_word_count = sum(len(section.text.split()) for section in policy_sections)
    corpus_document_count = len({section.document_id for section in policy_sections})
    report = {
        "embedding_model": DEFAULT_LOCAL_MODEL,
        "embedding_dimensions": 384,
        "corpus_document_count": corpus_document_count,
        "corpus_word_count": corpus_word_count,
        "corpus_page_equivalents_400_words": round(corpus_word_count / 400, 1),
        "query_count": len(QUERIES),
        "multi_document_query_count": sum(len(item["expected_prefixes"]) > 1 for item in QUERIES),
        "minimum_evidence_score": MINIMUM_EVIDENCE_SCORE,
        "global_top_k": TOP_K,
        "family_top_k": FAMILY_TOP_K,
        "selection_method": "global multi-document coverage, family-filtered score coverage, global coverage, family recall and family MRR; tie-break by index size, chunk count, chunk cap, warm build time, then p50 search latency",
        "configurations": configurations,
    }
    report["selected_configuration"] = select_configuration(configurations)
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    markdown_output = Path(args.markdown)
    if not markdown_output.is_absolute():
        markdown_output = ROOT / markdown_output
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(to_markdown(report), encoding="utf-8")
    print(to_markdown(report))


if __name__ == "__main__":
    main()
