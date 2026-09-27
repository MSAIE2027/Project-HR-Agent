from __future__ import annotations

from pathlib import Path

import rag.index as index_module
from rag.index import HASH_MODEL, RagIndex


def _semantic_vectors(texts: list[str], config: dict[str, str]) -> list[list[float]]:
    vectors: list[list[float]] = []
    for text in texts:
        lowered = text.lower()
        if "can i work overseas" in lowered or "rolling twelve-month period" in lowered:
            vectors.append([1.0, 0.0, 0.0])
        elif "benefit" in lowered or "medical" in lowered:
            vectors.append([0.0, 1.0, 0.0])
        else:
            vectors.append([0.0, 0.0, 1.0])
    return vectors


def test_remote_embedding_provider_builds_dense_index(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MSAIE_EMBEDDING_PROVIDER", "openrouter")
    monkeypatch.setenv("MSAIE_EMBEDDING_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("MSAIE_EMBEDDING_API_KEY", "test-key-not-real")
    monkeypatch.setenv("MSAIE_EMBEDDING_MODEL", "test/semantic-embedding-model")
    monkeypatch.setattr(index_module, "_remote_embeddings", _semantic_vectors)

    index = RagIndex(tmp_path / "semantic.sqlite3")
    stats = index.build(force=True)

    assert stats["semantic_embeddings"] is True
    assert stats["embedding_provider"] == "openrouter"
    assert stats["embedding_model"] == "test/semantic-embedding-model"
    assert stats["dimensions"] == 3
    results = index.search("Can I work overseas?", limit=3)
    assert results
    assert results[0]["document_id"].startswith("POL-RW-")


def test_embedding_failure_falls_back_without_rebuild_loop(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MSAIE_EMBEDDING_PROVIDER", "openrouter")
    monkeypatch.setenv("MSAIE_EMBEDDING_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("MSAIE_EMBEDDING_API_KEY", "test-key-not-real")
    monkeypatch.setenv("MSAIE_EMBEDDING_MODEL", "test/unavailable-model")

    def fail(texts: list[str], config: dict[str, str]) -> list[list[float]]:
        raise RuntimeError("simulated provider outage")

    monkeypatch.setattr(index_module, "_remote_embeddings", fail)
    index = RagIndex(tmp_path / "fallback.sqlite3")
    first = index.build(force=True)
    second = index.ensure()

    assert first["semantic_embeddings"] is False
    assert first["embedding_model"] == HASH_MODEL
    assert first["embedding_provider"] == "local-hashing-fallback"
    assert first["requested_embedding_model"] == "test/unavailable-model"
    assert "simulated provider outage" in str(first["embedding_error"])
    assert second["requested_embedding_model"] == "test/unavailable-model"
