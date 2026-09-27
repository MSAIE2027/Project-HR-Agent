from __future__ import annotations

import argparse
import asyncio
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluation.run_ablation import MINIMUM_EVIDENCE_SCORE, QUERIES
from rag.index import DEFAULT_LOCAL_MODEL, RagIndex, _dense_cosine, _local_embeddings, tokenize

POOL = 10
TOP_K = (1, 3, 5, 8)
WEIGHTS = {
    "current": {"dense": 1.0, "lexical_ratio": 0.08, "title_hits": 0.025, "phrase": 0.08},
    "dense_only": {"dense": 1.0, "lexical_ratio": 0.0, "title_hits": 0.0, "phrase": 0.0},
    "cosine_half": {"dense": 0.5, "lexical_ratio": 0.08, "title_hits": 0.025, "phrase": 0.08},
    "cosine_2x": {"dense": 2.0, "lexical_ratio": 0.08, "title_hits": 0.025, "phrase": 0.08},
    "lexical_2x": {"dense": 1.0, "lexical_ratio": 0.16, "title_hits": 0.05, "phrase": 0.16},
}
MMR_LAMBDAS = (0.7, 0.5)


def _configure(index_path: Path) -> None:
    os.environ["MSAIE_EMBEDDING_PROVIDER"] = "huggingface"
    os.environ["MSAIE_EMBEDDING_MODEL"] = DEFAULT_LOCAL_MODEL
    os.environ["MSAIE_INDEX_PATH"] = str(index_path)
    for name in (
        "MSAIE_EMBEDDING_BASE_URL",
        "MSAIE_EMBEDDING_API_KEY",
        "MSAIE_LLM_BASE_URL",
        "MSAIE_LLM_API_KEY",
        "MSAIE_LLM_FALLBACK_MODEL",
        "MSAIE_LLM_MODEL",
    ):
        os.environ.pop(name, None)


def _read_chunks(path: Path) -> list[dict[str, Any]]:
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT chunk_id, document_id, title, section, content, vector_json FROM chunks"
        ).fetchall()
    return [
        {
            "chunk_id": row["chunk_id"],
            "document_id": row["document_id"],
            "title": row["title"],
            "section": row["section"],
            "content": row["content"],
            "vector": [float(value) for value in json.loads(row["vector_json"])],
        }
        for row in rows
    ]


def _score(rows: list[dict[str, Any]], query: str, vector: list[float], weights: dict[str, float]) -> list[dict[str, Any]]:
    query_tokens = set(tokenize(query))
    query_lower = query.lower()
    candidates = []
    for row in rows:
        lexical = set(tokenize(f"{row['title']} {row['section']} {row['content']}"))
        overlap = query_tokens & lexical
        dense = _dense_cosine(vector, row["vector"])
        title_text = f"{row['title']} {row['section']}".lower()
        title_hits = sum(1 for token in overlap if token in title_text)
        ratio = len(overlap) / max(len(query_tokens), 1)
        phrase = float(query_lower in row["content"].lower())
        score = (
            dense * weights["dense"]
            + ratio * weights["lexical_ratio"]
            + title_hits * weights["title_hits"]
            + phrase * weights["phrase"]
        )
        if score > 0:
            candidates.append({**row, "score": score, "dense": dense})
    candidates.sort(key=lambda item: item["score"], reverse=True)
    return candidates


def _mmr(candidates: list[dict[str, Any]], lambda_value: float) -> list[dict[str, Any]]:
    pool = candidates[:POOL]
    if not pool:
        return []
    low, high = min(row["score"] for row in pool), max(row["score"] for row in pool)
    span = high - low
    relevance = {
        row["chunk_id"]: ((row["score"] - low) / span if span else 1.0)
        for row in pool
    }
    chosen, remaining = [], list(pool)
    while remaining:
        best, best_score = None, float("-inf")
        for candidate in remaining:
            redundancy = max(
                (max(0.0, _dense_cosine(candidate["vector"], row["vector"])) for row in chosen),
                default=0.0,
            )
            score = lambda_value * relevance[candidate["chunk_id"]] - (1 - lambda_value) * redundancy
            if score > best_score:
                best, best_score = candidate, score
        chosen.append(best)
        remaining.remove(best)
    return chosen


def _metrics(ranked: dict[str, list[dict[str, Any]]], k: int) -> dict[str, Any]:
    query_count = len(QUERIES)
    family_count = sum(len(item["expected_prefixes"]) for item in QUERIES)
    family_hits = 0
    hit_queries = 0
    complete_queries = 0
    multi_complete = 0
    multi_count = 0
    docs, sections = [], []
    for item in QUERIES:
        results = ranked[item["id"]][:k]
        found = [
            any(row["document_id"].startswith(prefix) for row in results)
            for prefix in item["expected_prefixes"]
        ]
        family_hits += sum(found)
        hit_queries += bool(any(found))
        complete_queries += bool(found) and all(found)
        if len(found) > 1:
            multi_count += 1
            multi_complete += all(found)
        docs.append(len({row["document_id"] for row in results}))
        sections.append(len({(row["document_id"], row["section"]) for row in results}))
    return {
        "hit_at_k": round(hit_queries / query_count, 4),
        "family_recall_at_k": round(family_hits / family_count, 4),
        "all_family_coverage_at_k": round(complete_queries / query_count, 4),
        "multi_document_all_family_coverage_at_k": round(multi_complete / max(multi_count, 1), 4),
        "mean_unique_documents": round(sum(docs) / query_count, 3),
        "mean_unique_sections": round(sum(sections) / query_count, 3),
    }


async def _route_results(index_path: Path) -> dict[str, Any]:
    _configure(index_path)
    from agent.orchestrator import MSAIEOrchestrator
    from evaluation.run_evaluation import evaluate_item
    from mcp_client.client import MCPGateway

    orchestrator = MSAIEOrchestrator(MCPGateway("inprocess"))
    records, methods = [], set()
    for item in QUERIES:
        result = await orchestrator.handle(item["query"], confirm_action=False)
        calls = [row for row in result.trace if row.get("event") == "tool_call"]
        names = [row.get("tool") for row in calls]
        if not calls or any(name != "search_policy_documents" for name in names):
            raise RuntimeError(f"Unexpected non-read-only route for {item['id']}: {names}")
        methods.update(
            str(citation["retrieval_method"])
            for citation in result.citations
            if citation.get("retrieval_method")
        )
        expected = item["expected_prefixes"]
        found = [
            any(citation["document_id"].startswith(prefix) for citation in result.citations)
            for prefix in expected
        ]
        records.append(
            {
                "id": item["id"],
                "expected_prefixes": expected,
                "selected_prefixes": [
                    call.get("arguments", {}).get("document_prefix")
                    for call in calls
                ],
                "citation_ids": [citation["document_id"] for citation in result.citations],
                "all_expected_families_cited": bool(found) and all(found),
                "status": result.status,
            }
        )
    expected_families = sum(len(row["expected_prefixes"]) for row in records)
    found_families = sum(
        sum(any(doc.startswith(prefix) for doc in row["citation_ids"]) for prefix in row["expected_prefixes"])
        for row in records
    )
    multi = [row for row in records if len(row["expected_prefixes"]) > 1]

    golden = json.loads((ROOT / "evaluation" / "golden_set.json").read_text(encoding="utf-8"))
    policy_items = [
        item for item in golden
        if item.get("category") in {"policy_qa", "multi_document"}
    ]
    if any(
        item.get("confirm_action", False)
        or set(item.get("expected_tools", [])) != {"search_policy_documents"}
        for item in policy_items
    ):
        raise RuntimeError("Read-only golden subset contains a non-policy or action case")
    policy_results = [await evaluate_item(orchestrator, item) for item in policy_items]
    if any(
        any(name != "search_policy_documents" for name in item["actual_tools"])
        for item in policy_results
    ):
        raise RuntimeError("Golden policy subset selected a non-search tool")
    policy_summary = {
        "item_count": len(policy_results),
        "status_accuracy": round(
            sum(item["status_pass"] for item in policy_results) / max(len(policy_results), 1), 4
        ),
        "citation_prefix_accuracy": round(
            sum(item["citation_accuracy_pass"] for item in policy_results) / max(len(policy_results), 1), 4
        ),
        "groundedness_proxy": round(
            sum(item["groundedness_pass"] for item in policy_results) / max(len(policy_results), 1), 4
        ),
        "items": [
            {
                "id": item["id"],
                "status": item["actual_status"],
                "status_pass": item["status_pass"],
                "citation_ids": item["citation_ids"],
                "citation_accuracy_pass": item["citation_accuracy_pass"],
                "keyword_score": item["keyword_score"],
                "groundedness_pass": item["groundedness_pass"],
            }
            for item in policy_results
        ],
    }
    return {
        "expected_family_recall": round(found_families / expected_families, 4),
        "all_family_query_coverage": round(
            sum(row["all_expected_families_cited"] for row in records) / len(records), 4
        ),
        "multi_document_all_family_coverage": round(
            sum(row["all_expected_families_cited"] for row in multi) / max(len(multi), 1), 4
        ),
        "retrieval_methods": sorted(methods),
        "queries": records,
        "read_only_golden_policy_subset": policy_summary,
    }


def run() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="msaie-retrieval-comparison-") as directory:
        path = Path(directory) / "index.sqlite3"
        _configure(path)
        index = RagIndex(path)
        stats = index.build(chunk_words=120, overlap_words=20, force=True)
        if (
            stats.get("embedding_model") != DEFAULT_LOCAL_MODEL
            or stats.get("embedding_provider") != "huggingface"
            or stats.get("dimensions") != 384
            or not stats.get("semantic_embeddings")
        ):
            raise RuntimeError(f"Expected local MiniLM/384 embeddings; received {stats}")

        rows = _read_chunks(path)
        query_vectors = {
            item["id"]: _local_embeddings([item["query"]], DEFAULT_LOCAL_MODEL)[0]
            for item in QUERIES
        }
        rankings = {
            name: {
                item["id"]: _score(rows, item["query"], query_vectors[item["id"]], weights)
                for item in QUERIES
            }
            for name, weights in WEIGHTS.items()
        }
        weight_results = {
            name: {
                "weights": WEIGHTS[name],
                "top_k": {str(k): _metrics(ranking, k) for k in TOP_K},
            }
            for name, ranking in rankings.items()
        }
        mmr_results = {}
        for lambda_value in MMR_LAMBDAS:
            reranked = {
                item["id"]: _mmr(rankings["current"][item["id"]], lambda_value)
                for item in QUERIES
            }
            mmr_results[str(lambda_value)] = {
                "candidate_pool": POOL,
                "top_k": {str(k): _metrics(reranked, k) for k in TOP_K},
            }

        top5_order_mismatches = []
        top10_candidate_mismatches = []
        for item in QUERIES:
            expected = [row["chunk_id"] for row in index.search(item["query"], limit=POOL)]
            actual = [row["chunk_id"] for row in rankings["current"][item["id"]][:POOL]]
            if expected[:5] != actual[:5]:
                top5_order_mismatches.append(item["id"])
            if set(expected) != set(actual):
                top10_candidate_mismatches.append(item["id"])

        route = asyncio.run(_route_results(path))
        return {
            "embedding_model": DEFAULT_LOCAL_MODEL,
            "embedding_dimensions": 384,
            "chunk_words": 120,
            "overlap_words": 20,
            "corpus_chunks": stats["chunks"],
            "query_count": len(QUERIES),
            "multi_document_query_count": sum(len(item["expected_prefixes"]) > 1 for item in QUERIES),
            "minimum_evidence_score": MINIMUM_EVIDENCE_SCORE,
            "top_k_values": list(TOP_K),
            "ranking_weights": weight_results,
            "mmr_comparison": mmr_results,
            "actual_route": route,
            "baseline_top5_order_mismatch_ids": top5_order_mismatches,
            "baseline_top10_candidate_set_mismatch_ids": top10_candidate_mismatches,
            "methodology": [
                "Retrieval comparison and read-only route verification; MiniLM 384d and 120/20 chunks are fixed.",
                "Weight variants rescore every chunk using the production cosine, lexical overlap, title-hit, and exact-phrase components.",
                "MMR reranks the production-score top 10 using chunk-to-chunk embedding cosine; lambda controls relevance versus diversity.",
                "Actual orchestrator routing is exercised only on policy questions; execution aborts if any tool besides policy search is selected.",
                "The route searches the top three results per selected family, seeds one result per family, then MMR-reranks up to ten candidates to five at lambda 0.5.",
                "Expected family labels are hand-authored and do not constitute independent semantic answer judgments.",
            ],
        }


def to_markdown(report: dict[str, Any]) -> str:
    names = {
        "current": "Current",
        "dense_only": "Dense only",
        "cosine_half": "Cosine 0.5x",
        "cosine_2x": "Cosine 2x",
        "lexical_2x": "Lexical 2x",
    }
    lines = [
        "# MiniLM Top-k, Routing, MMR, and Weight Comparison",
        "",
        "Retrieval-only experiment. MiniLM (384 dimensions), 120/20 chunks, corpus, and query labels are fixed. No pytest, LLM generation, employee lookups, or action tools are used.",
        "",
        f"Queries: {report['query_count']} total; {report['multi_document_query_count']} multi-family. Index chunks: {report['corpus_chunks']}.",
        "",
        f"Independent scoring matched production top-5 order on {report['query_count'] - len(report['baseline_top5_order_mismatch_ids'])}/{report['query_count']} queries and matched its top-10 candidate set on {report['query_count'] - len(report['baseline_top10_candidate_set_mismatch_ids'])}/{report['query_count']}.",
        "",
        "## Global top-k and ranking weights",
        "",
        "| Ranker | k | Hit@k | Family recall@k | All-family coverage@k | Multi-family all-family@k | Unique docs | Unique sections |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for variant, block in report["ranking_weights"].items():
        for k in report["top_k_values"]:
            m = block["top_k"][str(k)]
            lines.append(
                f"| {names[variant]} | {k} | {m['hit_at_k']:.2f} | {m['family_recall_at_k']:.2f} | "
                f"{m['all_family_coverage_at_k']:.2f} | {m['multi_document_all_family_coverage_at_k']:.2f} | "
                f"{m['mean_unique_documents']:.2f} | {m['mean_unique_sections']:.2f} |"
            )
    lines += [
        "",
        "## MMR",
        "",
        "| Method | k | Hit@k | Family recall@k | All-family coverage@k | Multi-family all-family@k | Unique docs | Unique sections |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for lambda_value, block in report["mmr_comparison"].items():
        for k in report["top_k_values"]:
            m = block["top_k"][str(k)]
            lines.append(
                f"| MMR lambda={lambda_value}, top-10 pool | {k} | {m['hit_at_k']:.2f} | "
                f"{m['family_recall_at_k']:.2f} | {m['all_family_coverage_at_k']:.2f} | "
                f"{m['multi_document_all_family_coverage_at_k']:.2f} | "
                f"{m['mean_unique_documents']:.2f} | {m['mean_unique_sections']:.2f} |"
            )
    route = report["actual_route"]
    lines += [
        "",
        "## Current application route",
        "",
        f"Actual route coverage: expected families cited for {route['all_family_query_coverage']:.0%} of all queries and {route['multi_document_all_family_coverage']:.0%} of multi-family queries; expected-family recall {route['expected_family_recall']:.0%}. Runtime retrieval: {', '.join(route['retrieval_methods']) or 'not reported'}.",
        "",
        "| Query | Expected families | Actual filters | Cited documents | Complete | Status |",
        "|---|---|---|---|---|---|",
    ]
    for row in route["queries"]:
        filters = ", ".join(prefix or "global" for prefix in row["selected_prefixes"])
        lines.append(
            f"| {row['id']} | {', '.join(row['expected_prefixes'])} | {filters} | "
            f"{', '.join(row['citation_ids']) or 'none'} | "
            f"{'yes' if row['all_expected_families_cited'] else 'no'} | {row['status']} |"
        )
    policy_slice = route["read_only_golden_policy_subset"]
    lines += [
        "",
        "## Read-only golden policy slice",
        "",
        f"{policy_slice['item_count']} policy QA cases were evaluated with the same rubric, separately from workflow/action cases: status accuracy {policy_slice['status_accuracy']:.0%}, citation-prefix accuracy {policy_slice['citation_prefix_accuracy']:.0%}, groundedness proxy {policy_slice['groundedness_proxy']:.0%}.",
        "",
        "| Golden item | Status | Citation IDs | Citation pass | Keyword score | Groundedness pass |",
        "|---|---|---|---|---:|---|",
    ]
    for row in policy_slice["items"]:
        lines.append(
            f"| {row['id']} | {row['status']} ({'yes' if row['status_pass'] else 'no'}) | "
            f"{', '.join(row['citation_ids']) or 'none'} | "
            f"{'yes' if row['citation_accuracy_pass'] else 'no'} | {row['keyword_score']:.2f} | "
            f"{'yes' if row['groundedness_pass'] else 'no'} |"
        )
    lines += [
        "",
        "## Limits",
        "",
        "The hand-authored query set is small and its labels are not independent semantic judgments. Global MMR and score-weight comparisons are retrieval diagnostics, not answer-correctness judgments. Production now uses lambda 0.5 MMR over the score-ranked top ten, with one seed per explicitly routed family and a five-citation limit. Embedding, chunk size, and scoring weights remain unchanged. Reassess this choice on a larger independently reviewed query set and latency measurements.",
        "",
    ]
    return "\n".join(lines)


def write_svg(report: dict[str, Any], path: Path) -> None:
    width, height = 1000, 570
    left, top, chart_width, chart_height = 80, 145, 660, 300
    series = [
        ("Current", report["ranking_weights"]["current"]["top_k"], "#166b63"),
        ("Dense only", report["ranking_weights"]["dense_only"]["top_k"], "#4260a8"),
        ("MMR lambda 0.5", report["mmr_comparison"]["0.5"]["top_k"], "#a4511b"),
    ]
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Multi-family retrieval coverage by top-k</title>',
        '<desc id="desc">Line chart compares global complete expected-family retrieval for current ranking, dense-only ranking, and MMR lambda 0.5, with actual multi-family route coverage shown separately.</desc>',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        '<text x="80" y="48" font-family="Arial,sans-serif" font-size="23" font-weight="700" fill="#183044">Multi-family coverage by top-k</text>',
        '<text x="80" y="75" font-family="Arial,sans-serif" font-size="14" fill="#536474">Global retrieval coverage by k; fraction of five multi-family queries complete</text>',
        f"<text x='80' y='104' font-family='Arial,sans-serif' font-size='14' font-weight='700' fill='#166b63'>Production route: MMR λ=0.5 + family seeding; {report['actual_route']['multi_document_all_family_coverage']:.0%} multi-family coverage</text>",
    ]
    for tick in (0, 0.25, 0.5, 0.75, 1):
        y = top + chart_height * (1 - tick)
        svg.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + chart_width}" y2="{y:.1f}" stroke="#d9e1e7"/>')
        svg.append(f'<text x="{left - 14}" y="{y + 4:.1f}" text-anchor="end" font-family="Arial,sans-serif" font-size="12" fill="#536474">{tick:.0%}</text>')
    svg.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_height}" stroke="#71808c"/>')
    svg.append(f'<line x1="{left}" y1="{top + chart_height}" x2="{left + chart_width}" y2="{top + chart_height}" stroke="#71808c"/>')
    x_values = [left + chart_width * i / (len(TOP_K) - 1) for i in range(len(TOP_K))]
    for x, k in zip(x_values, TOP_K, strict=True):
        svg.append(f'<text x="{x:.1f}" y="{top + chart_height + 23}" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" fill="#536474">k={k}</text>')
    for label, data, color in series:
        points = []
        for x, k in zip(x_values, TOP_K, strict=True):
            value = data[str(k)]["multi_document_all_family_coverage_at_k"]
            y = top + chart_height * (1 - value)
            points.append((x, y, value))
        svg.append('<polyline fill="none" stroke="' + color + '" stroke-width="3" points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in points) + '"/>')
        for x, y, value in points:
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}"/>')
            svg.append(f'<text x="{x:.1f}" y="{y - 10:.1f}" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" fill="{color}">{value:.0%}</text>')
    for i, (label, _, color) in enumerate(series):
        y = 490 + i * 23
        svg.append(f'<line x1="85" y1="{y}" x2="112" y2="{y}" stroke="{color}" stroke-width="3"/>')
        svg.append(f'<text x="122" y="{y + 4}" font-family="Arial,sans-serif" font-size="13" fill="#263746">{label}</text>')
    svg += ['<text x="535" y="515" font-family="Arial,sans-serif" font-size="12" fill="#536474">MiniLM 384d, fixed 120/20 chunks</text>', "</svg>"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(svg) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default="evaluation/retrieval-comparison.json")
    parser.add_argument("--markdown", default="evaluation/retrieval-comparison.md")
    parser.add_argument("--svg", default="visuals/retrieval-comparison.svg")
    args = parser.parse_args()
    report = run()
    paths = [
        Path(value) if Path(value).is_absolute() else ROOT / value
        for value in (args.json, args.markdown, args.svg)
    ]
    json_path, markdown_path, svg_path = paths
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(to_markdown(report), encoding="utf-8")
    write_svg(report, svg_path)
    print(to_markdown(report))


if __name__ == "__main__":
    main()
