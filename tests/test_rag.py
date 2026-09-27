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


def test_search_returns_complete_chunk_text_for_composition_and_citations(
    tmp_path: Path, monkeypatch
) -> None:
    import rag.index as index_module

    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()
    policy_text = "remote " * 120
    (policy_dir / "policy.md").write_text(
        "---\ndocument_id: POL-TST-01\ntitle: Test policy\nestimated_pages: 1\n---\n"
        "# Test policy\n## Scope\n" + policy_text,
        encoding="utf-8",
    )
    monkeypatch.setattr(index_module, "POLICY_DIR", policy_dir)
    monkeypatch.setattr(index_module, "_local_embeddings", lambda texts, model: [[1.0, 0.0] for _ in texts])
    index = RagIndex(tmp_path / "rag.sqlite3")

    result = index.search("remote policy", limit=1)[0]

    assert len(result["snippet"]) > 650
    assert result["snippet"].endswith("remote")
    assert not result["snippet"].endswith("…")


def test_sqlite_document_browser_returns_rows_without_vectors(tmp_path: Path, monkeypatch) -> None:
    import rag.index as index_module

    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()
    (policy_dir / "policy.md").write_text(
        "---\ndocument_id: POL-TST-01\ntitle: Test policy\nestimated_pages: 1\n---\n"
        "# Test policy\n## Scope\nA remote-work rule with evidence.",
        encoding="utf-8",
    )
    monkeypatch.setattr(index_module, "POLICY_DIR", policy_dir)
    monkeypatch.setattr(index_module, "_local_embeddings", lambda texts, model: [[1.0, 0.0] for _ in texts])
    index = RagIndex(tmp_path / "rag.sqlite3")

    documents = index.list_documents()
    chunks = index.get_chunks("POL-TST-01", limit=5)

    assert documents == [
        {
            "document_id": "POL-TST-01",
            "title": "Test policy",
            "chunk_count": 1,
            "section_count": 1,
            "estimated_pages": 1.0,
        }
    ]
    assert chunks[0]["chunk_id"] == "POL-TST-01:scope:1"
    assert chunks[0]["snippet"] == "A remote-work rule with evidence."
    assert "vector_json" not in chunks[0]


def test_existing_sqlite_index_refreshes_when_policy_source_changes(
    tmp_path: Path, monkeypatch
) -> None:
    import rag.index as index_module

    policy_dir = tmp_path / "policies"
    policy_dir.mkdir()
    policy_path = policy_dir / "policy.md"
    source_prefix = (
        "---\ndocument_id: POL-TST-01\ntitle: Test policy\nestimated_pages: 1\n---\n"
        "# Test policy\n## Scope\n"
    )
    policy_path.write_text(source_prefix + "remote " * 100, encoding="utf-8")
    monkeypatch.setattr(index_module, "POLICY_DIR", policy_dir)
    monkeypatch.setattr(
        index_module,
        "_local_embeddings",
        lambda texts, model: [[1.0, 0.0] for _ in texts],
    )

    index = RagIndex(tmp_path / "rag.sqlite3")
    initial = index.ensure()
    assert initial["chunks"] == 1

    policy_path.write_text(source_prefix + "remote " * 150, encoding="utf-8")

    refreshed = index.ensure()

    assert refreshed["chunks"] == 2
    assert refreshed["documents"] == 1


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
