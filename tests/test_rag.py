from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from rag.index import RagIndex
from rag.ingest import load_policy_sections


def test_multi_format_policy_loader() -> None:
    policy_dir = Path(__file__).resolve().parents[1] / "policies"
    sections = load_policy_sections(policy_dir)
    assert len({section.document_id for section in sections}) == 14
    assert any(section.source_path.endswith(".md") for section in sections)
    assert any(section.source_path.endswith(".html") for section in sections)
    assert sum(section.estimated_pages for section in {section.document_id: section for section in sections}.values()) >= 30


def test_persistent_index_and_citation_metadata(tmp_path: Path) -> None:
    index = RagIndex(tmp_path / "rag.sqlite3")
    stats = index.build(force=True)
    assert stats["documents"] == 14
    assert stats["chunks"] > 40
    results = index.search("international remote work rolling limit immigration", limit=3)
    assert results
    assert results[0]["document_id"].startswith("POL-RW-")
    assert results[0]["source_path"]
    assert results[0]["section"]
    assert results[0]["snippet"]


def test_mmr_reranking_preserves_relevance_and_reduces_redundancy(tmp_path: Path) -> None:
    index_path = tmp_path / "rerank.sqlite3"
    with sqlite3.connect(index_path) as connection:
        connection.execute("CREATE TABLE chunks (chunk_id TEXT, vector_json TEXT)")
        connection.executemany(
            "INSERT INTO chunks (chunk_id, vector_json) VALUES (?, ?)",
            [
                ("best", json.dumps([1.0, 0.0])),
                ("near-duplicate", json.dumps([0.99, 0.1])),
                ("diverse", json.dumps([0.0, 1.0])),
            ],
        )
    index = RagIndex(index_path)
    candidates = [
        {"chunk_id": "best", "score": 0.9},
        {"chunk_id": "near-duplicate", "score": 0.8},
        {"chunk_id": "diverse", "score": 0.7},
    ]

    selected = index.rerank_mmr(candidates, limit=3, lambda_value=0.5)

    assert [item["chunk_id"] for item in selected] == ["best", "diverse", "near-duplicate"]
