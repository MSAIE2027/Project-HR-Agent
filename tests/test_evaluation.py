from __future__ import annotations

import asyncio
import json
from pathlib import Path

from agent.orchestrator import MSAIEOrchestrator
from evaluation.run_ablation import QUERIES
from evaluation.run_evaluation import LATENCY_SAMPLE_IDS, evaluate_item, run
from mcp_client.client import MCPGateway


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
