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


def test_local_huggingface_index_records_pinned_quantized_backend(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MSAIE_EMBEDDING_PROVIDER", "huggingface")
    monkeypatch.setenv("MSAIE_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    monkeypatch.delenv("MSAIE_EMBEDDING_BASE_URL", raising=False)
    monkeypatch.delenv("MSAIE_EMBEDDING_API_KEY", raising=False)
    monkeypatch.setattr(index_module, "_local_embeddings", lambda texts, model: _semantic_vectors(texts, {}))

    index = RagIndex(tmp_path / "hf-onnx.sqlite3")
    stats = index.build(force=True)

    assert stats["embedding_provider"] == "huggingface"
    assert stats["embedding_backend"] == "onnxruntime-quint8-avx2"
    assert stats["embedding_revision"] == "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
    assert stats["embedding_model"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert stats["dimensions"] == 3
    results = index.search("Can I work overseas?", limit=3)
    assert results
    assert results[0]["document_id"].startswith("POL-RW-")


def test_local_index_rebuilds_when_pinned_embedding_revision_changes(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MSAIE_EMBEDDING_PROVIDER", "huggingface")
    monkeypatch.setenv("MSAIE_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    monkeypatch.delenv("MSAIE_EMBEDDING_BASE_URL", raising=False)
    monkeypatch.delenv("MSAIE_EMBEDDING_API_KEY", raising=False)
    import numpy as np

    loaded_revisions: list[str] = []

    class FakeEmbedder:
        def __init__(self, model_name: str, revision: str) -> None:
            assert model_name == "sentence-transformers/all-MiniLM-L6-v2"
            loaded_revisions.append(revision)

        def encode(self, texts: list[str], **_kwargs) -> np.ndarray:
            return np.tile(np.array([[1.0, 0.0, 0.0]], dtype=np.float32), (len(texts), 1))

    monkeypatch.setattr(index_module, "HuggingFaceOnnxEmbedder", FakeEmbedder)
    index_module._local_embedding_model.cache_clear()
    index = RagIndex(tmp_path / "hf-revision.sqlite3")

    first = index.build(force=True)
    monkeypatch.setattr(index_module, "HF_EMBEDDING_REVISION", "b" * 40, raising=False)
    second = index.build()
    index_module._local_embedding_model.cache_clear()

    assert first["embedding_revision"] == "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
    assert second["embedding_revision"] == "b" * 40
    assert loaded_revisions == ["1110a243fdf4706b3f48f1d95db1a4f5529b4d41", "b" * 40]


def test_local_index_rejects_unsupported_huggingface_model_without_downloading(
    monkeypatch, tmp_path: Path
) -> None:
    import huggingface_hub

    monkeypatch.setenv("MSAIE_EMBEDDING_PROVIDER", "huggingface")
    monkeypatch.setenv("MSAIE_EMBEDDING_MODEL", "example/unsupported-model")
    monkeypatch.delenv("MSAIE_EMBEDDING_BASE_URL", raising=False)
    monkeypatch.delenv("MSAIE_EMBEDDING_API_KEY", raising=False)

    def no_download(*args, **kwargs):
        raise AssertionError("unsupported model should be rejected before download")

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", no_download)

    index = RagIndex(tmp_path / "unsupported-hf.sqlite3")
    stats = index.build(force=True)

    assert stats["embedding_provider"] == "local-hashing-fallback"
    assert stats["embedding_backend"] == "sparse-hash"
    assert stats["requested_embedding_model"] == "example/unsupported-model"
    assert "supports only" in str(stats["embedding_error"])
