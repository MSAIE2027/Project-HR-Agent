from __future__ import annotations

import asyncio
import json
from pathlib import Path

from agent.orchestrator import MSAIEOrchestrator
from evaluation.run_ablation import QUERIES, to_markdown as ablation_markdown
from evaluation.run_evaluation import (
    LATENCY_SAMPLE_IDS,
    _nearest_rank_percentile,
    evaluate_item,
    evaluation_failures,
    markdown,
    run,
    summarize_results,
)
from mcp_client.client import MCPGateway
from rag.index import HF_EMBEDDING_BACKEND, HF_EMBEDDING_REVISION


def test_golden_set_evaluation_thresholds() -> None:
    report = asyncio.run(run("inprocess"))
    summary = report["summary"]
    failed_grounding = [item for item in report["results"] if not item["groundedness_pass"]]
    for item in failed_grounding:
        print(
            "GROUNDING_REVIEW "
            f"id={item['id']} status={item['actual_status']} "
            f"keyword={item['keyword_score']} citation={item['citation_accuracy_pass']}"
        )
    assert summary["items"] >= 20
    assert summary["groundedness_proxy"] >= 0.9, [item["id"] for item in failed_grounding]
    assert summary["citation_prefix_accuracy"] >= 0.9
    assert summary["exact_tool_sequence_accuracy"] >= 0.9
    assert summary["workflow_completion_rate"] >= 0.9
    assert summary["action_safety_pass_rate"] == 1.0
    assert summary["latency_sample_count"] == len(LATENCY_SAMPLE_IDS)
    assert 10 <= summary["latency_sample_count"] <= 20
    assert summary["latency_ms_priming_request"] > 0
    assert summary["embedding_backend"] == HF_EMBEDDING_BACKEND
    assert summary["embedding_revision"] == HF_EMBEDDING_REVISION


def test_latency_percentiles_use_nearest_rank() -> None:
    assert _nearest_rank_percentile([1, 2, 3, 4, 5], 0.50) == 3
    assert _nearest_rank_percentile([1, 2, 3, 4, 5], 0.95) == 5


def test_evaluation_threshold_regression_is_reported_for_ci_gate() -> None:
    report = {
        "summary": {
            "items": 25,
            "groundedness_proxy": 1.0,
            "citation_prefix_accuracy": 1.0,
            "exact_tool_sequence_accuracy": 1.0,
            "workflow_completion_rate": 1.0,
            "clarification_escalation_accuracy": 1.0,
            "action_safety_pass_rate": 1.0,
            "status_accuracy": 1.0,
            "latency_sample_count": 15,
        },
        "results": [],
    }

    assert evaluation_failures(report) == []

    report["summary"]["action_safety_pass_rate"] = 0.99

    assert evaluation_failures(report) == ["action_safety_pass_rate must equal 1.0; got 0.99"]


def test_evaluation_case_failure_blocks_ci_even_above_aggregate_thresholds() -> None:
    report = {
        "summary": {
            "items": 25,
            "groundedness_proxy": 1.0,
            "citation_prefix_accuracy": 1.0,
            "exact_tool_sequence_accuracy": 0.96,
            "workflow_completion_rate": 1.0,
            "clarification_escalation_accuracy": 1.0,
            "action_safety_pass_rate": 1.0,
            "status_accuracy": 1.0,
            "latency_sample_count": 15,
        },
        "results": [
            {
                "id": "POL-05",
                "status_pass": True,
                "tool_selection_pass": False,
                "citation_accuracy_pass": True,
                "groundedness_pass": True,
                "clarification_escalation_pass": True,
                "action_safety_pass": True,
            }
        ],
    }

    assert evaluation_failures(report) == ["POL-05: tool_selection_pass failed"]


def test_ablation_summary_describes_current_corpus_and_reports_no_stale_counts() -> None:
    metrics = {
        "hit_at_1": 1.0,
        "hit_at_3": 1.0,
        "hit_at_5": 1.0,
        "family_recall_at_5": 0.7619,
        "family_mrr": 0.7488,
        "all_family_coverage_at_5": 0.7333,
        "multi_document_all_family_coverage_at_5": 0.2,
        "filtered_all_family_coverage_at_5": 1.0,
        "filtered_family_score_coverage": 1.0,
        "mean_unique_documents_top5": 1.267,
        "mean_unique_sections_top5": 5.0,
        "index_bytes": 1792208,
        "search_ms_p50": 16.871,
        "search_ms_p95": 75.087,
        "build_seconds_warm": 3.527,
    }
    configurations = [
        {
            "chunk_words": chunk_words,
            "overlap_words": overlap_words,
            "metrics": metrics,
            "index": {"chunks": 182, "documents": 14, "estimated_pages": 37.5},
        }
        for chunk_words, overlap_words in ((120, 20), (160, 24), (220, 30))
    ]
    report = {
        "query_count": 15,
        "multi_document_query_count": 5,
        "corpus_document_count": 14,
        "corpus_word_count": 15034,
        "corpus_page_equivalents_400_words": 37.6,
        "configurations": configurations,
        "selected_configuration": configurations[0],
    }

    rendered = ablation_markdown(report)

    assert "15,034 parsed policy-text words" in rendered
    assert "182 chunks" in rendered
    assert "1/5 (0.20)" in rendered
    assert "126 chunks" not in rendered
    assert "Only the international remote-work plus security route currently exists" not in rendered


def test_workflow_completion_excludes_lookups_and_missing_records() -> None:
    def scored_result(category: str, status_pass: bool, latency_ms: float) -> dict:
        return {
            "category": category,
            "id": category,
            "actual_status": "completed",
            "actual_tools": [],
            "citation_ids": [],
            "status_pass": status_pass,
            "latency_sample": True,
            "latency_ms": latency_ms,
            "groundedness_pass": True,
            "citation_accuracy_pass": True,
            "tool_selection_pass": True,
            "clarification_escalation_pass": True,
            "action_safety_pass": True,
            "keyword_score": 1.0,
        }

    results = [scored_result("policy_qa", True, float(i)) for i in range(15)]
    results[0] = scored_result("workflow", True, 1.0)
    results[1] = scored_result("structured_lookup", False, 2.0)
    results[2] = scored_result("missing_record", False, 3.0)

    summary = summarize_results(results, transport="inprocess", priming_request_ms=1.0)

    assert summary["workflow_case_count"] == 1
    assert summary["workflow_completion_rate"] == 1.0
    assert summary["llm_generation_included"] is False
    assert summary["embedding_backend"] is None
    assert "OpenRouter answer generation included | No; orchestrator-level evaluation" in markdown(
        {"summary": summary, "results": results}
    )


def test_multi_document_item_requires_both_policy_families() -> None:
    golden_path = Path(__file__).resolve().parents[1] / "evaluation" / "golden_set.json"
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    item = next(result for result in golden if result["id"] == "POL-04")

    async def evaluate_policy_only() -> dict:
        orchestrator = MSAIEOrchestrator(MCPGateway("inprocess"))
        return await evaluate_item(orchestrator, item)

    result = asyncio.run(evaluate_policy_only())

    assert result["expected_tools"] == ["search_policy_documents", "search_policy_documents"]
    assert result["actual_tools"] == result["expected_tools"]
    assert any(document_id.startswith("POL-RW-") for document_id in result["citation_ids"])
    assert any(document_id.startswith("POL-SEC-") for document_id in result["citation_ids"])
    assert result["citation_accuracy_pass"] is True


def test_read_only_multifamily_queries_cite_each_requested_policy_family() -> None:
    async def retrieve_all():
        orchestrator = MSAIEOrchestrator(MCPGateway("inprocess"))
        results = []
        for item in QUERIES:
            if len(item["expected_prefixes"]) < 2:
                continue
            result = await orchestrator.handle(item["query"], confirm_action=False)
            calls = [row for row in result.trace if row.get("event") == "tool_call"]
            assert calls and all(row["tool"] == "search_policy_documents" for row in calls)
            results.append((item, result))
        return results

    for item, result in asyncio.run(retrieve_all()):
        cited_ids = [citation["document_id"] for citation in result.citations]
        assert all(
            any(document_id.startswith(prefix) for document_id in cited_ids)
            for prefix in item["expected_prefixes"]
        ), item["id"]
